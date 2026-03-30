import argparse
import os
from mcp.server.fastmcp import FastMCP
from tg.core import load_yaml_config, load_profiles, connect_client, start_client, parse_chat_id
from tg.commands import (
    get_updates, send_message, add_reaction, forward_message,
    send_cross_chat_reply, edit_message, click_button, delete_message, download_file,
    list_chats, search_messages, search, search_chat, get_entities,
)

mcp = FastMCP("telegram")

_client = None

async def get_client():
    global _client
    if _client is None:
        load_profiles()
        yaml_cfg = load_yaml_config()
        _client = connect_client(yaml_cfg)
        if not _client:
            raise RuntimeError("Failed to create Telegram client. Check api_id/api_hash/session.")
        if not await start_client(_client):
            raise RuntimeError("Failed to connect Telegram client. Session may be invalid.")
    return _client

def make_args(**kwargs):
    defaults = dict(
        from_id=None, to_id=None, limit=None,
        forward=False, backward=False, inclusive=False,
        profile='default',
        incoming_only=False, outgoing_only=False,
        from_user=None, pattern=None,
        has_media=False, forwarded_only=False,
        replies_only=False, has_reactions=False,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)

# --- Tools ---

@mcp.tool()
async def tg_get_messages(
    chat_id: str,
    limit: int = 20,
    from_id: int | None = None,
    to_id: int | None = None,
    forward: bool = False,
    backward: bool = False,
    inclusive: bool = False,
    profile: str = 'default',
    incoming_only: bool = False,
    outgoing_only: bool = False,
    from_user: str | None = None,
    pattern: str | None = None,
    has_media: bool = False,
    forwarded_only: bool = False,
    replies_only: bool = False,
    has_reactions: bool = False,
) -> list[dict]:
    """Read messages from a Telegram chat. Returns list of message objects."""
    client = await get_client()
    args = make_args(
        from_id=from_id, to_id=to_id, limit=limit,
        forward=forward, backward=backward, inclusive=inclusive,
        profile=profile,
        incoming_only=incoming_only, outgoing_only=outgoing_only,
        from_user=from_user, pattern=pattern,
        has_media=has_media, forwarded_only=forwarded_only,
        replies_only=replies_only, has_reactions=has_reactions,
    )
    return await get_updates(client, parse_chat_id(chat_id), args)

@mcp.tool()
async def tg_send_message(chat_id: str, text: str | None = None, files: list[str] | None = None, reply_to: int | None = None) -> str:
    """Send a message to a Telegram chat. Supports text, files, or both.
    Files can be local paths or HTTP URLs. For URLs, Telegram downloads the file itself.
    Multiple local files are sent as an album. Multiple URLs must be sent one at a time."""
    client = await get_client()
    await send_message(client, parse_chat_id(chat_id), text=text, files=files, reply_to=reply_to)
    return "ok"

@mcp.tool()
async def tg_edit_message(chat_id: str, message_id: int, text: str) -> str:
    """Edit a message in a Telegram chat."""
    client = await get_client()
    await edit_message(client, parse_chat_id(chat_id), message_id, text)
    return "ok"

@mcp.tool()
async def tg_forward_message(chat_id: str, message_id: int, target_chat: str) -> str:
    """Forward a message to another chat."""
    client = await get_client()
    await forward_message(client, parse_chat_id(chat_id), message_id, parse_chat_id(target_chat))
    return "ok"

@mcp.tool()
async def tg_add_reaction(chat_id: str, message_id: int, emoji: str) -> str:
    """Add an emoji reaction to a message."""
    client = await get_client()
    await add_reaction(client, parse_chat_id(chat_id), message_id, emoji)
    return "ok"

@mcp.tool()
async def tg_delete_message(chat_id: str, message_id: int) -> str:
    """Delete a message from a Telegram chat. Only works for your own messages or in chats where you have delete permissions."""
    client = await get_client()
    await delete_message(client, parse_chat_id(chat_id), message_id)
    return "ok"

@mcp.tool()
async def tg_download_file(chat_id: str, message_id: int) -> str:
    """Download a file from a message. Returns the file path."""
    client = await get_client()
    path = await download_file(client, parse_chat_id(chat_id), message_id)
    return path or "no file found"

@mcp.tool()
async def tg_search_messages(
    query: str,
    limit: int = 100,
    filter: str | None = None,
    min_date: str | None = None,
    max_date: str | None = None,
    groups_only: bool = False,
    users_only: bool = False,
    broadcasts_only: bool = False,
    profile: str = 'default',
) -> dict:
    """Search message text across all Telegram chats.
    Filter by media type: photo, video, document, url, voice, gif, music, round_video, mentions, pinned.
    Filter by chat type: groups_only, users_only, broadcasts_only.
    Dates in ISO format: '2026-01-01'."""
    client = await get_client()
    return await search_messages(client, query, limit, filter=filter,
        min_date=min_date, max_date=max_date,
        groups_only=groups_only, users_only=users_only,
        broadcasts_only=broadcasts_only, profile=profile)

@mcp.tool()
async def tg_search_chat(
    chat_id: str,
    query: str,
    limit: int = 100,
    filter: str | None = None,
    from_user: str | None = None,
    min_date: str | None = None,
    max_date: str | None = None,
    profile: str = 'default',
) -> list[dict]:
    """Search messages within a specific chat (server-side).
    Faster than tg_get_messages with pattern — search runs on Telegram servers.
    Filter by media type: photo, video, document, url, voice, gif, music, round_video, mentions, pinned."""
    client = await get_client()
    return await search_chat(client, parse_chat_id(chat_id), query, limit,
        filter=filter, from_user=from_user,
        min_date=min_date, max_date=max_date, profile=profile)

@mcp.tool()
async def tg_search(query: str, limit: int = 20, profile: str = 'default') -> list[dict]:
    """Search Telegram users, groups, and channels by name or username.
    Returns matching entities (not messages). Use tg_search_messages to search message text."""
    client = await get_client()
    return await search(client, query, limit, profile)

@mcp.tool()
async def tg_list_chats(limit: int = 100, profile: str = 'default') -> list[dict]:
    """List recent Telegram chats."""
    client = await get_client()
    return await list_chats(client, limit, profile)

@mcp.tool()
async def tg_get_entities(entity_id: str, profile: str = 'default') -> list[dict]:
    """Get full info about a Telegram user, chat or channel by ID or username."""
    client = await get_client()
    return await get_entities(client, [entity_id], profile)

def main():
    mcp.run()

if __name__ == "__main__":
    main()
