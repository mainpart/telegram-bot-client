import asyncio
import json
import sys
import logging
import yaml
from getpass import getpass
from telethon import TelegramClient
from telethon.sessions import StringSession
from tg import (
    logger, load_yaml_config, load_profiles,
    connect_client, start_client, add_common_args, resolve_bot_token, parse_chat_id,
    get_updates, send_message, add_reaction, forward_message,
    send_cross_chat_reply, edit_message, click_button, delete_message, download_file,
    list_chats, search_messages, search, search_chat, get_entities,
)
import argparse
import os

async def async_main():
    parser = argparse.ArgumentParser(description="Telegram CLI — one-shot commands")

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--init', action='store_true', help='Login and generate StringSession token.')
    group.add_argument('--list-chats', action='store_true', help='List recent chats.')
    group.add_argument('--search-messages', type=str, help='Search message text across all chats.')
    group.add_argument('--search-contacts', type=str, help='Search users, groups, channels by name or username.')
    group.add_argument('--search-chat', type=str, help='Search messages within a specific chat (requires --chat).')

    parser.add_argument('--chat', type=str, help='Chat username or ID.')
    parser.add_argument('--from-id', type=int, help='Start message ID.')
    parser.add_argument('--to-id', type=int, help='End message ID.')
    parser.add_argument('--inclusive', action='store_true', help='Include boundary messages.')
    parser.add_argument('--forward', action='store_true', help='Read newer messages.')
    parser.add_argument('--backward', action='store_true', help='Read older messages.')
    parser.add_argument('--send-message', type=str, help='Text to send.')
    parser.add_argument('--send-files', nargs='+', help='Files to send.')
    parser.add_argument('--reply-to', type=int, help='Message ID to reply to.')
    parser.add_argument('--target-chat', type=str, help='Target chat for forward/cross-chat reply.')
    parser.add_argument('--click-button', type=str, help='Button text to click.')
    parser.add_argument('--message-id', type=int, help='Message ID for actions.')
    parser.add_argument('--forward-message', action='store_true', help='Forward message.')
    parser.add_argument('--reply-message', type=str, help='Reply text.')
    parser.add_argument('--download', action='store_true', help='Download file from message.')
    parser.add_argument('--add-reaction', type=str, help='Add reaction emoji.')
    parser.add_argument('--edit-message', type=str, help='New text for message.')
    parser.add_argument('--delete-message', action='store_true', help='Delete a message. Requires --chat and --message-id.')
    parser.add_argument('--get-entities', nargs='+', help='Get info for users/chats by ID or username.')
    parser.add_argument('--filter', type=str, help='Media type filter: photo, video, document, url, voice, gif, music, round_video, mentions, pinned.')
    parser.add_argument('--min-date', type=str, help='Min date in ISO format (e.g. 2026-01-01).')
    parser.add_argument('--max-date', type=str, help='Max date in ISO format.')
    parser.add_argument('--groups-only', action='store_true', help='Search in groups only.')
    parser.add_argument('--users-only', action='store_true', help='Search in private chats only.')
    parser.add_argument('--broadcasts-only', action='store_true', help='Search in channels only.')
    parser.add_argument('--limit', type=int, help='Number of items to fetch.')
    add_common_args(parser)
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        return

    if args.incoming_only and args.outgoing_only:
        logger.error("--incoming-only and --outgoing-only are mutually exclusive.")
        return
    if args.forward and args.backward:
        logger.error("--forward and --backward are mutually exclusive.")
        return

    logger.setLevel(logging.WARNING)
    load_profiles()

    yaml_cfg = load_yaml_config('config.yaml')
    telegram_cfg = (yaml_cfg or {}).get('telegram') or {}

    if args.init:
        api_hash = telegram_cfg.get('api_hash')
        try:
            api_id = int(telegram_cfg.get('api_id'))
        except (TypeError, ValueError):
            logger.error("api_id not set or invalid in config.yaml")
            return
        if not api_hash:
            logger.error("api_hash not set in config.yaml")
            return
        session = StringSession()
        client = TelegramClient(session, api_id, api_hash)
        try:
            await client.start(
                phone=lambda: str(telegram_cfg.get('phone_number') or '') or input('Phone number: '),
                code_callback=lambda: getpass('Enter the code: '),
                password=lambda: getpass('Enter your 2FA password: ')
            )
            token = StringSession.save(client.session)
            yaml_cfg.setdefault('telegram', {})['session_string'] = token
            with open('config.yaml', 'w') as f:
                yaml.dump(yaml_cfg, f, default_flow_style=False, allow_unicode=True)
            print(f"Session saved to config.yaml")
        finally:
            await client.disconnect()
        return

    bot_token = None
    if args.bot:
        bot_token = resolve_bot_token(yaml_cfg)
        if not bot_token:
            return

    client = connect_client(yaml_cfg, bot_token=bot_token)
    if not client:
        return

    chat_entity = parse_chat_id(args.chat)
    target_chat_entity = parse_chat_id(getattr(args, 'target_chat', None))

    try:
        if not await start_client(client, bot_token=bot_token):
            return

        def output(data):
            print(json.dumps(data, indent=2, ensure_ascii=False))

        if args.list_chats:
            output(await list_chats(client, args.limit, args.profile))
        elif args.search_messages:
            output(await search_messages(client, args.search_messages, args.limit,
                filter=args.filter, min_date=args.min_date, max_date=args.max_date,
                groups_only=args.groups_only, users_only=args.users_only,
                broadcasts_only=args.broadcasts_only, profile=args.profile))
        elif args.search_contacts:
            output(await search(client, args.search_contacts, args.limit, args.profile))
        elif args.search_chat:
            if not chat_entity:
                logger.error("--chat is required for --search-chat.")
                return
            output(await search_chat(client, chat_entity, args.search_chat, args.limit,
                filter=args.filter, from_user=getattr(args, 'from_user', None),
                min_date=args.min_date, max_date=args.max_date, profile=args.profile))
        elif args.get_entities:
            output(await get_entities(client, args.get_entities, args.profile))
        elif args.forward_message:
            if not (chat_entity and target_chat_entity and args.message_id):
                logger.error("--forward-message requires --chat, --message-id and --target-chat.")
                return
            await forward_message(client, chat_entity, args.message_id, target_chat_entity)
        elif args.reply_message:
            if not (chat_entity and args.message_id):
                logger.error("--reply-message requires --chat and --message-id.")
                return
            if target_chat_entity:
                if args.send_files:
                    logger.error("--reply-message with --target-chat does not support files.")
                    return
                await send_cross_chat_reply(client, target_chat_entity, args.reply_message, None, args.message_id, chat_entity)
            else:
                await send_message(client, chat_entity, args.reply_message, args.send_files, args.message_id)
        elif args.send_message or args.send_files:
            if not chat_entity:
                logger.error("--chat is required for --send-message/--send-files.")
                return
            await send_message(client, chat_entity, args.send_message, args.send_files, args.reply_to)
        elif args.click_button:
            if not chat_entity or not args.message_id:
                logger.error("--chat and --message-id are required for --click-button.")
                return
            await click_button(client, chat_entity, args.message_id, args.click_button)
        elif args.download:
            if not chat_entity or not args.message_id:
                logger.error("--chat and --message-id are required for --download.")
                return
            path = await download_file(client, chat_entity, args.message_id)
            if path:
                print(f"File downloaded to: {path}")
        elif args.add_reaction:
            if not chat_entity or not args.message_id:
                logger.error("--chat and --message-id are required for --add-reaction.")
                return
            await add_reaction(client, chat_entity, args.message_id, args.add_reaction)
        elif args.edit_message:
            if not chat_entity or not args.message_id:
                logger.error("--chat and --message-id are required for --edit-message.")
                return
            await edit_message(client, chat_entity, args.message_id, args.edit_message)
        elif args.delete_message:
            if not chat_entity or not args.message_id:
                logger.error("--chat and --message-id are required for --delete-message.")
                return
            await delete_message(client, chat_entity, args.message_id)
        else:
            if not chat_entity:
                logger.error("A --chat must be provided to fetch updates.")
                return
            output(await get_updates(client, chat_entity, args))

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    finally:
        if client.is_connected():
            await client.disconnect()

def main():
    try:
        asyncio.run(async_main())
    except (KeyboardInterrupt, SystemExit):
        print("\nExiting gracefully.")

if __name__ == '__main__':
    main()
