import asyncio
import json
from telethon import events
from telethon.events import CallbackQuery
from tg.core import logger, apply_message_filters, cleanup_json, emit_message_to_adapters

async def message_event_handler(event, args):
    try:
        message_json = json.loads(event.message.to_json())
        if not apply_message_filters(message_json, args):
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

async def listen_chat(client, chat_entity, args):
    logger.info(f"Listening for new messages in '{chat_entity}'... Press Ctrl+C to stop.")
    client.add_event_handler(lambda event: message_event_handler(event, args), events.NewMessage(chats=chat_entity))
    client.add_event_handler(lambda event: message_event_handler(event, args), events.MessageEdited(chats=chat_entity))
    client.add_event_handler(lambda event: message_deleted_handler(event, args), events.MessageDeleted(chats=chat_entity))
    if args.bot_token:
        client.add_event_handler(lambda event: callback_query_handler(event, args), CallbackQuery(chats=chat_entity))
    await client.run_until_disconnected()

async def listen_private(client, args):
    logger.info("Listening for all incoming private messages... Press Ctrl+C to stop.")
    client.add_event_handler(
        lambda event: message_event_handler(event, args),
        events.NewMessage(incoming=True, func=lambda e: e.is_private)
    )
    client.add_event_handler(
        lambda event: message_event_handler(event, args),
        events.MessageEdited(func=lambda e: e.is_private)
    )
    client.add_event_handler(
        lambda event: message_deleted_handler(event, args),
        events.MessageDeleted()
    )
    if args.bot_token:
        client.add_event_handler(
            lambda event: callback_query_handler(event, args),
            CallbackQuery(func=lambda e: e.is_private)
        )
    await client.run_until_disconnected()

async def listen_all(client, args):
    logger.info("Listening for all incoming messages from every chat... Press Ctrl+C to stop.")
    client.add_event_handler(
        lambda event: message_event_handler(event, args),
        events.NewMessage()
    )
    client.add_event_handler(
        lambda event: message_event_handler(event, args),
        events.MessageEdited()
    )
    client.add_event_handler(
        lambda event: message_deleted_handler(event, args),
        events.MessageDeleted()
    )
    if args.bot_token:
        client.add_event_handler(
            lambda event: callback_query_handler(event, args),
            CallbackQuery()
        )
    await client.run_until_disconnected()
