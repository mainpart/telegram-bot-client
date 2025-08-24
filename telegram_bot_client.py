import asyncio
import re
import logging
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
from telethon.events import CallbackQuery
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.messages import GetFullChatRequest
import yaml
import aiohttp
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional

# --- Configuration ---
SESSION_NAME = 'anon'
SESSION_NAME_BOT = 'anon-bot'

# --- Setup ---
warnings.filterwarnings("ignore", message="The session already had an authorized user.*")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# --- JSON Filtering ---
PROFILES = {}

# --- Adapters ---
ADAPTERS = []

class BaseAdapter:
    async def init(self):
        return

    async def exec(self, message: dict):
        raise NotImplementedError

class StdoutAdapter(BaseAdapter):
    def __init__(self, config: dict):
        self.pretty = bool(config.get('pretty', True))

    async def exec(self, message: dict):
        try:
            if self.pretty:
                print(json.dumps(message, indent=2, ensure_ascii=False))
            else:
                print(json.dumps(message, ensure_ascii=False))
        except Exception as e:
            logger.error(f"StdoutAdapter error: {e}")

class HttpAdapter(BaseAdapter):
    def __init__(self, config: dict):
        self.url = config.get('url')
        self.method = (config.get('method') or 'POST').upper()
        self.headers = config.get('headers') or {}
        self.timeout_seconds = int(config.get('timeout', 10))
        self._session: Optional[aiohttp.ClientSession] = None

    async def init(self):
        timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
        self._session = aiohttp.ClientSession(timeout=timeout)

    async def exec(self, message: dict):
        if not self.url:
            logger.error("HttpAdapter: 'url' is required")
            return
        if not self._session:
            await self.init()
        try:
            async with self._session.request(self.method, self.url, json=message, headers=self.headers) as resp:
                # Optionally read response to release connection properly
                await resp.read()
                if resp.status >= 400:
                    logger.error(f"HttpAdapter failed with status {resp.status}")
        except Exception as e:
            logger.error(f"HttpAdapter error: {e}")

    async def close(self):
        if self._session:
            try:
                await self._session.close()
            except Exception as e:
                logger.error(f"HttpAdapter close error: {e}")
            finally:
                self._session = None

class MongoDBAdapter(BaseAdapter):
    def __init__(self, config: dict):
        self.uri = config.get('uri')
        self.database_name = config.get('database') or config.get('db')
        self.collection_name = config.get('collection') or 'messages'
        self._client: Optional[AsyncIOMotorClient] = None
        self._collection = None

    async def init(self):
        if not self.uri or not self.database_name:
            logger.error("MongoDBAdapter requires 'uri' and 'database'")
            return
        self._client = AsyncIOMotorClient(self.uri)
        db = self._client[self.database_name]
        self._collection = db[self.collection_name]

    async def exec(self, message: dict):
        if not self._collection:
            await self.init()
            if not self._collection:
                return
        try:
            await self._collection.insert_one(message)
        except Exception as e:
            logger.error(f"MongoDBAdapter error: {e}")

    async def close(self):
        try:
            if self._client:
                self._client.close()
        except Exception as e:
            logger.error(f"MongoDBAdapter close error: {e}")

async def _safe_adapter_exec(adapter: BaseAdapter, message: dict):
    try:
        await adapter.exec(message)
    except Exception as e:
        logger.error(f"Adapter {adapter.__class__.__name__} failed: {e}")

async def emit_message_to_adapters(message: dict):
    if not ADAPTERS:
        # Fallback to console if no adapters are configured
        print(json.dumps(message, indent=2, ensure_ascii=False))
        return
    await asyncio.gather(*[_safe_adapter_exec(a, message) for a in ADAPTERS], return_exceptions=True)

async def close_adapters():
    tasks = []
    for adapter in ADAPTERS:
        close_coro = getattr(adapter, 'close', None)
        if close_coro and callable(close_coro):
            tasks.append(close_coro())
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

def load_yaml_config(path: str = 'config.yaml') -> dict:
    try:
        with open(path, 'r') as f:
            data = yaml.safe_load(f) or {}
            return data
    except FileNotFoundError:
        logger.error(f"Config file '{path}' not found.")
    except Exception as e:
        logger.error(f"Failed to read YAML config '{path}': {e}")
    return {}

async def init_adapters_from_config(cfg: dict):
    global ADAPTERS
    ADAPTERS = []
    adapters_cfg = (cfg or {}).get('adapters') or []
    for entry in adapters_cfg:
        if not isinstance(entry, dict):
            continue
        if not entry.get('enabled', True):
            continue
        adapter_type = (entry.get('type') or '').lower()
        adapter = None
        if adapter_type == 'stdout':
            adapter = StdoutAdapter(entry)
        elif adapter_type == 'http':
            adapter = HttpAdapter(entry)
        elif adapter_type == 'mongodb':
            adapter = MongoDBAdapter(entry)
        else:
            logger.warning(f"Unknown adapter type: {adapter_type}")
            continue
        try:
            await adapter.init()
        except Exception as e:
            logger.error(f"Failed to init adapter {adapter_type}: {e}")
            continue
        ADAPTERS.append(adapter)

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
    # Normalize limit: 0 -> unlimited (None for Telethon), None -> default 20
    if limit is None:
        limit_effective = 20
        logger.info(f"No --limit specified. Using default limit {limit_effective}.")
    elif limit == 0:
        limit_effective = None
        logger.info("--limit 0 specified. Fetching without limit (may take a long time).")
    else:
        limit_effective = limit

    if from_id:
        if args.forward:
            if args.toId:
                logger.info(f"Fetching forward from {from_id} up to (excl) {args.toId} in '{chat}'.")
            else:
                logger.info(f"Fetching messages from '{chat}' forward (newer) starting after ID {from_id}.")
        elif args.backward or not (args.forward or args.backward):
            if args.toId:
                logger.info(f"Fetching backward from {from_id} down to (excl) {args.toId} in '{chat}'.")
            else:
                logger.info(f"Fetching messages from '{chat}' backward (older) starting before ID {from_id}.")
    else:
        if args.forward:
            logger.info(f"Fetching messages from '{chat}' forward from the beginning (oldest -> newest).")
        elif args.backward:
            logger.info(f"Fetching messages from '{chat}' backward from the end (newest -> oldest).")
        else:
            logger.info(f"Fetching messages from '{chat}' with default direction.")

    try:
        # Build fetch parameters
        kwargs = {}
        if limit_effective is not None:
            kwargs['limit'] = limit_effective
        # Decide direction: if both fromId and toId given, infer and override user flags if conflicting
        direction = None
        to_id = getattr(args, 'toId', None)
        if from_id is not None and to_id is not None and from_id != to_id:
            inferred = 'forward' if to_id > from_id else 'backward'
            if args.forward and inferred == 'backward':
                logger.warning("Direction overridden by range: using backward due to --fromId/--toId order.")
            if args.backward and inferred == 'forward':
                logger.warning("Direction overridden by range: using forward due to --fromId/--toId order.")
            direction = inferred
        else:
            if args.forward:
                direction = 'forward'
            elif args.backward:
                direction = 'backward'

        # Set reverse flag based on direction or default behaviour
        if direction == 'forward':
            kwargs['reverse'] = True
        elif direction == 'backward':
            kwargs['reverse'] = False
        else:
            # Default Telethon behaviour: newest -> oldest
            if args.forward:
                kwargs['reverse'] = True
            elif args.backward:
                kwargs['reverse'] = False

        # Compute range bounds respecting inclusivity
        inclusive = bool(getattr(args, 'inclusive', False))
        if kwargs.get('reverse', False):
            # forward: min_id (lower), max_id (upper), Telethon treats bounds as exclusive
            if from_id is not None:
                kwargs['min_id'] = max(0, from_id - 1) if inclusive else from_id
            if to_id is not None:
                kwargs['max_id'] = (to_id + 1) if inclusive else to_id
        else:
            # backward: max_id (upper), min_id (lower)
            if from_id is not None:
                kwargs['max_id'] = (from_id + 1) if inclusive else from_id
            if to_id is not None:
                kwargs['min_id'] = max(0, to_id - 1) if inclusive else to_id
        # If no from_id provided, keep Telethon defaults (newest -> oldest)
        printed_any = False
        async for message in client.iter_messages(chat, **kwargs):
            message_dict = json.loads(message.to_json())

            # Apply command-line filters
            if not apply_message_filters(message_dict, args):
                continue

            cleaned_msg = cleanup_json(message_dict, args.profile)
            if cleaned_msg:
                asyncio.create_task(emit_message_to_adapters(cleaned_msg))
                printed_any = True

        if not printed_any:
            if from_id:
                logger.warning(f"No messages found starting from ID {from_id}. This might indicate:")
                logger.warning("1. The message ID doesn't exist in this chat")
                logger.warning("2. The chat was migrated to a channel (old message IDs become invalid)")
                logger.warning("3. All messages from that ID are older than available history")
            print("[]")

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

async def forward_message(client, source_chat, message_id, target_chat):
    """Forward a message from source_chat to target_chat. Returns the forwarded message."""
    try:
        logger.info(f"Forwarding message {message_id} from '{source_chat}' to '{target_chat}'.")
        forwarded = await client.forward_messages(
            entity=target_chat,
            messages=message_id,
            from_peer=source_chat
        )
        logger.info("Successfully forwarded message.")
        return forwarded
    except Exception as e:
        logger.error(f"Failed to forward message: {e}")
        return None

async def _resolve_source_peer_via_message(client, chat_identifier, message_id):
    msg = await client.get_messages(chat_identifier, ids=message_id)
    if not msg:
        logger.error("Could not fetch source message to resolve source peer.")
        return None
    try:
        return await client.get_input_entity(msg.peer_id)
    except Exception as e:
        logger.error(f"Failed to resolve source peer from message: {e}")
        return None

async def _resolve_dest_peer(client, chat_identifier):
    try:
        return await client.get_input_entity(chat_identifier)
    except Exception as e:
        from telethon.tl.types import InputPeerChat
        if isinstance(chat_identifier, int):
            return InputPeerChat(chat_identifier)
        logger.error(f"Failed to resolve destination chat: {e}")
        return None

async def send_cross_chat_reply(client, chat, text=None, files=None, reply_to=None, source_chat=None):
    """Send a reply in another chat pointing to a message in source_chat.

    Parameters mirror send_message order for consistency:
    - chat: destination chat (target)
    - text: text to send
    - files: not supported for cross-chat replies
    - reply_to: source message id (required)
    - source_chat: source chat where reply_to message lives (required)
    """
    from telethon.tl.functions.messages import SendMessageRequest
    from telethon.tl.types import InputReplyToMessage
    if files:
        logger.error("Cross-chat reply with files is not supported in this mode.")
        return
    if source_chat is None or reply_to is None:
        logger.error("send_cross_chat_reply requires source_chat and reply_to (message id).")
        return
    # Resolve source peer deterministically via the message's peer id
    source_peer = await _resolve_source_peer_via_message(client, source_chat, reply_to)
    if not source_peer:
        return

    dest_peer = await _resolve_dest_peer(client, chat)
    if not dest_peer:
        return
    reply_to_obj = InputReplyToMessage(reply_to_peer_id=source_peer, reply_to_msg_id=reply_to)
    try:
        await client(SendMessageRequest(peer=dest_peer, message=text or "", reply_to=reply_to_obj))
        logger.info("Cross-chat reply sent successfully.")
    except Exception as e:
        logger.error(f"Failed to send cross-chat reply: {e}")

async def edit_message(client, chat, message_id, new_text):
    """Edit own message text or caption in a chat or channel."""
    try:
        logger.info(f"Editing message {message_id} in '{chat}'.")
        await client.edit_message(chat, message_id, new_text)
        logger.info(f"Successfully edited message {message_id}.")
    except Exception as e:
        logger.error(f"Failed to edit message: {e}")

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


# --- Entity Inspection ---
async def get_entities(client, identifiers, args):
	"""Fetch and print entities (users/chats/channels) and their full info."""
	results = []
	for ident in identifiers:
		lookup = ident
		# Try convert numeric IDs
		try:
			lookup = int(ident)
		except Exception:
			pass
		try:
			entity = await client.get_entity(lookup)
			entity_json = json.loads(entity.to_json())
			full = None
			# Try to enrich with full info depending on type
			etype = entity_json.get('_')
			if etype == 'User':
				try:
					full = await client(GetFullUserRequest(entity))
				except Exception:
					full = None
			elif etype == 'Channel':
				try:
					full = await client(GetFullChannelRequest(channel=entity))
				except Exception:
					full = None
			elif etype == 'Chat':
				try:
					full = await client(GetFullChatRequest(chat_id=entity.id))
				except Exception:
					full = None

			obj = {
				'entity': entity_json,
				'full': json.loads(full.to_json()) if full else None,
				'input': ident
			}
			cleaned = cleanup_json(obj, args.profile)
			results.append(cleaned)
		except Exception as e:
			results.append({'input': ident, 'error': str(e)})

	print(json.dumps(results, indent=2, ensure_ascii=False))

# --- Real-time Event Handling ---

async def message_event_handler(event, args):
    """Unified handler for new and edited messages."""
    try:
        kind = 'edited' if isinstance(event, events.MessageEdited.Event) else 'new'
        logger.info(f"Message {kind} in chat {event.chat_id}")
        message_json = json.loads(event.message.to_json())
        if not apply_message_filters(message_json, args):
            return
        cleaned_msg = cleanup_json(message_json, args.profile)
        if cleaned_msg:
            asyncio.create_task(emit_message_to_adapters(cleaned_msg))
    except Exception as e:
        logger.error(f"Error in message_event_handler: {e}")

async def callback_query_handler(event, args):
    """Event handler for inline keyboard button presses (callback queries)."""
    try:
        logger.info(f"Callback query in chat {event.chat_id} from user {getattr(event.sender_id, 'value', event.sender_id)}")
        # Try to fetch the related message to apply filters and include in payload
        msg = None
        try:
            await event.answer(cache_time=0)
            msg = await event.get_message()
        except Exception:
            msg = None

        if msg:
            message_json = json.loads(msg.to_json())
            cleaned_message = cleanup_json(message_json, args.profile)
        else:
            cleaned_message = None

        # Primary output: structured JSON akin to message output
        payload = {
            'type': 'callback_query',
            'id': getattr(event, 'id', None),
            'chat_id': getattr(event, 'chat_id', None),
            'message_id': getattr(event, 'message_id', None),
            'sender_id': getattr(event, 'sender_id', None),
            'chat_instance': getattr(event, 'chat_instance', None),
            'data': None
        }

        try:
            payload['data'] = event.data.decode('utf-8') if event.data else None
        except Exception:
            payload['data'] = str(getattr(event, 'data', None))

        if cleaned_message:
            payload['message'] = cleaned_message

        cleaned_payload = cleanup_json(payload, args.profile)
        if cleaned_payload:
            asyncio.create_task(emit_message_to_adapters(cleaned_payload))

    except Exception as e:
        logger.error(f"Error in callback_query_handler: {e}")

async def main():
    """Main function to connect and interact with Telegram."""
    parser = argparse.ArgumentParser(description="Telegram User/Bot Client CLI")
    # Add a mutually exclusive group to ensure --listen is used alone
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--listen', type=str, help='Listen for real-time messages from a specific chat ID or username.')
    group.add_argument('--listen-private', action='store_true', help='Listen for all incoming private messages.')
    group.add_argument('--listen-all', action='store_true', help='Listen for all incoming messages from every chat.')
    group.add_argument('--list-chats', action='store_true', help='List the 100 most recent chats.')
    group.add_argument('--search', type=str, help='Search for a text query across all chats.')
    
    parser.add_argument('--chat', type=str, help='Chat username or ID (for non-listening actions).')
    parser.add_argument('--fromId', type=int, help='Fetch messages older than this message ID.')
    parser.add_argument('--toId', type=int, help='Exclusive boundary message ID to stop before when reading a range.')
    parser.add_argument('--inclusive', action='store_true', help='Include boundary messages specified by --fromId/--toId in the range.')
    parser.add_argument('--limit', type=int, help='Fetch a specific number of items (e.g., messages or chats).')
    parser.add_argument('--profile', type=str, default='default', help='Name of the filtering profile to apply to the output.')
    parser.add_argument('--botToken', type=str, help='Bot token to run in bot mode (enables CallbackQuery handling).')
    parser.add_argument('--session', type=str, help='Optional custom session name/file to avoid sqlite locks when running multiple instances.')
    parser.add_argument('--forward', action='store_true', help='When used with --fromId, read newer messages (IDs greater than fromId).')
    parser.add_argument('--backward', action='store_true', help='When used with --fromId, read older messages (IDs less than fromId).')
    parser.add_argument('--sendMessage', type=str, help='Text of message to send (non-reply flow).')
    parser.add_argument('--sendFiles', nargs='+', help='Files to send (photos, videos, documents). Can specify multiple files.')
    parser.add_argument('--replyTo', type=int, help='Message ID to reply to.')
    parser.add_argument('--targetChat', type=str, help='Target chat for sending. With --replyTo, replies in target chat to message from --chat.')
    parser.add_argument('--clickButton', type=str, help='Text of button to click.')
    parser.add_argument('--messageId', type=int, help='Message ID for button click, download, forward, or reply.')
    parser.add_argument('--forwardMessage', action='store_true', help='Forward message: requires --chat, --messageId and --targetChat.')
    parser.add_argument('--replyMessage', type=str, help='Reply to --replyTo message ID. Requires text. With --targetChat replies there; else replies in --chat.')
    parser.add_argument('--download', action='store_true', help='Download file from message.')
    parser.add_argument('--addReaction', type=str, help='Add reaction (emoji) to a message specified by --messageId.')
    parser.add_argument('--editMessage', type=str, help='New text to replace the message text/caption for --messageId.')
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
    parser.add_argument('--get-entities', nargs='+', help='Fetch full info for users/chats/channels by ID or @username.')
    args = parser.parse_args()

    # If no arguments are provided, print help and exit.
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    # Validate mutually exclusive filter options
    if args.incoming_only and args.outgoing_only:
        logger.error("--incoming-only and --outgoing-only are mutually exclusive.")
        return

    # Validate directional options (allow forward/backward without fromId)
    if args.forward and args.backward:
        logger.error("--forward and --backward are mutually exclusive.")
        return

    if not args.debug:
        logger.setLevel(logging.WARNING)

    load_profiles() # Load the profiles at the start

    yaml_cfg = load_yaml_config('config.yaml')
    telegram_cfg = (yaml_cfg or {}).get('telegram') or {}
    api_id_str = str(telegram_cfg.get('api_id')) if telegram_cfg.get('api_id') is not None else None
    api_hash = telegram_cfg.get('api_hash')
    phone_number = telegram_cfg.get('phone_number')
    if phone_number is not None:
        phone_number = str(phone_number)

    if not api_id_str or api_id_str == 'YOUR_API_ID_HERE' or not api_hash or api_hash == 'YOUR_API_HASH_HERE':
        logger.error("API ID or API Hash not set in config.yaml")
        return
        
    try:
        api_id = int(api_id_str)
    except ValueError:
        logger.error("Invalid api_id in config.yaml. It must be an integer.")
        return

    # Use separate session files for user and bot, allow override via --session
    session_name = args.session or (SESSION_NAME_BOT if args.botToken else SESSION_NAME)
    client = TelegramClient(session_name, api_id, api_hash)
    
    # Convert chat to int if it's a numeric ID, especially for negative ones
    chat_entity = args.chat
    if chat_entity:
        try:
            chat_entity = int(chat_entity)
        except ValueError:
            pass  # It's a username, leave it as a string
    # Convert targetChat similarly
    target_chat_entity = args.targetChat
    if target_chat_entity:
        try:
            target_chat_entity = int(target_chat_entity)
        except ValueError:
            pass

    try:
        if args.botToken:
            # Bot mode: start handles connect+login
            await client.start(bot_token=args.botToken)
        else:
            # User mode: prefer start (connect+login+2FA)
            if not phone_number or phone_number == 'YOUR_PHONE_NUMBER_HERE':
                logger.error("Phone number not set in config.yaml")
                return
            try:
                await client.start(
                    phone=lambda: phone_number,
                    code_callback=lambda: getpass('Enter the code: '),
                    password=lambda: getpass('Enter your 2FA password: ')
                )
            except Exception as e:
                logger.error(f"Failed to start user session: {e}")
                return

        # Default action for pure bot mode: start listening to all updates
        if args.botToken and not any([
            args.listen, args.listen_private, args.listen_all,
            args.list_chats, args.search, args.sendMessage, args.sendFiles,
            args.clickButton, args.download, args.addReaction, args.chat, args.editMessage,
            args.forwardMessage, args.replyMessage,
            args.get_entities
        ]):
            logger.info("--botToken provided without an explicit action; defaulting to --listen-all.")
            args.listen_all = True

        # Initialize adapters once connected
        await init_adapters_from_config(yaml_cfg)

        if args.listen:
            listen_chat_entity = args.listen
            try:
                listen_chat_entity = int(listen_chat_entity)
            except ValueError:
                pass # It's a username
            
            logger.info(f"Listening for new messages in '{listen_chat_entity}'... Press Ctrl+C to stop.")
            # Register handlers
            client.add_event_handler(lambda event: message_event_handler(event, args), events.NewMessage(chats=listen_chat_entity))
            client.add_event_handler(lambda event: message_event_handler(event, args), events.MessageEdited(chats=listen_chat_entity))
            if args.botToken:
                client.add_event_handler(lambda event: callback_query_handler(event, args), CallbackQuery(chats=listen_chat_entity))
            # Run until disconnected
            await client.run_until_disconnected()
        
        elif args.listen_private:
            logger.info("Listening for all incoming private messages... Press Ctrl+C to stop.")
            # Register the handler with a filter for incoming private messages
            client.add_event_handler(
                lambda event: message_event_handler(event, args),
                events.NewMessage(incoming=True, func=lambda e: e.is_private)
            )
            client.add_event_handler(
                lambda event: message_event_handler(event, args),
                events.MessageEdited(func=lambda e: e.is_private)
            )
            if args.botToken:
                client.add_event_handler(
                    lambda event: callback_query_handler(event, args),
                    CallbackQuery(func=lambda e: e.is_private)
                )
            await client.run_until_disconnected()

        elif args.listen_all:
            logger.info("Listening for all incoming messages from every chat... Press Ctrl+C to stop.")
            # Register a handler for all messages without any filters
            client.add_event_handler(
                lambda event: message_event_handler(event, args),
                events.NewMessage()
            )
            client.add_event_handler(
                lambda event: message_event_handler(event, args),
                events.MessageEdited()
            )
            if args.botToken:
                client.add_event_handler(
                    lambda event: callback_query_handler(event, args),
                    CallbackQuery()
                )
            await client.run_until_disconnected()

        elif args.list_chats:
            await list_chats(client, args)
        elif args.search:
            await search_messages(client, args.search, args)
        elif args.get_entities:
            await get_entities(client, args.get_entities, args)
        elif args.forwardMessage:
            # Forward only
            if not (chat_entity and target_chat_entity and args.messageId):
                logger.error("--forwardMessage requires --chat, --messageId and --targetChat.")
                return
            await forward_message(client, chat_entity, args.messageId, target_chat_entity)
        elif args.replyMessage:
            if not (chat_entity and args.messageId):
                logger.error("--replyMessage requires --chat and --messageId.")
                return
            if target_chat_entity:
                if args.sendFiles:
                    logger.error("--replyMessage with --targetChat does not support files.")
                    return
                await send_cross_chat_reply(client, target_chat_entity, args.replyMessage, None, args.messageId, chat_entity)
            else:
                await send_message(client, chat_entity, args.replyMessage, args.sendFiles, args.messageId)
        elif args.sendMessage or args.sendFiles:
            # Plain send within chat (no targetChat allowed here)
            if not chat_entity:
                logger.error("--chat is required for --sendMessage/--sendFiles.")
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
        elif args.editMessage:
            if not chat_entity or not args.messageId:
                logger.error("--chat and --messageId are required for --editMessage.")
                return
            await edit_message(client, chat_entity, args.messageId, args.editMessage)
        else:
            if not chat_entity:
                # If no other action is specified, default to get_updates, which requires a chat
                logger.error("A --chat must be provided to fetch updates.")
                return

            await get_updates(client, chat_entity, args.fromId, args.limit, args)

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    finally:
        try:
            await close_adapters()
        except Exception as e:
            logger.error(f"Failed to close adapters: {e}")
        if client.is_connected():
            await client.disconnect()
            logger.info("Client disconnected.")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\nExiting gracefully.") 