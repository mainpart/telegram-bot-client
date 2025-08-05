# Telegram User Client CLI

This script is a command-line tool for interacting with Telegram as a user. It is designed for non-interactive use in scripts and automation, mimicking the `getUpdates` flow of the Telegram Bot API.

## Features

*   Connect to Telegram using your user account.
*   Fetch new messages from a chat since a given timestamp, outputting them as clean, filtered JSON.
*   Send messages to a chat.
*   Click buttons on existing messages.
*   Download files attached to messages.
*   Controlled, minimal output for easy parsing.
*   Debug mode for detailed logging.

## Setup

1.  **Install Dependencies**: This script requires several Python libraries. You can install them using pip:
    ```bash
    # Install from requirements.txt
    pip3 install -r requirements.txt
    
    # Or install manually
    pip3 install telethon configparser
    ```

2.  **Configure the application**: 
    
    a. Rename the configuration template:
    ```bash
    cp config.ini-default config.ini
    ```
    
    b. Edit `config.ini` and populate it with your credentials. You can get your `api_id` and `api_hash` from [my.telegram.org](https://my.telegram.org).

    ```ini
    [telegram]
    phone_number = YOUR_PHONE_NUMBER_HERE
    api_id = YOUR_API_ID_HERE
    api_hash = YOUR_API_HASH_HERE
    ```

    Replace the placeholder values with your actual credentials.

### Getting API Credentials

To use this script, you need to obtain your Telegram API credentials (`api_id` and `api_hash`). Here's how:

1. **Visit Telegram API Development Tools**:
   - Go to [my.telegram.org](https://my.telegram.org)
   - Log in with your phone number

2. **Create a New Application**:
   - Click on "API development tools"
   - Fill in the required fields:
     - **App title**: Any name for your application (e.g., "My Telegram Client")
     - **Short name**: A short identifier (e.g., "myclient")
     - **Platform**: Choose "Desktop" or "Other"
     - **Description**: Brief description of your app (optional)

3. **Get Your Credentials**:
   - After creating the app, you'll receive:
     - **api_id**: A numeric identifier (e.g., 12345678)
     - **api_hash**: A 32-character hexadecimal string (e.g., "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6")

4. **Configure Your Script**:
   - Copy these values to your `config.ini` file
   - Add your phone number in international format (e.g., "+1234567890")

**Important Notes**:
- Keep your `api_hash` secret and never share it publicly
- The `api_id` and `api_hash` are tied to your Telegram account
- You can create multiple applications with different credentials
- These credentials are required for the Telethon library to authenticate with Telegram's servers

## Usage

The script is controlled via command-line arguments. The primary actions are fetching updates, listing chats, searching, and sending messages.

**Core Arguments**:
*   `--chat <id>`: The username or ID of the chat to interact with.
*   `--fromId <id>`: Fetch messages that are older than the specified message ID.
*   `--limit <number>`: Fetch a specific number of messages.
*   `--profile <name>`: Apply a filtering profile from `profiles.json`.
*   `--search <query>`: Perform a global search for a text query.
*   `--listen <chat_id>`: Subscribe to a specific chat and listen for new messages in real-time.
*   `--listen-private`: Subscribe to all incoming private (one-to-one) messages.
*   `--listen-all`: Subscribe to all incoming messages from every chat and channel.

**Message Filtering Options**:
*   `--incoming-only`: Filter only incoming messages (from others to you).
*   `--outgoing-only`: Filter only outgoing messages (from you to others).
*   `--from-user <user_id>`: Filter messages from a specific user ID.
*   `--pattern <regex>`: Filter messages matching a regex pattern.
*   `--has-media`: Filter only messages that contain media (photos, videos, documents, etc.).
*   `--forwarded-only`: Filter only forwarded messages.
*   `--replies-only`: Filter only messages that are replies to other messages.
*   `--has-reactions`: Filter only messages that have reactions (likes, emojis, etc.).

**Message Sending Arguments**:
*   `--sendMessage <text>`: Send a text message to the specified chat.
*   `--sendFiles <file1> [file2] ...`: Send one or more files (photos, videos, documents).
*   `--replyTo <message_id>`: Reply to a specific message by its ID.
*   `--addReaction <emoji>`: Add a reaction (emoji) to a message specified by `--messageId`.

**Interaction Arguments**:
*   `--clickButton <button_text>`: Click a button on a message specified by `--messageId`.
*   `--download`: Download a file from a message specified by `--messageId`.

**Secondary Arguments**:
*   `--chat <id>`: The username or ID of the chat to interact with (for non-listening actions).
*   `--messageId <id>`: Message ID for button clicks, downloads, or reactions.

If no other action is specified, the script will fetch the most recent messages from the given `--chat`.

```bash
# Get the last 100 messages from a chat, cleaned with the 'dialogue' profile
python3 telegram_bot_client.py --chat "Trofei Gorgony 18+" --limit 100 --profile dialogue

# Get only incoming messages with media
python3 telegram_bot_client.py --chat "Trofei Gorgony 18+" --limit 50 --incoming-only --has-media

# Get messages matching a pattern
python3 telegram_bot_client.py --chat "Trofei Gorgony 18+" --limit 50 --pattern "привет|hello"

# Get only replies from a specific user
python3 telegram_bot_client.py --chat "Trofei Gorgony 18+" --from-user 809799943 --replies-only

# Get outgoing messages with reactions
python3 telegram_bot_client.py --chat "Trofei Gorgony 18+" --outgoing-only --has-reactions

# Send a text message
python3 telegram_bot_client.py --chat "Trofei Gorgony 18+" --sendMessage "Hello, world!"

# Send multiple files with a caption
python3 telegram_bot_client.py --chat "Trofei Gorgony 18+" --sendFiles photo1.jpg photo2.jpg video.mp4 --sendMessage "Check out these files!"

# Reply to a message
python3 telegram_bot_client.py --chat "Trofei Gorgony 18+" --sendMessage "Thanks!" --replyTo 27620

# Add a reaction to a message
python3 telegram_bot_client.py --chat "Trofei Gorgony 18+" --addReaction "🔥" --messageId 27620

# Send only files without text
python3 telegram_bot_client.py --chat "Trofei Gorgony 18+" --sendFiles document.pdf --replyTo 12345
```

The script will output the ID of the last message received. You can use this ID with the `--fromId` argument to get the next "page" of older messages.

```bash
# Get the next page of messages
python3 telegram_bot_client.py --chat "Trofei Gorgony 18+" --fromId <last_message_id> --limit 100
```

## Profiles

You can customize the JSON output by creating filter profiles in a `profiles.json` file. This file should contain a dictionary of profiles. Each profile can have two lists:

*   `stop_keys`: A list of dictionary keys to remove from the output.
*   `stop_objects`: A list of Telegram object types (based on the `_` key) to completely remove.

### Example `profiles.json`

```json
{
  "dialogue": {
    "stop_keys": ["access_hash", "file_reference", "dc_id"],
    "stop_objects": ["MessageEntityBold", "MessageActionPinMessage"]
  }
}
```

## Commands

### 1. Get Updates

Fetch messages from a specific chat.

```bash
# Get the most recent messages (default limit is set by Telegram)
python3 telegram_bot_client.py --chat <username>

# Get the last 50 messages
python3 telegram_bot_client.py --chat <username> --limit 50

# Get messages older than a specific message ID
python3 telegram_bot_client.py --chat <username> --from-id 12345
```

### 2. Subscribe to Real-Time Messages

Use the `--listen` or `--listen-private` flags to enter a persistent listening mode. The script will connect to Telegram and print any new messages to the console as they arrive. This is the most efficient way to monitor chats in real-time.

```bash
# Listen for new messages in a specific chat (group, channel, or user)
python3 telegram_bot_client.py --listen <username_or_id>

# Listen for all new incoming messages from any private (one-to-one) chat
python3 telegram_bot_client.py --listen-private

# Listen for ALL incoming messages from every chat, group, and channel
python3 telegram_bot_client.py --listen-all

# You can also use a profile to clean the output in real-time
python3 telegram_bot_client.py --listen-all --profile dialogue
```
Press `Ctrl+C` to stop listening.

### 3. List Recent Chats

Lists the 100 most recent dialogs as raw JSON objects, which includes information about the chat and the last message.

```bash
python3 telegram_bot_client.py --list-chats
```

### 4. Global Search

Search for a text query across all of your chats. The results will be grouped by chat.

```bash
python3 telegram_bot_client.py --search "your search query"
```

### 5. Send a Message

Send a text message to a specific chat.

```bash
python3 telegram_bot_client.py --chat <username> --sendMessage "Hello, world!"
```

### 6. Click a Button

Click a button on a specific message. You must provide the message ID and the text of the button.

```bash
python3 telegram_bot_client.py --chat <username> --messageId 12345 --clickButton "Click Me"
```

### 7. Download a File

Download a file from a specific message. You only need to provide the message ID.

```bash
python3 telegram_bot_client.py --chat <username> --messageId 12345 --download
```

## Debugging

To see detailed logs of what the script is doing, add the `--debug` flag to any command.

```bash
python3 telegram_bot_client.py --chat <username> --debug
``` 