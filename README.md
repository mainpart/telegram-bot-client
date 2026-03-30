# Telegram Client

CLI and REST API for interacting with Telegram via a user account. Designed for automation, scripting and integrations.

## Project Structure

```
telegram_cli.py        — CLI for one-shot commands and real-time listener
telegram_api.py        — REST API server (FastAPI)
telegram_mcp.py        — MCP server for AI assistants
tg/                    — Shared library (core, commands, listeners)
adapters/              — Output adapters (stdout, http, mongodb, rabbitmq)
```

## Installation

### Homebrew

```bash
brew tap mainpart/telegram-client
brew install telegram-client
```

This installs `telegram-cli` with shell completions for bash, zsh and fish.

### pip

```bash
pip install git+https://github.com/mainpart/telegram-client.git
```

### From source

```bash
git clone https://github.com/mainpart/telegram-client.git
cd telegram-client
pip install .
```

### Docker

```bash
docker run -e TELEGRAM_API_ID=12345678 \
           -e TELEGRAM_API_HASH=a1b2c3d4... \
           -e TELEGRAM_SESSION=1ApW... \
           mainpart/telegram-client
```

With config file:

```bash
docker run -v ./config.yaml:/app/config.yaml mainpart/telegram-client
```

Override entrypoint for CLI commands:

```bash
docker run --entrypoint telegram-cli \
           -e TELEGRAM_API_ID=12345678 \
           -e TELEGRAM_API_HASH=a1b2c3d4... \
           -e TELEGRAM_SESSION=1ApW... \
           mainpart/telegram-client chats
```

### Optional dependencies

```bash
pip install 'telegram-client[mcp]'       # for telegram_mcp.py (MCP server)
pip install 'telegram-client[http]'      # for http adapter
pip install 'telegram-client[mongodb]'   # for mongodb adapter
pip install 'telegram-client[rabbitmq]'  # for rabbitmq adapter
pip install 'telegram-client[all]'       # all adapters
pip install fastapi uvicorn              # for telegram_api.py
```

## Setup

1. Get `api_id` and `api_hash` at [my.telegram.org](https://my.telegram.org)

2. Create `config.yaml` (or copy from `config.yaml-default`):

```yaml
telegram:
  api_id: 12345678
  api_hash: "a1b2c3d4e5f6..."
```

3. Generate a session token:

```bash
telegram-cli init
```

The token is saved to `config.yaml` automatically. Alternatively, set it via environment variable:

```bash
export TELEGRAM_SESSION="..."
```

Phone number can be specified in config (only needed for `init`):

```yaml
telegram:
  phone_number: "+79001234567"
```

## Commands

All commands output JSON to stdout, errors to stderr. Run `telegram-cli <command> --help` for details.

### init

Interactive login. Prompts for phone number, confirmation code and 2FA password (if enabled). Saves the StringSession token to `config.yaml`.

```bash
telegram-cli init
```

### read

Read messages from a chat. Chat accepts a username (`mike_kuleshov`) or numeric ID (`1744485600`, `-1001605174968`). Without `--limit`, returns the last 20 messages.

```bash
# Last 20 messages
telegram-cli read mike_kuleshov

# By numeric ID
telegram-cli read -1001605174968

# Specify limit
telegram-cli read mike_kuleshov --limit 100

# All messages (no limit)
telegram-cli read mike_kuleshov --limit 0

# Read forward (newer) from message ID 5000
telegram-cli read mike_kuleshov --from-id 5000 --forward

# Range from 1000 to 2000 (boundaries excluded)
telegram-cli read mike_kuleshov --from-id 1000 --to-id 2000 --forward

# Range with boundaries included
telegram-cli read mike_kuleshov --from-id 1000 --to-id 2000 --forward --inclusive

# With filtering profile
telegram-cli read mike_kuleshov --limit 50 --profile dialogue

# Only incoming messages with media
telegram-cli read mike_kuleshov --limit 50 --incoming-only --has-media

# Messages matching a regex pattern
telegram-cli read mike_kuleshov --pattern "hello|привет"

# Messages from a specific user
telegram-cli read -1001605174968 --from-user 809799943

# Only forwarded / replies / with reactions / outgoing
telegram-cli read mike_kuleshov --forwarded-only
telegram-cli read mike_kuleshov --replies-only
telegram-cli read mike_kuleshov --has-reactions
telegram-cli read mike_kuleshov --outgoing-only
```

### send

Send a message, files, or both. Text is optional when sending files.

```bash
# Text message
telegram-cli send 1744485600 "Hello!"

# Single file
telegram-cli send 1744485600 --files photo.jpg

# Multiple files
telegram-cli send 1744485600 --files photo1.jpg photo2.jpg video.mp4

# Files with caption
telegram-cli send 1744485600 "Document" --files doc.pdf

# Reply to a message
telegram-cli send 1744485600 "Thanks!" --reply-to 12345

# File as reply
telegram-cli send 1744485600 --files result.pdf --reply-to 12345
```

### edit

Edit your own message.

```bash
telegram-cli edit 1744485600 123 "Corrected text"
```

### delete

Delete a message. Only works for your own messages or in chats where you have delete permissions.

```bash
telegram-cli delete 1744485600 123
```

### forward

Forward a message from one chat to another.

```bash
telegram-cli forward -1001605174968 123 1744485600
```

### reply

Reply to a message. Text is optional when sending files. With `--target-chat` — cross-chat reply (files not supported).

```bash
# Reply in the same chat
telegram-cli reply 1744485600 123 "Reply text"

# Reply with files
telegram-cli reply 1744485600 123 --files photo.jpg

# Cross-chat reply
telegram-cli reply -1001605174968 123 "Check this" --target-chat 1744485600
```

### react

Add an emoji reaction to a message.

```bash
telegram-cli react 1744485600 123 "🔥"
telegram-cli react 1744485600 123 "👍"
```

### click

Click an inline button on a message.

```bash
telegram-cli click 1744485600 123 "Confirm"
```

### download

Download a file from a message (photo, video, document, voice). Saves to the current directory.

```bash
telegram-cli download 1744485600 211175
```

### search-messages

Search message text across all chats. Results are grouped by chat.

```bash
# Simple search
telegram-cli search-messages "search query"

# With limit
telegram-cli search-messages "search query" --limit 50

# Only in groups / channels
telegram-cli search-messages "search query" --groups-only
telegram-cli search-messages "search query" --broadcasts-only

# Only photos
telegram-cli search-messages "search query" --filter photo

# Date range
telegram-cli search-messages "search query" --min-date 2026-01-01 --max-date 2026-03-01

# With filtering profile
telegram-cli search-messages "search query" --profile dialogue
```

### search-contacts

Search users, groups, channels by name or username.

```bash
telegram-cli search-contacts "John"
telegram-cli search-contacts "channel name" --limit 5
```

### search-chat

Search messages within a specific chat (server-side). Faster than `--pattern` which filters locally.

```bash
# Search in a specific chat
telegram-cli search-chat -5241856808 "FAR manager"

# With media filter
telegram-cli search-chat 1744485600 "photo" --filter photo

# From a specific user
telegram-cli search-chat -1001605174968 "test" --from-user 809799943

# Date range
telegram-cli search-chat 1744485600 "test" --min-date 2026-03-01
```

### info

Full information about users, chats or channels.

```bash
# By username
telegram-cli info mike_kuleshov

# By numeric ID
telegram-cli info 1744485600

# Multiple entities
telegram-cli info mike_kuleshov Kuleshov 123456789
```

### listen

Real-time message listener. Outputs each new, edited or deleted message as JSON. Press Ctrl+C to stop.

Output goes through adapters (stdout by default). Configure adapters in `config.yaml`.

```bash
# Listen to everything
telegram-cli listen

# Specific chat
telegram-cli listen --chat 1744485600

# Multiple chats
telegram-cli listen --chat 1744485600 --chat -1001605174968

# Private messages only
telegram-cli listen --private-only

# Only messages mentioning me
telegram-cli listen --mentioned-only

# Incoming only with regex filter
telegram-cli listen --incoming-only --pattern "urgent"

# Only incoming messages with media in a specific chat
telegram-cli listen --chat 1744485600 --incoming-only --has-media

# With filtering profile
telegram-cli listen --profile dialogue
```

### Message Filters

Filters work with `read` and `listen`:

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

`--profile <name>` applies a profile from `profiles.json` to clean JSON output. Removes unwanted keys and object types:

```json
{
  "dialogue": {
    "stop_keys": ["access_hash", "file_reference", "dc_id"],
    "stop_objects": ["MessageEntityBold", "MessageActionPinMessage"]
  }
}
```

### Listener Events

- **NewMessage** — new messages
- **MessageEdited** — edited messages
- **MessageDeleted** — deleted messages (only IDs, no content)
- **CallbackQuery** — inline button presses (bot mode only)

### Output Adapters

Configured in `config.yaml`. If `adapters` section is missing, stdout is used by default.

```yaml
adapters:
  - type: stdout
    pretty: true              # formatted JSON (default true)

  - type: http
    url: "https://example.com/webhook"
    method: POST              # default POST
    headers:
      Authorization: "Bearer token"
    timeout: 10               # seconds, default 10

  - type: mongodb
    uri: "mongodb://user:pass@mongo:27017"
    database: "telegram"
    collection: "messages"    # default "messages"

  - type: rabbitmq
    url: "amqp://guest:guest@localhost/"   # default localhost
    routing_key: "telegram"                # default "telegram"
```

Adapters run in parallel — each message is sent to all active adapters simultaneously.

## telegram_api.py

REST API server built with FastAPI. Auto-generated Swagger docs at `http://localhost:8000/docs`.

```bash
python telegram_api.py
# or
uvicorn telegram_api:app --host 0.0.0.0 --port 8000
```

### Endpoints

| Method | URL | Description | Parameters |
|--------|-----|-------------|------------|
| GET | `/messages/{chat_id}` | Read messages | query: fromId, toId, inclusive, forward, backward, limit, profile, filters |
| POST | `/messages/{chat_id}` | Send message | body: `{text, replyTo}` |
| PUT | `/messages/{chat_id}/{message_id}` | Edit message | body: `{text}` |
| POST | `/messages/{chat_id}/{message_id}/forward` | Forward message | body: `{targetChat}` |
| POST | `/messages/{chat_id}/{message_id}/reaction` | Add reaction | body: `{emoji}` |
| POST | `/messages/{chat_id}/{message_id}/click` | Click button | body: `{buttonText}` |
| GET | `/messages/{chat_id}/{message_id}/download` | Download file | returns file |
| GET | `/search/messages` | Search messages | query: q, limit, profile |
| GET | `/search/contacts` | Search contacts | query: q, limit, profile |
| GET | `/chats` | List chats | query: limit, profile |
| GET | `/entities/{id}` | Entity info | query: profile |

### Examples

```bash
curl 'http://localhost:8000/chats?limit=5'
curl 'http://localhost:8000/search/contacts?q=John&limit=3'
curl 'http://localhost:8000/messages/1744485600?limit=10&has_media=true'
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

## Bot Mode

No session required. Uses `bot_token` from `config.yaml` or `TELEGRAM_BOT_TOKEN` env.

```yaml
# config.yaml
telegram:
  api_id: 12345678
  api_hash: "a1b2c3d4..."
  bot_token: "123456:ABC-DEF..."
```

```bash
# Bot listens to all chats
telegram-cli listen --bot

# Bot listens to a specific chat
telegram-cli listen --bot --chat -1001605174968

# Bot listens to private messages only
telegram-cli listen --bot --private-only

# Send a message as bot
telegram-cli send 123 "test" --bot
```

In bot mode, `CallbackQuery` events (inline button presses) are also handled.

## telegram_mcp.py

MCP server exposing all Telegram commands as tools. Works with any MCP-compatible client (Claude Code, Claude Desktop, Cursor, etc.).

### Configuration

Reads credentials from `config.yaml` or environment variables:

| config.yaml | env |
|-------------|-----|
| `telegram.api_id` | `TELEGRAM_API_ID` |
| `telegram.api_hash` | `TELEGRAM_API_HASH` |
| `telegram.session_string` | `TELEGRAM_SESSION` |
| `telegram.bot_token` | `TELEGRAM_BOT_TOKEN` |

### Local setup (Claude Code)

```bash
pip install mcp

claude mcp add -s user \
  -e TELEGRAM_API_ID=12345678 \
  -e TELEGRAM_API_HASH=a1b2c3d4... \
  -e TELEGRAM_SESSION=1ApW... \
  telegram -- python /path/to/telegram_mcp.py
```

Or add manually to `~/.claude.json`:

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

### Remote setup (via git)

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

`uvx` caches the package — no re-download on subsequent runs.

### Available tools

| Tool | Description |
|------|-------------|
| `tg_get_messages` | Read messages from a chat (with filters) |
| `tg_send_message` | Send a message with text, files (local paths or URLs), or both |
| `tg_edit_message` | Edit a message |
| `tg_delete_message` | Delete a message |
| `tg_forward_message` | Forward a message |
| `tg_add_reaction` | Add emoji reaction |
| `tg_download_file` | Download file from message |
| `tg_search_messages` | Search message text across all chats (with filters: media type, date range, chat type) |
| `tg_search_chat` | Search messages within a specific chat (server-side, fast) |
| `tg_search` | Search users, groups, and channels by name or username |
| `tg_list_chats` | List recent chats |
| `tg_get_entities` | Get user/chat info |
