import asyncio
import re
import logging
import configparser
import argparse
import json
import sys
import warnings
from datetime import datetime, timezone, timedelta
from getpass import getpass
from telethon import TelegramClient
from telethon.errors.rpcerrorlist import SessionPasswordNeededError
from telethon.tl.functions.messages import SearchGlobalRequest
from telethon.tl.types import InputPeerEmpty, InputMessagesFilterEmpty
from telethon import events

# --- Configuration ---
SESSION_NAME = 'anon' 

# --- Setup ---
warnings.filterwarnings("ignore", message="The session already had an authorized user.*")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# --- JSON Filtering ---
PROFILES = {}

def load_profiles():
    """Loads the filtering profiles from profiles.json."""
    global PROFILES
    try:
        with open('profiles.json', 'r') as f:
            PROFILES = json.load(f)
        logger.info("Successfully loaded filtering profiles.")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not load profiles.json: {e}. Using default empty filters.")
        PROFILES = {}

def apply_message_filters(message, args):
    """Apply command-line filters to a message."""
    # Incoming/outgoing filter
    if args.incoming_only and message.get('out', False):
        return False
    if args.outgoing_only and not message.get('out', False):
        return False
    
    # From user filter
    if args.from_user:
        from_id = message.get('from_id', {})
        if isinstance(from_id, dict):
            user_id = from_id.get('user_id')
            if user_id:
                # Try to match both by ID and potentially by username (would need resolution)
                try:
                    if str(user_id) != str(args.from_user):
                        return False
                except:
                    return False
            else:
                return False
    
    # Pattern filter (regex on message text)
    if args.pattern:
        message_text = message.get('message', '')
        if not re.search(args.pattern, message_text, re.IGNORECASE):
            return False
    
    # Media filter
    if args.has_media and not message.get('media'):
        return False
    
    # Forwarded messages filter
    if args.forwarded_only and not message.get('fwd_from'):
        return False
    
    # Reply messages filter
    if args.replies_only and not message.get('reply_to'):
        return False
    
    # Reactions filter
    if args.has_reactions and not message.get('reactions'):
        return False
    
    return True

def cleanup_json(obj, profile_name="default"):
    """Recursively removes empty values and keys based on the selected profile."""
    profile = PROFILES.get(profile_name, {})
    stop_keys = profile.get("stop_keys", [])
    stop_objects = profile.get("stop_objects", [])

    if isinstance(obj, dict):
        if obj.get('_') in stop_objects:
            return None
        # Process and filter the dictionary
        cleaned_dict = {}
        for k, v in obj.items():
            if k in stop_keys:
                continue
            cleaned_v = cleanup_json(v, profile_name)
            if cleaned_v not in [None, False, "", []]:
                cleaned_dict[k] = cleaned_v
        return cleaned_dict if cleaned_dict else None
    elif isinstance(obj, list):
        # Process and filter the list
        cleaned_list = [cleanup_json(elem, profile_name) for elem in obj]
        return [elem for elem in cleaned_list if elem not in [None, False, "", []]]
    return obj

# --- Core Functions ---
async def get_updates(client, chat, from_id, limit, args):
    """Fetches and prints messages from a chat."""
    if not limit and not from_id:
        limit = 20
        logger.info(f"No --limit or --from-id specified. Fetching the last {limit} messages by default.")

    if limit:
        logger.info(f"Fetching the last {limit} messages from '{chat}'.")
    elif from_id:
        logger.info(f"Fetching messages from '{chat}' older than message ID {from_id}.")
    else:
        # When no limit or from_id is specified, telethon has a default limit.
        logger.info(f"Fetching the most recent messages from '{chat}'.")

    try:
        messages_list = []
        # Fetch messages (newest to oldest by default)
        kwargs = {}
        if limit:
            kwargs['limit'] = limit
        if from_id:
            kwargs['offset_id'] = from_id
        async for message in client.iter_messages(chat, **kwargs):
            messages_list.append(message)
        
        if not messages_list:
            if from_id:
                logger.warning(f"No messages found starting from ID {from_id}. This might indicate:")
                logger.warning("1. The message ID doesn't exist in this chat")
                logger.warning("2. The chat was migrated to a channel (old message IDs become invalid)")
                logger.warning("3. All messages from that ID are older than available history")
            print("[]")
            return

        # The ID for the next page is the ID of the OLDEST message from this batch.
        # Since we fetched newest-to-oldest, the oldest is the last one in the list.
        next_from_id = messages_list[-1].id
        
        messages_json = []
        # Reverse the list to process and print in chronological order (oldest to newest)
        for message in reversed(messages_list):
            message_dict = json.loads(message.to_json())
            
            # Apply command-line filters
            if not apply_message_filters(message_dict, args):
                continue
                
            cleaned_msg = cleanup_json(message_dict, args.profile)
            if cleaned_msg:
                messages_json.append(cleaned_msg)
        
        print(json.dumps(messages_json, indent=2, ensure_ascii=False))
        print(f"\n# Next --from-id value to use: {next_from_id}")

    except Exception as e:
        logger.error(f"An error occurred during get_updates: {e}")

async def send_message(client, chat, text=None, files=None, reply_to=None):
    """Send a message with optional files and reply."""
    import os
    
    if files:
        # Check if files exist
        valid_files = []
        for file_path in files:
            if os.path.exists(file_path):
                valid_files.append(file_path)
                logger.info(f"Found file: {file_path}")
            else:
                logger.error(f"File not found: {file_path}")
        
        if not valid_files:
            logger.error("No valid files found to send.")
            return
        
        if len(valid_files) == 1:
            # Single file
            logger.info(f"Sending file '{valid_files[0]}' to '{chat}'" + (f" as reply to {reply_to}" if reply_to else ""))
            await client.send_file(chat, valid_files[0], caption=text or "", reply_to=reply_to)
        else:
            # Multiple files
            logger.info(f"Sending {len(valid_files)} files to '{chat}'" + (f" as reply to {reply_to}" if reply_to else ""))
            await client.send_file(chat, valid_files, caption=text or "", reply_to=reply_to)
    else:
        # Text-only message
        if not text:
            logger.error("No text or files provided to send.")
            return
        logger.info(f"Sending message to '{chat}': {text}" + (f" as reply to {reply_to}" if reply_to else ""))
        await client.send_message(chat, text, reply_to=reply_to)
    
    logger.info("Message sent successfully.")

async def add_reaction(client, chat, message_id, reaction):
    """Add a reaction to a message."""
    from telethon.tl.functions.messages import SendReactionRequest
    from telethon.tl.types import ReactionEmoji
    
    try:
        logger.info(f"Adding reaction '{reaction}' to message {message_id} in '{chat}'.")
        
        # Create reaction object
        reaction_obj = ReactionEmoji(emoticon=reaction)
        
        # Send reaction
        await client(SendReactionRequest(
            peer=chat,
            msg_id=message_id,
            reaction=[reaction_obj]
        ))
        
        logger.info(f"Successfully added reaction '{reaction}' to message {message_id}.")
    except Exception as e:
        logger.error(f"Failed to add reaction: {e}")

async def click_button(client, chat, message_id, button_text):
    logger.info(f"Attempting to click button '{button_text}' on message {message_id} in '{chat}'.")
    message = await client.get_messages(chat, ids=message_id)
    if message and message.buttons:
        for row in message.buttons:
            for button in row:
                if button_text in button.text:
                    logger.info(f"Found button: '{button.text}', clicking.")
                    await button.click()
                    await asyncio.sleep(2)
                    return
    logger.error("Button not found or message has no buttons.")

async def download_file(client, chat, message_id):
    logger.info(f"Downloading file from message {message_id} in '{chat}'.")
    message = await client.get_messages(chat, ids=message_id)
    if message and message.file:
        path = await client.download_media(message)
        print(f"File downloaded to: {path}")
    else:
        logger.error("Message not found or has no file.")

async def list_chats(client, args):
    """Lists the most recent chats as raw JSON objects."""
    limit = args.limit or 100  # Default to 100 if no limit is provided
    logger.info(f"Fetching the {limit} most recent chats...")
    try:
        dialogs_json = []
        async for dialog in client.iter_dialogs(limit=limit):
            # The entity (User, Chat, Channel) is what can be converted to JSON
            entity_json = json.loads(dialog.entity.to_json()) if dialog.entity else None

            # We also want the last message, so we'll construct a new object
            dialog_obj = {
                'entity': entity_json,
                'last_message': json.loads(dialog.message.to_json()) if dialog.message else None,
                'name': dialog.name,
                'id': dialog.id
                # You can add other dialog properties here if needed, e.g., 'unread_count': dialog.unread_count
            }
            
            cleaned_dialog = cleanup_json(dialog_obj, args.profile)
            dialogs_json.append(cleaned_dialog)
        
        print(json.dumps(dialogs_json, indent=2, ensure_ascii=False))

    except Exception as e:
        logger.error(f"An error occurred while listing chats: {e}")


async def search_messages(client, query, args):
    """Searches for a text query across all chats in a single request."""
    logger.info(f"Searching for '{query}' across all chats...")
    try:
        # Make a single, global search request for the top 100 results
        results = await client(SearchGlobalRequest(
            q=query,
            limit=100,
            filter=InputMessagesFilterEmpty(),
            min_date=None,
            max_date=None,
            offset_rate=0,
            offset_peer=InputPeerEmpty(),
            offset_id=0
        ))

        # Create a map of all user/chat IDs to their objects for easy lookup
        entities = {entity.id: entity for entity in results.chats + results.users}
        
        # Group messages by their chat ID
        grouped_messages = {}
        for message in results.messages:
            chat_id = message.chat_id
            if chat_id:
                if chat_id not in grouped_messages:
                    grouped_messages[chat_id] = []
                
                cleaned_msg = cleanup_json(json.loads(message.to_json()), args.profile)
                if cleaned_msg:
                    grouped_messages[chat_id].append(cleaned_msg)

        # Print the grouped results
        if not grouped_messages:
            print("No results found.")
            return

        for chat_id, messages in sorted(grouped_messages.items()):
            entity = entities.get(chat_id)
            name = "Unknown Chat"
            if entity:
                name = getattr(entity, 'title', None)  # For channels/groups
                if not name:  # Fallback for users
                    first = getattr(entity, 'first_name', '') or ''
                    last = getattr(entity, 'last_name', '') or ''
                    name = (f"{first} {last}").strip()

            print(f"\n--- Results from Chat: '{name}' (ID: {chat_id}) ---")
            print(json.dumps(messages, indent=2, ensure_ascii=False))

    except Exception as e:
        logger.error(f"An error occurred during search: {e}")


# --- Real-time Event Handling ---

async def new_message_handler(event, args):
    """Event handler for new messages."""
    logger.info(f"New message received in chat {event.chat_id}")
    message_json = json.loads(event.message.to_json())
    
    # Apply command-line filters
    if not apply_message_filters(message_json, args):
        return
        
    cleaned_msg = cleanup_json(message_json, args.profile)
    if cleaned_msg:
        # We add a separator to make it clear where one message ends and another begins
        print(json.dumps(cleaned_msg, indent=2, ensure_ascii=False))

async def main():
    """Main function to connect and interact with Telegram."""
    parser = argparse.ArgumentParser(description="Telegram User Client CLI")
    # Add a mutually exclusive group to ensure --listen is used alone
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--listen', type=str, help='Listen for real-time messages from a specific chat ID or username.')
    group.add_argument('--listen-private', action='store_true', help='Listen for all incoming private messages.')
    group.add_argument('--listen-all', action='store_true', help='Listen for all incoming messages from every chat.')
    group.add_argument('--list-chats', action='store_true', help='List the 100 most recent chats.')
    group.add_argument('--search', type=str, help='Search for a text query across all chats.')
    
    parser.add_argument('--chat', type=str, help='Chat username or ID (for non-listening actions).')
    parser.add_argument('--fromId', type=int, help='Fetch messages older than this message ID.')
    parser.add_argument('--limit', type=int, help='Fetch a specific number of items (e.g., messages or chats).')
    parser.add_argument('--profile', type=str, default='default', help='Name of the filtering profile to apply to the output.')
    parser.add_argument('--sendMessage', type=str, help='Text of message to send.')
    parser.add_argument('--sendFiles', nargs='+', help='Files to send (photos, videos, documents). Can specify multiple files.')
    parser.add_argument('--replyTo', type=int, help='Message ID to reply to.')
    parser.add_argument('--clickButton', type=str, help='Text of button to click.')
    parser.add_argument('--messageId', type=int, help='Message ID for button click or download.')
    parser.add_argument('--download', action='store_true', help='Download file from message.')
    parser.add_argument('--addReaction', type=str, help='Add reaction (emoji) to a message specified by --messageId.')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging.')
    
    # Message filtering options
    parser.add_argument('--incoming-only', action='store_true', help='Filter only incoming messages.')
    parser.add_argument('--outgoing-only', action='store_true', help='Filter only outgoing messages.')
    parser.add_argument('--from-user', type=str, help='Filter messages from specific user ID or username.')
    parser.add_argument('--pattern', type=str, help='Filter messages matching regex pattern.')
    parser.add_argument('--has-media', action='store_true', help='Filter messages with media only.')
    parser.add_argument('--forwarded-only', action='store_true', help='Filter only forwarded messages.')
    parser.add_argument('--replies-only', action='store_true', help='Filter only reply messages.')
    parser.add_argument('--has-reactions', action='store_true', help='Filter messages with reactions only.')
    args = parser.parse_args()

    # If no arguments are provided, print help and exit.
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    # Validate mutually exclusive filter options
    if args.incoming_only and args.outgoing_only:
        logger.error("--incoming-only and --outgoing-only are mutually exclusive.")
        return

    if not args.debug:
        logger.setLevel(logging.WARNING)

    load_profiles() # Load the profiles at the start

    config = configparser.ConfigParser()
    config.read('config.ini')
    
    phone_number = config.get('telegram', 'phone_number', fallback=None)
    api_id_str = config.get('telegram', 'api_id', fallback=None)
    api_hash = config.get('telegram', 'api_hash', fallback=None)

    if not phone_number or phone_number == 'YOUR_PHONE_NUMBER_HERE':
        logger.error("Phone number not set in config.ini")
        return
    
    if not api_id_str or api_id_str == 'YOUR_API_ID_HERE' or not api_hash or api_hash == 'YOUR_API_HASH_HERE':
        logger.error("API ID or API Hash not set in config.ini")
        return
        
    try:
        api_id = int(api_id_str)
    except ValueError:
        logger.error("Invalid api_id in config.ini. It must be an integer.")
        return

    client = TelegramClient(SESSION_NAME, api_id, api_hash)
    
    # Convert chat to int if it's a numeric ID, especially for negative ones
    chat_entity = args.chat
    if chat_entity:
        try:
            chat_entity = int(chat_entity)
        except ValueError:
            pass  # It's a username, leave it as a string

    try:
        await client.connect()
        if not await client.is_user_authorized():
            logger.warning("User not authorized. Sending code request.")
            await client.send_code_request(phone_number)
            try:
                await client.sign_in(phone_number, getpass('Enter the code: '))
            except SessionPasswordNeededError:
                await client.sign_in(password=getpass('Enter your 2FA password: '))
            except Exception as e:
                logger.error(f"Failed to sign in: {e}")
                return

        if args.listen:
            listen_chat_entity = args.listen
            try:
                listen_chat_entity = int(listen_chat_entity)
            except ValueError:
                pass # It's a username
            
            logger.info(f"Listening for new messages in '{listen_chat_entity}'... Press Ctrl+C to stop.")
            # Register the handler
            client.add_event_handler(lambda event: new_message_handler(event, args), events.NewMessage(chats=listen_chat_entity))
            # Run until disconnected
            await client.run_until_disconnected()
        
        elif args.listen_private:
            logger.info("Listening for all incoming private messages... Press Ctrl+C to stop.")
            # Register the handler with a filter for incoming private messages
            client.add_event_handler(
                lambda event: new_message_handler(event, args),
                events.NewMessage(incoming=True, func=lambda e: e.is_private)
            )
            await client.run_until_disconnected()

        elif args.listen_all:
            logger.info("Listening for all incoming messages from every chat... Press Ctrl+C to stop.")
            # Register a handler for all messages without any filters
            client.add_event_handler(
                lambda event: new_message_handler(event, args),
                events.NewMessage()
            )
            await client.run_until_disconnected()

        elif args.list_chats:
            await list_chats(client, args)
        elif args.search:
            await search_messages(client, args.search, args)
        elif args.sendMessage or args.sendFiles:
            if not chat_entity:
                logger.error("--chat is required for sending messages or files.")
                return
            await send_message(client, chat_entity, args.sendMessage, args.sendFiles, args.replyTo)
        elif args.clickButton:
            if not chat_entity or not args.messageId:
                logger.error("--chat and --messageId are required for --clickButton.")
                return
            await click_button(client, chat_entity, args.messageId, args.clickButton)
        elif args.download:
            if not chat_entity or not args.messageId:
                logger.error("--chat and --messageId are required for --download.")
                return
            await download_file(client, chat_entity, args.messageId)
        elif args.addReaction:
            if not chat_entity or not args.messageId:
                logger.error("--chat and --messageId are required for --addReaction.")
                return
            await add_reaction(client, chat_entity, args.messageId, args.addReaction)
        else:
            if not chat_entity:
                # If no other action is specified, default to get_updates, which requires a chat
                logger.error("A --chat must be provided to fetch updates.")
                return

            await get_updates(client, chat_entity, args.fromId, args.limit, args)

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    finally:
        if client.is_connected():
            await client.disconnect()
            logger.info("Client disconnected.")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\nExiting gracefully.") 