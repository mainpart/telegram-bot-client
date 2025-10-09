# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a Telegram User Client CLI built with Python's Telethon library. It provides a command-line interface for interacting with Telegram as a user account (not a bot), designed for non-interactive use in scripts and automation. The tool mimics the `getUpdates` flow of the Telegram Bot API but operates through a user account.

## Common Development Commands

### Environment Setup
```bash
# Install dependencies
pip3 install -r requirements.txt

# Configure credentials (copy template and edit)
cp config.ini-default config.ini
# Edit config.ini with your Telegram API credentials from my.telegram.org
```

### Running the Application
```bash
# Basic message fetching
python3 telegram_bot_client.py --chat "username" --limit 50

# Real-time message listening (most common use case)
python3 telegram_bot_client.py --listen-all --profile dialogue

# Debug mode (enables detailed logging)
python3 telegram_bot_client.py --chat "username" --debug

# Send messages
python3 telegram_bot_client.py --chat "username" --sendMessage "Hello world"

# Send files
python3 telegram_bot_client.py --chat "username" --sendFiles photo.jpg --sendMessage "Caption"
```

### Docker/Cloud Run Deployment
```bash
# Build and push to Google Artifact Registry
gcloud builds submit --tag "$REGION-docker.pkg.dev/$PROJECT_ID/ttt-repo/ttt-bot:latest" .

# Deploy to Cloud Run (see GCLOUD.md for complete setup)
gcloud run deploy ttt-bot --image "$IMAGE_URL" --region us-central1 --no-cpu-throttling --min-instances 1
```

### Testing Message Filtering
```bash
# Test different message filters
python3 telegram_bot_client.py --chat "username" --incoming-only --has-media --limit 20
python3 telegram_bot_client.py --chat "username" --pattern "hello|привет" --limit 50
python3 telegram_bot_client.py --chat "username" --from-user 123456789 --replies-only
```

## Architecture and Code Structure

### Core Components

**Main Script (`telegram_bot_client.py`):**
- **Session Management**: Uses Telethon's session system with `anon.session` file for persistent authentication
- **Message Fetching Engine**: Implements bidirectional message retrieval with support for ranges, limits, and filtering
- **Real-time Listener**: Event-driven architecture for live message monitoring across chats
- **JSON Processing Pipeline**: Custom filtering system using profiles for clean, structured output
- **Multi-modal Operations**: Handles text messages, media files, reactions, button clicks, and downloads

**Configuration System:**
- `config.ini`: Stores Telegram API credentials (phone, api_id, api_hash)
- `profiles.json`: Defines JSON filtering profiles to clean Telethon's verbose output
- Environment variable support for containerized deployments

**Deployment Infrastructure:**
- `Dockerfile`: Multi-stage Python container optimized for Cloud Run
- `entrypoint.sh`: Container startup script handling config generation and process management  
- `health_server.py`: Lightweight HTTP server for container health checks

### Key Architectural Patterns

**Message Processing Flow:**
1. Telethon API call → Raw message objects
2. JSON serialization → Structured data
3. Filter application → Command-line filters (incoming/outgoing, media, patterns, etc.)
4. Profile cleaning → Remove verbose Telegram internals using `profiles.json`
5. Output formatting → Clean JSON for consumption

**Authentication & Session Management:**
- Persistent session storage in `.session` files
- Cloud Storage mounting for containerized environments (`/sessions` volume)
- Environment-based credential injection for secure deployments

**Event-Driven Real-time Processing:**
- Telethon event handlers for `NewMessage` events
- Chat-specific, private-only, or global message listening modes
- Graceful shutdown handling with `Ctrl+C` signal management

### Data Flow Architecture

**Message Fetching (Batch):**
```
CLI Args → Telethon iter_messages() → JSON Conversion → Filtering → Profile Cleaning → Output
```

**Real-time Listening:**
```
Telegram Events → Event Handler → Filter Check → Profile Cleaning → Immediate Output
```

**File Operations:**
```
Message ID → Telethon Media API → Local File System → Path Output
```

### Configuration Dependencies

**Required for Operation:**
- Telegram API credentials from my.telegram.org
- Valid phone number with Telegram account
- Session file creation through initial authentication

**Optional Enhancements:**
- Custom filtering profiles in `profiles.json`
- Docker environment variables for Cloud Run deployment
- GCS bucket for persistent session storage in cloud environments

### Cloud Run Deployment Architecture

The application is designed as a long-running service with:
- **Always-on CPU allocation** for reliable background listening
- **Cloud Storage volume mounting** for session persistence
- **Health check endpoint** for container orchestration
- **Environment-based configuration** for secure credential management
- **Minimal resource footprint** (512Mi memory, 1 vCPU recommended)

### Message Range and Direction Logic

The system implements sophisticated message navigation:
- **Forward reading**: `--forward` with `--fromId` reads newer messages (higher IDs)
- **Backward reading**: `--backward` with `--fromId` reads older messages (lower IDs)  
- **Range support**: `--fromId` and `--toId` with `--inclusive` for precise boundaries
- **Default behavior**: Without direction flags, reads newest to oldest (Telethon default)

This architecture supports both real-time monitoring and historical message analysis workflows.
