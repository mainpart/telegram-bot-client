import asyncio
import json
import os
import logging
from telethon.tl.functions.messages import SearchGlobalRequest
from telethon.tl.functions.contacts import SearchRequest as ContactsSearchRequest
from telethon.tl.types import InputPeerEmpty, InputMessagesFilterEmpty
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.messages import GetFullChatRequest
from tg.core import logger, apply_message_filters, cleanup_json, emit_message_to_adapters

async def get_updates(client, chat, from_id, limit, args):
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
        kwargs = {}
        if limit_effective is not None:
            kwargs['limit'] = limit_effective
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

        if direction == 'forward':
            kwargs['reverse'] = True
        elif direction == 'backward':
            kwargs['reverse'] = False
        else:
            if args.forward:
                kwargs['reverse'] = True
            elif args.backward:
                kwargs['reverse'] = False

        inclusive = bool(getattr(args, 'inclusive', False))
        if kwargs.get('reverse', False):
            if from_id is not None:
                kwargs['min_id'] = max(0, from_id - 1) if inclusive else from_id
            if to_id is not None:
                kwargs['max_id'] = (to_id + 1) if inclusive else to_id
        else:
            if from_id is not None:
                kwargs['max_id'] = (from_id + 1) if inclusive else from_id
            if to_id is not None:
                kwargs['min_id'] = max(0, to_id - 1) if inclusive else to_id

        printed_any = False
        async for message in client.iter_messages(chat, **kwargs):
            message_dict = json.loads(message.to_json())
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
    if files:
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
            logger.info(f"Sending file '{valid_files[0]}' to '{chat}'" + (f" as reply to {reply_to}" if reply_to else ""))
            await client.send_file(chat, valid_files[0], caption=text or "", reply_to=reply_to)
        else:
            logger.info(f"Sending {len(valid_files)} files to '{chat}'" + (f" as reply to {reply_to}" if reply_to else ""))
            await client.send_file(chat, valid_files, caption=text or "", reply_to=reply_to)
    else:
        if not text:
            logger.error("No text or files provided to send.")
            return
        logger.info(f"Sending message to '{chat}': {text}" + (f" as reply to {reply_to}" if reply_to else ""))
        await client.send_message(chat, text, reply_to=reply_to)
    logger.info("Message sent successfully.")

async def add_reaction(client, chat, message_id, reaction):
    from telethon.tl.functions.messages import SendReactionRequest
    from telethon.tl.types import ReactionEmoji
    try:
        logger.info(f"Adding reaction '{reaction}' to message {message_id} in '{chat}'.")
        reaction_obj = ReactionEmoji(emoticon=reaction)
        await client(SendReactionRequest(peer=chat, msg_id=message_id, reaction=[reaction_obj]))
        logger.info(f"Successfully added reaction '{reaction}' to message {message_id}.")
    except Exception as e:
        logger.error(f"Failed to add reaction: {e}")

async def forward_message(client, source_chat, message_id, target_chat):
    try:
        logger.info(f"Forwarding message {message_id} from '{source_chat}' to '{target_chat}'.")
        forwarded = await client.forward_messages(entity=target_chat, messages=message_id, from_peer=source_chat)
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
    from telethon.tl.functions.messages import SendMessageRequest
    from telethon.tl.types import InputReplyToMessage
    if files:
        logger.error("Cross-chat reply with files is not supported in this mode.")
        return
    if source_chat is None or reply_to is None:
        logger.error("send_cross_chat_reply requires source_chat and reply_to (message id).")
        return
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
    limit = args.limit or 100
    logger.info(f"Fetching the {limit} most recent chats...")
    try:
        dialogs_json = []
        async for dialog in client.iter_dialogs(limit=limit):
            entity_json = json.loads(dialog.entity.to_json()) if dialog.entity else None
            dialog_obj = {
                'entity': entity_json,
                'last_message': json.loads(dialog.message.to_json()) if dialog.message else None,
                'name': dialog.name,
                'id': dialog.id
            }
            cleaned_dialog = cleanup_json(dialog_obj, args.profile)
            dialogs_json.append(cleaned_dialog)
        print(json.dumps(dialogs_json, indent=2, ensure_ascii=False))
    except Exception as e:
        logger.error(f"An error occurred while listing chats: {e}")

async def search_messages(client, query, args):
    logger.info(f"Searching for '{query}' across all chats...")
    try:
        results = await client(SearchGlobalRequest(
            q=query, limit=args.limit or 100,
            filter=InputMessagesFilterEmpty(),
            min_date=None, max_date=None,
            offset_rate=0, offset_peer=InputPeerEmpty(), offset_id=0
        ))
        entities = {entity.id: entity for entity in results.chats + results.users}
        grouped_messages = {}
        for message in results.messages:
            chat_id = message.chat_id
            if chat_id:
                if chat_id not in grouped_messages:
                    grouped_messages[chat_id] = []
                cleaned_msg = cleanup_json(json.loads(message.to_json()), args.profile)
                if cleaned_msg:
                    grouped_messages[chat_id].append(cleaned_msg)
        if not grouped_messages:
            print("No results found.")
            return
        for chat_id, messages in sorted(grouped_messages.items()):
            entity = entities.get(chat_id)
            name = "Unknown Chat"
            if entity:
                name = getattr(entity, 'title', None)
                if not name:
                    first = getattr(entity, 'first_name', '') or ''
                    last = getattr(entity, 'last_name', '') or ''
                    name = (f"{first} {last}").strip()
            print(f"\n--- Results from Chat: '{name}' (ID: {chat_id}) ---")
            print(json.dumps(messages, indent=2, ensure_ascii=False))
    except Exception as e:
        logger.error(f"An error occurred during search: {e}")

async def search_contacts(client, query, args):
    try:
        result = await client(ContactsSearchRequest(q=query, limit=args.limit or 20))
        output = []
        for user in result.users:
            obj = json.loads(user.to_json())
            cleaned = cleanup_json(obj, args.profile)
            if cleaned:
                output.append(cleaned)
        for chat in result.chats:
            obj = json.loads(chat.to_json())
            cleaned = cleanup_json(obj, args.profile)
            if cleaned:
                output.append(cleaned)
        print(json.dumps(output, indent=2, ensure_ascii=False))
    except Exception as e:
        logger.error(f"An error occurred during contact search: {e}")

async def get_entities(client, identifiers, args):
    results = []
    for ident in identifiers:
        lookup = ident
        try:
            lookup = int(ident)
        except Exception:
            pass
        try:
            entity = await client.get_entity(lookup)
            entity_json = json.loads(entity.to_json())
            full = None
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
