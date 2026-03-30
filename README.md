# Telegram Client

CLI, REST API and MCP server for interacting with Telegram via a user account. Designed for automation, scripting and integrations.

## Features

- Read, send, edit, delete, forward messages
- Search across all chats, within a chat, or by contacts
- Download files, add reactions, click inline buttons
- Real-time message listener with output adapters (stdout, HTTP webhook, MongoDB, RabbitMQ)
- Bot mode — same commands using a bot token instead of user session
- Filtering by sender, media type, regex, date range, reactions, forwards, replies
- Filtering profiles to clean up JSON output

## Modes of Operation

| Mode | Description |
|------|-------------|
| **CLI** | One-shot commands from terminal or scripts |
| **Listener** | Real-time message streaming with output adapters |
| **REST API** | HTTP server for web integrations |
| **MCP Server** | AI assistant tool integration (Claude, Cursor, etc.) |

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

## Setup

1. Go to [my.telegram.org](https://my.telegram.org), log in with your phone number, and create an application. You will get `api_id` and `api_hash` — these are required by Telegram for any third-party client to connect to their API.

2. Create `config.yaml`:

```yaml
telegram:
  api_id: 12345678
  api_hash: "a1b2c3d4e5f6..."
```

3. Generate a session token:

```bash
telegram-cli init --phone +79001234567
```

This will prompt for a confirmation code and 2FA password (if enabled). The session token is saved to `config.yaml` automatically.

Alternatively, all credentials can be set via environment variables:

```bash
export TELEGRAM_API_ID=12345678
export TELEGRAM_API_HASH=a1b2c3d4...
export TELEGRAM_SESSION=1ApW...
```

### Config file location

`telegram-cli` looks for `config.yaml` in this order:

1. `--config /path/to/config.yaml` — explicit path (highest priority)
2. `./config.yaml` — current working directory
3. `~/.config/telegram-client/config.yaml` — XDG standard location

`profiles.json` is looked up next to the resolved config file.

In Docker, `./config.yaml` maps to `/app/config.yaml` (the container's `WORKDIR`). If no config file is found, environment variables are used as fallback.

---

## 1. CLI

One-shot commands. Outputs JSON to stdout, errors to stderr. Run `telegram-cli <command> --help` for full usage of any command.

### init

Login and generate a session token.

```bash
telegram-cli init --phone +79001234567
```

| Arg | Description |
|-----|-------------|
| `--phone` | Phone number in international format |

### chats

```bash
telegram-cli chats                         # last 100 dialogs
telegram-cli chats --limit 500 --bot       # as bot, 500 dialogs
```

| Arg | Description |
|-----|-------------|
| `--limit` | Number of chats (default: 100) |
| `--profile` | Filtering profile (see [Profiles](#filtering-profiles)) |
| `--bot` | Use bot token (see [Bot Mode](#bot-mode)) |

### read

Read messages from a chat.

```bash
telegram-cli read mike_kuleshov                                # last 20 messages by username
telegram-cli read 1744485600 --limit 100 --has-media           # last 100 with media by ID
telegram-cli read 123 --from-id 5000 --forward --incoming-only # newer from ID 5000, incoming only
telegram-cli read 123 --from-id 1000 --to-id 2000 --inclusive  # range with boundaries included
telegram-cli read 123 --pattern "hello|привет" --from-user 809 # regex + specific sender
telegram-cli read 123 --forwarded-only --has-reactions         # forwarded messages with reactions
```

| Arg | Description |
|-----|-------------|
| `chat` | **Required.** Chat ID or username |
| `--limit` | Number of messages (default: 20, 0 = all) |
| `--from-id` | Start message ID |
| `--to-id` | End message ID |
| `--forward` | Read newer messages |
| `--backward` | Read older messages |
| `--inclusive` | Include boundary messages in range |
| `--profile` | Filtering profile |
| `--bot` | Use bot token |
| Filters | `--incoming-only` `--outgoing-only` `--from-user` `--pattern` `--has-media` `--forwarded-only` `--replies-only` `--has-reactions` |

### send

Send a message, files, or both. Text is optional when sending files.

```bash
telegram-cli send 123 "Hello!"                          # text message
telegram-cli send 123 --files photo.jpg video.mp4       # files only
telegram-cli send 123 "Caption" --files doc.pdf         # text + file
telegram-cli send 123 "Reply" --reply-to 456 --bot      # reply as bot
```

| Arg | Description |
|-----|-------------|
| `chat` | **Required.** Chat ID or username |
| `text` | Message text (optional if `--files` provided) |
| `--files` | One or more file paths |
| `--reply-to` | Message ID to reply to |
| `--bot` | Use bot token |

### edit

```bash
telegram-cli edit 123 456 "Corrected text"              # 123=chat, 456=message ID
```

| Arg | Description |
|-----|-------------|
| `chat` | **Required.** Chat ID or username |
| `message_id` | **Required.** Message ID to edit |
| `text` | **Required.** New message text |
| `--bot` | Use bot token |

### delete

```bash
telegram-cli delete 123 456                             # 123=chat, 456=message ID
```

| Arg | Description |
|-----|-------------|
| `chat` | **Required.** Chat ID or username |
| `message_id` | **Required.** Message ID to delete |
| `--bot` | Use bot token |

### forward

```bash
telegram-cli forward -1001605174968 123 1744485600      # source_chat msg_id target_chat
```

| Arg | Description |
|-----|-------------|
| `chat` | **Required.** Source chat ID or username |
| `message_id` | **Required.** Message ID to forward |
| `target_chat` | **Required.** Target chat ID or username |
| `--bot` | Use bot token |

### reply

Reply to a message. Text is optional when sending files. With `--target-chat` — cross-chat reply (files not supported in cross-chat mode).

```bash
telegram-cli reply 123 456 "Reply text"                 # 123=chat, 456=message ID
telegram-cli reply 123 456 --files photo.jpg            # reply with file, no text
telegram-cli reply 123 456 "See this" --target-chat 789 # cross-chat reply
```

| Arg | Description |
|-----|-------------|
| `chat` | **Required.** Chat ID or username |
| `message_id` | **Required.** Message ID to reply to |
| `text` | Reply text (optional if `--files` provided) |
| `--files` | One or more file paths |
| `--target-chat` | Target chat for cross-chat reply |
| `--bot` | Use bot token |

### react

```bash
telegram-cli react 123 456 "🔥"                         # 123=chat, 456=message ID
```

| Arg | Description |
|-----|-------------|
| `chat` | **Required.** Chat ID or username |
| `message_id` | **Required.** Message ID |
| `emoji` | **Required.** Reaction emoji |
| `--bot` | Use bot token |

### click

Click an inline button on a message.

```bash
telegram-cli click 123 456 "Confirm"                    # 123=chat, 456=message ID
```

| Arg | Description |
|-----|-------------|
| `chat` | **Required.** Chat ID or username |
| `message_id` | **Required.** Message ID |
| `button_text` | **Required.** Button text to click |
| `--bot` | Use bot token |

### download

Download a file attached to a message. Saves to the current directory.

```bash
telegram-cli download 123 456                           # 123=chat, 456=message ID
```

| Arg | Description |
|-----|-------------|
| `chat` | **Required.** Chat ID or username |
| `message_id` | **Required.** Message ID |
| `--bot` | Use bot token |

### search-messages

Search message text across all chats.

```bash
telegram-cli search-messages "query"                                      # basic search
telegram-cli search-messages "query" --groups-only --limit 50             # groups, max 50
telegram-cli search-messages "query" --filter photo --min-date 2026-01-01 # photos since date
telegram-cli search-messages "query" --broadcasts-only --profile dialogue # channels + profile
```

| Arg | Description |
|-----|-------------|
| `query` | **Required.** Search text |
| `--limit` | Max results |
| `--filter` | Media type: `photo` `video` `document` `url` `voice` `gif` `music` `round_video` `mentions` `pinned` |
| `--min-date` | Start date (YYYY-MM-DD) |
| `--max-date` | End date (YYYY-MM-DD) |
| `--groups-only` | Search in groups only |
| `--users-only` | Search in private chats only |
| `--broadcasts-only` | Search in channels only |
| `--profile` | Filtering profile |
| `--bot` | Use bot token |

### search-contacts

Search users, groups, channels by name or username.

```bash
telegram-cli search-contacts "John" --limit 5           # search with limit
```

| Arg | Description |
|-----|-------------|
| `query` | **Required.** Search text |
| `--limit` | Max results |
| `--profile` | Filtering profile |
| `--bot` | Use bot token |

### search-chat

Search within a specific chat (server-side, fast).

```bash
telegram-cli search-chat 123 "query"                              # basic search in chat
telegram-cli search-chat 123 "photo" --filter photo --from-user 8 # photos from user
telegram-cli search-chat 123 "test" --min-date 2026-03-01         # since date
```

| Arg | Description |
|-----|-------------|
| `chat` | **Required.** Chat ID or username |
| `query` | **Required.** Search text |
| `--limit` | Max results |
| `--filter` | Media type filter (same values as search-messages) |
| `--from-user` | Filter by sender ID |
| `--min-date` | Start date (YYYY-MM-DD) |
| `--max-date` | End date (YYYY-MM-DD) |
| `--profile` | Filtering profile |
| `--bot` | Use bot token |

### info

Get full info about users or chats.

```bash
telegram-cli info mike_kuleshov 1744485600               # multiple entities at once
```

| Arg | Description |
|-----|-------------|
| `entity` | **Required.** One or more user/chat IDs or usernames |
| `--profile` | Filtering profile |
| `--bot` | Use bot token |

### Bot Mode

By default, `telegram-cli` works as a user client using a session token. With `--bot`, it uses a bot token instead. The difference:

- **User mode** — full access: read any chat you're in, search globally, download from any chat. Requires session token from `telegram-cli init`.
- **Bot mode** — limited to chats where the bot was added. Cannot search globally. Requires `bot_token` in `config.yaml` or `TELEGRAM_BOT_TOKEN` env.

```yaml
telegram:
  bot_token: "123456:ABC-DEF..."
```

```bash
telegram-cli listen --bot --chat -1001605174968  # bot listens to a group
telegram-cli send 123 "hello" --bot              # bot sends a message
```

In bot mode, `listen` also handles `CallbackQuery` events (inline button presses).

### Filtering Profiles

Telegram returns verbose JSON with many internal fields. Profiles let you strip unwanted keys and object types from the output.

Define profiles in `profiles.json` (same directory as `config.yaml`):

```json
{
  "dialogue": {
    "stop_keys": ["access_hash", "file_reference", "dc_id", "phone"],
    "stop_objects": ["MessageEntityBold", "MessageActionPinMessage"]
  }
}
```

Use with `--profile`:

```bash
telegram-cli read 123 --profile dialogue
telegram-cli chats --profile dialogue
```

Without `--profile`, the default profile is used (no filtering).

---

## 2. Listener

Real-time message streaming. Runs until Ctrl+C. Each message is output as JSON through configured adapters.

```bash
telegram-cli listen                                          # all messages, stdout
telegram-cli listen --chat 123 --chat 456 --incoming-only    # specific chats, incoming only
telegram-cli listen --private-only --has-media                # private messages with media
telegram-cli listen --mentioned-only --pattern "urgent"       # mentions matching regex
telegram-cli listen --bot --chat -1001605174968               # bot mode
```

| Arg | Description |
|-----|-------------|
| `--chat` | Chat to listen (repeatable for multiple chats) |
| `--private-only` | Private messages only |
| `--mentioned-only` | Only messages mentioning me |
| `--profile` | Filtering profile |
| `--bot` | Use bot token |
| Filters | `--incoming-only` `--outgoing-only` `--from-user` `--pattern` `--has-media` `--forwarded-only` `--replies-only` `--has-reactions` |

### Events

- **NewMessage** — new messages
- **MessageEdited** — edited messages
- **MessageDeleted** — deleted messages (only IDs)
- **CallbackQuery** — inline button presses (bot mode only)

### Output Adapters

Configure in `config.yaml`. If `adapters` section is missing, stdout is used.

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

```bash
# Run listener with env variables
docker run -e TELEGRAM_API_ID=12345678 \
           -e TELEGRAM_API_HASH=a1b2c3d4... \
           -e TELEGRAM_SESSION=1ApW... \
           mainpart/telegram-client telegram-cli listen

# Run listener with config (for adapter settings)
docker run -v ./config.yaml:/app/config.yaml \
           mainpart/telegram-client telegram-cli listen --chat 123

# Run REST API server
docker run -p 8000:8000 \
           -v ./config.yaml:/app/config.yaml \
           mainpart/telegram-client \
           uvicorn telegram_api:app --host 0.0.0.0 --port 8000
```

---

## 3. REST API

HTTP server built with FastAPI. Swagger docs at `http://localhost:8000/docs`.

```bash
pip install fastapi uvicorn
python telegram_api.py
```

### Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/chats` | List chats |
| GET | `/messages/{chat_id}` | Read messages (supports all read filters) |
| POST | `/messages/{chat_id}` | Send message `{text, replyTo}` |
| PUT | `/messages/{chat_id}/{message_id}` | Edit message `{text}` |
| POST | `/messages/{chat_id}/{message_id}/forward` | Forward `{targetChat}` |
| POST | `/messages/{chat_id}/{message_id}/reaction` | React `{emoji}` |
| POST | `/messages/{chat_id}/{message_id}/click` | Click button `{buttonText}` |
| GET | `/messages/{chat_id}/{message_id}/download` | Download file |
| GET | `/search/messages` | Search messages `?q=...` |
| GET | `/search/contacts` | Search contacts `?q=...` |
| GET | `/entities/{id}` | Entity info |

### Examples

```bash
curl 'http://localhost:8000/chats?limit=5'
curl 'http://localhost:8000/messages/1744485600?limit=10&has_media=true'
curl 'http://localhost:8000/search/contacts?q=John&limit=3'
curl -X POST http://localhost:8000/messages/1744485600 \
  -H 'Content-Type: application/json' -d '{"text": "Hello!"}'
curl -X POST http://localhost:8000/messages/1744485600/12345/reaction \
  -H 'Content-Type: application/json' -d '{"emoji": "🔥"}'
```

---

## 4. MCP Server

Exposes all Telegram commands as tools for AI assistants (Claude Code, Claude Desktop, Cursor, etc.).

### Setup

Credentials are the same as described in [Setup](#setup) — `api_id`, `api_hash` and `session_string` from `config.yaml` or environment variables.

```bash
claude mcp add -s user \
  -e TELEGRAM_API_ID=... \
  -e TELEGRAM_API_HASH=... \
  -e TELEGRAM_SESSION=... \
  telegram -- python /path/to/telegram_mcp.py
```

Remote setup (no local clone needed):

```json
{
  "mcpServers": {
    "telegram": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/mainpart/telegram-client", "telegram_mcp"],
      "env": {
        "TELEGRAM_API_ID": "...",
        "TELEGRAM_API_HASH": "...",
        "TELEGRAM_SESSION": "..."
      }
    }
  }
}
```

### Available Tools

| Tool | Description |
|------|-------------|
| `tg_get_messages` | Read messages from a chat (with filters) |
| `tg_send_message` | Send text, files, or both |
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
