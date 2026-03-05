import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
REQUEST_TIMEOUT_SECONDS = 30

offset = 0
memory = {}
language_mode = {}

SYSTEM_PROMPT = """
You are Gemini Hindustani AI.

Rules:
1. Reply in friendly Indian casual style.
2. If user speaks Hindi → reply Hindi.
3. If user speaks Hinglish → reply Hinglish.
4. If user speaks English → reply English.
5. Never use abusive language.
6. Keep replies simple and natural.
"""

def send_typing(chat_id):
    requests.get(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendChatAction",
        params={"chat_id": chat_id, "action": "typing"},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )


def ask_gemini(chat_id, text):

    history = memory.get(chat_id, [])

    history.append({"role": "user", "parts": [{"text": text}]})

    payload = {
        "contents": history,
        "system_instruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        }
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key={GEMINI_API_KEY}"

    r = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)

    data = r.json()

    try:
        reply = data["candidates"][0]["content"]["parts"][0]["text"]
    except:
        reply = "Mujhe abhi jawab dene me problem ho rahi hai."

    history.append({"role": "model", "parts": [{"text": reply}]})

    memory[chat_id] = history[-20:]

    return reply


def send_message(chat_id, text):

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )


def process_commands(chat_id, text):

    if text.startswith("/reset"):

        memory[chat_id] = []

        send_message(chat_id, "Conversation memory reset ho gayi.")

        return True

    if text.startswith("/lan"):

        parts = text.split()

        if len(parts) < 2:

            send_message(
                chat_id,
                "Language options:\n/lan hindi\n/lan hinglish\n/lan english\n/lan auto"
            )
            return True

        mode = parts[1].lower()

        language_mode[chat_id] = mode

        send_message(chat_id, f"Language set to: {mode}")

        return True

    return False


def validate_env():
    missing = []
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")
    if missing:
        raise RuntimeError(
            f"Missing required environment variable(s): {', '.join(missing)}"
        )


def run_bot():
    global offset
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"

            params = {
                "timeout": 60,
                "offset": offset
            }

            response = requests.get(
                url,
                params=params,
                timeout=REQUEST_TIMEOUT_SECONDS + 65,
            ).json()

            for update in response.get("result", []):
                offset = update["update_id"] + 1

                message = update.get("message")

                if not message:
                    continue

                chat_id = message["chat"]["id"]
                text = message.get("text", "")

                if process_commands(chat_id, text):
                    continue

                send_typing(chat_id)
                reply = ask_gemini(chat_id, text)
                send_message(chat_id, reply)

        except Exception as e:
            print("Error:", e, flush=True)
            time.sleep(5)


if __name__ == "__main__":
    validate_env()
    print("Bot started with long polling.", flush=True)
    run_bot()
