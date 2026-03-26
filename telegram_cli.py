import asyncio
import sys
import logging
import yaml
from getpass import getpass
from telethon import TelegramClient
from telethon.sessions import StringSession
from tg import (
    logger, load_yaml_config, load_profiles, init_adapters_from_config,
    close_adapters, connect_client, start_client, add_common_args, parse_chat_id,
    get_updates, send_message, add_reaction, forward_message,
    send_cross_chat_reply, edit_message, click_button, download_file,
    list_chats, search_messages, search_contacts, get_entities,
)
import argparse
import os

async def main():
    parser = argparse.ArgumentParser(description="Telegram CLI — one-shot commands")

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--init', action='store_true', help='Login and generate StringSession token.')
    group.add_argument('--list-chats', action='store_true', help='List recent chats.')
    group.add_argument('--searchMessages', type=str, help='Search message text across all chats.')
    group.add_argument('--searchContacts', type=str, help='Search contacts/users by name or username.')

    parser.add_argument('--chat', type=str, help='Chat username or ID.')
    parser.add_argument('--fromId', type=int, help='Start message ID.')
    parser.add_argument('--toId', type=int, help='End message ID.')
    parser.add_argument('--inclusive', action='store_true', help='Include boundary messages.')
    parser.add_argument('--forward', action='store_true', help='Read newer messages.')
    parser.add_argument('--backward', action='store_true', help='Read older messages.')
    parser.add_argument('--sendMessage', type=str, help='Text to send.')
    parser.add_argument('--sendFiles', nargs='+', help='Files to send.')
    parser.add_argument('--replyTo', type=int, help='Message ID to reply to.')
    parser.add_argument('--targetChat', type=str, help='Target chat for forward/cross-chat reply.')
    parser.add_argument('--clickButton', type=str, help='Button text to click.')
    parser.add_argument('--messageId', type=int, help='Message ID for actions.')
    parser.add_argument('--forwardMessage', action='store_true', help='Forward message.')
    parser.add_argument('--replyMessage', type=str, help='Reply text.')
    parser.add_argument('--download', action='store_true', help='Download file from message.')
    parser.add_argument('--addReaction', type=str, help='Add reaction emoji.')
    parser.add_argument('--editMessage', type=str, help='New text for message.')
    parser.add_argument('--get-entities', nargs='+', help='Get info for users/chats by ID or username.')
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

    client = connect_client(yaml_cfg, bot_token=args.botToken)
    if not client:
        return

    chat_entity = parse_chat_id(args.chat)
    target_chat_entity = parse_chat_id(getattr(args, 'targetChat', None))

    try:
        if not await start_client(client, bot_token=args.botToken):
            return

        await init_adapters_from_config(yaml_cfg)

        if args.list_chats:
            await list_chats(client, args)
        elif args.searchMessages:
            await search_messages(client, args.searchMessages, args)
        elif args.searchContacts:
            await search_contacts(client, args.searchContacts, args)
        elif args.get_entities:
            await get_entities(client, args.get_entities, args)
        elif args.forwardMessage:
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

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\nExiting gracefully.")
