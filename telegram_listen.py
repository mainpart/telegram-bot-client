import asyncio
import sys
import logging
from tg import (
    logger, load_yaml_config, load_profiles, init_adapters_from_config,
    close_adapters, connect_client, start_client, add_common_args, parse_chat_id,
    listen_chat, listen_private, listen_all,
)
import argparse

async def main():
    parser = argparse.ArgumentParser(description="Telegram Listener — real-time message streaming")

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--listen', type=str, help='Listen to a specific chat (ID or username).')
    group.add_argument('--listen-private', action='store_true', help='Listen to all private messages.')
    group.add_argument('--listen-all', action='store_true', help='Listen to all messages from every chat.')
    add_common_args(parser)
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        return

    if args.incoming_only and args.outgoing_only:
        logger.error("--incoming-only and --outgoing-only are mutually exclusive.")
        return

    logger.setLevel(logging.WARNING)
    load_profiles()

    yaml_cfg = load_yaml_config('config.yaml')

    # Default to --listen-all if botToken without explicit listen mode
    if args.bot_token and not any([args.listen, args.listen_private, args.listen_all]):
        args.listen_all = True

    if not any([args.listen, args.listen_private, args.listen_all]):
        parser.print_help()
        return

    client = connect_client(yaml_cfg, bot_token=args.bot_token)
    if not client:
        return

    try:
        if not await start_client(client, bot_token=args.bot_token):
            return

        await init_adapters_from_config(yaml_cfg)

        if args.listen:
            chat_entity = parse_chat_id(args.listen)
            await listen_chat(client, chat_entity, args)
        elif args.listen_private:
            await listen_private(client, args)
        elif args.listen_all:
            await listen_all(client, args)

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
