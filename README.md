# Secure-Chat
Project to establish a secure messaging channel between multiple users.

Authors: Dani Dimovski, Robby Loeffler, Adam Secrest

## Hosted Architecture
SecureChat is now split into two deployable pieces:

1. Python WebSocket backend (`server.py`)
2. Static hosted browser client (`hosted/`)

This keeps the chat service compatible with Python hosting providers such as Render while still allowing the frontend to be uploaded to InfinityFree or any other static/PHP web host.

## Local Setup
Install dependencies for local development:

```bash
python -m pip install -r requirements.txt
```

For backend-only hosting, install the smaller backend dependency set:

```bash
python -m pip install -r requirements-backend.txt
```

Create a `.env` file:

```bash
MESSAGE_ENCRYPTION_KEY=your_fernet_key_here
SECURECHAT_WS_URL=ws://localhost:10000/ws
```

Generate a Fernet key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Run the backend:

```bash
uvicorn server:app --host 0.0.0.0 --port 10000
```

Open `hosted/index.html` in two browser windows to test two clients.

## Deploying the Backend
Render can deploy the backend directly using `render.yaml`. It installs `requirements-backend.txt`, so the hosted server does not need the desktop Eel client dependencies.

Required environment variable:

```bash
MESSAGE_ENCRYPTION_KEY=<fernet key>
```

Start command:

```bash
uvicorn server:app --host 0.0.0.0 --port $PORT
```

Health check:

```text
/health
```

## Deploying the Frontend
Upload the files inside `hosted/` to InfinityFree or another static web host.

Set the WebSocket backend URL in `hosted/config.js`:

```javascript
window.SECURECHAT_WS_URL = "wss://your-python-backend.example.com/ws";
```

Use `wss://` for hosted HTTPS sites. Browsers usually block insecure `ws://` connections from HTTPS pages.

## Security Features
- Passwords are hashed with Scrypt and per-user salts.
- Stored text messages are encrypted with Fernet before being saved.
- WebSocket login attempts are rate-limited by IP.
- Chat messages are rate-limited per user.
- DM channel names are normalized so both users share the same private channel.
- Stored channel filenames are sanitized before writing message history.

## Deliverables
A video presentation showing the following:
An explanation of the functionality of the programs
Present two clients (simulated on separate browser windows or systems) connected to the WebSocket server.
Executable(s)
Client (if through the browser, you must explain this access through documentation)
Server (required)
Documentation
User Guide
Changelog (Easiest through Github)
Document each edit made to the program
Show various versions that represent multiple iterations

## Requirements
- Real Time Messaging - Appears instantly for all connected users
- Secure connection - All connections over a websocket
- Authentication - Username and Password
- Rate Limiting - Prevent server spam
- Connection handling - Proper join / disconnect. Reconnect automatically upon user fail
