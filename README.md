# Telegram Client

CLI, REST API and MCP server for interacting with Telegram via a user account. Designed for automation, scripting and integrations.

## Features

- Read, send, edit, delete, forward messages
- Search across all chats, within a chat, or by contacts
- Download files, add reactions, click inline buttons
- Real-time message listener with output adapters (stdout, HTTP webhook, MongoDB, RabbitMQ)
- Bot mode (works with bot tokens)
- Filtering by sender, media, regex, date range, reactions, forwards, replies

## Modes of Operation

| Mode | Use case | Entry point |
|------|----------|-------------|
| **CLI** | One-shot commands from terminal or scripts | `telegram-cli <command>` |
| **Listener** | Real-time message streaming with adapters | `telegram-cli listen` |
| **REST API** | HTTP endpoints for web integrations | `telegram_api.py` |
| **MCP Server** | AI assistant tool integration | `telegram_mcp.py` |

## Installation

### Homebrew

```bash
brew tap mainpart/telegram-client
brew install telegram-client
```

### pip

```bash
pip install git+https://github.com/mainpart/telegram-client.git
```

### Docker

```bash
docker run -e TELEGRAM_API_ID=12345678 \
           -e TELEGRAM_API_HASH=a1b2c3d4... \
           -e TELEGRAM_SESSION=1ApW... \
           mainpart/telegram-client
```

### Optional dependencies

```bash
pip install 'telegram-client[mcp]'       # MCP server
pip install 'telegram-client[http]'      # HTTP webhook adapter
pip install 'telegram-client[mongodb]'   # MongoDB adapter
pip install 'telegram-client[rabbitmq]'  # RabbitMQ adapter
pip install 'telegram-client[all]'       # all adapters
pip install fastapi uvicorn              # REST API
```

## Setup

1. Go to [my.telegram.org](https://my.telegram.org), log in with your phone number, and create an application. You will get `api_id` and `api_hash` — these are required by Telegram for any third-party client to connect to their API.

2. Create `config.yaml` (or copy from `config.yaml-default`):

```yaml
telegram:
  api_id: 12345678
  api_hash: "a1b2c3d4e5f6..."
```

3. Generate a session token:

```bash
telegram-cli init --phone +79001234567
```

The token is saved to `config.yaml` automatically. Alternatively, set credentials via environment variables:

```bash
export TELEGRAM_API_ID=12345678
export TELEGRAM_API_HASH=a1b2c3d4...
export TELEGRAM_SESSION=1ApW...
```

---

## 1. CLI

One-shot commands. Outputs JSON to stdout, errors to stderr. Run `telegram-cli <command> --help` for details on any command.

### init

Interactive login. Prompts for confirmation code and 2FA password (if enabled).

```bash
telegram-cli init --phone +79001234567
```

### chats

List recent dialogs.

```bash
telegram-cli chats
telegram-cli chats --limit 500
telegram-cli chats --profile dialogue
```

### read

Read messages from a chat. Chat accepts a username or numeric ID.

```bash
telegram-cli read mike_kuleshov
telegram-cli read 1744485600 --limit 100
telegram-cli read 123 --from-id 5000 --forward
telegram-cli read 123 --from-id 1000 --to-id 2000 --inclusive
telegram-cli read 123 --has-media --incoming-only
telegram-cli read 123 --pattern "hello|привет"
telegram-cli read 123 --from-user 809799943
```

### send

Send a message, files, or both.

```bash
telegram-cli send 123 "Hello!"
telegram-cli send 123 --files photo.jpg video.mp4
telegram-cli send 123 "Caption" --files doc.pdf
telegram-cli send 123 "Reply" --reply-to 456
```

### edit / delete

```bash
telegram-cli edit 123 456 "Corrected text"
telegram-cli delete 123 456
```

### forward / reply

```bash
telegram-cli forward -1001605174968 123 1744485600
telegram-cli reply 123 456 "Reply text"
telegram-cli reply 123 456 --files photo.jpg
telegram-cli reply 123 456 "Check this" --target-chat 789
```

### react / click / download

```bash
telegram-cli react 123 456 "🔥"
telegram-cli click 123 456 "Confirm"
telegram-cli download 123 456
```

### search-messages

Search across all chats.

```bash
telegram-cli search-messages "query"
telegram-cli search-messages "query" --groups-only --limit 50
telegram-cli search-messages "query" --filter photo --min-date 2026-01-01
```

### search-contacts

Search users, groups, channels by name.

```bash
telegram-cli search-contacts "John"
telegram-cli search-contacts "channel" --limit 5
```

### search-chat

Search within a specific chat (server-side).

```bash
telegram-cli search-chat 123 "query"
telegram-cli search-chat 123 "photo" --filter photo
telegram-cli search-chat 123 "test" --from-user 809799943
```

### info

Get full info about users or chats.

```bash
telegram-cli info mike_kuleshov
telegram-cli info 1744485600 123456789
```

### Message Filters

Available for `read` and `listen`:

| Filter | Description |
|---|---|
| `--incoming-only` | Incoming messages only |
| `--outgoing-only` | Outgoing messages only |
| `--from-user <id>` | From a specific user |
| `--pattern <regex>` | Match text by regex |
| `--has-media` | Messages with media only |
| `--forwarded-only` | Forwarded messages only |
| `--replies-only` | Replies only |
| `--has-reactions` | Messages with reactions only |

### Filtering Profiles

`--profile <name>` applies a profile from `profiles.json` to clean JSON output:

```json
{
  "dialogue": {
    "stop_keys": ["access_hash", "file_reference", "dc_id"],
    "stop_objects": ["MessageEntityBold", "MessageActionPinMessage"]
  }
}
```

### Bot Mode

Add `--bot` to any command. Uses `bot_token` from `config.yaml` or `TELEGRAM_BOT_TOKEN` env.

```bash
telegram-cli send 123 "test" --bot
telegram-cli listen --bot --chat -1001605174968
```

---

## 2. Listener

Real-time message streaming. Runs until interrupted (Ctrl+C). Outputs each new, edited or deleted message as JSON through output adapters.

```bash
telegram-cli listen
telegram-cli listen --chat 123 --chat 456
telegram-cli listen --private-only
telegram-cli listen --incoming-only --has-media
telegram-cli listen --mentioned-only
telegram-cli listen --profile dialogue
```

### Events

- **NewMessage** — new messages
- **MessageEdited** — edited messages
- **MessageDeleted** — deleted messages (only IDs)
- **CallbackQuery** — inline button presses (bot mode)

### Output Adapters

Configured in `config.yaml`. If `adapters` section is missing, stdout is used.

```yaml
adapters:
  - type: stdout
    pretty: true

  - type: http
    url: "https://example.com/webhook"
    method: POST
    headers:
      Authorization: "Bearer token"
    timeout: 10

  - type: mongodb
    uri: "mongodb://user:pass@mongo:27017"
    database: "telegram"
    collection: "messages"

  - type: rabbitmq
    url: "amqp://guest:guest@localhost/"
    routing_key: "telegram"
```

Adapters run in parallel — each message is sent to all active adapters simultaneously.

### Docker

The default Docker entrypoint runs the listener:

```bash
docker run -e TELEGRAM_API_ID=12345678 \
           -e TELEGRAM_API_HASH=a1b2c3d4... \
           -e TELEGRAM_SESSION=1ApW... \
           mainpart/telegram-client

# With config file (for adapter settings)
docker run -v ./config.yaml:/app/config.yaml mainpart/telegram-client

# Run CLI commands instead
docker run --entrypoint telegram-cli \
           -v ./config.yaml:/app/config.yaml \
           mainpart/telegram-client chats
```

---

## 3. REST API

HTTP server built with FastAPI. Auto-generated Swagger docs at `http://localhost:8000/docs`.

```bash
pip install fastapi uvicorn
python telegram_api.py
# or
uvicorn telegram_api:app --host 0.0.0.0 --port 8000
```

### Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/chats` | List chats |
| GET | `/messages/{chat_id}` | Read messages (with filters) |
| POST | `/messages/{chat_id}` | Send message |
| PUT | `/messages/{chat_id}/{message_id}` | Edit message |
| POST | `/messages/{chat_id}/{message_id}/forward` | Forward message |
| POST | `/messages/{chat_id}/{message_id}/reaction` | Add reaction |
| POST | `/messages/{chat_id}/{message_id}/click` | Click button |
| GET | `/messages/{chat_id}/{message_id}/download` | Download file |
| GET | `/search/messages` | Search messages |
| GET | `/search/contacts` | Search contacts |
| GET | `/entities/{id}` | Entity info |

### Examples

```bash
curl 'http://localhost:8000/chats?limit=5'
curl 'http://localhost:8000/messages/1744485600?limit=10&has_media=true'
curl 'http://localhost:8000/search/contacts?q=John&limit=3'
curl 'http://localhost:8000/entities/mike_kuleshov'
curl -X POST http://localhost:8000/messages/1744485600 \
  -H 'Content-Type: application/json' \
  -d '{"text": "Hello!"}'
curl -X PUT http://localhost:8000/messages/1744485600/12345 \
  -H 'Content-Type: application/json' \
  -d '{"text": "Edited text"}'
curl -X POST http://localhost:8000/messages/1744485600/12345/reaction \
  -H 'Content-Type: application/json' \
  -d '{"emoji": "🔥"}'
```

---

## 4. MCP Server

Exposes all Telegram commands as tools for AI assistants. Works with Claude Code, Claude Desktop, Cursor, and any MCP-compatible client.

### Setup with Claude Code

```bash
pip install 'telegram-client[mcp]'

claude mcp add -s user \
  -e TELEGRAM_API_ID=12345678 \
  -e TELEGRAM_API_HASH=a1b2c3d4... \
  -e TELEGRAM_SESSION=1ApW... \
  telegram -- python /path/to/telegram_mcp.py
```

Or add to `~/.claude.json`:

```json
{
  "mcpServers": {
    "telegram": {
      "type": "stdio",
      "command": "python",
      "args": ["telegram_mcp.py"],
      "env": {
        "TELEGRAM_API_ID": "12345678",
        "TELEGRAM_API_HASH": "a1b2c3d4...",
        "TELEGRAM_SESSION": "1ApW..."
      }
    }
  }
}
```

If `config.yaml` exists in the working directory, env variables are not needed.

### Remote setup (no local clone)

```json
{
  "mcpServers": {
    "telegram": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/mainpart/telegram-client", "telegram_mcp"],
      "env": {
        "TELEGRAM_API_ID": "12345678",
        "TELEGRAM_API_HASH": "a1b2c3d4...",
        "TELEGRAM_SESSION": "1ApW..."
      }
    }
  }
}
```

### Available Tools

| Tool | Description |
|------|-------------|
| `tg_get_messages` | Read messages from a chat (with filters) |
| `tg_send_message` | Send text, files (local paths or URLs), or both |
| `tg_edit_message` | Edit a message |
| `tg_delete_message` | Delete a message |
| `tg_forward_message` | Forward a message |
| `tg_add_reaction` | Add emoji reaction |
| `tg_download_file` | Download file from message |
| `tg_search_messages` | Search across all chats |
| `tg_search_chat` | Search within a specific chat |
| `tg_search` | Search users, groups, channels |
| `tg_list_chats` | List recent chats |
| `tg_get_entities` | Get user/chat info |
