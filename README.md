# Telegram Bot (Gemini + Long Polling)

This project runs a Telegram bot using long polling and Gemini API.

## Requirements

- Python 3.10+
- Telegram bot token from BotFather
- Gemini API key

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
GEMINI_API_KEY=...
GEMINI_MODELS=gemini-2.0-flash,gemini-2.5-flash
AI_MIN_INTERVAL_SECONDS=8
QUOTA_COOLDOWN_SECONDS=120
MENU_TIMEOUT_SECONDS=60
MENU_HIDE_SECONDS=30
MENU_MAX_LIFETIME_SECONDS=120
POLL_TIMEOUT_SECONDS=15
ADMIN_CHAT_ID=-1001234567890
```

5. Run the bot:

```bash
python bot.py
```

## Required Environment Variables

- `BOT_TOKEN`: Telegram bot token
- `GEMINI_API_KEY`: Gemini API key

If either variable is missing, the bot exits immediately with a clear error.

## Deploy to GitHub

From project root:

```bash
git init
git add .
git commit -m "Initial deploy-ready Telegram bot"
git branch -M main
git remote add origin https://github.com/<USERNAME>/<REPO>.git
git push -u origin main
```

## Deploy to Railway

1. Login to Railway.
2. Create `New Project`.
3. Select `Deploy from GitHub repo`.
4. Choose this repository.
5. In Railway project variables, add:
   - `BOT_TOKEN`
   - `GEMINI_API_KEY`
6. Start command (only if auto-detection fails):

```bash
python bot.py
```

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
- Bot responds only when invoked with: `Hindustani AI`, `Gemini`, `Gemini Hindustani`, or when replying to bot's previous message.
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
- Gemini reply errors:
  - Verify `GEMINI_API_KEY` is active and has model access.
  - If quota is exceeded, bot automatically switches to local fallback replies.

## Notes

- Architecture remains polling-based by design for minimal deployment changes.
- `memory.yml` is currently not used by `bot.py`; in-memory conversation history is used.
