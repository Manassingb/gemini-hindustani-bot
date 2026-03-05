import os
import requests
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# ======================
# KEEP ALIVE SERVER
# ======================

def keep_alive():

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is running")

    server = HTTPServer(("0.0.0.0", 10000), Handler)
    server.serve_forever()

threading.Thread(target=keep_alive, daemon=True).start()

# ======================
# CONFIG
# ======================

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

offset = 0
memory = {}
language_mode = {}

SYSTEM_PROMPT = """
You are Gemini Hindustani AI.

Rules:
1. Reply casually like an Indian friend.
2. Hindi → reply Hindi
3. Hinglish → reply Hinglish
4. English → reply English
5. Never use abusive words.
"""

# ======================
# TELEGRAM FUNCTIONS
# ======================

def send_typing(chat_id):

    requests.get(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendChatAction",
        params={"chat_id": chat_id, "action": "typing"}
    )


def send_message(chat_id, text):

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": text}
    )

# ======================
# GEMINI AI
# ======================

def ask_gemini(chat_id, text):

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": text}
                ]
            }
        ]
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

    r = requests.post(url, json=payload)

    data = r.json()

    try:
        reply = data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print("Gemini error:", data)
        reply = "Gemini se response nahi mila."

    return reply

# ======================
# COMMAND HANDLER
# ======================

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

# ======================
# MAIN BOT LOOP
# ======================

print("Bot started with long polling.")

while True:

    try:

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"

        params = {
            "timeout": 60,
            "offset": offset
        }

        response = requests.get(url, params=params).json()

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

        print("Error:", e)

        time.sleep(5)
