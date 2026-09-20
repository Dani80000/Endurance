# Secure-Chat

Secure-Chat is a Python/FastAPI WebSocket chat app with account login, direct messages, encrypted passphrase-based rooms, online presence, typing indicators, rich text, emoji support, and encrypted file sharing.

Authors: Dani Dimovski, Robby Loeffler, Adam Secrest

## Production URLs

Current production deployment:

| Purpose | URL |
| --- | --- |
| Frontend app | `https://www.securechat455.dev` |
| Backend API/WebSocket host | `https://chat.securechat455.dev` |
| Health check | `https://chat.securechat455.dev/health` |
| WebSocket endpoint | `wss://chat.securechat455.dev/ws` |

Users should visit the frontend app URL. Monitoring tools should use the health check URL.

## Architecture

Secure-Chat is split into two deployable pieces:

1. Static frontend in [hosted/](hosted/)
2. Python backend in [server.py](server.py)

Production hosting:

1. Cloudflare Pages serves the static frontend at `www.securechat455.dev`.
2. Jerome, the Windows home server, runs the FastAPI backend locally on `127.0.0.1:10000`.
3. A named Cloudflare Tunnel publishes Jerome's backend as `chat.securechat455.dev`.
4. The frontend connects to the backend using `wss://chat.securechat455.dev/ws`.

This keeps the public frontend fast and reliable while keeping Jerome's backend hidden behind Cloudflare Tunnel instead of direct port forwarding.

## Repository Layout

```text
hosted/                 Static browser frontend
server.py               FastAPI app and WebSocket server
accounts.py             Account storage and password verification
connections.py          Message history storage and decrypt/rehydrate logic
server_crypto.py        Fernet encryption helpers
config.py               Environment-based runtime settings
storage_utils.py        Atomic JSON read/write helpers
requirements-backend.txt
.env.example
```

Runtime data is intentionally not committed:

```text
.env
accounts.json
messages/
uploads/
__pycache__/
```

## Local Development

Install backend dependencies:

```powershell
python -m pip install -r requirements-backend.txt
```

Create a local `.env` file:

```powershell
Copy-Item .env.example .env
```

Generate a Fernet key:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Edit `.env`:

```text
ENVIRONMENT=development
HOST=127.0.0.1
PORT=10000
LOG_LEVEL=INFO
SECRET_KEY=replace_with_a_long_random_secret
FERNET_KEY=paste_generated_fernet_key_here
ALLOWED_ORIGINS=*
UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE=5242880
```

Run the backend:

```powershell
python -m uvicorn server:app --host 127.0.0.1 --port 10000
```

Open [hosted/index.html](hosted/index.html) in two browser windows to test two clients locally.

## Frontend Configuration

The production frontend config is [hosted/config.js](hosted/config.js):

```javascript
window.SECURECHAT_WS_URL = "wss://chat.securechat455.dev/ws";
```

If running everything on one domain in the future, this can be left blank and the browser will auto-detect `/ws` on the current host.

## Backend Startup

Manual backend startup on Jerome:

```powershell
cd C:\Users\Admin\Endurance
python -m uvicorn server:app --host 127.0.0.1 --port 10000 --proxy-headers --forwarded-allow-ips="*"
```

The backend should bind to `127.0.0.1` when Cloudflare Tunnel runs on the same machine. This prevents direct LAN/public exposure.

## Cloudflare Tunnel

Named tunnel:

```text
securechat
```

Tunnel hostname:

```text
chat.securechat455.dev
```

Expected Cloudflare tunnel config on Jerome:

```yaml
tunnel: fdfb4472-78e1-4f8d-8e8f-10351eef6301
credentials-file: C:\Users\Admin\.cloudflared\fdfb4472-78e1-4f8d-8e8f-10351eef6301.json

ingress:
  - hostname: chat.securechat455.dev
    service: http://127.0.0.1:10000
  - service: http_status:404

logfile: C:\SecureChatLogs\cloudflared-service.log
```

Manual tunnel startup:

```powershell
cd C:\Users\Admin\Downloads
.\cloudflared-windows-amd64.exe tunnel run securechat
```

## Windows Scheduled Tasks

Jerome uses Windows scheduled tasks so the backend and tunnel can recover after reboot.

Expected tasks:

```text
SecureChat Backend
SecureChat Permanent Cloudflare Tunnel
```

Check task status:

```powershell
schtasks /Query /TN "SecureChat Backend" /V /FO LIST
schtasks /Query /TN "SecureChat Permanent Cloudflare Tunnel" /V /FO LIST
```

Check backend health locally:

```powershell
Invoke-RestMethod http://127.0.0.1:10000/health
```

Check public backend health:

```powershell
Invoke-RestMethod "https://chat.securechat455.dev/health"
```

Logs are written under:

```text
C:\SecureChatLogs
```

## Cloudflare Pages

Cloudflare Pages serves the static frontend from the `hosted/` folder.

Recommended Pages settings:

```text
Framework preset: None
Build command: leave blank
Build output directory: hosted
Production branch: main
```

Custom frontend domain:

```text
www.securechat455.dev
```

## Monitoring

Use UptimeRobot or a similar service to monitor:

```text
https://chat.securechat455.dev/health
```

Expected response:

```json
{
  "status": "ok"
}
```

## Environment Variables

| Variable | Purpose |
| --- | --- |
| `ENVIRONMENT` | `development` or `production`. |
| `HOST` | Bind address used when running `python server.py`. |
| `PORT` | Backend port, usually `10000`. |
| `LOG_LEVEL` | Python logging level, for example `INFO` or `WARNING`. |
| `SECRET_KEY` | Reserved application secret. Use a long random value. |
| `FERNET_KEY` | Required Fernet key for server-side encrypted storage. |
| `ALLOWED_ORIGINS` | Comma-separated frontend origins allowed to use the backend. |
| `UPLOAD_DIR` | Reserved upload directory setting. Files are currently stored as encrypted JSON payloads. |
| `MAX_UPLOAD_SIZE` | Maximum WebSocket file/encrypted payload size. |

Older deployments that still use `MESSAGE_ENCRYPTION_KEY` are supported, but new installs should use `FERNET_KEY`.

For production, prefer:

```text
ENVIRONMENT=production
ALLOWED_ORIGINS=https://www.securechat455.dev
```

## Security Notes

- Passwords are hashed with Scrypt and per-user salts.
- Chat passphrases are not stored in accounts and are not sent to the server.
- Browser room messages and file payloads are encrypted with AES-GCM before leaving the client.
- The server stores encrypted client-side envelopes and also applies Fernet encryption at rest.
- Login attempts have basic temporary lockout protection.
- Chat messages are rate-limited per user.
- Message payloads, usernames, channel names, filenames, file extensions, and file sizes are validated server-side.
- The backend is exposed through Cloudflare Tunnel, not direct public port forwarding.
- Do not commit `.env`, `accounts.json`, `messages/`, tunnel credentials, or logs.
- Do not log plaintext passwords, passphrases, encryption keys, or message contents.

## Backup Notes

Back up these files/directories regularly from Jerome:

```text
C:\Users\Admin\Endurance\.env
C:\Users\Admin\Endurance\accounts.json
C:\Users\Admin\Endurance\messages\
C:\Users\Admin\.cloudflared\
```

Keep backups private. If the Fernet key is lost, server-side encrypted history cannot be decrypted.

## Storage

The app currently uses JSON storage:

```text
accounts.json
messages/*.json
```

Writes are atomic and locked inside the Python process to reduce corruption risk. For heavier usage, SQLite is the recommended next migration because it improves concurrency, indexing, and backups without requiring a larger database server.

## Troubleshooting

If login hangs or WebSocket connection fails:

1. Confirm backend health:

```powershell
Invoke-RestMethod "https://chat.securechat455.dev/health"
```

2. Confirm the frontend config:

```javascript
window.SECURECHAT_WS_URL = "wss://chat.securechat455.dev/ws";
```

3. Check Jerome scheduled tasks:

```powershell
schtasks /Query /TN "SecureChat Backend" /V /FO LIST
schtasks /Query /TN "SecureChat Permanent Cloudflare Tunnel" /V /FO LIST
```

4. Check Jerome logs:

```powershell
dir C:\SecureChatLogs
```

5. Check browser DevTools Console for WebSocket errors.

## Features

- Real-time WebSocket messaging
- Account creation and login
- Direct messages
- Encrypted passphrase-based rooms
- Online user list
- Typing indicators
- Emoji picker
- Rich text formatting
- File sharing
- Client-side file validation
- Basic rate limiting
- Reconnect behavior
