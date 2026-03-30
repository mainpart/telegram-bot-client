import asyncio
import re
import json
import os
import logging
import warnings
import yaml
from getpass import getpass
from telethon import TelegramClient
from telethon.sessions import StringSession
from adapters import ADAPTER_TYPES
from adapters.base import BaseAdapter

# --- Setup ---
warnings.filterwarnings("ignore", message="The session already had an authorized user.*")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# --- Globals ---
PROFILES = {}
ADAPTERS = []

# --- Adapters ---

async def _safe_adapter_exec(adapter: BaseAdapter, message: dict):
    adapter_name = adapter.__class__.__name__
    try:
        await adapter.exec(message)
    except Exception as e:
        logger.error(f"Adapter {adapter_name} failed: {e}")

async def emit_message_to_adapters(message: dict):
    if not ADAPTERS:
        print(json.dumps(message, indent=2, ensure_ascii=False))
        return

    tasks = [_safe_adapter_exec(a, message) for a in ADAPTERS]
    await asyncio.gather(*tasks, return_exceptions=True)

async def close_adapters():
    tasks = []
    for adapter in ADAPTERS:
        close_coro = getattr(adapter, 'close', None)
        if close_coro and callable(close_coro):
            tasks.append(close_coro())
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

async def init_adapters_from_config(cfg: dict):
    global ADAPTERS
    ADAPTERS = []
    adapters_cfg = (cfg or {}).get('adapters') or []
    if not adapters_cfg:
        adapters_cfg = [{'type': 'stdout'}]
    for entry in adapters_cfg:
        if not isinstance(entry, dict):
            continue
        adapter_type = (entry.get('type') or '').lower()
        adapter_class = ADAPTER_TYPES.get(adapter_type)
        if not adapter_class:
            logger.warning(f"Unknown adapter type: {adapter_type}")
            continue
        adapter = adapter_class(entry)
        try:
            await adapter.init()
        except Exception as e:
            logger.error(f"Failed to init adapter {adapter_type}: {e}")
            continue
        ADAPTERS.append(adapter)

# --- Config ---

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

def load_profiles():
    global PROFILES
    try:
        with open('profiles.json', 'r') as f:
            PROFILES = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not load profiles.json: {e}. Using default empty filters.")
        PROFILES = {}

# --- Filters & Cleanup ---

def apply_message_filters(message, args):
    if args.incoming_only and message.get('out', False):
        return False
    if args.outgoing_only and not message.get('out', False):
        return False
    if args.from_user:
        from_id = message.get('from_id', {})
        if isinstance(from_id, dict):
            user_id = from_id.get('user_id')
            if user_id:
                try:
                    if str(user_id) != str(args.from_user):
                        return False
                except:
                    return False
            else:
                return False
    if args.pattern:
        message_text = message.get('message', '')
        if not re.search(args.pattern, message_text, re.IGNORECASE):
            return False
    if args.has_media and not message.get('media'):
        return False
    if args.forwarded_only and not message.get('fwd_from'):
        return False
    if args.replies_only and not message.get('reply_to'):
        return False
    if args.has_reactions and not message.get('reactions'):
        return False
    return True

def cleanup_json(obj, profile_name="default"):
    profile = PROFILES.get(profile_name, {})
    stop_keys = profile.get("stop_keys", [])
    stop_objects = profile.get("stop_objects", [])

    if isinstance(obj, dict):
        if obj.get('_') in stop_objects:
            return None
        cleaned_dict = {}
        for k, v in obj.items():
            if k in stop_keys:
                continue
            cleaned_v = cleanup_json(v, profile_name)
            if cleaned_v not in [None, False, "", []]:
                cleaned_dict[k] = cleaned_v
        return cleaned_dict if cleaned_dict else None
    elif isinstance(obj, list):
        cleaned_list = [cleanup_json(elem, profile_name) for elem in obj]
        return [elem for elem in cleaned_list if elem not in [None, False, "", []]]
    return obj

# --- Client Connection ---

def connect_client(yaml_cfg, bot_token=None, session_string=None):
    """Create a TelegramClient from config. Returns (client, api_id, api_hash, telegram_cfg)."""
    telegram_cfg = (yaml_cfg or {}).get('telegram') or {}
    api_hash = telegram_cfg.get('api_hash') or os.environ.get('TELEGRAM_API_HASH')
    try:
        api_id = int(telegram_cfg.get('api_id') or os.environ.get('TELEGRAM_API_ID'))
    except (TypeError, ValueError):
        logger.error("api_id not set or invalid")
        return None
    if not api_hash:
        logger.error("api_hash not set")
        return None

    if bot_token:
        client = TelegramClient(StringSession(), api_id, api_hash)
    elif session_string:
        client = TelegramClient(StringSession(session_string), api_id, api_hash)
    else:
        ss = telegram_cfg.get('session_string') or os.environ.get('TELEGRAM_SESSION')
        if not ss:
            logger.error("Session not set. Use telegram_cli.py --init to generate a token.")
            return None
        client = TelegramClient(StringSession(ss), api_id, api_hash)
    return client

async def start_client(client, bot_token=None):
    """Connect and authorize. Returns True on success."""
    if bot_token:
        await client.start(bot_token=bot_token)
    else:
        await client.connect()
        if not await client.is_user_authorized():
            logger.error("Session is invalid or expired. Run telegram_cli.py --init to generate a new token.")
            return False
    return True

# --- Shared argparse ---

def resolve_bot_token(yaml_cfg):
    """Read bot token from config.yaml or env."""
    telegram_cfg = (yaml_cfg or {}).get('telegram') or {}
    token = telegram_cfg.get('bot_token') or os.environ.get('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("bot_token not set in config.yaml or TELEGRAM_BOT_TOKEN env.")
    return token

def add_common_args(parser):
    parser.add_argument('--profile', type=str, default='default', help='Filtering profile from profiles.json.')
    parser.add_argument('--bot', action='store_true', help='Bot mode (token from config.yaml telegram.bot_token).')
    parser.add_argument('--incoming-only', action='store_true', help='Filter only incoming messages.')
    parser.add_argument('--outgoing-only', action='store_true', help='Filter only outgoing messages.')
    parser.add_argument('--from-user', type=str, help='Filter messages from specific user ID.')
    parser.add_argument('--pattern', type=str, help='Filter messages matching regex pattern.')
    parser.add_argument('--has-media', action='store_true', help='Filter messages with media only.')
    parser.add_argument('--forwarded-only', action='store_true', help='Filter only forwarded messages.')
    parser.add_argument('--replies-only', action='store_true', help='Filter only reply messages.')
    parser.add_argument('--has-reactions', action='store_true', help='Filter messages with reactions only.')

def parse_chat_id(value):
    """Convert string to int if it's a numeric ID."""
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return value
