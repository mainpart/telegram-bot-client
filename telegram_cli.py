import asyncio
import json
import sys
import logging
import argparse
import os
import yaml
from getpass import getpass
from telethon import TelegramClient
from telethon.sessions import StringSession
from tg import (
    logger, find_config, load_yaml_config, load_profiles,
    connect_client, start_client, resolve_bot_token, parse_chat_id,
    init_adapters_from_config, close_adapters, listen,
    get_updates, send_message, add_reaction, forward_message,
    send_cross_chat_reply, edit_message, click_button, delete_message, download_file,
    list_chats, search_messages, search, search_chat, get_entities,
)

FILTER_CHOICES = ['photo', 'video', 'document', 'url', 'voice', 'gif', 'music', 'round_video', 'mentions', 'pinned']


def _add_bot_arg(p):
    p.add_argument('--bot', action='store_true', help='Bot mode (uses bot_token from config).')


def _add_filter_args(p):
    p.add_argument('--incoming-only', action='store_true', help='Only incoming messages.')
    p.add_argument('--outgoing-only', action='store_true', help='Only outgoing messages.')
    p.add_argument('--from-user', type=str, help='Messages from specific user ID.')
    p.add_argument('--pattern', type=str, help='Filter by regex pattern.')
    p.add_argument('--has-media', action='store_true', help='Only messages with media.')
    p.add_argument('--forwarded-only', action='store_true', help='Only forwarded messages.')
    p.add_argument('--replies-only', action='store_true', help='Only replies.')
    p.add_argument('--has-reactions', action='store_true', help='Only messages with reactions.')


def _sub(subparsers, name, help, epilog=None):
    return subparsers.add_parser(name, help=help, epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter)


def build_parser():
    parser = argparse.ArgumentParser(prog='telegram-cli',
        description='Telegram CLI — one-shot commands and real-time listener')
    parser.add_argument('--config', type=str, help='Path to config.yaml.')
    subparsers = parser.add_subparsers(dest='command')

    # init
    p = _sub(subparsers, 'init', 'Login and generate session token',
        epilog='example:\n  telegram-cli init --phone +79001234567')
    p.add_argument('--phone', type=str, help='Phone number for login.')

    # chats
    p = _sub(subparsers, 'chats', 'List recent chats', epilog="""\
examples:
  telegram-cli chats
  telegram-cli chats --limit 500
  telegram-cli chats --profile dialogue""")
    p.add_argument('--limit', type=int, default=100, help='Number of chats (default: 100).')
    p.add_argument('--profile', default='default', help='Filtering profile.')
    _add_bot_arg(p)

    # read
    p = _sub(subparsers, 'read', 'Read messages from a chat', epilog="""\
examples:
  telegram-cli read mike_kuleshov
  telegram-cli read 1744485600 --limit 100
  telegram-cli read 123 --from-id 5000 --forward
  telegram-cli read 123 --from-id 1000 --to-id 2000 --inclusive
  telegram-cli read 123 --has-media --incoming-only""")
    p.add_argument('chat', help='Chat ID or username.')
    p.add_argument('--from-id', type=int, help='Start message ID.')
    p.add_argument('--to-id', type=int, help='End message ID.')
    p.add_argument('--forward', action='store_true', help='Read newer messages.')
    p.add_argument('--backward', action='store_true', help='Read older messages.')
    p.add_argument('--inclusive', action='store_true', help='Include boundary messages.')
    p.add_argument('--limit', type=int, help='Number of messages.')
    p.add_argument('--profile', default='default', help='Filtering profile.')
    _add_bot_arg(p)
    _add_filter_args(p)

    # send
    p = _sub(subparsers, 'send', 'Send message or files', epilog="""\
examples:
  telegram-cli send 123 "Hello!"
  telegram-cli send 123 --files photo.jpg video.mp4
  telegram-cli send 123 "Caption" --files doc.pdf
  telegram-cli send 123 "Reply" --reply-to 456""")
    p.add_argument('chat', help='Chat ID or username.')
    p.add_argument('text', nargs='?', help='Message text.')
    p.add_argument('--files', nargs='+', help='Files to send.')
    p.add_argument('--reply-to', type=int, help='Message ID to reply to.')
    _add_bot_arg(p)

    # edit
    p = _sub(subparsers, 'edit', 'Edit a message', epilog="""\
example:
  telegram-cli edit 123 456 "Corrected text\"""")
    p.add_argument('chat', help='Chat ID or username.')
    p.add_argument('message_id', type=int, help='Message ID.')
    p.add_argument('text', help='New message text.')
    _add_bot_arg(p)

    # delete
    p = _sub(subparsers, 'delete', 'Delete a message', epilog="""\
example:
  telegram-cli delete 123 456""")
    p.add_argument('chat', help='Chat ID or username.')
    p.add_argument('message_id', type=int, help='Message ID.')
    _add_bot_arg(p)

    # forward
    p = _sub(subparsers, 'forward', 'Forward a message to another chat', epilog="""\
example:
  telegram-cli forward -1001605174968 123 1744485600""")
    p.add_argument('chat', help='Source chat ID or username.')
    p.add_argument('message_id', type=int, help='Message ID.')
    p.add_argument('target_chat', help='Target chat ID or username.')
    _add_bot_arg(p)

    # reply
    p = _sub(subparsers, 'reply', 'Reply to a message', epilog="""\
examples:
  telegram-cli reply 123 456 "Reply text"
  telegram-cli reply 123 456 --files photo.jpg
  telegram-cli reply 123 456 "Check this" --target-chat 789""")
    p.add_argument('chat', help='Chat ID or username.')
    p.add_argument('message_id', type=int, help='Message ID to reply to.')
    p.add_argument('text', nargs='?', help='Reply text.')
    p.add_argument('--files', nargs='+', help='Files to send.')
    p.add_argument('--target-chat', help='Target chat for cross-chat reply.')
    _add_bot_arg(p)

    # react
    p = _sub(subparsers, 'react', 'Add reaction to a message', epilog="""\
examples:
  telegram-cli react 123 456 "\U0001f44d"
  telegram-cli react 123 456 "\U0001f525\"""")
    p.add_argument('chat', help='Chat ID or username.')
    p.add_argument('message_id', type=int, help='Message ID.')
    p.add_argument('emoji', help='Reaction emoji.')
    _add_bot_arg(p)

    # click
    p = _sub(subparsers, 'click', 'Click an inline button', epilog="""\
example:
  telegram-cli click 123 456 "Confirm\"""")
    p.add_argument('chat', help='Chat ID or username.')
    p.add_argument('message_id', type=int, help='Message ID.')
    p.add_argument('button_text', help='Button text to click.')
    _add_bot_arg(p)

    # download
    p = _sub(subparsers, 'download', 'Download file from a message', epilog="""\
example:
  telegram-cli download 123 456""")
    p.add_argument('chat', help='Chat ID or username.')
    p.add_argument('message_id', type=int, help='Message ID.')
    _add_bot_arg(p)

    # search-messages
    p = _sub(subparsers, 'search-messages', 'Search messages across all chats', epilog="""\
examples:
  telegram-cli search-messages "query"
  telegram-cli search-messages "query" --groups-only --limit 50
  telegram-cli search-messages "query" --filter photo --min-date 2026-01-01""")
    p.add_argument('query', help='Search query.')
    p.add_argument('--limit', type=int, help='Max results.')
    p.add_argument('--filter', type=str, choices=FILTER_CHOICES, help='Media type filter.')
    p.add_argument('--min-date', type=str, help='Min date (YYYY-MM-DD).')
    p.add_argument('--max-date', type=str, help='Max date (YYYY-MM-DD).')
    p.add_argument('--groups-only', action='store_true', help='Groups only.')
    p.add_argument('--users-only', action='store_true', help='Private chats only.')
    p.add_argument('--broadcasts-only', action='store_true', help='Channels only.')
    p.add_argument('--profile', default='default', help='Filtering profile.')
    _add_bot_arg(p)

    # search-contacts
    p = _sub(subparsers, 'search-contacts', 'Search users, groups, channels', epilog="""\
examples:
  telegram-cli search-contacts "John"
  telegram-cli search-contacts "channel name" --limit 5""")
    p.add_argument('query', help='Search query.')
    p.add_argument('--limit', type=int, help='Max results.')
    p.add_argument('--profile', default='default', help='Filtering profile.')
    _add_bot_arg(p)

    # search-chat
    p = _sub(subparsers, 'search-chat', 'Search messages within a chat', epilog="""\
examples:
  telegram-cli search-chat -5241856808 "FAR manager"
  telegram-cli search-chat 123 "photo" --filter photo
  telegram-cli search-chat 123 "test" --from-user 809799943""")
    p.add_argument('chat', help='Chat ID or username.')
    p.add_argument('query', help='Search query.')
    p.add_argument('--limit', type=int, help='Max results.')
    p.add_argument('--filter', type=str, choices=FILTER_CHOICES, help='Media type filter.')
    p.add_argument('--from-user', type=str, help='From specific user ID.')
    p.add_argument('--min-date', type=str, help='Min date (YYYY-MM-DD).')
    p.add_argument('--max-date', type=str, help='Max date (YYYY-MM-DD).')
    p.add_argument('--profile', default='default', help='Filtering profile.')
    _add_bot_arg(p)

    # info
    p = _sub(subparsers, 'info', 'Get info about users or chats', epilog="""\
examples:
  telegram-cli info mike_kuleshov
  telegram-cli info 1744485600 123456789""")
    p.add_argument('entity', nargs='+', help='User/chat IDs or usernames.')
    p.add_argument('--profile', default='default', help='Filtering profile.')
    _add_bot_arg(p)

    # listen
    p = _sub(subparsers, 'listen', 'Real-time message listener', epilog="""\
examples:
  telegram-cli listen
  telegram-cli listen --chat 123 --chat 456
  telegram-cli listen --private-only
  telegram-cli listen --incoming-only --has-media""")
    p.add_argument('--chat', type=str, action='append', help='Chat to listen (repeatable).')
    p.add_argument('--private-only', action='store_true', help='Private messages only.')
    p.add_argument('--mentioned-only', action='store_true', help='Only messages mentioning me.')
    p.add_argument('--profile', default='default', help='Filtering profile.')
    _add_bot_arg(p)
    _add_filter_args(p)

    return parser


async def async_main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return

    logger.setLevel(logging.WARNING)

    config_path = args.config
    yaml_cfg = load_yaml_config(config_path)
    load_profiles()

    # init — special case, no client needed
    if args.command == 'init':
        telegram_cfg = (yaml_cfg or {}).get('telegram') or {}
        api_hash = telegram_cfg.get('api_hash') or os.environ.get('TELEGRAM_API_HASH')
        try:
            api_id = int(telegram_cfg.get('api_id') or os.environ.get('TELEGRAM_API_ID'))
        except (TypeError, ValueError):
            logger.error("api_id not set in config or TELEGRAM_API_ID env.")
            return
        if not api_hash:
            logger.error("api_hash not set in config or TELEGRAM_API_HASH env.")
            return
        session = StringSession()
        client = TelegramClient(session, api_id, api_hash)
        try:
            await client.start(
                phone=lambda: args.phone or input('Phone number: '),
                code_callback=lambda: getpass('Enter the code: '),
                password=lambda: getpass('Enter your 2FA password: ')
            )
            token = StringSession.save(client.session)
            save_path = find_config(config_path) or 'config.yaml'
            yaml_cfg.setdefault('telegram', {})['session_string'] = token
            os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
            with open(save_path, 'w') as f:
                yaml.dump(yaml_cfg, f, default_flow_style=False, allow_unicode=True)
            print(f"Session saved to {save_path}")
        finally:
            await client.disconnect()
        return

    # all other commands need a client

    bot_token = None
    if getattr(args, 'bot', False):
        bot_token = resolve_bot_token(yaml_cfg)
        if not bot_token:
            return

    client = connect_client(yaml_cfg, bot_token=bot_token)
    if not client:
        return

    try:
        if not await start_client(client, bot_token=bot_token):
            return

        def output(data):
            print(json.dumps(data, indent=2, ensure_ascii=False))

        cmd = args.command
        chat = parse_chat_id(getattr(args, 'chat', None))

        if cmd == 'chats':
            output(await list_chats(client, args.limit, args.profile))

        elif cmd == 'read':
            output(await get_updates(client, chat, args))

        elif cmd == 'send':
            if not args.text and not args.files:
                logger.error("Provide text and/or --files.")
                return
            await send_message(client, chat, args.text, args.files, args.reply_to)

        elif cmd == 'edit':
            await edit_message(client, chat, args.message_id, args.text)

        elif cmd == 'delete':
            await delete_message(client, chat, args.message_id)

        elif cmd == 'forward':
            target = parse_chat_id(args.target_chat)
            await forward_message(client, chat, args.message_id, target)

        elif cmd == 'reply':
            if not args.text and not args.files:
                logger.error("Provide text and/or --files.")
                return
            target = parse_chat_id(getattr(args, 'target_chat', None))
            if target:
                if args.files:
                    logger.error("Cross-chat reply does not support --files.")
                    return
                await send_cross_chat_reply(client, target, args.text, None, args.message_id, chat)
            else:
                await send_message(client, chat, args.text, args.files, args.message_id)

        elif cmd == 'react':
            await add_reaction(client, chat, args.message_id, args.emoji)

        elif cmd == 'click':
            await click_button(client, chat, args.message_id, args.button_text)

        elif cmd == 'download':
            path = await download_file(client, chat, args.message_id)
            if path:
                print(f"File downloaded to: {path}")

        elif cmd == 'search-messages':
            output(await search_messages(client, args.query, args.limit,
                filter=args.filter, min_date=args.min_date, max_date=args.max_date,
                groups_only=args.groups_only, users_only=args.users_only,
                broadcasts_only=args.broadcasts_only, profile=args.profile))

        elif cmd == 'search-contacts':
            output(await search(client, args.query, args.limit, args.profile))

        elif cmd == 'search-chat':
            output(await search_chat(client, chat, args.query, args.limit,
                filter=args.filter, from_user=getattr(args, 'from_user', None),
                min_date=args.min_date, max_date=args.max_date, profile=args.profile))

        elif cmd == 'info':
            output(await get_entities(client, args.entity, args.profile))

        elif cmd == 'listen':
            await init_adapters_from_config(yaml_cfg)
            try:
                await listen(client, args)
            finally:
                await close_adapters()

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    finally:
        if client.is_connected():
            await client.disconnect()


def main(argv=None):
    try:
        asyncio.run(async_main(argv))
    except (KeyboardInterrupt, SystemExit):
        print("\nExiting gracefully.")


if __name__ == '__main__':
    main()
