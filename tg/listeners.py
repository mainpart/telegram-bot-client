import asyncio
import json
from telethon import events
from telethon.events import CallbackQuery
from tg.core import logger, apply_message_filters, cleanup_json, emit_message_to_adapters, parse_chat_id


async def message_event_handler(event, args):
    try:
        message_json = json.loads(event.message.to_json())
        # Client-side filters for what Telethon events don't support
        if args.has_media and not message_json.get('media'):
            return
        if args.replies_only and not message_json.get('reply_to'):
            return
        if args.has_reactions and not message_json.get('reactions'):
            return
        cleaned_msg = cleanup_json(message_json, args.profile)
        if cleaned_msg:
            asyncio.create_task(emit_message_to_adapters(cleaned_msg))
    except Exception as e:
        logger.error(f"Error in message_event_handler: {e}")

async def message_deleted_handler(event, args):
    try:
        payload = {
            'type': 'message_deleted',
            'deleted_ids': event.deleted_ids,
            'chat_id': getattr(event, 'chat_id', None),
        }
        asyncio.create_task(emit_message_to_adapters(payload))
    except Exception as e:
        logger.error(f"Error in message_deleted_handler: {e}")

async def callback_query_handler(event, args):
    try:
        logger.info(f"Callback query in chat {event.chat_id} from user {getattr(event.sender_id, 'value', event.sender_id)}")
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


async def listen(client, args):
    chats = [parse_chat_id(c) for c in args.chat] if args.chat else None

    # func= predicate for listener-only filters
    predicates = []
    if getattr(args, 'private_only', False):
        predicates.append(lambda e: e.is_private)
    if getattr(args, 'mentioned_only', False):
        predicates.append(lambda e: e.mentioned)
    func = (lambda e: all(p(e) for p in predicates)) if predicates else None

    msg_kwargs = dict(
        chats=chats,
        incoming=True if args.incoming_only else None,
        outgoing=True if args.outgoing_only else None,
        from_users=args.from_user or None,
        forwards=True if args.forwarded_only else None,
        pattern=args.pattern,
        func=func,
    )

    client.add_event_handler(
        lambda e: message_event_handler(e, args),
        events.NewMessage(**msg_kwargs))
    client.add_event_handler(
        lambda e: message_event_handler(e, args),
        events.MessageEdited(**msg_kwargs))
    client.add_event_handler(
        lambda e: message_deleted_handler(e, args),
        events.MessageDeleted(chats=chats))

    if args.bot:
        client.add_event_handler(
            lambda e: callback_query_handler(e, args),
            CallbackQuery(chats=chats))

    await client.run_until_disconnected()
