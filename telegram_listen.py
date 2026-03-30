import asyncio
import sys
import logging
from tg import (
    logger, load_yaml_config, load_profiles, init_adapters_from_config,
    close_adapters, connect_client, start_client, add_common_args,
    resolve_bot_token, listen,
)
import argparse

def build_parser():
    parser = argparse.ArgumentParser(description="Telegram Listener — real-time message streaming")

    parser.add_argument('--chat', type=str, action='append', help='Chat to listen (ID or username). Can be repeated.')
    parser.add_argument('--private-only', action='store_true', help='Listen to private messages only.')
    parser.add_argument('--mentioned-only', action='store_true', help='Only messages mentioning me.')
    add_common_args(parser)
    return parser

async def async_main():
    parser = build_parser()
    args = parser.parse_args()

    if args.incoming_only and args.outgoing_only:
        logger.error("--incoming-only and --outgoing-only are mutually exclusive.")
        return

    logger.setLevel(logging.WARNING)
    load_profiles()

    yaml_cfg = load_yaml_config('config.yaml')

    bot_token = None
    if args.bot:
        bot_token = resolve_bot_token(yaml_cfg)
        if not bot_token:
            return

    client = connect_client(yaml_cfg, bot_token=bot_token)
    if not client:
        return

    try:
        if not await start_client(client, bot_token=bot_token):
            return

        await init_adapters_from_config(yaml_cfg)
        await listen(client, args)

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    finally:
        try:
            await close_adapters()
        except Exception as e:
            logger.error(f"Failed to close adapters: {e}")
        if client.is_connected():
            await client.disconnect()

def main():
    try:
        asyncio.run(async_main())
    except (KeyboardInterrupt, SystemExit):
        print("\nExiting gracefully.")

if __name__ == '__main__':
    main()
