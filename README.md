# Telegram Client

CLI and REST API for interacting with Telegram via a user account. Designed for automation, scripting and integrations.

## Project Structure

```
telegram_cli.py        — CLI for one-shot commands (read, send, search, download)
telegram_listen.py     — Real-time message listener with output adapters
telegram_api.py        — REST API server (FastAPI)
tg/                    — Shared library (core, commands, listeners)
adapters/              — Output adapters (stdout, http, mongodb, rabbitmq)
```

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

To run without activating the venv:

```bash
.venv/bin/python telegram_cli.py --list-chats
```

Optional dependencies (install as needed):

```bash
pip install fastapi uvicorn    # for telegram_api.py
pip install aiohttp            # for http adapter
pip install motor              # for mongodb adapter
pip install aio-pika           # for rabbitmq adapter
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
python telegram_cli.py --init
```

The token is saved to `config.yaml` automatically. Alternatively, set it via environment variable:

```bash
export TELEGRAM_SESSION="..."
```

Phone number can be specified in config (only needed for `--init`):

```yaml
telegram:
  phone_number: "+79001234567"
```

## telegram_cli.py

One-shot commands. Outputs JSON to stdout, errors to stderr.

### --init

Interactive login. Prompts for phone number, confirmation code and 2FA password (if enabled). Saves the StringSession token to `config.yaml`.

```bash
python telegram_cli.py --init
```

### Reading Messages (--chat)

`--chat` accepts a username (`mike_kuleshov`) or numeric ID (`1744485600`, `-1001605174968`). Groups often don't have usernames — use their numeric ID (find via `--search-contacts` or `--list-chats`).

Without additional arguments, returns the last 20 messages.

```bash
# Last 20 messages (default)
python telegram_cli.py --chat mike_kuleshov

# By numeric ID
python telegram_cli.py --chat -1001605174968

# Specify limit
python telegram_cli.py --chat mike_kuleshov --limit 100

# All messages (no limit)
python telegram_cli.py --chat mike_kuleshov --limit 0

# Read backward (older) from message ID 5000
python telegram_cli.py --chat mike_kuleshov --from-id 5000

# Read forward (newer) from message ID 5000
python telegram_cli.py --chat mike_kuleshov --from-id 5000 --forward

# Range from 1000 to 2000 (boundaries excluded)
python telegram_cli.py --chat mike_kuleshov --from-id 1000 --to-id 2000 --forward

# Range with boundaries included
python telegram_cli.py --chat mike_kuleshov --from-id 1000 --to-id 2000 --forward --inclusive

# With filtering profile
python telegram_cli.py --chat mike_kuleshov --limit 50 --profile dialogue

# Only incoming messages with media
python telegram_cli.py --chat mike_kuleshov --limit 50 --incoming-only --has-media

# Messages matching a regex pattern
python telegram_cli.py --chat mike_kuleshov --pattern "hello|привет"

# Messages from a specific user
python telegram_cli.py --chat -1001605174968 --from-user 809799943

# Only forwarded messages
python telegram_cli.py --chat mike_kuleshov --forwarded-only

# Only replies
python telegram_cli.py --chat mike_kuleshov --replies-only

# Only messages with reactions
python telegram_cli.py --chat mike_kuleshov --has-reactions

# Only outgoing messages
python telegram_cli.py --chat mike_kuleshov --outgoing-only
```

### Search

#### --search-contacts

Search users, groups, channels by name or username. Uses Telegram's `contacts.Search` API.

```bash
# Search by name
python telegram_cli.py --search-contacts "Михаил Кулешов"

# Partial name
python telegram_cli.py --search-contacts "Кулешов"

# With limit (default 20)
python telegram_cli.py --search-contacts "марс и венера" --limit 5
```

#### --search-messages

Search message text across all chats. Results are grouped by chat.

```bash
# Simple search
python telegram_cli.py --search-messages "search query"

# With limit (default 100)
python telegram_cli.py --search-messages "search query" --limit 50

# Only in groups
python telegram_cli.py --search-messages "search query" --groups-only

# Only in channels
python telegram_cli.py --search-messages "search query" --broadcasts-only

# Only photos
python telegram_cli.py --search-messages "search query" --filter photo

# Date range
python telegram_cli.py --search-messages "search query" --min-date 2026-01-01 --max-date 2026-03-01

# With filtering profile
python telegram_cli.py --search-messages "search query" --profile dialogue
```

#### --search-chat

Search messages within a specific chat (server-side). Faster than `--pattern` which filters locally.

```bash
# Search in a specific chat
python telegram_cli.py --search-chat "FAR manager" --chat -5241856808

# With media filter
python telegram_cli.py --search-chat "photo" --chat 1744485600 --filter photo

# From a specific user
python telegram_cli.py --search-chat "test" --chat -1001605174968 --from-user 809799943

# Date range
python telegram_cli.py --search-chat "test" --chat 1744485600 --min-date 2026-03-01
```

### --list-chats

List recent dialogs with chat info and last message.

```bash
# Last 100 dialogs (default)
python telegram_cli.py --list-chats

# More dialogs
python telegram_cli.py --list-chats --limit 500

# With profile
python telegram_cli.py --list-chats --profile dialogue
```

### --get-entities

Full information about users, chats or channels. Includes bio, photo, birthday, common chats count.

```bash
# By username
python telegram_cli.py --get-entities mike_kuleshov

# By numeric ID
python telegram_cli.py --get-entities 1744485600

# Multiple entities
python telegram_cli.py --get-entities mike_kuleshov Kuleshov 123456789

# With profile
python telegram_cli.py --get-entities mike_kuleshov --profile dialogue
```

### Sending Messages (--send-message / --send-files)

```bash
# Text message
python telegram_cli.py --chat 1744485600 --send-message "Hello!"

# Single file
python telegram_cli.py --chat 1744485600 --send-files photo.jpg

# Multiple files
python telegram_cli.py --chat 1744485600 --send-files photo1.jpg photo2.jpg video.mp4

# Files with caption
python telegram_cli.py --chat 1744485600 --send-files doc.pdf --send-message "Document"

# Reply to a message
python telegram_cli.py --chat 1744485600 --send-message "Thanks!" --reply-to 12345

# File as reply
python telegram_cli.py --chat 1744485600 --send-files result.pdf --reply-to 12345
```

### --forward-message

Forward a message from one chat to another.

```bash
# Forward message 123 from chat A to chat B
python telegram_cli.py --chat -1001605174968 --message-id 123 --forward-message --target-chat 1744485600

# By numeric IDs
python telegram_cli.py --chat -1001234567890 --message-id 456 --forward-message --target-chat -1009876543210
```

### --reply-message

Reply to a message. Without `--target-chat` — replies in the same chat. With `--target-chat` — cross-chat reply.

```bash
# Reply in the same chat
python telegram_cli.py --chat 1744485600 --message-id 123 --reply-message "Reply text"

# Cross-chat reply (reply in another chat referencing a message from --chat)
python telegram_cli.py --chat -1001605174968 --message-id 123 --reply-message "Check this" --target-chat 1744485600
```

### --edit-message

Edit your own message.

```bash
python telegram_cli.py --chat 1744485600 --message-id 123 --edit-message "Corrected text"
```

### --delete-message

Delete a message. Only works for your own messages or in chats where you have delete permissions.

```bash
python telegram_cli.py --chat 1744485600 --message-id 123 --delete-message
```

### --add-reaction

Add an emoji reaction to a message.

```bash
python telegram_cli.py --chat 1744485600 --message-id 123 --add-reaction "🔥"
python telegram_cli.py --chat 1744485600 --message-id 123 --add-reaction "👍"
```

### --click-button

Click an inline button on a message.

```bash
python telegram_cli.py --chat 1744485600 --message-id 123 --click-button "Confirm"
```

### --download

Download a file from a message (photo, video, document, voice). Saves to the current directory.

```bash
python telegram_cli.py --chat 1744485600 --message-id 211175 --download
```

### Message Filters

Filters work with `--chat` for reading messages:

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

## telegram_listen.py

Real-time message listener. Outputs each new, edited or deleted message as JSON. Press Ctrl+C to stop.

Output goes through adapters (stdout by default). Configure adapters in `config.yaml`.

Without arguments, listens to all messages from every chat.

```bash
# Listen to everything
python telegram_listen.py

# Specific chat
python telegram_listen.py --chat 1744485600

# Multiple chats
python telegram_listen.py --chat 1744485600 --chat -1001605174968

# Private messages only
python telegram_listen.py --private-only

# Only messages mentioning me
python telegram_listen.py --mentioned-only

# Incoming only with regex filter
python telegram_listen.py --incoming-only --pattern "urgent"

# Only incoming messages with media in a specific chat
python telegram_listen.py --chat 1744485600 --incoming-only --has-media

# With filtering profile
python telegram_listen.py --profile dialogue
```

### Listener Filters

| Filter | Description |
|---|---|
| `--chat <id>` | Specific chat (repeatable) |
| `--private-only` | Private messages only |
| `--mentioned-only` | Messages mentioning me |
| `--incoming-only` | Incoming messages only |
| `--outgoing-only` | Outgoing messages only |
| `--from-user <id>` | From a specific user |
| `--pattern <regex>` | Match text by regex |
| `--has-media` | Messages with media only |
| `--forwarded-only` | Forwarded messages only |
| `--replies-only` | Replies only |
| `--has-reactions` | Messages with reactions only |

### Events Handled

- **NewMessage** — new messages
- **MessageEdited** — edited messages
- **MessageDeleted** — deleted messages (only IDs, no content)
- **CallbackQuery** — inline button presses (bot mode only)

### Output Adapters

Configured in `config.yaml`. If `adapters` section is missing, stdout is used by default. Commented-out adapters are disabled.

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
curl 'http://localhost:8000/search/contacts?q=Кулешов&limit=3'
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

No session required. Uses `bot_token` from `config.yaml` or `TELEGRAM_BOT_TOKEN` env. Works with both `telegram_listen.py` and `telegram_cli.py`.

```yaml
# config.yaml
telegram:
  api_id: 12345678
  api_hash: "a1b2c3d4..."
  bot_token: "123456:ABC-DEF..."
```

```bash
# Bot listens to all chats
python telegram_listen.py --bot

# Bot listens to a specific chat
python telegram_listen.py --bot --chat -1001605174968

# Bot listens to private messages only
python telegram_listen.py --bot --private-only

# Send a message as bot
python telegram_cli.py --bot --chat 123 --send-message "test"
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
