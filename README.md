# Secure-Chat

Secure-Chat is a Python/FastAPI WebSocket chat app with authentication, encrypted message storage, browser-side room encryption, direct messages, channels, presence, and file sharing.

Authors: Dani Dimovski, Robby Loeffler, Adam Secrest

## Architecture

The project has two deployable pieces:

1. Python backend: [server.py](server.py)
2. Static browser client: [hosted/](hosted/)

The backend can run on a home server behind Cloudflare Tunnel or a reverse proxy. The frontend can be served from the same domain as the backend or from a separate static host.

## Local Development

Install backend dependencies:

```powershell
python -m pip install -r requirements-backend.txt
```

Create a local `.env` from the template:

```powershell
Copy-Item .env.example .env
```

Generate a Fernet key:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Edit `.env` and set:

```text
FERNET_KEY=paste_generated_fernet_key_here
SECRET_KEY=replace_with_a_long_random_secret
HOST=127.0.0.1
PORT=10000
ENVIRONMENT=development
ALLOWED_ORIGINS=*
```

Run the backend:

```powershell
python -m uvicorn server:app --host 127.0.0.1 --port 10000
```

Open [hosted/index.html](hosted/index.html) in two browser windows to test two clients.

## Production Startup

For a home server behind Cloudflare Tunnel or a reverse proxy, bind the app locally:

```powershell
python -m uvicorn server:app --host 127.0.0.1 --port 10000 --proxy-headers --forwarded-allow-ips="*"
```

Use `127.0.0.1` when Cloudflare Tunnel or your reverse proxy runs on the same machine. This avoids exposing the app directly to your LAN or the public internet.

If another machine on your LAN must proxy to it, use your server's LAN IP or `0.0.0.0`, then firewall it carefully.

## Environment Variables

| Variable | Purpose |
| --- | --- |
| `ENVIRONMENT` | `development` or `production`. |
| `HOST` | Bind address used by `python server.py`. |
| `PORT` | Backend port, usually `10000`. |
| `LOG_LEVEL` | Python logging level, for example `INFO` or `WARNING`. |
| `SECRET_KEY` | Reserved app secret for production features. Use a long random value. |
| `FERNET_KEY` | Required Fernet key for server-side encrypted storage. |
| `ALLOWED_ORIGINS` | Comma-separated browser origins allowed to use the backend. |
| `UPLOAD_DIR` | Reserved upload directory setting. Files are currently stored as encrypted JSON payloads. |
| `MAX_UPLOAD_SIZE` | Maximum WebSocket file/encrypted payload size. |

Older deployments that still use `MESSAGE_ENCRYPTION_KEY` are supported, but new installs should use `FERNET_KEY`.

## Frontend Configuration

If the frontend is served from the same public domain as the backend, leave [hosted/config.js](hosted/config.js) blank:

```javascript
window.SECURECHAT_WS_URL = "";
```

The browser will automatically use:

```text
wss://your-domain.example/ws
```

If the frontend is hosted somewhere else, set:

```javascript
window.SECURECHAT_WS_URL = "wss://your-backend-domain.example/ws";
```

## Cloudflare Tunnel Overview

Recommended setup:

1. Run Secure-Chat on the server at `http://127.0.0.1:10000`.
2. Create a Cloudflare Tunnel public hostname such as `chat.example.com`.
3. Point the tunnel service to:

```text
http://127.0.0.1:10000
```

Cloudflare handles HTTPS/WSS publicly. Uvicorn receives local HTTP/WebSocket traffic from the tunnel.

## Windows Continuous Startup

A simple Windows option is Task Scheduler:

1. Open Task Scheduler.
2. Create Task.
3. Trigger: At startup or At log on.
4. Action: Start a program.
5. Program:

```text
python
```

6. Arguments:

```text
-m uvicorn server:app --host 127.0.0.1 --port 10000 --proxy-headers --forwarded-allow-ips="*"
```

7. Start in:

```text
C:\path\to\Endurance
```

For a more service-like setup, NSSM also works well with the same command.

## Health Check

Local:

```powershell
Invoke-RestMethod http://127.0.0.1:10000/health
```

Expected:

```json
{
  "status": "ok"
}
```

Public tunnel:

```powershell
Invoke-RestMethod https://chat.example.com/health
```

## WebSocket Test

Install the `websockets` package if needed:

```powershell
python -m pip install websockets
```

Then test a connection:

```powershell
python -c "exec(\"import asyncio, websockets\\nasync def main():\\n    async with websockets.connect('ws://127.0.0.1:10000/ws'):\\n        print('connected')\\nasyncio.run(main())\")"
```

For the public tunnel, use:

```text
wss://chat.example.com/ws
```

## Security Notes

- Passwords are hashed with Scrypt and per-user salts.
- The browser passphrase is not stored in the account and is not sent to the server.
- Browser room messages and file payloads are encrypted with AES-GCM before leaving the client.
- The server stores encrypted client-side envelopes and also applies Fernet encryption at rest.
- Login attempts have basic temporary lockout protection.
- Message payloads, usernames, channel names, filenames, file extensions, and file sizes are validated server-side.
- Do not commit `.env`, `accounts.json`, or `messages/`.
- Do not log plaintext passwords, passphrases, encryption keys, or message contents.

## Backup Notes

Back up these files/directories regularly:

```text
.env
accounts.json
messages/
```

Keep the `.env` backup private. If you lose the Fernet key, existing server-side encrypted message history cannot be decrypted.

## Storage

The app currently uses JSON storage:

- `accounts.json`
- `messages/*.json`

Writes are atomic and locked inside the Python process to reduce corruption risk. For heavier usage, migrate to SQLite later. SQLite would improve concurrency, indexing, and backups without requiring a large database server.

## Required Features

- Real-time WebSocket messaging
- Authentication
- Direct messages
- Encrypted passphrase-based rooms
- File sharing
- Presence and typing indicators
- Basic rate limiting
- Reconnect behavior
