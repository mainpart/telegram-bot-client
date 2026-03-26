import argparse
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, Path, Body, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from tg import (
    load_yaml_config, load_profiles, init_adapters_from_config,
    close_adapters, connect_client, start_client, parse_chat_id,
    get_updates, send_message, add_reaction, forward_message,
    send_cross_chat_reply, edit_message, click_button, download_file,
    list_chats, search_messages, search_contacts, get_entities,
)

# --- Pydantic models for request bodies ---

class SendMessageBody(BaseModel):
    text: Optional[str] = None
    replyTo: Optional[int] = None

class EditMessageBody(BaseModel):
    text: str

class ForwardBody(BaseModel):
    targetChat: str

class ReactionBody(BaseModel):
    emoji: str

class ClickBody(BaseModel):
    buttonText: str

# --- App ---

client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global client
    load_profiles()
    yaml_cfg = load_yaml_config('config.yaml')
    await init_adapters_from_config(yaml_cfg)
    client = connect_client(yaml_cfg)
    if not client:
        raise RuntimeError("Failed to create Telegram client")
    if not await start_client(client):
        raise RuntimeError("Failed to connect Telegram client")
    yield
    await close_adapters()
    if client.is_connected():
        await client.disconnect()

app = FastAPI(title="Telegram API", lifespan=lifespan)

# --- Helper ---

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

# --- Endpoints ---

@app.get("/messages/{chat_id}")
async def api_get_messages(
    chat_id: str = Path(...),
    fromId: Optional[int] = None,
    toId: Optional[int] = None,
    inclusive: bool = False,
    forward: bool = False,
    backward: bool = False,
    limit: Optional[int] = None,
    profile: str = 'default',
    incoming_only: bool = False,
    outgoing_only: bool = False,
    from_user: Optional[str] = None,
    pattern: Optional[str] = None,
    has_media: bool = False,
    forwarded_only: bool = False,
    replies_only: bool = False,
    has_reactions: bool = False,
):
    args = make_args(
        from_id=fromId, to_id=toId, inclusive=inclusive,
        forward=forward, backward=backward,
        limit=limit, profile=profile,
        incoming_only=incoming_only, outgoing_only=outgoing_only,
        from_user=from_user, pattern=pattern,
        has_media=has_media, forwarded_only=forwarded_only,
        replies_only=replies_only, has_reactions=has_reactions,
    )
    return await get_updates(client, parse_chat_id(chat_id), args)

@app.post("/messages/{chat_id}")
async def api_send_message(chat_id: str = Path(...), body: SendMessageBody = Body(...)):
    await send_message(client, parse_chat_id(chat_id), text=body.text, reply_to=body.replyTo)
    return {"ok": True}

@app.put("/messages/{chat_id}/{message_id}")
async def api_edit_message(chat_id: str = Path(...), message_id: int = Path(...), body: EditMessageBody = Body(...)):
    await edit_message(client, parse_chat_id(chat_id), message_id, body.text)
    return {"ok": True}

@app.post("/messages/{chat_id}/{message_id}/forward")
async def api_forward_message(chat_id: str = Path(...), message_id: int = Path(...), body: ForwardBody = Body(...)):
    await forward_message(client, parse_chat_id(chat_id), message_id, parse_chat_id(body.targetChat))
    return {"ok": True}

@app.post("/messages/{chat_id}/{message_id}/reaction")
async def api_add_reaction(chat_id: str = Path(...), message_id: int = Path(...), body: ReactionBody = Body(...)):
    await add_reaction(client, parse_chat_id(chat_id), message_id, body.emoji)
    return {"ok": True}

@app.post("/messages/{chat_id}/{message_id}/click")
async def api_click_button(chat_id: str = Path(...), message_id: int = Path(...), body: ClickBody = Body(...)):
    await click_button(client, parse_chat_id(chat_id), message_id, body.buttonText)
    return {"ok": True}

@app.get("/messages/{chat_id}/{message_id}/download")
async def api_download_file(chat_id: str = Path(...), message_id: int = Path(...)):
    path = await download_file(client, parse_chat_id(chat_id), message_id)
    if not path:
        raise HTTPException(404, "File not found")
    return FileResponse(path)

@app.get("/search/messages")
async def api_search_messages(q: str = Query(...), limit: int = 100, profile: str = 'default'):
    return await search_messages(client, q, limit, profile)

@app.get("/search/contacts")
async def api_search_contacts(q: str = Query(...), limit: int = 20, profile: str = 'default'):
    return await search_contacts(client, q, limit, profile)

@app.get("/chats")
async def api_list_chats(limit: int = 100, profile: str = 'default'):
    return await list_chats(client, limit, profile)

@app.get("/entities/{entity_id}")
async def api_get_entity(entity_id: str = Path(...), profile: str = 'default'):
    return await get_entities(client, [entity_id], profile)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
