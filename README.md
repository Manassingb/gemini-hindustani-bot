# Telegram Bot (Long Polling)

This project runs a Telegram bot using long polling.

## Requirements

- Python 3.10+
- Telegram bot token from BotFather
- At least one NVIDIA API key

## Local Setup

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create environment file:

```bash
cp .env.example .env
```

4. Edit `.env` and set:

```env
BOT_TOKEN=...
NVIDIA_API_KEY_1=...
NVIDIA_API_KEY_2=...
NVIDIA_API_KEY_3=...
```

5. Run the bot:

```bash
python bot.py
```

## Required Environment Variables

- `BOT_TOKEN`: Telegram bot token
- `NVIDIA_API_KEY_1` or `NVIDIA_API_KEYS`: NVIDIA API access for AI replies

If either variable is missing, the bot exits immediately with a clear error.

## Push to GitHub

From project root:

```bash
git init
git add .
git commit -m "Initial deploy-ready Telegram bot"
git branch -M main
git remote add origin https://github.com/<USERNAME>/<REPO>.git
git push -u origin main
```

## Deploy from GitHub to Railway

GitHub stores the code. The always-on polling bot itself should run on Railway.

This repo includes [`railway.json`](./railway.json), so Railway will automatically start the bot with:

```bash
python3 bot.py
```

1. Login to Railway.
2. Create `New Project`.
3. Select `Deploy from GitHub repo`.
4. Choose this repository.
5. In Railway project variables, add:
   - `BOT_TOKEN`
   - `NVIDIA_API_KEY_1`
   - Optional: `NVIDIA_API_KEY_2`, `NVIDIA_API_KEY_3`
6. Click deploy.

Every push to `main` will trigger auto-redeploy.

## Validation Checklist

- Build logs show successful install of `requirements.txt`.
- Runtime logs show `Bot started with long polling.`
- Telegram messages receive a response.
- `/start` shows quick command menu.
- `/setname Manas` stores preferred name.
- `/myname` returns saved name.
- `/status` returns current mode, memory count, and models.
- `/about` returns AI/developer/admin info.
- `/models` shows active model list.
- `/fallback` shows current fallback/cooldown status.
- `/stopai` disables continuous AI communication mode.
- `/reset` clears conversation memory.
- `/lan hindi|hinglish|english|auto` returns language confirmation.
<!-- - Bot responds only when invoked with: `Hindustani AI`, `Gemini`, `Gemini Hindustani`, or when replying to bot's previous message. -->
- If user sends only bot name trigger, bot shows 4 communication options (Help/Admin call/Admin message/Audio access).
- Communication menu is button-based and includes `5. AI with communication` for continuous chat mode.
- If no menu option is selected within 60 seconds, menu auto-resets.
- Menu buttons auto-hide in 30 seconds.
- Menu session max lifetime is 120 seconds (after that AI trigger needed again).
- For admin routing features, set `ADMIN_CHAT_ID` in `.env`.

## Troubleshooting

- `Missing required environment variable(s)`:
  - Add missing keys in Railway Variables or local `.env`.
- Bot starts but no Telegram reply:
  - Re-check `BOT_TOKEN` validity from BotFather.
  - Confirm no second process is polling same token.
- AI reply errors:
  - Verify `NVIDIA_API_KEY_1` is active.
  - Add extra NVIDIA keys if you want fallback rotation.

## Notes

- Architecture remains polling-based by design for minimal deployment changes.
- GitHub alone does not run this bot 24/7; Railway (or another backend host) should run it.
- `memory.yml` is currently not used by `bot.py`; in-memory conversation history is used.
