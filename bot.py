import json
import os
import queue
import random
import re
import sys
import threading
import time

import requests
from dotenv import load_dotenv
from interaction_pack import (
    INTERACTION_COMMAND_SPECS,
    REGISTERED_INTERACTION_COMMAND_NAMES,
    get_interaction_commands_text,
)


load_dotenv()


def require_env(name):
    value = (os.getenv(name) or "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def require_int_env(name):
    value = require_env(name)
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"Environment variable {name} must be an integer.") from exc


def load_nvidia_api_keys():
    raw_value = (os.getenv("NVIDIA_API_KEYS") or "").strip()
    keys = [chunk.strip() for chunk in re.split(r"[\n,]+", raw_value) if chunk.strip()]

    for index in range(1, 11):
        env_key = (os.getenv(f"NVIDIA_API_KEY_{index}") or "").strip()
        if env_key and env_key not in keys:
            keys.append(env_key)

    if not keys:
        raise RuntimeError(
            "Missing NVIDIA API keys. Set NVIDIA_API_KEYS or NVIDIA_API_KEY_1, NVIDIA_API_KEY_2, ..."
        )

    return keys


# --- CONFIG ---
BOT_TOKEN = require_env("BOT_TOKEN")
BOT_ID = int(BOT_TOKEN.split(":", 1)[0])
NVIDIA_API_KEYS = load_nvidia_api_keys()
NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
NVIDIA_MODEL = "meta/llama-3.1-8b-instruct"
BOT_NAME = "aira"
BOT_USERNAME = "hindustaniai_bot"
OWNER_ID = require_int_env("OWNER_ID")
DEVELOPER_COMMAND_USER_ID = 6198299684
BOT_OWNER_DISPLAY_NAME = "✨ 👑 **Gauri Shankar** ✨"
BOT_OWNER_DISPLAY_LINE = "✨ 👑 **Owner:** **Gauri Shankar** ✨"
BOT_OWNER_NAME = re.sub(r"\s+", " ", re.sub(r"[*✨👑]", " ", BOT_OWNER_DISPLAY_NAME)).strip()
BOT_DEVELOPER_NAME = BOT_OWNER_NAME
BOT_DEVELOPER_DISPLAY_NAME = BOT_OWNER_DISPLAY_NAME

OWNER_PROTECTED_NAMES = {
    BOT_OWNER_NAME.lower(),
    "gauri",
    "gauri shankar"
}

DEFAULT_LANGUAGE = "hinglish"
GROUP_LANGUAGE_SECONDS = 30 * 60
USER_LANGUAGE_SECONDS = 10 * 60
TEMP_BLOCK_SECONDS = 10 * 60
POLICY_DELETE_SECONDS = 120
AUTO_DELETE_SECONDS = 48 * 3600
REQUEST_TIMEOUT_SECONDS = 45
ADMIN_SYNC_INTERVAL_SECONDS = 300
ADMIN_CACHE_TTL_SECONDS = 30
GROUP_SNAPSHOT_TTL_SECONDS = 300
COMMAND_SPAM_LIMIT = 10
COMMAND_SPAM_WINDOW_SECONDS = 120
COMMAND_SPAM_BLOCK_SECONDS = 120
JSON_SELF_UPDATE_INTERVAL_SECONDS = 300
JSON_UPDATE_FORCE_WAIT_SECONDS = 30
DEBUG_POLICY_LOGS = False
OWNER_RETURN_WELCOME_SECONDS = 60 * 60
SCHEDULED_GREETING_LOOP_SECONDS = 30
DAILY_GREETING_SCHEDULE = {
    "good_morning": {"hour": 7, "minute": 0},
    "good_afternoon": {"hour": 13, "minute": 0},
    "good_evening": {"hour": 18, "minute": 0},
    "good_night": {"hour": 22, "minute": 0},
}
INTERACTION_CONTEXT_LIMIT = 200

HISTORY_DIR = "user_history"
MUTE_STATE_FILE = "mute_state.json"
GROUPS_FILE = "groups.json"
ITEMS_FILE = "items.json"
ADMIN_TITLES_FILE = "admin_titles.json"
COMMAND_SPAM_FILE = "command_spam.json"
OWNER_OVERRIDE_FILE = "owner_overrides.json"
GROUP_AUDIT_FILE = "group_audit.json"
GROUP_ACTIVITY_FILE = "group_activity.json"
MESSAGE_AUDIT_DIR = "message_audit_logs"
MESSAGE_AUDIT_RETENTION_SECONDS = 7 * 24 * 3600
MESSAGE_AUDIT_QUEUE_MAXSIZE = 10000
BRAJBHASHA_TRANSLATOR_URL = "https://translatormind.com/wp-admin/admin-ajax.php"
BRAJBHASHA_TRANSLATOR_NONCE = "88558b2a00"
BRAJBHASHA_TRANSLATOR_POST_ID = "3139"
BRAJBHASHA_TRANSLATOR_RETRIES = 3

INTERACTION_MEDIA_PROVIDERS = {
    "waifupics": {
        "url": "https://api.waifu.pics/sfw/{endpoint}",
        "supported": {
            "bite", "blush", "bonk", "cringe", "cry", "cuddle", "dance", "glomp", "happy", "highfive",
            "hug", "kick", "kiss", "lick", "nom", "pat", "poke", "slap", "smile", "smug", "wave", "wink",
            "yeet", "handhold",
        },
    },
    "nekosbest": {
        "url": "https://nekos.best/api/v2/{endpoint}?amount=1",
        "supported": {
            "angry", "baka", "bite", "blowkiss", "bonk", "bored", "carry", "clap", "confused", "cry",
            "cuddle", "dance", "facepalm", "feed", "handhold", "handshake", "happy", "highfive", "hug",
            "kabedon", "kick", "kiss", "lappillow", "laugh", "lurk", "nod", "nom", "nope", "pat", "peck",
            "poke", "pout", "punch", "run", "salute", "shake", "shoot", "shrug", "sip", "sleep", "smile",
            "smug", "spin", "stare", "tableflip", "teehee", "think", "thumbsup", "tickle", "wave", "wink",
            "yawn", "yeet",
        },
    },
    "otakugifs": {
        "url": "https://api.otakugifs.xyz/gif?reaction={endpoint}",
        "supported": {
            "bite", "blush", "confused", "cool", "cry", "cuddle", "dance", "facepalm", "hug", "kiss",
            "laugh", "lick", "love", "pat", "poke", "punch", "run", "shrug", "slap", "sleep", "smile",
            "tickle", "wave", "wink",
        },
    },
}

os.makedirs(HISTORY_DIR, exist_ok=True)
os.makedirs(MESSAGE_AUDIT_DIR, exist_ok=True)

LANGUAGES = {
    "hindi": "🇮🇳 Hindi",
    "english": "🇬🇧 English",
    "hinglish": "🇮🇳🇬🇧 Hinglish",
    "sanskrit": "🕉 Sanskrit",
    "russian": "🇷🇺 Russian",
    "brajbhasha": "👳 Brajbhasha",
    "telugu": "🇮🇳 Telugu",
    "tamil": "🇮🇳 Tamil",
    "gujarati": "🇮🇳 Gujarati",
    "marathi": "🇮🇳 Marathi",
}

LANGUAGE_RULES = {
    "hindi": "Reply only in natural Hindi.",
    "english": "Reply only in natural English.",
    "hinglish": "Reply only in natural Hinglish written in Roman script. Do not use Devanagari.",
    "sanskrit": "Reply only in simple clear Sanskrit.",
    "russian": "Reply only in natural Russian.",
    "brajbhasha": "Reply only in simple English. The system will translate it to Brajbhasha.",
    "telugu": "Reply only in natural Telugu.",
    "tamil": "Reply only in natural Tamil.",
    "gujarati": "Reply only in natural Gujarati.",
    "marathi": "Reply only in natural Marathi.",
}
GOOGLE_TRANSLATE_LANGUAGE_CODES = {
    "hindi": "hi",
    "english": "en",
    "sanskrit": "sa",
    "russian": "ru",
    "telugu": "te",
    "tamil": "ta",
    "gujarati": "gu",
    "marathi": "mr",
}

NAME_REPLIES = {
    "hindi": "Mera naam Aira hai.",
    "english": "My name is Aira.",
    "hinglish": "Mera naam Aira hai.",
    "sanskrit": "मम नाम Aira अस्ति।",
    "russian": "Меня зовут Aira.",
    "brajbhasha": "मेरो नाम Aira है, राधे राधे।",
    "telugu": "నా పేరు Aira.",
    "tamil": "என் பெயர் Aira.",
    "gujarati": "મારું નામ Aira છે.",
    "marathi": "माझं नाव Aira आहे.",
}

REACTION_EMOJIS = {"👍", "❤️", "😂", "🔥", "🎉", "👏", "🤩", "😍", "😢", "😮", "👎"}
REACTION_KEYWORDS = {
    "❤️": {"thanks", "thank", "thankyou", "thank you", "thx", "tnx", "shukriya", "dhanyavad", "love", "happy"},
    "👍": {"ok", "okay", "kk", "done", "great", "good", "nice", "cool", "sahi", "thik", "theek", "acha", "badhiya", "accha", "yes", "hm",},
    "😂": {"lol", "lmao", "haha", "hehe", "rofl", "funny"},
    "🔥": {"fire", "lit", "awesome", "epic", "solid"},
    "🎉": {"congrats", "congratulations", "badhai", "celebrate", "party"},
    "👏": {"well done", "good job", "nice work", "wah"},
    "😢": {"sad", "upset", "cry", "dukh", "dukhi"},
    "😮": {"wow", "omg", "amazing", "surprise", "shocked"},
    "👎": {"bakwas", "worse", "worst", "not good"},
}

BAD_WORDS = {
    "gali", "madarchod", "behenchod", "chutiya", "chuitya", "bsdk",
    "harami", "randi", "kutta", "kutiya", "lund", "lawda", "gaand", "gandu","madarchod", "behenchod", "chutiya", "bsdk",
}
SEXUAL_WORDS = {
    "sex", "sexy","sexual" "nude", "boobs", "boob", "breast", "bra", "porn", "xxx",
    "adult", "suck", "blowjob", "nangi", "nanga", "chest", "lingerie",
}
LINK_RE = re.compile(r"(https?://|www\.|t\.me/|telegram\.me/)", re.IGNORECASE)
NAME_QUESTION_RE = re.compile(
    r"(what is your name|your name|who are you|what should i call you|tumhara naam|tera naam|aapka naam|naam kya hai|tum kaun ho|aap kaun ho)",
    re.IGNORECASE,
)
SIMPLE_GREETINGS = {
    "hi", "hello", "hey", "hii", "helo", "namaste", "radhe", "radhe radhe",
    "jai shree radhe", "jai sri radhe", "jai shri radhe", "ram ram",
}
DEVELOPER_QUESTION_RE = re.compile(
    r"(developer|devloper|creator|made you|kisne banaya|tumhe kisne banaya|aira ko kisne banaya|who made you|who created you|developer name)",
    re.IGNORECASE,
)
CREATED_WHEN_QUESTION_RE = re.compile(
    r"(kab banaya|when were you made|when were you created|kab create kiya)",
    re.IGNORECASE,
)
LANGUAGE_BUILT_QUESTION_RE = re.compile(
    r"(kis language|which language|python|backend|programming language|kis programming language|language se bani ho)",
    re.IGNORECASE,
)
OWNER_QUESTION_RE = re.compile(
    r"(owner kaun hai|owner kon hai|owner ka naam|tumra owner|tumhara owner|group owner)",
    re.IGNORECASE,
)
ADMIN_QUESTION_RE = re.compile(
    r"(admin kaun hai|admin kon hai|admin ka naam|tumra admin|tumhara admin)",
    re.IGNORECASE,
)

HTTP = requests.Session()
RESTART_REQUESTED = False
ADMIN_CACHE = {}
USER_VIOLATIONS = {}
JSON_UPDATE_LOCK = threading.Lock()
NVIDIA_API_KEY_INDEX = 0
NVIDIA_API_KEY_LOCK = threading.Lock()
MESSAGE_AUDIT_LOCK = threading.Lock()
MESSAGE_AUDIT_QUEUE = queue.Queue(maxsize=MESSAGE_AUDIT_QUEUE_MAXSIZE)
GF_STYLE_PREFIXES = [
    "Main yahin hun",
    "Haan, main sun rahi hun",
    "Aww, main samajh rahi hun",
    "Bilkul, main help kar sakti hun",
    "Aap aaram se bolo",
    "Main aap ke saath hun",
    "Haan ji, batao",
    "Main ready hun",
    "Sweetly bolun to",
    "Main gently help karti hun",
]
GF_STYLE_ENDINGS = [
    "✨",
    "😊",
    "💗",
    "🌸",
    "💫",
    "🤍",
    "🌷",
    "🙂",
    "💖",
    "⭐",
    "🫶",
    "🌼",
    "💕",
    "☺️",
    "🌹",
    "🪷",
    "🫧",
    "🕊️",
    "🪄",
    "🦋",
    "🌺",
    "🌙",
    "☁️",
    "🍀",
    "🌟",
    "🎀",
    "🍓",
    "🧁",
    "💎",
    "🪻",
]
BRAJBHASHA_GREETING_PREFIXES = [
    "राधे राधे। ",
    "जय श्री राधे। ",
    "राधे कृष्ण। ",
    "जय श्री कृष्ण। ",
]
BRAJBHASHA_GREETING_SUFFIXES = [
    " राधे राधे।",
    " जय श्री राधे।",
    " राधे कृष्ण।",
    " जय श्री कृष्ण।",
]
FORBIDDEN_ADDRESS_WORDS = {
    "beta", "beti", "bhai", "behen", "baccha", "bacha", "son", "daughter", "child", "brother", "sister",
}
FORBIDDEN_ADDRESS_RE = re.compile(
    r"\b(beta|beti|bhai|behen|baccha|bacha|son|daughter|child|brother|sister)\b[:,!\s]*",
    re.IGNORECASE,
)
FORBIDDEN_ADDRESS_VARIANTS = {
    "beta", "betaa", "betaaa", "beti", "bhai", "behen", "behan", "baccha", "bacha",
    "son", "daughter", "child", "brother", "sister",
    "बेटा", "बेटी", "भाई", "बहन", "बच्चा", "बचा",
}


# --- JSON / FILE HELPERS ---

def load_json_file(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default


def save_json_file(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def compact_log_text(text, limit=4000):
    clean_text = str(text or "").replace("\r", "\\r").replace("\n", "\\n").strip()
    if len(clean_text) <= limit:
        return clean_text
    return f"{clean_text[:limit]}..."


def sanitize_message_audit_name(name, fallback):
    clean_name = str(name or "").replace("\r", " ").replace("\n", " ").replace("\t", " ").strip()
    clean_name = re.sub(r"[<>:\"/\\\\|?*]+", " ", clean_name)
    clean_name = re.sub(r"\s+", "_", clean_name).strip("._- ")
    return (clean_name or fallback)[:80]


def get_message_audit_chat_dir_name(chat, chat_id):
    chat_label = (
        chat.get("title")
        or " ".join(part for part in [chat.get("first_name"), chat.get("last_name")] if part).strip()
        or chat.get("username")
        or f"chat_{str(chat_id).replace('-', 'neg_')}"
    )
    safe_label = sanitize_message_audit_name(chat_label, fallback=f"chat_{str(chat_id).replace('-', 'neg_')}")
    return f"{safe_label}__{chat_id}"


def infer_message_audit_chat_name(log_path, chat_id):
    try:
        with open(log_path, "r", encoding="utf-8") as file_obj:
            first_line = (file_obj.readline() or "").strip()
        if not first_line:
            return ""
        if first_line.startswith("{"):
            record = json.loads(first_line)
            chat = record.get("chat") or {}
            if str(chat.get("id")) == str(chat_id):
                return chat.get("title") or chat.get("username") or ""
        match = re.search(r"chat=(.*?) \[" + re.escape(str(chat_id)) + r"\]", first_line)
        if match:
            return match.group(1).strip()
    except Exception:
        pass
    return ""


def migrate_message_audit_dirs():
    try:
        entries = os.listdir(MESSAGE_AUDIT_DIR)
    except Exception:
        return

    for entry in entries:
        legacy_dir = os.path.join(MESSAGE_AUDIT_DIR, entry)
        if not os.path.isdir(legacy_dir):
            continue
        if not re.fullmatch(r"-?\d+", entry):
            continue

        txt_files = sorted(
            file_name for file_name in os.listdir(legacy_dir)
            if file_name.endswith(".txt")
        )
        if not txt_files:
            continue

        chat_id = entry
        inferred_name = infer_message_audit_chat_name(os.path.join(legacy_dir, txt_files[0]), chat_id)
        dir_name = get_message_audit_chat_dir_name({"title": inferred_name}, chat_id)
        named_dir = os.path.join(MESSAGE_AUDIT_DIR, dir_name)
        if named_dir == legacy_dir or os.path.exists(named_dir):
            continue
        try:
            os.rename(legacy_dir, named_dir)
        except OSError:
            continue


def get_message_audit_filepath(chat, chat_id, event_ts=None):
    event_ts = int(time.time()) if event_ts is None else int(event_ts)
    date_key = time.strftime("%Y-%m-%d", time.localtime(event_ts))
    named_dir = os.path.join(MESSAGE_AUDIT_DIR, get_message_audit_chat_dir_name(chat, chat_id))
    legacy_dir = os.path.join(MESSAGE_AUDIT_DIR, str(chat_id))
    if legacy_dir != named_dir and os.path.isdir(legacy_dir) and not os.path.exists(named_dir):
        try:
            os.rename(legacy_dir, named_dir)
        except OSError:
            pass
    chat_dir = named_dir
    os.makedirs(chat_dir, exist_ok=True)
    return os.path.join(chat_dir, f"{date_key}.txt")


def summarize_message_content(msg):
    text = compact_log_text((msg.get("text") or "").strip(), limit=8000)
    caption = compact_log_text((msg.get("caption") or "").strip(), limit=8000)
    media_keys = []
    for key in ("photo", "video", "video_note", "animation", "document", "audio", "voice", "sticker", "location", "contact", "poll"):
        if msg.get(key):
            media_keys.append(key)
    return {
        "text": text,
        "caption": caption,
        "media_types": media_keys,
        "has_media": bool(media_keys),
        "content_preview": " | ".join(
            part
            for part in [
                f"text={text}" if text else "",
                f"caption={caption}" if caption else "",
                f"media={','.join(media_keys)}" if media_keys else "",
            ]
            if part
        ) or "content=<empty>",
    }


def write_message_audit_line(log_path, line):
    with MESSAGE_AUDIT_LOCK:
        with open(log_path, "a", encoding="utf-8") as file_obj:
            file_obj.write(line)


def message_audit_writer_loop():
    while True:
        item = MESSAGE_AUDIT_QUEUE.get()
        try:
            write_message_audit_line(item["path"], item["line"])
        except Exception as exc:
            print(f"Message audit writer error: {exc}", flush=True)
        finally:
            MESSAGE_AUDIT_QUEUE.task_done()


def record_message_audit_entry(msg):
    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    if chat_id is None:
        return

    event_ts = coerce_int(msg.get("date"), int(time.time()))
    log_path = get_message_audit_filepath(chat, chat_id, event_ts=event_ts)
    chat_title = chat.get("title") or chat.get("first_name") or str(chat_id)
    sender_chat = msg.get("sender_chat", {}) or {}
    from_user = msg.get("from", {}) or {}

    if sender_chat:
        actor_name = sender_chat.get("title") or sender_chat.get("username") or "SenderChat"
        actor_id = sender_chat.get("id") or 0
        actor_kind = "sender_chat"
        actor_username = sender_chat.get("username") or ""
        actor_is_bot = False
    else:
        actor_name = get_user_display_name(from_user) if from_user else "Unknown"
        actor_id = from_user.get("id") or 0
        actor_kind = "user"
        actor_username = from_user.get("username") or ""
        actor_is_bot = bool(from_user.get("is_bot"))

    reply_to = msg.get("reply_to_message") or {}
    reply_sender = reply_to.get("from") or {}
    reply_to_id = reply_to.get("message_id")
    timestamp_text = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(event_ts))
    content = summarize_message_content(msg)
    record = {
        "logged_at": timestamp_text,
        "logged_at_unix": event_ts,
        "chat": {
            "id": chat_id,
            "type": chat.get("type") or "",
            "title": chat_title,
            "username": chat.get("username") or "",
        },
        "message": {
            "id": msg.get("message_id") or 0,
            "thread_id": msg.get("message_thread_id") or 0,
            "reply_to_message_id": reply_to_id or 0,
            "reply_to_user_id": reply_sender.get("id") or 0,
            "reply_to_user_name": get_user_display_name(reply_sender) if reply_sender else "",
            "reply_to_username": reply_sender.get("username") or "",
            "text": content["text"],
            "caption": content["caption"],
            "media_types": content["media_types"],
            "preview": content["content_preview"],
        },
        "sender": {
            "kind": actor_kind,
            "id": actor_id,
            "name": actor_name,
            "username": actor_username,
            "is_bot": actor_is_bot,
        },
    }
    line = json.dumps(record, ensure_ascii=False) + "\n"

    try:
        MESSAGE_AUDIT_QUEUE.put_nowait({"path": log_path, "line": line})
    except queue.Full:
        write_message_audit_line(log_path, line)


def get_user_filepath(chat_id):
    return os.path.join(HISTORY_DIR, f"{chat_id}.json")


def default_user_data():
    return {
        "lang": DEFAULT_LANGUAGE,
        "lang_set_at": 0,
        "user_lang_overrides": {},
        "history": [],
        "interaction_contexts": [],
        "tracked_messages": [],
        "temp_blocked_users": {},
    }


def coerce_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def normalize_tracked_message_entry(item):
    if isinstance(item, int):
        return {"message_id": item, "user_id": 0, "kind": "text", "has_link": False}
    if not isinstance(item, dict):
        return None

    message_id = coerce_int(item.get("message_id"), None)
    if message_id is None:
        return None

    return {
        "message_id": message_id,
        "user_id": coerce_int(item.get("user_id"), 0),
        "kind": str(item.get("kind") or "text"),
        "has_link": bool(item.get("has_link", False)),
    }


def normalize_interaction_context_entry(item):
    if not isinstance(item, dict):
        return None

    message_id = coerce_int(item.get("message_id"), None)
    command = str(item.get("command") or "").strip().lower()
    if message_id is None or command not in INTERACTION_COMMAND_SPECS:
        return None

    return {
        "message_id": message_id,
        "command": command,
        "command_display": str(item.get("command_display") or INTERACTION_COMMAND_SPECS[command]["display"]).strip(),
        "emoji": str(item.get("emoji") or INTERACTION_COMMAND_SPECS[command]["emoji"]).strip(),
        "actor_id": coerce_int(item.get("actor_id"), 0),
        "actor_name": str(item.get("actor_name") or "User").strip() or "User",
        "target_id": coerce_int(item.get("target_id"), 0),
        "target_name": str(item.get("target_name") or "").strip(),
        "caption_text": str(item.get("caption_text") or "").strip(),
        "summary": str(item.get("summary") or "").strip(),
        "created_at": max(0, coerce_int(item.get("created_at"), 0)),
    }


def normalize_user_data(data, now=None):
    now = int(time.time()) if now is None else int(now)
    raw = data if isinstance(data, dict) else {}
    normalized = default_user_data()

    lang_code = raw.get("lang", DEFAULT_LANGUAGE)
    if lang_code not in LANGUAGES:
        lang_code = DEFAULT_LANGUAGE
    lang_set_at = max(0, coerce_int(raw.get("lang_set_at"), 0))
    if lang_code != DEFAULT_LANGUAGE and lang_set_at and (now - lang_set_at) >= GROUP_LANGUAGE_SECONDS:
        lang_code = DEFAULT_LANGUAGE
        lang_set_at = 0
    if lang_code == DEFAULT_LANGUAGE:
        lang_set_at = 0

    history = []
    raw_history = raw.get("history", [])
    if not isinstance(raw_history, list):
        raw_history = []
    for item in raw_history:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        text = str(item.get("text") or "").strip()
        if role in {"user", "assistant"} and text:
            history.append({"role": role, "text": text})

    interaction_contexts = []
    raw_contexts = raw.get("interaction_contexts", [])
    if not isinstance(raw_contexts, list):
        raw_contexts = []
    for item in raw_contexts:
        normalized_item = normalize_interaction_context_entry(item)
        if normalized_item:
            interaction_contexts.append(normalized_item)

    tracked_source = raw.get("tracked_messages")
    if tracked_source is None:
        tracked_source = raw.get("tracked_message_ids", [])
    if not isinstance(tracked_source, list):
        tracked_source = []
    tracked_messages = []
    for item in tracked_source or []:
        normalized_item = normalize_tracked_message_entry(item)
        if normalized_item:
            tracked_messages.append(normalized_item)

    overrides = {}
    raw_overrides = raw.get("user_lang_overrides", {})
    if not isinstance(raw_overrides, dict):
        raw_overrides = {}
    for user_id, row in raw_overrides.items():
        if not isinstance(row, dict):
            continue
        override_lang = row.get("lang", DEFAULT_LANGUAGE)
        set_at = max(0, coerce_int(row.get("set_at"), 0))
        if override_lang not in LANGUAGES:
            continue
        if override_lang != DEFAULT_LANGUAGE and set_at and (now - set_at) < USER_LANGUAGE_SECONDS:
            overrides[str(user_id)] = {"lang": override_lang, "set_at": set_at}

    blocked_users = {}
    raw_blocked_users = raw.get("temp_blocked_users", {})
    if not isinstance(raw_blocked_users, dict):
        raw_blocked_users = {}
    for user_id, expiry in raw_blocked_users.items():
        expiry_ts = coerce_int(expiry, 0)
        if expiry_ts > now:
            blocked_users[str(user_id)] = expiry_ts

    normalized.update({
        "lang": lang_code,
        "lang_set_at": lang_set_at,
        "user_lang_overrides": overrides,
        "history": history[-30:],
        "interaction_contexts": interaction_contexts[-INTERACTION_CONTEXT_LIMIT:],
        "tracked_messages": tracked_messages[-500:],
        "temp_blocked_users": blocked_users,
    })
    return normalized


def count_mute_entries(data):
    if not isinstance(data, dict):
        return 0
    group_count = len(data.get("groups", {})) if isinstance(data.get("groups"), dict) else 0
    user_count = 0
    raw_users = data.get("users", {})
    if not isinstance(raw_users, dict):
        raw_users = {}
    for chat_users in raw_users.values():
        if isinstance(chat_users, dict):
            user_count += len(chat_users)
    return group_count + user_count


def normalize_group_store(data):
    if not isinstance(data, dict):
        return {}
    normalized = {}
    for chat_id, snapshot in data.items():
        if not isinstance(snapshot, dict):
            continue
        chat_id_int = coerce_int(snapshot.get("chat_id"), coerce_int(chat_id, None))
        if chat_id_int is None:
            continue
        raw_admin_ids = snapshot.get("admin_ids", [])
        if not isinstance(raw_admin_ids, list):
            raw_admin_ids = []
        admin_ids = []
        for admin_id in raw_admin_ids:
            normalized_admin_id = coerce_int(admin_id, None)
            if normalized_admin_id is not None:
                admin_ids.append(normalized_admin_id)
        raw_admins = snapshot.get("admins", [])
        if not isinstance(raw_admins, list):
            raw_admins = []
        admins = [str(name).strip() for name in raw_admins if str(name).strip()]
        normalized[str(chat_id_int)] = {
            "chat_id": chat_id_int,
            "title": str(snapshot.get("title") or chat_id_int),
            "owner_id": coerce_int(snapshot.get("owner_id"), None),
            "owner": str(snapshot.get("owner") or "Owner"),
            "admin_ids": sorted(set(admin_ids)),
            "admins": admins,
            "members": max(0, coerce_int(snapshot.get("members"), 0)),
            "updated_at": max(0, coerce_int(snapshot.get("updated_at"), 0)),
        }
    return normalized


def normalize_items_store(data):
    if not isinstance(data, dict):
        return {}
    normalized = {}
    for chat_id, chat_rows in data.items():
        if not isinstance(chat_rows, dict):
            continue
        clean_rows = {}
        for user_id, row in chat_rows.items():
            if not isinstance(row, dict):
                continue
            clean_rows[str(user_id)] = {
                "name": str(row.get("name") or "Admin"),
                "images": max(0, coerce_int(row.get("images"), 0)),
                "videos": max(0, coerce_int(row.get("videos"), 0)),
                "files": max(0, coerce_int(row.get("files"), 0)),
                "texts": max(0, coerce_int(row.get("texts"), 0)),
            }
        normalized[str(chat_id)] = clean_rows
    return normalized


def normalize_title_store(data):
    if not isinstance(data, dict):
        return {}
    normalized = {}
    for chat_id, chat_titles in data.items():
        if not isinstance(chat_titles, dict):
            continue
        clean_titles = {}
        for user_id, title in chat_titles.items():
            clean_title = str(title or "").strip()
            if clean_title:
                clean_titles[str(user_id)] = clean_title
        normalized[str(chat_id)] = clean_titles
    return normalized


def normalize_mute_store(data, now=None):
    now = int(time.time()) if now is None else int(now)
    raw = data if isinstance(data, dict) else {}
    normalized = {"groups": {}, "users": {}}

    raw_groups = raw.get("groups", {})
    if not isinstance(raw_groups, dict):
        raw_groups = {}
    for chat_id, expiry in raw_groups.items():
        expiry_ts = coerce_int(expiry, 0)
        if expiry_ts > now:
            normalized["groups"][str(chat_id)] = expiry_ts

    raw_users = raw.get("users", {})
    if not isinstance(raw_users, dict):
        raw_users = {}
    for chat_id, chat_users in raw_users.items():
        if not isinstance(chat_users, dict):
            continue
        active_users = {}
        for user_id, expiry in chat_users.items():
            expiry_ts = coerce_int(expiry, 0)
            if expiry_ts > now:
                active_users[str(user_id)] = expiry_ts
        if active_users:
            normalized["users"][str(chat_id)] = active_users

    return normalized


def normalize_command_spam_store(data, now=None):
    now = int(time.time()) if now is None else int(now)
    raw = data if isinstance(data, dict) else {}
    normalized = {}
    for key, row in raw.items():
        if not isinstance(row, dict):
            continue
        start = max(0, coerce_int(row.get("start"), 0))
        count = max(0, coerce_int(row.get("count"), 0))
        if not start or not count:
            continue
        if now - start > COMMAND_SPAM_WINDOW_SECONDS:
            continue
        normalized[str(key)] = {"count": count, "start": start}
    return normalized


def normalize_owner_override_store(data):
    if not isinstance(data, dict):
        return {}
    normalized = {}
    for chat_id, row in data.items():
        if not isinstance(row, dict):
            continue
        owner_id = coerce_int(row.get("owner_id"), None)
        owner_name = str(row.get("owner_name") or row.get("owner") or "").strip()
        if owner_id is None or not owner_name:
            continue
        normalized[str(chat_id)] = {
            "owner_id": owner_id,
            "owner_name": owner_name,
            "set_by": coerce_int(row.get("set_by"), 0),
            "set_at": max(0, coerce_int(row.get("set_at"), 0)),
        }
    return normalized


def normalize_group_audit_store(data):
    if not isinstance(data, dict):
        return {}
    normalized = {}
    for chat_id, row in data.items():
        if not isinstance(row, dict):
            continue
        chat_id_int = coerce_int(row.get("chat_id"), coerce_int(chat_id, None))
        if chat_id_int is None:
            continue
        raw_admin_ids = row.get("admin_ids", [])
        if not isinstance(raw_admin_ids, list):
            raw_admin_ids = []
        admin_ids = []
        for admin_id in raw_admin_ids:
            normalized_admin_id = coerce_int(admin_id, None)
            if normalized_admin_id is not None:
                admin_ids.append(normalized_admin_id)
        raw_admins = row.get("admins", [])
        if not isinstance(raw_admins, list):
            raw_admins = []
        admins = [str(name).strip() for name in raw_admins if str(name).strip()]
        normalized[str(chat_id_int)] = {
            "chat_id": chat_id_int,
            "title": str(row.get("title") or chat_id_int),
            "status": "removed" if str(row.get("status") or "").lower() == "removed" else "active",
            "owner_id": coerce_int(row.get("owner_id"), None),
            "owner": str(row.get("owner") or "Owner"),
            "admin_ids": sorted(set(admin_ids)),
            "admins": admins,
            "members": max(0, coerce_int(row.get("members"), 0)),
            "added_by_id": coerce_int(row.get("added_by_id"), None),
            "added_by_name": str(row.get("added_by_name") or "").strip(),
            "added_at": max(0, coerce_int(row.get("added_at"), 0)),
            "promoted_by_id": coerce_int(row.get("promoted_by_id"), None),
            "promoted_by_name": str(row.get("promoted_by_name") or "").strip(),
            "promoted_at": max(0, coerce_int(row.get("promoted_at"), 0)),
            "removed_by_id": coerce_int(row.get("removed_by_id"), None),
            "removed_by_name": str(row.get("removed_by_name") or "").strip(),
            "removed_at": max(0, coerce_int(row.get("removed_at"), 0)),
            "welcome_message": str(row.get("welcome_message") or "").strip(),
            "updated_at": max(0, coerce_int(row.get("updated_at"), 0)),
        }
    return normalized


def normalize_group_activity_store(data):
    if not isinstance(data, dict):
        return {}
    normalized = {}
    for chat_id, row in data.items():
        if not isinstance(row, dict):
            continue
        presence_source = row.get("presence_last_seen", {})
        if not isinstance(presence_source, dict):
            presence_source = {}
        presence_last_seen = {}
        for user_id, ts in presence_source.items():
            seen_at = max(0, coerce_int(ts, 0))
            if seen_at:
                presence_last_seen[str(user_id)] = seen_at

        greetings_source = row.get("daily_greetings", {})
        if not isinstance(greetings_source, dict):
            greetings_source = {}
        daily_greetings = {}
        for key, date_value in greetings_source.items():
            date_text = str(date_value or "").strip()
            if date_text:
                daily_greetings[str(key)] = date_text

        normalized[str(chat_id)] = {
            "presence_last_seen": presence_last_seen,
            "daily_greetings": daily_greetings,
        }
    return normalized


def refresh_managed_json_files(include_chat_id=None, include_chat_type=None):
    now = int(time.time())
    os.makedirs(HISTORY_DIR, exist_ok=True)

    group_store = normalize_group_store(load_json_file(GROUPS_FILE, {}))
    save_json_file(GROUPS_FILE, group_store)
    save_json_file(ITEMS_FILE, normalize_items_store(load_json_file(ITEMS_FILE, {})))
    save_json_file(ADMIN_TITLES_FILE, normalize_title_store(load_json_file(ADMIN_TITLES_FILE, {})))
    save_json_file(OWNER_OVERRIDE_FILE, normalize_owner_override_store(load_json_file(OWNER_OVERRIDE_FILE, {})))
    save_json_file(GROUP_AUDIT_FILE, normalize_group_audit_store(load_json_file(GROUP_AUDIT_FILE, {})))
    save_json_file(GROUP_ACTIVITY_FILE, normalize_group_activity_store(load_json_file(GROUP_ACTIVITY_FILE, {})))

    raw_mute_store = load_json_file(MUTE_STATE_FILE, {"groups": {}, "users": {}})
    normalized_mute_store = normalize_mute_store(raw_mute_store, now=now)
    save_json_file(MUTE_STATE_FILE, normalized_mute_store)

    raw_spam_store = load_json_file(COMMAND_SPAM_FILE, {})
    normalized_spam_store = normalize_command_spam_store(raw_spam_store, now=now)
    save_json_file(COMMAND_SPAM_FILE, normalized_spam_store)
    raw_spam_count = len(raw_spam_store) if isinstance(raw_spam_store, dict) else 0

    refreshed_history_files = 0
    for file_name in os.listdir(HISTORY_DIR):
        if not file_name.endswith(".json"):
            continue
        chat_id = coerce_int(os.path.splitext(file_name)[0], None)
        if chat_id is None:
            continue
        save_user_data(chat_id, load_user_data(chat_id))
        refreshed_history_files += 1

    group_ids = {coerce_int(chat_id, None) for chat_id in group_store.keys()}
    if include_chat_type in {"group", "supergroup"} and include_chat_id is not None:
        group_ids.add(int(include_chat_id))

    groups_synced = 0
    groups_failed = 0
    for group_id in sorted(chat_id for chat_id in group_ids if chat_id is not None):
        try:
            snapshot = sync_admin_state(group_id, force=True)
            if snapshot:
                groups_synced += 1
            else:
                groups_failed += 1
        except Exception as e:
            print(f"Update sync error for {group_id}: {e}", flush=True)
            groups_failed += 1

    return {
        "history_files": refreshed_history_files,
        "groups_synced": groups_synced,
        "groups_failed": groups_failed,
        "expired_mutes_removed": max(0, count_mute_entries(raw_mute_store) - count_mute_entries(normalized_mute_store)),
        "expired_spam_removed": max(0, raw_spam_count - len(normalized_spam_store)),
    }


def run_json_update_cycle(trigger="manual", include_chat_id=None, include_chat_type=None, force=False):
    if force:
        acquired = JSON_UPDATE_LOCK.acquire(timeout=JSON_UPDATE_FORCE_WAIT_SECONDS)
    else:
        acquired = JSON_UPDATE_LOCK.acquire(blocking=False)
    if not acquired:
        return {"skipped": True, "trigger": trigger, "forced": force, "reason": "busy"}

    try:
        summary = refresh_managed_json_files(include_chat_id=include_chat_id, include_chat_type=include_chat_type)
        summary["trigger"] = trigger
        summary["forced"] = force
        summary["updated_at"] = int(time.time())
        return summary
    finally:
        JSON_UPDATE_LOCK.release()


def format_update_summary(summary):
    if summary.get("skipped"):
        return "⚠️ JSON self update is already running. Please use /update again in a few seconds."

    title = "✅ Force JSON update complete." if summary.get("forced") else "✅ JSON self update complete."
    trigger_label = "force /update command" if summary.get("forced") else summary.get("trigger", "auto")
    return (
        f"{title}\n"
        f"Trigger: {trigger_label}\n"
        f"History files refreshed: {summary.get('history_files', 0)}\n"
        f"Group snapshots synced: {summary.get('groups_synced', 0)}\n"
        f"Group sync failed: {summary.get('groups_failed', 0)}\n"
        f"Expired mute entries removed: {summary.get('expired_mutes_removed', 0)}\n"
        f"Expired spam entries removed: {summary.get('expired_spam_removed', 0)}"
    )


def load_user_data(chat_id):
    return normalize_user_data(load_json_file(get_user_filepath(chat_id), {}))


def save_user_data(chat_id, data):
    save_json_file(get_user_filepath(chat_id), normalize_user_data(data))


def save_interaction_context(chat_id, entry):
    normalized_entry = normalize_interaction_context_entry(entry)
    if not normalized_entry:
        return
    user_data = load_user_data(chat_id)
    contexts = user_data.get("interaction_contexts", [])
    contexts.append(normalized_entry)
    user_data["interaction_contexts"] = contexts[-INTERACTION_CONTEXT_LIMIT:]
    save_user_data(chat_id, user_data)


def get_interaction_context(chat_id, message_id):
    if not message_id:
        return None
    user_data = load_user_data(chat_id)
    for row in reversed(user_data.get("interaction_contexts", [])):
        if row.get("message_id") == int(message_id):
            return row
    return None


def build_interaction_context_summary(command_name, actor_name, target_name=None):
    spec = INTERACTION_COMMAND_SPECS[command_name]
    if target_name:
        return f"{actor_name} used {spec['display']} on {target_name} with {spec['emoji']}."
    return f"{actor_name} used {spec['display']} with {spec['emoji']}."


def get_owner_override_store():
    return normalize_owner_override_store(load_json_file(OWNER_OVERRIDE_FILE, {}))


def save_owner_override_store(data):
    save_json_file(OWNER_OVERRIDE_FILE, normalize_owner_override_store(data))


def get_owner_override(chat_id):
    return get_owner_override_store().get(str(chat_id))


def set_owner_override(chat_id, owner_id, owner_name, set_by):
    store = get_owner_override_store()
    store[str(chat_id)] = {
        "owner_id": int(owner_id),
        "owner_name": str(owner_name or "Owner").strip() or "Owner",
        "set_by": int(set_by or 0),
        "set_at": int(time.time()),
    }
    save_owner_override_store(store)
    ADMIN_CACHE.pop(chat_id, None)


def clear_owner_override(chat_id):
    store = get_owner_override_store()
    removed = store.pop(str(chat_id), None)
    save_owner_override_store(store)
    ADMIN_CACHE.pop(chat_id, None)
    return bool(removed)


def is_set_owner_developer(user_id):
    return int(user_id or 0) == DEVELOPER_COMMAND_USER_ID


def apply_owner_override_to_snapshot(chat_id, snapshot):
    if not snapshot:
        return snapshot
    override = get_owner_override(chat_id)
    result = dict(snapshot)
    if override:
        result["owner_id"] = override.get("owner_id")
        result["owner"] = override.get("owner_name") or result.get("owner") or "Owner"
        result["owner_override"] = True
    else:
        result["owner_override"] = False
    return result


def is_current_static_owner(chat_id, user_id):
    if user_id in (None, 0):
        return False
    override = get_owner_override(chat_id)
    if not override:
        return False
    return int(user_id) == int(override.get("owner_id") or -1)


def get_group_activity_store():
    return normalize_group_activity_store(load_json_file(GROUP_ACTIVITY_FILE, {}))


def save_group_activity_store(data):
    save_json_file(GROUP_ACTIVITY_FILE, normalize_group_activity_store(data))


def get_group_activity_entry(chat_id):
    store = get_group_activity_store()
    return store.get(str(chat_id), {"presence_last_seen": {}, "daily_greetings": {}})


def upsert_group_activity_entry(chat_id, updates):
    store = get_group_activity_store()
    existing = store.get(str(chat_id), {"presence_last_seen": {}, "daily_greetings": {}})
    merged = {
        "presence_last_seen": dict(existing.get("presence_last_seen", {})),
        "daily_greetings": dict(existing.get("daily_greetings", {})),
    }
    for key, value in (updates or {}).items():
        if value is not None:
            merged[key] = value
    store[str(chat_id)] = merged
    save_group_activity_store(store)
    return merged


def note_user_presence(chat_id, user_id):
    if user_id in (None, 0):
        return 0, 0
    row = get_group_activity_entry(chat_id)
    last_seen = coerce_int(row.get("presence_last_seen", {}).get(str(user_id)), 0)
    now = int(time.time())
    presence_last_seen = dict(row.get("presence_last_seen", {}))
    presence_last_seen[str(user_id)] = now
    upsert_group_activity_entry(chat_id, {"presence_last_seen": presence_last_seen})
    return last_seen, now


def mark_daily_greeting_sent(chat_id, greeting_key, date_key):
    row = get_group_activity_entry(chat_id)
    greetings = dict(row.get("daily_greetings", {}))
    greetings[greeting_key] = date_key
    upsert_group_activity_entry(chat_id, {"daily_greetings": greetings})


def get_group_audit_store():
    return normalize_group_audit_store(load_json_file(GROUP_AUDIT_FILE, {}))


def save_group_audit_store(data):
    save_json_file(GROUP_AUDIT_FILE, normalize_group_audit_store(data))


def get_group_audit_entry(chat_id):
    return get_group_audit_store().get(str(chat_id), {})


def upsert_group_audit_entry(chat_id, updates):
    store = get_group_audit_store()
    existing = store.get(str(chat_id), {})
    merged = {
        "chat_id": int(chat_id),
        "title": str(existing.get("title") or chat_id),
        "status": existing.get("status") or "active",
        "owner_id": existing.get("owner_id"),
        "owner": existing.get("owner") or "Owner",
        "admin_ids": list(existing.get("admin_ids", [])),
        "admins": list(existing.get("admins", [])),
        "members": max(0, coerce_int(existing.get("members"), 0)),
        "added_by_id": existing.get("added_by_id"),
        "added_by_name": existing.get("added_by_name") or "",
        "added_at": max(0, coerce_int(existing.get("added_at"), 0)),
        "promoted_by_id": existing.get("promoted_by_id"),
        "promoted_by_name": existing.get("promoted_by_name") or "",
        "promoted_at": max(0, coerce_int(existing.get("promoted_at"), 0)),
        "removed_by_id": existing.get("removed_by_id"),
        "removed_by_name": existing.get("removed_by_name") or "",
        "removed_at": max(0, coerce_int(existing.get("removed_at"), 0)),
        "welcome_message": existing.get("welcome_message") or "",
        "updated_at": max(0, coerce_int(existing.get("updated_at"), 0)),
    }
    for key, value in (updates or {}).items():
        if value is not None:
            merged[key] = value
    merged["chat_id"] = int(chat_id)
    merged["updated_at"] = int(time.time())
    store[str(chat_id)] = merged
    save_group_audit_store(store)
    return merged


def get_actor_display_name(user):
    if not user:
        return "Unknown"
    return get_user_display_name(user) or "Unknown"


def update_group_audit_from_snapshot(snapshot):
    if not snapshot:
        return
    upsert_group_audit_entry(
        snapshot.get("chat_id"),
        {
            "title": str(snapshot.get("title") or snapshot.get("chat_id")),
            "status": "active",
            "owner_id": snapshot.get("owner_id"),
            "owner": str(snapshot.get("owner") or "Owner"),
            "admin_ids": list(snapshot.get("admin_ids", [])),
            "admins": list(snapshot.get("admins", [])),
            "members": max(0, coerce_int(snapshot.get("members"), 0)),
        },
    )


def remove_group_from_active_store(chat_id):
    groups = normalize_group_store(load_json_file(GROUPS_FILE, {}))
    if str(chat_id) in groups:
        groups.pop(str(chat_id), None)
        save_json_file(GROUPS_FILE, groups)
    title_store = normalize_title_store(load_json_file(ADMIN_TITLES_FILE, {}))
    if str(chat_id) in title_store:
        title_store.pop(str(chat_id), None)
        save_json_file(ADMIN_TITLES_FILE, title_store)
    item_store = normalize_items_store(load_json_file(ITEMS_FILE, {}))
    if str(chat_id) in item_store:
        item_store.pop(str(chat_id), None)
        save_json_file(ITEMS_FILE, item_store)
    activity_store = normalize_group_activity_store(load_json_file(GROUP_ACTIVITY_FILE, {}))
    if str(chat_id) in activity_store:
        activity_store.pop(str(chat_id), None)
        save_json_file(GROUP_ACTIVITY_FILE, activity_store)
    ADMIN_CACHE.pop(chat_id, None)


def build_bot_added_message(chat_title, actor_name):
    safe_title = escape_markdown_text(chat_title or "this group")
    safe_actor = escape_markdown_text(actor_name or "friend")
    return (
        f"💖 Thank you *{safe_actor}* for adding Aira to *{safe_title}*\\!\n"
        "🌸 Main warmly ready hun.\n"
        "🛡 Safety, chat aur admin help ke liye bas bula lena."
    )


def build_bot_promoted_message(chat_title, actor_name):
    safe_title = escape_markdown_text(chat_title or "this group")
    safe_actor = escape_markdown_text(actor_name or "friend")
    return (
        f"🛡 Thank you *{safe_actor}* for making Aira admin in *{safe_title}*\\! 💖\n"
        "✨ Ab main safety aur admin support aur smoothly handle kar paungi.\n"
        "🌸 Trust ke liye shukriya."
    )


def build_member_welcome_message(member_name, chat_title):
    safe_name = escape_markdown_text(member_name or "Friend")
    safe_title = escape_markdown_text(chat_title or "group")
    return (
        f"🎉 Welcome *{safe_name}* to *{safe_title}*\\! 🌸\n"
        "💖 Pyaar se raho, maze karo aur achchhi vibes spread karo.\n"
        "🤍 Aira yahin hai agar help chahiye ho."
    )


def build_owner_return_message(owner_name):
    safe_name = escape_markdown_text(owner_name or "Owner")
    return (
        f"👑 Welcome back *{safe_name}*\\! 💫\n"
        "💖 Kaafi der baad aap aaye ho, group aur Aira dono khush hain.\n"
        "🌷 Main yahin hun, kuchh chahiye ho to bata do."
    )


def build_owner_changed_message(chat_title, previous_owner_name, new_owner_name):
    safe_title = escape_markdown_text(chat_title or "group")
    safe_new = escape_markdown_text(new_owner_name or "Owner")
    safe_old = escape_markdown_text(previous_owner_name or "Previous Owner")
    return (
        f"👑 Owner update in *{safe_title}*\\! 💞\n"
        f"🌸 Welcome *{safe_new}*.\n"
        f"🤍 Previous owner: *{safe_old}*.\n"
        "✨ Aira aapka warmly welcome karti hai."
    )


def build_daily_greeting_message(greeting_key):
    messages = {
        "good_morning": (
            "☀️ Good morning sabko 💖\n"
            "Aaj ka din sweet, peaceful aur lucky rahe.\n"
            "🌸 Main Aira yahin hun, jab bhi baat karni ho bula lena."
        ),
        "good_afternoon": (
            "🌤 Good afternoon cuties 💗\n"
            "Lunch ke baad bhi energy soft aur bright bani rahe.\n"
            "✨ Agar help chahiye ho to Aira ready hai."
        ),
        "good_evening": (
            "🌆 Good evening everyone 💞\n"
            "Shaam pyari ho, mood halka ho aur vibes cozy rahen.\n"
            "🌷 Aira ke saath aaram se baat kar sakte ho."
        ),
        "good_night": (
            "🌙 Good night sweet people 🤍\n"
            "Aaj ki thakan halka sa chhod do aur chain se rest karo.\n"
            "💫 Kal phir milte hain, Aira yahin rahegi."
        ),
    }
    return messages.get(greeting_key, "")


def record_bot_added_event(chat, actor, welcome_message=None):
    chat_id = chat.get("id")
    if chat_id is None:
        return
    chat_title = str(chat.get("title") or chat.get("first_name") or chat_id)
    actor_id = coerce_int((actor or {}).get("id"), None)
    actor_name = get_actor_display_name(actor)
    upsert_group_audit_entry(
        chat_id,
        {
            "title": chat_title,
            "status": "active",
            "added_by_id": actor_id,
            "added_by_name": actor_name,
            "added_at": int(time.time()),
            "removed_by_id": 0,
            "removed_by_name": "",
            "removed_at": 0,
            "welcome_message": welcome_message or build_bot_added_message(chat_title, actor_name),
        },
    )


def record_bot_promoted_event(chat, actor):
    chat_id = chat.get("id")
    if chat_id is None:
        return
    actor_id = coerce_int((actor or {}).get("id"), None)
    actor_name = get_actor_display_name(actor)
    upsert_group_audit_entry(
        chat_id,
        {
            "promoted_by_id": actor_id,
            "promoted_by_name": actor_name,
            "promoted_at": int(time.time()),
        },
    )


def record_bot_removed_event(chat, actor):
    chat_id = chat.get("id")
    if chat_id is None:
        return
    existing = get_group_audit_entry(chat_id)
    chat_title = str(chat.get("title") or existing.get("title") or chat.get("first_name") or chat_id)
    actor_id = coerce_int((actor or {}).get("id"), None)
    actor_name = get_actor_display_name(actor)
    upsert_group_audit_entry(
        chat_id,
        {
            "title": chat_title,
            "status": "removed",
            "removed_by_id": actor_id,
            "removed_by_name": actor_name,
            "removed_at": int(time.time()),
        },
    )
    remove_group_from_active_store(chat_id)


def has_global_group_admin_access(user_id):
    user_id_int = coerce_int(user_id, 0)
    if not user_id_int:
        return False
    if user_id_int in {OWNER_ID, DEVELOPER_COMMAND_USER_ID}:
        return True
    groups = normalize_group_store(load_json_file(GROUPS_FILE, {}))
    for snapshot in groups.values():
        if user_id_int == coerce_int(snapshot.get("owner_id"), 0):
            return True
        if user_id_int in {coerce_int(admin_id, 0) for admin_id in snapshot.get("admin_ids", [])}:
            return True
    return False


def format_unix_timestamp(ts):
    if not ts:
        return "Not recorded"
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(ts)))


def split_markdown_pages(paragraphs, limit=3500):
    pages = []
    current = ""
    for paragraph in paragraphs:
        piece = paragraph if not current else f"{current}\n\n{paragraph}"
        if len(piece) <= limit:
            current = piece
            continue
        if current:
            pages.append(current)
        if len(paragraph) <= limit:
            current = paragraph
            continue
        lines = paragraph.split("\n")
        chunk = ""
        for line in lines:
            tentative = line if not chunk else f"{chunk}\n{line}"
            if len(tentative) <= limit:
                chunk = tentative
            else:
                if chunk:
                    pages.append(chunk)
                chunk = line
        current = chunk
    if current:
        pages.append(current)
    return pages


def send_markdown_pages(chat_id, paragraphs):
    for page in split_markdown_pages(paragraphs):
        send_message(chat_id, page)


def maybe_send_owner_return_welcome(chat, user):
    chat_id = chat.get("id")
    user_id = (user or {}).get("id")
    if chat_id is None or user_id in (None, 0):
        return
    if not is_owner(chat_id, user_id):
        return
    last_seen, _ = note_user_presence(chat_id, user_id)
    if not last_seen:
        return
    if int(time.time()) - last_seen < OWNER_RETURN_WELCOME_SECONDS:
        return
    send_message(chat_id, build_owner_return_message(get_user_display_name(user)))


def maybe_send_daily_greetings():
    now = time.localtime()
    date_key = time.strftime("%Y-%m-%d", now)
    for greeting_key, schedule in DAILY_GREETING_SCHEDULE.items():
        if now.tm_hour != schedule["hour"] or now.tm_min != schedule["minute"]:
            continue
        groups = normalize_group_store(load_json_file(GROUPS_FILE, {}))
        for snapshot in groups.values():
            chat_id = snapshot.get("chat_id")
            if chat_id is None or is_group_muted(chat_id):
                continue
            activity_entry = get_group_activity_entry(chat_id)
            if activity_entry.get("daily_greetings", {}).get(greeting_key) == date_key:
                continue
            greeting_text = build_daily_greeting_message(greeting_key)
            if greeting_text:
                send_message(chat_id, greeting_text)
                mark_daily_greeting_sent(chat_id, greeting_key, date_key)


def scheduled_greeting_loop():
    while True:
        try:
            maybe_send_daily_greetings()
        except Exception as e:
            print(f"Scheduled greeting error: {e}", flush=True)
        time.sleep(SCHEDULED_GREETING_LOOP_SECONDS)


def build_all_group_view_paragraphs():
    groups = normalize_group_store(load_json_file(GROUPS_FILE, {}))
    audit_store = get_group_audit_store()
    active_entries = []
    removed_entries = []

    known_chat_ids = sorted(
        {str(chat_id) for chat_id in groups.keys()} | {str(chat_id) for chat_id in audit_store.keys()},
        key=lambda value: coerce_int(value, 0),
    )

    for chat_id in known_chat_ids:
        active_snapshot = groups.get(str(chat_id))
        audit_entry = audit_store.get(str(chat_id), {})
        if active_snapshot:
            merged = dict(audit_entry)
            merged.update(active_snapshot)
            merged["status"] = "active"
            merged["chat_id"] = active_snapshot.get("chat_id", coerce_int(chat_id, 0))
            merged["welcome_message"] = audit_entry.get("welcome_message", "")
            merged["added_by_id"] = audit_entry.get("added_by_id")
            merged["added_by_name"] = audit_entry.get("added_by_name", "")
            merged["added_at"] = audit_entry.get("added_at", 0)
            merged["promoted_by_id"] = audit_entry.get("promoted_by_id")
            merged["promoted_by_name"] = audit_entry.get("promoted_by_name", "")
            merged["promoted_at"] = audit_entry.get("promoted_at", 0)
            merged["removed_by_id"] = audit_entry.get("removed_by_id")
            merged["removed_by_name"] = audit_entry.get("removed_by_name", "")
            merged["removed_at"] = audit_entry.get("removed_at", 0)
            active_entries.append(merged)
        elif audit_entry:
            removed_entries.append(audit_entry)

    total_members = sum(max(0, coerce_int(entry.get("members"), 0)) for entry in active_entries)
    paragraphs = [
        (
            "🌍 **Aira Global Group View**\n"
            f"🟢 Active Groups: `{len(active_entries)}`\n"
            f"💔 Removed Groups: `{len(removed_entries)}`\n"
            f"👥 Total Members Across Active Groups: `{total_members}`"
        )
    ]

    if not active_entries and not removed_entries:
        paragraphs.append("⚠️ No group audit data is available yet.")
        return paragraphs

    if active_entries:
        active_entries.sort(key=lambda row: (str(row.get("title") or "").lower(), row.get("chat_id") or 0))
        for index, entry in enumerate(active_entries, start=1):
            admin_names = ", ".join(entry.get("admins", [])) or "No admins found"
            actor_name = entry.get("added_by_name") or "Not recorded"
            actor_id = entry.get("added_by_id")
            actor_line = escape_markdown_text(actor_name)
            if actor_id:
                actor_line += f" \\(`{actor_id}`\\)"
            promoter_name = entry.get("promoted_by_name") or "Not recorded"
            promoter_id = entry.get("promoted_by_id")
            promoter_line = escape_markdown_text(promoter_name)
            if promoter_id:
                promoter_line += f" \\(`{promoter_id}`\\)"
            paragraphs.append(
                "\n".join(
                    [
                        f"🟢 **Active Group {index}**",
                        f"📛 Group: {escape_markdown_text(str(entry.get('title') or entry.get('chat_id')))}",
                        f"🆔 Chat ID: `{entry.get('chat_id')}`",
                        f"👑 Owner: {escape_markdown_text(str(entry.get('owner') or 'Owner'))}",
                        f"🛡 Admin Count: `{len(entry.get('admin_ids', []))}`",
                        f"🧑‍✈️ Admins: {escape_markdown_text(admin_names)}",
                        f"👥 Members: `{max(0, coerce_int(entry.get('members'), 0))}`",
                        f"➕ Added By: {actor_line}",
                        f"🛡 Bot Admin By: {promoter_line}",
                        f"🕒 Added At: {escape_markdown_text(format_unix_timestamp(entry.get('added_at')))}",
                        f"🕒 Bot Admin At: {escape_markdown_text(format_unix_timestamp(entry.get('promoted_at')))}",
                        f"💌 Welcome Msg: {escape_markdown_text(entry.get('welcome_message') or 'Not recorded')}",
                        f"🔄 Last Sync: {escape_markdown_text(format_unix_timestamp(entry.get('updated_at')))}",
                    ]
                )
            )

    if removed_entries:
        removed_entries.sort(key=lambda row: row.get("removed_at") or 0, reverse=True)
        for index, entry in enumerate(removed_entries, start=1):
            remover_name = entry.get("removed_by_name") or "Not recorded"
            remover_id = entry.get("removed_by_id")
            remover_line = escape_markdown_text(remover_name)
            if remover_id:
                remover_line += f" \\(`{remover_id}`\\)"
            admin_names = ", ".join(entry.get("admins", [])) or "No admins saved"
            paragraphs.append(
                "\n".join(
                    [
                        f"💔 **Removed Group {index}**",
                        f"📛 Group: {escape_markdown_text(str(entry.get('title') or entry.get('chat_id')))}",
                        f"🆔 Chat ID: `{entry.get('chat_id')}`",
                        f"👑 Last Owner: {escape_markdown_text(str(entry.get('owner') or 'Owner'))}",
                        f"🛡 Last Admins: {escape_markdown_text(admin_names)}",
                        f"👥 Last Member Count: `{max(0, coerce_int(entry.get('members'), 0))}`",
                        f"➕ Added By: {escape_markdown_text(entry.get('added_by_name') or 'Not recorded')}",
                        f"💔 Removed By: {remover_line}",
                        f"🕒 Removed At: {escape_markdown_text(format_unix_timestamp(entry.get('removed_at')))}",
                    ]
                )
            )

    return paragraphs


def track_message(chat_id, message_id, user_id, kind, has_link=False):
    if not message_id:
        return
    user_data = load_user_data(chat_id)
    tracked = user_data.get("tracked_messages", [])
    tracked.append({"message_id": message_id, "user_id": user_id or 0, "kind": kind, "has_link": has_link})
    user_data["tracked_messages"] = tracked[-500:]
    save_user_data(chat_id, user_data)


# --- TELEGRAM HELPERS ---

def telegram_api_json(method, api_method, *, params=None, payload=None, timeout=10, retries=3):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{api_method}"
    last_error = None
    for attempt in range(retries):
        try:
            response = HTTP.request(method, url, params=params, json=payload, timeout=timeout)
            return response.json()
        except Exception as e:
            last_error = e
            if attempt < retries - 1:
                time.sleep(0.5 * (attempt + 1))
    raise last_error


def extract_interaction_media_url(provider_name, data):
    if provider_name == "nekosbest":
        results = data.get("results") or []
        if results:
            return str(results[0].get("url") or "").strip()
        return ""
    return str(data.get("url") or "").strip()


def fetch_interaction_media_url(command_name):
    spec = INTERACTION_COMMAND_SPECS.get(command_name)
    if not spec:
        return None

    for endpoint in spec.get("media_candidates", []):
        for provider_name, provider in INTERACTION_MEDIA_PROVIDERS.items():
            if endpoint not in provider.get("supported", set()):
                continue
            try:
                response = HTTP.get(provider["url"].format(endpoint=endpoint), timeout=12)
                if response.status_code != 200:
                    continue
                media_url = extract_interaction_media_url(provider_name, response.json())
                if media_url:
                    return media_url
            except Exception:
                continue
    return None


def send_message(chat_id, text, reply_markup=None, track_kind="bot_text", reply_to_message_id=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id
    try:
        data = telegram_api_json("POST", "sendMessage", payload=payload, timeout=10)
        result_message = data.get("result", {}) or {}
        message_id = result_message.get("message_id")
        if data.get("ok") and message_id:
            track_message(chat_id, message_id, 0, track_kind)
            record_message_audit_entry(result_message)
        return data
    except Exception as e:
        print(f"Send Error: {e}")
        return {}


def send_animation_message(chat_id, animation_url, caption, reply_to_message_id=None, track_kind="bot_animation"):
    payload = {
        "chat_id": chat_id,
        "animation": animation_url,
        "caption": caption,
        "parse_mode": "Markdown",
    }
    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id
    try:
        data = telegram_api_json("POST", "sendAnimation", payload=payload, timeout=20)
        result_message = data.get("result", {}) or {}
        message_id = result_message.get("message_id")
        if data.get("ok") and message_id:
            track_message(chat_id, message_id, 0, track_kind)
            record_message_audit_entry(result_message)
        return data
    except Exception as e:
        print(f"Animation Send Error: {e}")
        return {}


def send_temporary_message(chat_id, text, delay_seconds=POLICY_DELETE_SECONDS):
    data = send_message(chat_id, text, track_kind="bot_text")
    message_id = data.get("result", {}).get("message_id")
    if message_id:
        delete_message_later(chat_id, message_id, delay_seconds)


def edit_message(chat_id, message_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        telegram_api_json("POST", "editMessageText", payload=payload, timeout=10)
    except Exception:
        pass


def answer_callback(callback_id, text, show_alert=False):
    try:
        telegram_api_json(
            "POST",
            "answerCallbackQuery",
            payload={"callback_query_id": callback_id, "text": text, "show_alert": show_alert},
            timeout=10,
        )
    except Exception:
        pass


def send_typing(chat_id):
    try:
        telegram_api_json("GET", "sendChatAction", params={"chat_id": chat_id, "action": "typing"}, timeout=5)
    except Exception:
        pass


def send_reaction(chat_id, message_id, emoji_char):
    try:
        data = telegram_api_json(
            "POST",
            "setMessageReaction",
            payload={"chat_id": chat_id, "message_id": message_id, "reaction": [{"type": "emoji", "emoji": emoji_char}]},
            timeout=10,
        )
        return data.get("ok", False)
    except Exception as e:
        print(f"Reaction Error: {e}")
        return False


def delete_message(chat_id, message_id):
    try:
        data = telegram_api_json("POST", "deleteMessage", payload={"chat_id": chat_id, "message_id": message_id}, timeout=10)
        return data.get("ok", False)
    except Exception as e:
        print(f"Delete Error: {e}")
        return False


def delete_message_later(chat_id, message_id, delay_seconds):
    def _worker():
        time.sleep(delay_seconds)
        delete_message(chat_id, message_id)
    threading.Thread(target=_worker, daemon=True).start()


# --- TELEGRAM UI ---

def get_main_menu_keyboard():
    return {
        "keyboard": [
            [{"text": "🗣 Change Language"}, {"text": "🗑 Reset Memory"}],
            [{"text": "ℹ️ About AI"}, {"text": "🆘 Help"}],
        ],
        "resize_keyboard": True,
    }


def get_language_keyboard():
    rows = []
    row = []
    for code, label in LANGUAGES.items():
        row.append({"text": label, "callback_data": f"set_lang_{code}"})
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return {"inline_keyboard": rows}


def get_reset_confirm_keyboard():
    return {
        "inline_keyboard": [[
            {"text": "✅ Yes, Delete", "callback_data": "confirm_reset"},
            {"text": "❌ No, Cancel", "callback_data": "cancel_reset"},
        ]]
    }


def get_owner_keyboard():
    return {
        "inline_keyboard": [[
            {"text": "📨 Message Owner", "callback_data": "contact_owner"},
            {"text": "🧹 Full Clear", "callback_data": "owner_full_clear"},
        ]]
    }


def get_help_contact_keyboard():
    return {
        "inline_keyboard": [[
            {"text": "📨 Message Owner", "callback_data": "contact_owner"},
        ]]
    }


def get_start_panel_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "➕ Add Me To Your Group 👥", "url": f"https://t.me/{BOT_USERNAME}?startgroup=true"}],
            [
                {"text": "🤖 AI Chat", "callback_data": "start_ai_chat"},
                {"text": "⚙️ Commands", "callback_data": "start_commands"},
            ],
            [
                {"text": "🎮 Games", "callback_data": "start_games"},
                {"text": "🛡 Admin Panel", "callback_data": "start_admin_panel"},
            ],
            [
                {"text": "👑 Owner", "callback_data": "start_owner"},
                {"text": "📢 Updates", "callback_data": "start_updates"},
            ],
            [
                {"text": "✨ Extra", "callback_data": "start_extra"},
            ],
        ]
    }


def get_anonymous_fallback_name(chat_id, user_id):
    if is_owner(chat_id, user_id):
        return "Owner"
    return "Friend"


def get_start_display_name(msg):
    chat = msg.get("chat", {})
    user = msg.get("from", {}) or {}
    if user.get("username") == "GroupAnonymousBot" or user.get("first_name") == "Group":
        return get_anonymous_fallback_name(chat.get("id"), user.get("id"))
    first_name = (user.get("first_name") or "").strip()
    last_name = (user.get("last_name") or "").strip()
    full_name = " ".join(filter(None, [first_name, last_name])).strip()
    if full_name:
        return full_name
    username = (user.get("username") or "").strip()
    if username:
        return username
    return "Friend"


def get_safe_reply_display_name(chat_id, user):
    if not user:
        return "Friend"
    if user.get("username") == "GroupAnonymousBot" or user.get("first_name") == "Group":
        return get_anonymous_fallback_name(chat_id, user.get("id"))
    return get_user_display_name(user)


def build_start_text(display_name):
    safe_name = escape_markdown_text(display_name)
    return (
        f"**Aira ✧ (Updating..)**\n"
        f"✨ Hieeeee *{safe_name}* 🌸\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "💗 **Simple, smart & friendly chat bot**\n\n"
        "**What can I do?**\n"
        "• 💬 Fun & Easy Conversations\n"
        "• 🎮 Awesome Games & Economy\n"
        "• 🛡 Group Management & Safety\n"
        "• ✨ A Safe & Smooth Experience\n\n"
        "✦ **Choose An Option Below :**"
    )


def get_gf_style_patterns():
    patterns = []
    for prefix in GF_STYLE_PREFIXES:
        for ending in GF_STYLE_ENDINGS:
            patterns.append(f"{prefix} {ending}")
            if len(patterns) >= 150:
                return patterns
    return patterns


def sanitize_ai_reply(reply):
    text = (reply or "").strip()
    if not text:
        return text
    text = FORBIDDEN_ADDRESS_RE.sub("", text)
    text = re.sub(r"\s{2,}", " ", text).strip(" ,:-")
    normalized = re.sub(r"[^a-zA-Z\u0900-\u097F]+", "", text.lower())
    if any(variant in normalized for variant in FORBIDDEN_ADDRESS_VARIANTS):
        return "Main yahin hun, aapki help ke liye. ✨"
    lowered = text.lower()
    if lowered in FORBIDDEN_ADDRESS_WORDS or not text:
        return "Main yahin hun, aapki help ke liye. ✨"
    return text


def decorate_brajbhasha_reply(reply):
    clean_reply = sanitize_ai_reply(reply)
    if not clean_reply:
        return "राधे राधे।"
    lowered = clean_reply.lower()
    if any(phrase in lowered for phrase in ("राधे", "radhe", "कृष्ण", "krishna")):
        return clean_reply
    if random.random() < 0.65:
        return f"{random.choice(BRAJBHASHA_GREETING_PREFIXES)}{clean_reply}"
    return f"{clean_reply}{random.choice(BRAJBHASHA_GREETING_SUFFIXES)}"


def handle_new_chat_members(msg):
    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    chat_type = chat.get("type")
    new_members = msg.get("new_chat_members") or []
    if chat_type not in {"group", "supergroup"} or not new_members:
        return False

    handled = False
    for member in new_members:
        if member.get("id") == BOT_ID:
            existing = get_group_audit_entry(chat_id)
            recently_tracked = (
                existing.get("status") == "active"
                and (int(time.time()) - coerce_int(existing.get("added_at"), 0)) < 60
            )
            if not recently_tracked:
                actor = msg.get("from", {}) or {}
                welcome_message = build_bot_added_message(
                    str(chat.get("title") or chat.get("first_name") or chat_id),
                    get_actor_display_name(actor),
                )
                record_bot_added_event(chat, actor, welcome_message=welcome_message)
                send_message(chat_id, welcome_message)
            continue
        display_name = get_user_display_name(member) or "Friend"
        send_message(
            chat_id,
            build_member_welcome_message(display_name, str(chat.get("title") or chat_id)),
        )
        handled = True
    return handled


def process_my_chat_member(update):
    chat = update.get("chat", {})
    chat_id = chat.get("id")
    chat_type = chat.get("type")
    if chat_id is None or chat_type not in {"group", "supergroup"}:
        return

    old_status = str((update.get("old_chat_member") or {}).get("status") or "").lower()
    new_status = str((update.get("new_chat_member") or {}).get("status") or "").lower()
    actor = update.get("from", {}) or {}

    if old_status in {"left", "kicked"} and new_status in {"member", "administrator"}:
        welcome_message = build_bot_added_message(
            str(chat.get("title") or chat.get("first_name") or chat_id),
            get_actor_display_name(actor),
        )
        record_bot_added_event(chat, actor, welcome_message=welcome_message)
        snapshot = sync_admin_state(chat_id, force=True)
        if snapshot:
            update_group_audit_from_snapshot(snapshot)
        send_message(chat_id, welcome_message)
        return

    if old_status == "member" and new_status == "administrator":
        record_bot_promoted_event(chat, actor)
        snapshot = sync_admin_state(chat_id, force=True)
        if snapshot:
            update_group_audit_from_snapshot(snapshot)
        send_message(
            chat_id,
            build_bot_promoted_message(
                str(chat.get("title") or chat.get("first_name") or chat_id),
                get_actor_display_name(actor),
            ),
        )
        return

    if new_status in {"left", "kicked"} and old_status not in {"left", "kicked"}:
        snapshot = get_group_snapshot(chat_id, force=False)
        if snapshot:
            update_group_audit_from_snapshot(snapshot)
        record_bot_removed_event(chat, actor)
        return

    if new_status in {"member", "administrator"}:
        snapshot = sync_admin_state(chat_id, force=True)
        if snapshot:
            update_group_audit_from_snapshot(snapshot)


def translate_text_with_google(text, lang_code):
    target = GOOGLE_TRANSLATE_LANGUAGE_CODES.get(lang_code)
    clean_text = (text or "").strip()
    if not target or not clean_text:
        return clean_text
    try:
        response = HTTP.get(
            "https://translate.googleapis.com/translate_a/single",
            params={
                "client": "gtx",
                "sl": "auto",
                "tl": target,
                "dt": "t",
                "q": clean_text,
            },
            timeout=15,
        )
        data = response.json()
        translated = "".join(part[0] for part in data[0] if part and part[0])
        return translated.strip() or clean_text
    except Exception:
        return clean_text


def translate_to_brajbhasha(text):

    payload = {
        "action": "do_translation",
        "translator_nonce": BRAJBHASHA_TRANSLATOR_NONCE,
        "post_id": BRAJBHASHA_TRANSLATOR_POST_ID,
        "to_translate": text,
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "X-Requested-With": "XMLHttpRequest",
    }

    for _ in range(BRAJBHASHA_TRANSLATOR_RETRIES):

        try:
            r = HTTP.post(
                BRAJBHASHA_TRANSLATOR_URL,
                data=payload,
                headers=headers,
                timeout=15
            )

            data = r.json()

            if data.get("success") and data.get("data"):
                return data["data"].strip()

        except Exception as e:
            print("Braj API error:", e)

    return ""

#.........
def finalize_language_reply(reply, lang_code):

    clean_reply = sanitize_ai_reply(reply)

    if lang_code == "brajbhasha":
    # ensure English before Braj API

        english_text = translate_text_with_google(clean_reply, "english")
        braj = translate_to_brajbhasha(english_text)

        print("AI RAW:", clean_reply)
        print("FORCED EN:", english_text)
        print("Braj:", braj)

        if braj:
            # अगर Braj result English है तो reject
            if re.search(r"[A-Za-z]{4,}", braj):
                print("⚠ Braj API returned English, ignoring")

            else:
                return decorate_brajbhasha_reply(braj)
        return decorate_brajbhasha_reply(clean_reply)


    if lang_code == "hinglish":
        return clean_reply

    translated_reply = translate_text_with_google(clean_reply, lang_code)

    if translated_reply and translated_reply.strip():
        return sanitize_ai_reply(translated_reply)

    return clean_reply


def translate_to_hindi(text):
    clean_text = (text or "").strip()
    if not clean_text:
        return clean_text
    has_devanagari = bool(re.search(r"[\u0900-\u097F]", clean_text))
    has_latin = bool(re.search(r"[A-Za-z]", clean_text))
    if has_latin and not has_devanagari:
        try:
            response = HTTP.get(
                "https://inputtools.google.com/request",
                params={
                    "text": clean_text,
                    "itc": "hi-t-i0-und",
                    "num": 1,
                },
                timeout=15,
            )
            data = response.json()
            if data and data[0] == "SUCCESS":
                candidates = data[1][0][1]
                if candidates:
                    return candidates[0].strip()
        except Exception:
            pass
    translated = translate_text_with_google(clean_text, "hindi")
    return translated.strip() or clean_text


def format_direct_call_reply(chat_id, user, reply):
    display_name = get_safe_reply_display_name(chat_id, user)
    if not display_name or display_name == "User":
        return sanitize_ai_reply(reply)
    return f"{escape_markdown_text(display_name)} 😊\n{sanitize_ai_reply(reply)}"


# --- PERMISSION / GROUP SNAPSHOT ---

def get_chat_info(chat_id):
    try:
        data = telegram_api_json("GET", "getChat", params={"chat_id": chat_id}, timeout=10)
        if data.get("ok"):
            return data.get("result", {})
    except Exception as e:
        print(f"Chat info error: {e}")
    return {}


def get_chat_member_count(chat_id):
    try:
        data = telegram_api_json("GET", "getChatMemberCount", params={"chat_id": chat_id}, timeout=10)
        if data.get("ok"):
            return data.get("result", 0)
    except Exception as e:
        print(f"Member count error: {e}")
    return 0


def get_admin_members(chat_id):
    try:
        data = telegram_api_json("GET", "getChatAdministrators", params={"chat_id": chat_id}, timeout=10)
        if data.get("ok"):
            return data.get("result", [])
    except Exception as e:
        print(f"Admin member error: {e}")
    return []


def get_user_display_name(user):
    return " ".join(filter(None, [user.get("first_name", ""), user.get("last_name", "")])).strip() or user.get("username", "User")


def get_styled_known_owner_name(display_name, user_id=None):
    if user_id is not None and int(user_id) == OWNER_ID:
        return BOT_OWNER_DISPLAY_NAME
    if (display_name or "").strip().lower() == BOT_OWNER_NAME.lower():
        return BOT_OWNER_DISPLAY_NAME
    return display_name or "User"


def sync_admin_state(chat_id, force=False):
    now = time.time()
    cached = ADMIN_CACHE.get(chat_id)
    if cached and not force and now - cached["ts"] < ADMIN_CACHE_TTL_SECONDS:
        return apply_owner_override_to_snapshot(chat_id, cached["data"])

    previous_audit = get_group_audit_entry(chat_id)
    admins = get_admin_members(chat_id)
    if not admins:
        return apply_owner_override_to_snapshot(chat_id, cached["data"]) if cached else None

    owner_id = None
    owner_name = "Owner"
    admin_ids = []
    admin_names = []

    for member in admins:
        user = member.get("user", {})
        user_id = user.get("id")
        if user_id is None:
            continue
        admin_ids.append(int(user_id))
        display_name = get_styled_known_owner_name(get_user_display_name(user), user_id)
        if member.get("status") == "creator":
            owner_id = int(user_id)
            owner_name = display_name
        else:
            admin_names.append(display_name)

    chat_info = get_chat_info(chat_id)
    snapshot = {
        "chat_id": chat_id,
        "title": chat_info.get("title") or chat_info.get("first_name") or str(chat_id),
        "owner_id": owner_id,
        "owner": owner_name,
        "admin_ids": sorted(admin_ids),
        "admins": admin_names,
        "members": get_chat_member_count(chat_id),
        "updated_at": int(now),
    }
    ADMIN_CACHE[chat_id] = {"ts": now, "data": snapshot}

    groups = normalize_group_store(load_json_file(GROUPS_FILE, {}))
    groups[str(chat_id)] = snapshot
    save_json_file(GROUPS_FILE, groups)

    title_store = normalize_title_store(load_json_file(ADMIN_TITLES_FILE, {}))
    chat_titles = title_store.get(str(chat_id), {})
    filtered_titles = {uid: title for uid, title in chat_titles.items() if int(uid) in admin_ids and int(uid) != OWNER_ID}
    if filtered_titles != chat_titles:
        title_store[str(chat_id)] = filtered_titles
        save_json_file(ADMIN_TITLES_FILE, title_store)

    item_store = normalize_items_store(load_json_file(ITEMS_FILE, {}))
    chat_items = item_store.get(str(chat_id), {})
    filtered_items = {uid: row for uid, row in chat_items.items() if int(uid) in admin_ids}
    if filtered_items != chat_items:
        item_store[str(chat_id)] = filtered_items
        save_json_file(ITEMS_FILE, item_store)

    effective_snapshot = apply_owner_override_to_snapshot(chat_id, snapshot)
    previous_owner_id = coerce_int(previous_audit.get("owner_id"), None)
    current_owner_id = coerce_int(effective_snapshot.get("owner_id"), None)
    owner_changed = (
        previous_audit
        and previous_audit.get("status") == "active"
        and previous_owner_id is not None
        and current_owner_id is not None
        and previous_owner_id != current_owner_id
    )
    previous_owner_name = str(previous_audit.get("owner") or "Owner")
    update_group_audit_from_snapshot(effective_snapshot)
    if owner_changed:
        send_message(
            chat_id,
            build_owner_changed_message(
                str(effective_snapshot.get("title") or chat_id),
                previous_owner_name,
                str(effective_snapshot.get("owner") or "Owner"),
            ),
        )
    return effective_snapshot


def get_group_snapshot(chat_id, force=False):
    snapshot = sync_admin_state(chat_id, force=force)
    if snapshot:
        return snapshot
    groups = normalize_group_store(load_json_file(GROUPS_FILE, {}))
    return apply_owner_override_to_snapshot(chat_id, groups.get(str(chat_id), {}))


def is_owner(chat_id, user_id):
    if user_id in (None, 0):
        return False
    if int(user_id) == OWNER_ID:
        return True
    snapshot = get_group_snapshot(chat_id)
    return int(user_id) == int(snapshot.get("owner_id") or -1)


def is_admin(chat_id, user_id):
    if user_id in (None, 0):
        return False

    if int(user_id) == OWNER_ID:
        return True

    # use cached snapshot first
    cached = ADMIN_CACHE.get(chat_id)
    if cached:
        snapshot = cached["data"]
        return int(user_id) in snapshot.get("admin_ids", [])

    # fallback to sync
    snapshot = sync_admin_state(chat_id)
    if not snapshot:
        return False

    return int(user_id) in snapshot.get("admin_ids", [])


def has_admin_access(chat_id, user_id):
    if is_owner(chat_id, user_id) or is_admin(chat_id, user_id):
        return True
    snapshot = get_group_snapshot(chat_id, force=True)
    return int(user_id or 0) in {int(x) for x in snapshot.get("admin_ids", [])}


def is_anonymous_admin_message(msg):
    chat = msg.get("chat", {})
    sender_chat = msg.get("sender_chat", {})
    if chat.get("type") not in {"group", "supergroup"}:
        return False
    if not sender_chat:
        return False
    return sender_chat.get("id") == chat.get("id")


def is_protected_sender(chat_id, user_id):
    return has_admin_access(chat_id, user_id)


def get_owner_display_name(chat_id):
    return BOT_OWNER_DISPLAY_NAME


def get_owner_display_line(chat_id):
    return BOT_OWNER_DISPLAY_LINE


def get_admin_contact_list(chat_id):
    handles = []
    for member in get_admin_members(chat_id):
        if member.get("status") == "creator":
            continue
        username = member.get("user", {}).get("username")
        if username:
            handles.append(f"@{username}")
    return handles


def get_live_admin_help_text(chat_id):
    members = get_admin_members(chat_id)
    if not members:
        return ""

    owner_line = ""
    admin_lines = []

    for member in members:
        user = member.get("user", {})
        user_id = user.get("id")

        # OWNER → only name
        if member.get("status") == "creator":
            display_name = get_styled_known_owner_name(get_user_display_name(user), user_id)
            if display_name == BOT_OWNER_DISPLAY_NAME:
                label = display_name
            else:
                label = escape_markdown_text(display_name)
            owner_line = f"**Present Owner:**\n{label}"

        else:
            # ADMINS → clickable link
            label = format_user_link_markdown(user)

            custom_title = get_admin_title(chat_id, user_id)
            if custom_title:
                label = f"{label} \\- {escape_markdown_text(custom_title)}"

            admin_lines.append(label)

    lines = []

    if owner_line:
        lines.append(owner_line)

    if admin_lines:
        lines.append("**Present Admins:**")
        for idx, admin_label in enumerate(admin_lines, start=1):
            lines.append(f"{idx}\\. {admin_label}")

    return "\n".join(lines)


def get_group_summary_text(chat_id):
    snapshot = get_group_snapshot(chat_id, force=True)
    if not snapshot:
        return "Group info not available."
    admins = ", ".join(snapshot.get("admins", [])) or "No admins found"
    return (
        f"Group: {snapshot.get('title', chat_id)}\n"
        f"Group ID: `{snapshot.get('chat_id', chat_id)}`\n"
        f"Owner: {snapshot.get('owner', 'Owner')}\n"
        f"Admins: {admins}\n"
        f"Members: {snapshot.get('members', 0)}"
    )


def get_all_groups_summary():
    groups = normalize_group_store(load_json_file(GROUPS_FILE, {}))
    if not groups:
        return "No groups saved yet."
    lines = []
    for raw_info in groups.values():
        info = apply_owner_override_to_snapshot(raw_info.get("chat_id"), raw_info)
        lines.append(
            f"{info.get('title', 'Group')}\n"
            f"ID: `{info.get('chat_id')}`\n"
            f"Owner: {info.get('owner', 'Owner')}\n"
            f"Admins: {', '.join(info.get('admins', [])) or 'No admins'}\n"
            f"Members: {info.get('members', 0)}"
        )
    return "\n\n".join(lines)


# --- LANGUAGE ---

def set_group_language(chat_id, lang_code):
    user_data = load_user_data(chat_id)
    user_data["lang"] = lang_code
    user_data["lang_set_at"] = int(time.time())
    save_user_data(chat_id, user_data)


def set_user_language_override(chat_id, user_id, lang_code):
    user_data = load_user_data(chat_id)
    overrides = user_data.get("user_lang_overrides", {})
    overrides[str(user_id)] = {"lang": lang_code, "set_at": int(time.time())}
    user_data["user_lang_overrides"] = overrides
    save_user_data(chat_id, user_data)


def get_active_language(chat_id, user_id=None):
    user_data = load_user_data(chat_id)
    now = time.time()
    changed = False

    current_lang = user_data.get("lang", DEFAULT_LANGUAGE)
    set_at = user_data.get("lang_set_at", 0)
    if current_lang != DEFAULT_LANGUAGE and set_at and (now - set_at) >= GROUP_LANGUAGE_SECONDS:
        user_data["lang"] = DEFAULT_LANGUAGE
        user_data["lang_set_at"] = 0
        current_lang = DEFAULT_LANGUAGE
        changed = True

    if user_id is not None:
        overrides = user_data.get("user_lang_overrides", {})
        override = overrides.get(str(user_id))
        if override:
            if now - int(override.get("set_at", 0)) < USER_LANGUAGE_SECONDS:
                if changed:
                    save_user_data(chat_id, user_data)
                return override.get("lang", DEFAULT_LANGUAGE)
            overrides.pop(str(user_id), None)
            user_data["user_lang_overrides"] = overrides
            changed = True

    if changed:
        save_user_data(chat_id, user_data)
    return current_lang


# --- MODERATION / TRACKING ---

def normalize_policy_text(text):
    lowered = text.lower().translate(str.maketrans({
        "@": "a", "$": "s", "0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t",
    }))
    spaced = re.sub(r"[^a-zA-Z0-9\s]", " ", lowered)
    spaced = re.sub(r"\s+", " ", spaced).strip()
    compact = spaced.replace(" ", "")
    tokens = spaced.split() if spaced else []
    return compact, tokens


def contains_policy_words(text, words):
    compact, tokens = normalize_policy_text(text)
    for word in words:
        if len(word) <= 3:
            if word in tokens or compact == word:
                return True
        elif word in compact or word in tokens:
            return True
    return False


def contains_link(msg):
    text = (msg.get("text") or "") + " " + (msg.get("caption") or "")
    if LINK_RE.search(text):
        return True
    entities = msg.get("entities", []) + msg.get("caption_entities", [])
    return any(e.get("type") in {"url", "text_link"} for e in entities)


def contains_blocked_media(msg):
    return any(key in msg for key in ("photo", "audio", "voice", "video", "video_note", "animation", "document"))


def media_warning_text(name, msg):
    if "audio" in msg or "voice" in msg or "document" in msg:
        return f"{name}, file removed due to copyright policy."
    return f"{name}, image/video is not allowed here."


def add_temp_block_user(chat_id, user_id, seconds=TEMP_BLOCK_SECONDS):
    user_data = load_user_data(chat_id)
    blocked = user_data.get("temp_blocked_users", {})
    blocked[str(user_id)] = int(time.time()) + seconds
    user_data["temp_blocked_users"] = blocked
    save_user_data(chat_id, user_data)


def remove_temp_block_user(chat_id, user_id):
    user_data = load_user_data(chat_id)
    blocked = user_data.get("temp_blocked_users", {})
    if str(user_id) in blocked:
        blocked.pop(str(user_id), None)
        user_data["temp_blocked_users"] = blocked
        save_user_data(chat_id, user_data)
        return True
    return False


def is_temp_blocked(chat_id, user_id):
    user_data = load_user_data(chat_id)
    blocked = user_data.get("temp_blocked_users", {})
    expiry = blocked.get(str(user_id))
    if not expiry:
        return False
    if time.time() >= expiry:
        blocked.pop(str(user_id), None)
        user_data["temp_blocked_users"] = blocked
        save_user_data(chat_id, user_data)
        USER_VIOLATIONS.pop((chat_id, user_id), None)
        return False
    return True


def enforce_policy_text_value(chat_id, user, message_id, text):
    user_id = user.get("id")
    policy_text = (text or "").strip()
    if not policy_text:
        if DEBUG_POLICY_LOGS:
            print(f"[policy] skip empty chat={chat_id} user={user_id} text={policy_text!r}", flush=True)
        return False
    if user_id in (None, 0):
        if DEBUG_POLICY_LOGS:
            print(f"[policy] skip no-user chat={chat_id} user={user_id} text={policy_text!r}", flush=True)
        return False
    if int(user_id) == BOT_ID:
        if DEBUG_POLICY_LOGS:
            print(f"[policy] skip self-bot chat={chat_id} user={user_id} text={policy_text!r}", flush=True)
        return False
    if has_admin_access(chat_id, user_id):
        if DEBUG_POLICY_LOGS:
            print(f"[policy] skip admin chat={chat_id} user={user_id} text={policy_text!r}", flush=True)
        return False
    bad_match = contains_policy_words(policy_text, BAD_WORDS)
    sexual_match = contains_policy_words(policy_text, SEXUAL_WORDS)
    if not (bad_match or sexual_match):
        if DEBUG_POLICY_LOGS:
            print(f"[policy] no-match chat={chat_id} user={user_id} text={policy_text!r}", flush=True)
        return False
    if DEBUG_POLICY_LOGS:
        print(f"[policy] match chat={chat_id} user={user_id} bad={bad_match} sexual={sexual_match} text={policy_text!r}", flush=True)

    key = (chat_id, user_id)
    USER_VIOLATIONS[key] = USER_VIOLATIONS.get(key, 0) + 1
    delete_message(chat_id, message_id)
    name = user.get("first_name", "User")

    if USER_VIOLATIONS[key] >= 4:
        add_temp_block_user(chat_id, user_id)
        USER_VIOLATIONS.pop(key, None)
        send_temporary_message(chat_id, f"{name} has been blocked by AI due to policy violation.")
        send_temporary_message(chat_id, f"/owner call repeated policy violation by {name}")
    else:
        send_temporary_message(chat_id, f"{name}, due to policy this message is not allowed here.")
    return True


def enforce_policy_text(msg):
    chat = msg.get("chat", {})
    user = msg.get("from", {})
    text = ((msg.get("text") or "") + " " + (msg.get("caption") or "")).strip()
    return enforce_policy_text_value(chat.get("id"), user, msg.get("message_id"), text)


def moderate_group_message(msg):
    chat = msg.get("chat", {})
    user = msg.get("from", {})
    user_id = user.get("id")
    if chat.get("type") not in {"group", "supergroup"} or not user_id:
        return False
    if int(user_id) == BOT_ID:
        return False
    if has_admin_access(chat["id"], user_id):
        return False
    if is_temp_blocked(chat["id"], user_id):
        delete_message(chat["id"], msg["message_id"])
        return True
    if contains_link(msg):
        if delete_message(chat["id"], msg["message_id"]):
            send_temporary_message(chat["id"], f"{user.get('first_name', 'User')}, links are not allowed here.")
        return True
    if contains_blocked_media(msg):
        if delete_message(chat["id"], msg["message_id"]):
            send_temporary_message(chat["id"], media_warning_text(user.get("first_name", "User"), msg))
        return True
    return False


# --- MUTE / ITEMS / TITLES / SPAM ---

def parse_duration_to_seconds(raw_value):
    match = re.fullmatch(r"(\d+)([mhd])", (raw_value or "").strip().lower())
    if not match:
        return None
    amount = int(match.group(1))
    unit = match.group(2)
    return amount * {"m": 60, "h": 3600, "d": 86400}[unit]


def get_command_argument(text):
    parts = (text or "").strip().split(maxsplit=1)
    return parts[1].strip() if len(parts) > 1 else ""


def get_mute_store():
    return normalize_mute_store(load_json_file(MUTE_STATE_FILE, {"groups": {}, "users": {}}))


def save_mute_store(data):
    save_json_file(MUTE_STATE_FILE, data)


def set_group_mute(chat_id, seconds):
    store = get_mute_store()
    store["groups"][str(chat_id)] = int(time.time()) + seconds
    save_mute_store(store)


def clear_group_mute(chat_id):
    store = get_mute_store()
    store.get("groups", {}).pop(str(chat_id), None)
    save_mute_store(store)


def is_group_muted(chat_id):
    store = get_mute_store()
    expiry = store.get("groups", {}).get(str(chat_id))
    if not expiry:
        return False
    if time.time() >= expiry:
        store["groups"].pop(str(chat_id), None)
        save_mute_store(store)
        return False
    return True


def set_user_mute(chat_id, user_id, seconds):
    store = get_mute_store()
    store["users"].setdefault(str(chat_id), {})[str(user_id)] = int(time.time()) + seconds
    save_mute_store(store)


def clear_user_mute(chat_id, user_id):
    store = get_mute_store()
    chat_users = store.get("users", {}).get(str(chat_id), {})
    if str(user_id) in chat_users:
        chat_users.pop(str(user_id), None)
        save_mute_store(store)
        return True
    return False


def is_user_muted(chat_id, user_id):
    store = get_mute_store()
    chat_users = store.get("users", {}).get(str(chat_id), {})
    expiry = chat_users.get(str(user_id))
    if not expiry:
        return False
    if time.time() >= expiry:
        chat_users.pop(str(user_id), None)
        save_mute_store(store)
        return False
    return True


def track_item_stats(chat_id, user, msg):
    user_id = user.get("id")
    if not has_admin_access(chat_id, user_id):
        return
    item_store = normalize_items_store(load_json_file(ITEMS_FILE, {}))
    chat_stats = item_store.setdefault(str(chat_id), {})
    display_name = get_styled_known_owner_name(get_user_display_name(user), user_id)
    row = chat_stats.setdefault(str(user_id), {"name": display_name, "images": 0, "videos": 0, "files": 0, "texts": 0})
    row["name"] = display_name
    if msg.get("photo"):
        row["images"] += 1
    elif msg.get("video") or msg.get("video_note") or msg.get("animation"):
        row["videos"] += 1
    elif msg.get("document") or msg.get("audio") or msg.get("voice"):
        row["files"] += 1
    elif msg.get("text"):
        row["texts"] += 1
    save_json_file(ITEMS_FILE, item_store)


def get_items_summary(chat_id):
    chat_stats = normalize_items_store(load_json_file(ITEMS_FILE, {})).get(str(chat_id), {})
    if not chat_stats:
        return "No item stats found."
    lines = []
    for row in chat_stats.values():
        lines.append(
            f"{row.get('name', 'Admin')}\n"
            f"Images: {row.get('images', 0)}\n"
            f"Videos: {row.get('videos', 0)}\n"
            f"Files: {row.get('files', 0)}\n"
            f"Texts: {row.get('texts', 0)}"
        )
    return "\n\n".join(lines)


def set_admin_title(chat_id, user_id, title):
    store = normalize_title_store(load_json_file(ADMIN_TITLES_FILE, {}))
    store.setdefault(str(chat_id), {})[str(user_id)] = title
    save_json_file(ADMIN_TITLES_FILE, store)
    print(f"[title-debug] saved chat={chat_id} user={user_id} title={title!r}", flush=True)


def get_admin_title(chat_id, user_id):
    store = normalize_title_store(load_json_file(ADMIN_TITLES_FILE, {}))
    return store.get(str(chat_id), {}).get(str(user_id))


def check_command_spam(chat_id, user_id, command):
    if not user_id or not command or has_admin_access(chat_id, user_id):
        return False
    now = int(time.time())
    store = normalize_command_spam_store(load_json_file(COMMAND_SPAM_FILE, {}), now=now)
    key = f"{chat_id}:{user_id}:{command}"
    row = store.get(key, {"count": 0, "start": now})
    if now - row.get("start", now) > COMMAND_SPAM_WINDOW_SECONDS:
        row = {"count": 0, "start": now}
    row["count"] += 1
    store[key] = row
    save_json_file(COMMAND_SPAM_FILE, store)
    if row["count"] >= COMMAND_SPAM_LIMIT:
        add_temp_block_user(chat_id, user_id, COMMAND_SPAM_BLOCK_SECONDS)
        store.pop(key, None)
        save_json_file(COMMAND_SPAM_FILE, store)
        return True
    return False


def get_stats_text():
    groups = normalize_group_store(load_json_file(GROUPS_FILE, {}))
    items = normalize_items_store(load_json_file(ITEMS_FILE, {}))
    total_item_count = 0
    for chat_stats in items.values():
        for row in chat_stats.values():
            total_item_count += row.get("images", 0) + row.get("videos", 0) + row.get("files", 0) + row.get("texts", 0)
    return (
        f"Saved Groups: {len(groups)}\n"
        f"Tracked Item Entries: {total_item_count}\n"
        f"Tracked User History Files: {len(os.listdir(HISTORY_DIR))}"
    )


def get_show_commands_text():
    return (
        "Main Features:\n"
        "/start /help /about_ai /lan /reset /show\n"
        "/block /unblock /mute /unmute /ban /pin /unpin\n"
        "/title /setowne /translate /purge /sdelete\n"
        "/items /group /stats /update /broadcast /full_clear /restart /delete\n\n"
        "Interaction Command Pack:\n"
        f"{get_interaction_commands_text()}\n\n"
        "Usage Examples:\n"
        "Reply + /hug\n"
        "/goodnight\n"
        "Reply + /propose\n"
        "Reply + /setowne\n"
        "/setowne reset\n"
        "/allgroup  (owner-only)\n"
        "/reset all\n"
        "/purge 50\n"
        "Reply + /translate\n\n"
        "Tip:\n"
        "Aira ke interaction output par reply karke baat karoge to bot same vibe pakad legi.\n\n"
        "Telegram Note:\n"
        "Default slash menu me full interaction pack dikhega. Extra owner/admin commands private owner chat menu me visible rahenge."
    )










# --- OWNER PROTECTION ---

def contains_owner_mention(text):
    if not text:
        return False

    t = text.lower()

    if BOT_OWNER_NAME.lower() in t:
        return True

    for name in OWNER_PROTECTED_NAMES:
        if name in t:
            return True

    return False






# --- AI ---

def is_name_question(text):
    return bool(NAME_QUESTION_RE.search(" ".join((text or "").lower().split())))


def is_simple_greeting(text):
    return " ".join((text or "").lower().split()) in SIMPLE_GREETINGS


def build_system_instruction(lang_code):
    lang_label = LANGUAGES.get(lang_code, LANGUAGES[DEFAULT_LANGUAGE])
    lang_rule = LANGUAGE_RULES.get(lang_code, LANGUAGE_RULES[DEFAULT_LANGUAGE])
    if lang_code == "brajbhasha":
        lang_rule = "Reply ONLY in simple English. Do NOT use Hindi or Brajbhasha."
    style_examples = " | ".join(get_gf_style_patterns()[:12])
    translation_hint = (
        "Draft your answer in simple natural English first..."
        if lang_code not in {"hinglish", "english"} else ""
    )
    return (
        "You are Aira. Behave like a sweet AI girl with close-friend plus gentle girlfriend energy, while staying safe and respectful. "
        "Be friendly, supportive, natural, caring, emotionally warm, and use light emoji naturally. "
        "Your tone should feel like a close AI friend or gentle digital companion, not a family elder. "
        "Never address the user as beta, beti, bhai, behen, baccha, son, daughter, child, brother, or sister. "
        "Do not use parent-like or teacher-like wording. "
        "You may sound caring, sweet, emotionally close, and a little flirty-safe, but stay respectful and non-explicit. "
        "Do not be sexual. In groups stay respectful, casual, and friendly. "
        "If the user directly calls you as Aira, reply in a warmer personal tone. "
        "If the user directly asks your name or identity, answer that your name is Aira and do not give any other name. "
        f"Style examples: {style_examples}. "
        f"{translation_hint}"
        f"Selected reply language: {lang_label}. {lang_rule} "
        "Even if the user writes in another language, reply only in the selected reply language."
    )


def build_user_prompt(user_id, lang_code, prompt_text):
    return (
        f"User ID: {user_id}\n"
        f"Selected language: {LANGUAGES.get(lang_code, LANGUAGES[DEFAULT_LANGUAGE])}\n"
        f"Hard rule: reply only in that selected language.\n"
        f"Message: {prompt_text}"
    )


def extract_latest_user_question(prompt_text):
    text = (prompt_text or "").strip()
    marker = "User reply:\n"
    if marker in text:
        return text.split(marker, 1)[1].strip()
    return text


def get_static_reply(prompt_text, lang_code):
    latest_question = extract_latest_user_question(prompt_text)
    text = " ".join(latest_question.lower().split())

    if DEVELOPER_QUESTION_RE.search(text):
        replies = {
            "hindi": f"Mujhe {BOT_DEVELOPER_DISPLAY_NAME} ne banaya hai.",
            "english": f"I was created by {BOT_DEVELOPER_DISPLAY_NAME}.",
            "hinglish": f"Mujhe {BOT_DEVELOPER_DISPLAY_NAME} ne banaya hai.",
            "sanskrit": f"मां {BOT_DEVELOPER_DISPLAY_NAME} द्वारा निर्मिता अस्मि।",
            "russian": f"Меня создал {BOT_DEVELOPER_DISPLAY_NAME}.",
            "brajbhasha": f"मौका {BOT_DEVELOPER_DISPLAY_NAME} ने बनायो है।",
            "telugu": f"నన్ను {BOT_DEVELOPER_DISPLAY_NAME} రూపొందించారు.",
            "tamil": f"என்னை {BOT_DEVELOPER_DISPLAY_NAME} உருவாக்கினார்.",
            "gujarati": f"મને {BOT_DEVELOPER_DISPLAY_NAME} એ બનાવ્યો છે.",
            "marathi": f"मला {BOT_DEVELOPER_DISPLAY_NAME} यांनी तयार केले आहे.",
        }
        return finalize_language_reply(replies.get(lang_code, f"Mujhe {BOT_DEVELOPER_DISPLAY_NAME} ne banaya hai."), lang_code)

    if CREATED_WHEN_QUESTION_RE.search(text):
        replies = {
            "hindi": f"Mere paas exact creation date saved nahi hai, lekin mujhe {BOT_DEVELOPER_DISPLAY_NAME} ne develop kiya hai.",
            "english": f"I do not have an exact stored creation date, but I was developed by {BOT_DEVELOPER_DISPLAY_NAME}.",
            "hinglish": f"Mere paas exact creation date saved nahi hai, lekin mujhe {BOT_DEVELOPER_DISPLAY_NAME} ne develop kiya hai.",
            "brajbhasha": f"मौका ठीक बनायो गयो दिन संग्रहीत नाहीं, पर मौका {BOT_DEVELOPER_DISPLAY_NAME} ने बनायो है।",
        }
        return finalize_language_reply(replies.get(lang_code, f"Mere paas exact creation date saved nahi hai, lekin mujhe {BOT_DEVELOPER_DISPLAY_NAME} ne develop kiya hai."), lang_code)

    if OWNER_QUESTION_RE.search(text):
        replies = {
            "hindi": f"{BOT_OWNER_DISPLAY_LINE}\nGroup ka current owner live group data se dekha jata hai.",
            "english": f"{BOT_OWNER_DISPLAY_LINE}\nThe group owner still comes from live group data.",
            "hinglish": f"{BOT_OWNER_DISPLAY_LINE}\nGroup ka current owner live group data se aata hai.",
            "brajbhasha": f"{BOT_OWNER_DISPLAY_LINE}\nGroup को current owner live group data सों आवै है।",
        }
        return finalize_language_reply(replies.get(lang_code, BOT_OWNER_DISPLAY_LINE), lang_code)

    if ADMIN_QUESTION_RE.search(text):
        replies = {
            "hindi": "Current admins ke naam group ke live data se dekhe jaate hain.",
            "english": "The current admin names are taken from the live group data.",
            "hinglish": "Current admins ke naam group ke live data se dekhe jaate hain.",
            "brajbhasha": "वर्तमान admins के नाम live group data सों देखि जात हैं।",
        }
        return finalize_language_reply(replies.get(lang_code, "Current admins ke naam group ke live data se dekhe jaate hain."), lang_code)

    if LANGUAGE_BUILT_QUESTION_RE.search(text):
        replies = {
            "hindi": "Mera bot system Python me bana hai.",
            "english": "My bot system is built in Python.",
            "hinglish": "Mera bot system Python me bana hai.",
            "sanskrit": "मम bot system Python भाषायां निर्मितम् अस्ति।",
            "russian": "Моя система бота создана на Python.",
            "brajbhasha": "मोरो bot system Python मैं बनायो गयो है।",
            "telugu": "నా బాట్ సిస్టమ్ Python లో నిర్మించబడింది.",
            "tamil": "என் bot system Python-ல் உருவாக்கப்பட்டுள்ளது.",
            "gujarati": "મારું bot system Python માં બનાવાયું છે.",
            "marathi": "माझी bot system Python मध्ये तयार केली आहे.",
        }
        return finalize_language_reply(replies.get(lang_code, "Mera bot system Python me bana hai."), lang_code)

    return None


def get_nvidia_api_attempt_order():
    with NVIDIA_API_KEY_LOCK:
        start_index = NVIDIA_API_KEY_INDEX
    return [(start_index + offset) % len(NVIDIA_API_KEYS) for offset in range(len(NVIDIA_API_KEYS))]


def set_active_nvidia_api_key(index):
    global NVIDIA_API_KEY_INDEX
    with NVIDIA_API_KEY_LOCK:
        NVIDIA_API_KEY_INDEX = index % len(NVIDIA_API_KEYS)


def request_nvidia_reply(payload):
    attempt_order = get_nvidia_api_attempt_order()
    errors = []

    for key_index in attempt_order:
        headers = {
            "Authorization": f"Bearer {NVIDIA_API_KEYS[key_index]}",
            "Content-Type": "application/json",
        }
        try:
            response = HTTP.post(NVIDIA_API_URL, json=payload, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
            if response.status_code != 200:
                errors.append(f"key {key_index + 1}: HTTP {response.status_code}")
                print(f"NVIDIA fallback error on key {key_index + 1}: HTTP {response.status_code}", flush=True)
                continue

            data = response.json()
            ai_reply = data["choices"][0]["message"]["content"].strip()
            if key_index != attempt_order[0]:
                print(f"NVIDIA fallback switched to key {key_index + 1}.", flush=True)
            set_active_nvidia_api_key(key_index)
            return ai_reply, None
        except Exception as e:
            errors.append(f"key {key_index + 1}: {e}")
            print(f"NVIDIA fallback exception on key {key_index + 1}: {e}", flush=True)

    return None, " | ".join(errors)


def ask_ai(chat_id, user_id, prompt_text):
    user_data = load_user_data(chat_id)
    lang_code = get_active_language(chat_id, user_id)
    latest_question = extract_latest_user_question(prompt_text)

    if is_name_question(latest_question):
        return finalize_language_reply(NAME_REPLIES.get(lang_code, "My name is Aira."), lang_code)
    #if lang_code == "brajbhasha" and is_simple_greeting(latest_question):
        #return finalize_language_reply("जय श्री राधे राधे। कैसो हाल है?", lang_code)
    static_reply = get_static_reply(prompt_text, lang_code)
    if static_reply:
        return static_reply

    history = user_data.get("history", [])[-16:]
    messages = [{"role": "system", "content": build_system_instruction(lang_code)}]
    for item in history:
        role = item.get("role")
        text = item.get("text", "").strip()
        if role in {"user", "assistant"} and text:
            messages.append({"role": role, "content": text})
    messages.append({"role": "user", "content": build_user_prompt(user_id, lang_code, prompt_text)})

    payload = {"model": NVIDIA_MODEL, "messages": messages, "temperature": 0.5, "stream": False}

    ai_reply, error_details = request_nvidia_reply(payload)
    if not ai_reply:
        if error_details:
            print(f"NVIDIA fallback failed on all keys: {error_details}", flush=True)
        return "⚠️ All NVIDIA APIs are busy or failed. Please try again."
    reply = finalize_language_reply(ai_reply, lang_code)

    history.append({"role": "user", "text": prompt_text})
    history.append({"role": "assistant", "text": reply})
    user_data["history"] = history[-30:]
    save_user_data(chat_id, user_data)
    return reply


def detect_reaction_for_text(text):
    normalized = " ".join((text or "").lower().split())
    for emoji, keywords in REACTION_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return emoji
    return None


def extract_command(msg):
    text = (msg.get("text") or "").strip()
    if not text.startswith("/"):
        return None
    first = text.split()[0].lower()
    if "@" in first:
        base, username = first.split("@", 1)
        if username != BOT_USERNAME:
            return None
        return base
    return first


def extract_bot_prompt(text):
    raw = (text or "").strip()
    lowered = raw.lower()
    if BOT_NAME not in lowered:
        return None
    prompt = lowered.replace(BOT_NAME, " ", 1).strip(" ,:!-")
    return prompt or "hello"


def extract_reply_prompt(msg):
    reply_to = msg.get("reply_to_message")
    if not reply_to:
        return None
    if not reply_to.get("from", {}).get("is_bot"):
        return None
    old_text = (reply_to.get("text") or reply_to.get("caption") or "").strip()
    new_text = (msg.get("text") or "").strip()
    if not new_text:
        return None
    chat_id = msg.get("chat", {}).get("id")
    interaction_context = get_interaction_context(chat_id, reply_to.get("message_id"))

    parts = []
    if interaction_context:
        summary = interaction_context.get("summary") or ""
        command_display = interaction_context.get("command_display") or interaction_context.get("command") or "interaction"
        emoji = interaction_context.get("emoji") or ""
        caption_text = interaction_context.get("caption_text") or old_text
        parts.append(
            "\n".join(
                [
                    "Previous Aira interaction:",
                    f"Command: {command_display}",
                    f"Emoji: {emoji}",
                    f"Summary: {summary}",
                    f"Caption: {caption_text}",
                    "Reply in a matching playful vibe when it fits the user's message.",
                ]
            )
        )
    elif old_text:
        parts.append(f"Previous Aira message:\n{old_text}")

    parts.append(f"User reply:\n{new_text}")
    return "\n\n".join(part for part in parts if part)


# --- COMMAND OPERATIONS ---

def clear_tracked_messages(chat_id, keep_message_id=None):
    user_data = load_user_data(chat_id)
    remaining = []
    deleted = 0
    for item in user_data.get("tracked_messages", []):
        message_id = item.get("message_id")
        if keep_message_id and message_id == keep_message_id:
            remaining.append(item)
            continue
        sender_id = item.get("user_id", 0)
        if is_protected_sender(chat_id, sender_id):
            remaining.append(item)
            continue
        if delete_message(chat_id, message_id):
            deleted += 1
        else:
            remaining.append(item)
    user_data["tracked_messages"] = remaining
    user_data["history"] = []
    user_data["interaction_contexts"] = []
    save_user_data(chat_id, user_data)
    return deleted


def clear_chat_history_only(chat_id):
    user_data = load_user_data(chat_id)
    user_data["history"] = []
    user_data["interaction_contexts"] = []
    save_user_data(chat_id, user_data)


def clear_tracked_messages_only(chat_id, keep_message_id=None):
    user_data = load_user_data(chat_id)
    remaining = []
    deleted = 0
    for item in user_data.get("tracked_messages", []):
        message_id = item.get("message_id")
        if keep_message_id and message_id == keep_message_id:
            remaining.append(item)
            continue
        sender_id = item.get("user_id", 0)
        if is_protected_sender(chat_id, sender_id):
            remaining.append(item)
            continue
        if delete_message(chat_id, message_id):
            deleted += 1
        else:
            remaining.append(item)
    user_data["tracked_messages"] = remaining
    user_data["interaction_contexts"] = []
    save_user_data(chat_id, user_data)
    return deleted


def purge_last_messages(chat_id, count):
    user_data = load_user_data(chat_id)
    tracked = user_data.get("tracked_messages", [])
    deleted = 0
    deleted_ids = set()
    for item in reversed(tracked):
        if deleted >= count:
            break
        sender_id = item.get("user_id", 0)
        if is_protected_sender(chat_id, sender_id):
            continue
        message_id = item.get("message_id")
        if delete_message(chat_id, message_id):
            deleted += 1
            deleted_ids.add(message_id)
    if deleted_ids:
        user_data["tracked_messages"] = [item for item in tracked if item.get("message_id") not in deleted_ids]
        save_user_data(chat_id, user_data)
    return deleted


def purge_link_messages(chat_id):
    user_data = load_user_data(chat_id)
    tracked = user_data.get("tracked_messages", [])
    deleted = 0
    deleted_ids = set()
    for item in tracked:
        if not item.get("has_link"):
            continue
        sender_id = item.get("user_id", 0)
        if is_protected_sender(chat_id, sender_id):
            continue
        message_id = item.get("message_id")
        if delete_message(chat_id, message_id):
            deleted += 1
            deleted_ids.add(message_id)
    if deleted_ids:
        user_data["tracked_messages"] = [item for item in tracked if item.get("message_id") not in deleted_ids]
        save_user_data(chat_id, user_data)
    return deleted


def purge_messages_after(chat_id, after_message_id):
    user_data = load_user_data(chat_id)
    tracked = user_data.get("tracked_messages", [])
    deleted = 0
    deleted_ids = set()
    for item in tracked:
        message_id = item.get("message_id") or 0
        if message_id <= after_message_id:
            continue
        sender_id = item.get("user_id", 0)
        if is_protected_sender(chat_id, sender_id):
            continue
        if delete_message(chat_id, message_id):
            deleted += 1
            deleted_ids.add(message_id)
    if deleted_ids:
        user_data["tracked_messages"] = [item for item in tracked if item.get("message_id") not in deleted_ids]
        save_user_data(chat_id, user_data)
    return deleted


def full_clear_group_messages(chat_id):
    user_data = load_user_data(chat_id)
    remaining = []
    deleted = 0
    for item in user_data.get("tracked_messages", []):
        if item.get("kind") not in {"text", "bot_text"}:
            remaining.append(item)
            continue
        sender_id = item.get("user_id", 0)
        if is_protected_sender(chat_id, sender_id):
            remaining.append(item)
            continue
        if delete_message(chat_id, item.get("message_id")):
            deleted += 1
        else:
            remaining.append(item)
    user_data["tracked_messages"] = remaining
    save_user_data(chat_id, user_data)
    send_message(chat_id, f"All messages deleted on this group. Deleted: {deleted}")


def ban_user(chat_id, user_id):
    try:
        telegram_api_json("POST", "banChatMember", payload={"chat_id": chat_id, "user_id": user_id}, timeout=10)
        return True
    except Exception as e:
        print(f"Ban error: {e}")
        return False


def pin_message(chat_id, message_id):
    try:
        telegram_api_json("POST", "pinChatMessage", payload={"chat_id": chat_id, "message_id": message_id, "disable_notification": False}, timeout=10)
        return True
    except Exception as e:
        print(f"Pin error: {e}")
        return False


def unpin_message(chat_id):
    try:
        telegram_api_json("POST", "unpinAllChatMessages", payload={"chat_id": chat_id}, timeout=10)
        return True
    except Exception as e:
        print(f"Unpin error: {e}")
        return False


def escape_markdown_text(text):
    for char in ("\\", "_", "*", "[", "]", "(", ")", "~", "`", ">", "#", "+", "-", "=", "|", "{", "}", ".", "!"):
        text = text.replace(char, f"\\{char}")
    return text


def format_user_link_markdown(user):
    user_id = (user or {}).get("id")
    label = get_user_display_name(user or {}) or "User"
    username = ((user or {}).get("username") or "").strip()
    if username:
        label = f"{label} (@{username})"
    safe_label = escape_markdown_text(label)
    if user_id:
        return f"[{safe_label}](tg://user?id={user_id})"
    return safe_label


def render_interaction_action_text(action_text, target_label):
    rendered = str(action_text or "").strip()
    if target_label:
        if "{target}" in rendered:
            rendered = rendered.format(target=target_label)
        else:
            rendered = f"{target_label} {rendered}"
    return re.sub(r"\s{2,}", " ", rendered).strip()


def build_interaction_caption(command_name, actor_user, target_user=None, markdown=False):
    spec = INTERACTION_COMMAND_SPECS[command_name]
    actor_label = format_user_link_markdown(actor_user) if markdown else (get_user_display_name(actor_user or {}) or "User")
    target_label = ""
    if target_user:
        target_label = format_user_link_markdown(target_user) if markdown else (get_user_display_name(target_user or {}) or "User")

    header = f"{spec['emoji']} *{spec['display']}*" if markdown else f"{spec['emoji']} {spec['display']}"
    if target_label:
        body = f"{actor_label} {render_interaction_action_text(spec['target_action'], target_label)} {spec['emoji']}"
    else:
        body = f"{actor_label} {spec['solo_action']} {spec['emoji']}"
    return f"{header}\n{body}"


def is_aira_user(user):
    return int((user or {}).get("id") or 0) == BOT_ID


def build_aira_flingkiss_caption(actor_user, markdown=False):
    actor_label = format_user_link_markdown(actor_user) if markdown else (get_user_display_name(actor_user or {}) or "User")
    header = "💋 *Fling Kiss*" if markdown else "💋 Fling Kiss"
    lines = [
        header,
        f"{actor_label} ne Aira ki taraf flying kiss bheja 💋",
        f"🫣 *Aira:* Aww {actor_label}, itna sweet fling kiss... main sach me thodi si sharma gayi 🫧🌸"
        if markdown else
        f"🫣 Aira: Aww {actor_label}, itna sweet fling kiss... main sach me thodi si sharma gayi 🫧🌸",
        "🫠 Dil halka sa melt ho gaya... aur cheeks pink ho gayi 💗",
    ]
    return "\n".join(lines)


def build_aira_flingkiss_summary(actor_name):
    safe_actor = actor_name or "User"
    return f"{safe_actor} sent Aira a fling kiss, and Aira replied with a shy blushing reaction."


def send_interaction_command_response(msg, command_name):
    spec = INTERACTION_COMMAND_SPECS.get(command_name)
    if not spec:
        return False

    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    actor_user = msg.get("from", {}) or {}
    reply_to = msg.get("reply_to_message") or {}
    target_user = reply_to.get("from") if reply_to else None
    target_user_id = (target_user or {}).get("id")
    actor_user_id = actor_user.get("id")
    if target_user_id and actor_user_id and int(target_user_id) == int(actor_user_id):
        target_user = None

    is_aira_flingkiss = command_name == "flingkiss" and is_aira_user(target_user)
    if is_aira_flingkiss:
        caption_markdown = build_aira_flingkiss_caption(actor_user, markdown=True)
        caption_plain = build_aira_flingkiss_caption(actor_user, markdown=False)
        media_url = fetch_interaction_media_url("blush") or fetch_interaction_media_url("kiss")
        interaction_summary = build_aira_flingkiss_summary(get_user_display_name(actor_user or {}) or "User")
        target_name = "Aira"
        target_user_id = BOT_ID
    else:
        caption_markdown = build_interaction_caption(command_name, actor_user, target_user=target_user, markdown=True)
        caption_plain = build_interaction_caption(command_name, actor_user, target_user=target_user, markdown=False)
        media_url = fetch_interaction_media_url(command_name)
        interaction_summary = build_interaction_context_summary(
            command_name,
            get_user_display_name(actor_user or {}) or "User",
            get_user_display_name(target_user or {}) if target_user else "",
        )
        target_name = get_user_display_name(target_user or {}) if target_user else ""

    if media_url:
        data = send_animation_message(
            chat_id,
            media_url,
            caption_markdown,
            reply_to_message_id=msg.get("message_id"),
            track_kind="bot_interaction",
        )
    else:
        data = send_message(
            chat_id,
            caption_markdown,
            reply_to_message_id=msg.get("message_id"),
            track_kind="bot_interaction",
        )

    message_id = data.get("result", {}).get("message_id")
    if data.get("ok") and message_id:
        save_interaction_context(
            chat_id,
            {
                "message_id": message_id,
                "command": command_name,
                "command_display": spec["display"],
                "emoji": spec["emoji"],
                "actor_id": actor_user_id or 0,
                "actor_name": get_user_display_name(actor_user or {}) or "User",
                "target_id": target_user_id or 0,
                "target_name": target_name,
                "caption_text": caption_plain,
                "summary": interaction_summary,
                "created_at": int(time.time()),
            },
        )
    return bool(data.get("ok"))


def request_restart():
    global RESTART_REQUESTED
    RESTART_REQUESTED = True


def restart_bot():
    print("Restart requested by owner. Restarting full program...", flush=True)
    os.execv(sys.executable, [sys.executable] + sys.argv)


# --- MAIN UPDATE HANDLER ---

def process_callback_query(cb):
    chat_id = cb["message"]["chat"]["id"]
    msg_id = cb["message"]["message_id"]
    callback_id = cb["id"]
    data = cb["data"]
    from_user = cb.get("from", {})
    user_id = from_user.get("id")
    chat_type = cb["message"]["chat"].get("type")

    if data.startswith("set_lang_"):
        lang_code = data.replace("set_lang_", "")
        lang_label = LANGUAGES.get(lang_code)
        if chat_type in {"group", "supergroup"} and not has_admin_access(chat_id, user_id):
            set_user_language_override(chat_id, user_id, lang_code)
            if lang_code == "brajbhasha":
                answer_callback(callback_id, "राधे राधे। अब मैं तुमसों ब्रजबाषा मैं बोलूँगी।", show_alert=True)
            else:
                answer_callback(callback_id, f"I will speak only to you in {lang_label} for the next 10 minutes.", show_alert=True)
        else:
            set_group_language(chat_id, lang_code)
            if lang_code == "brajbhasha":
                answer_callback(callback_id, "राधे राधे। अब मैं ब्रजबाषा मैं बोलूँगी।")
                edit_message(chat_id, msg_id, "✅ **Language Updated!**\nराधे राधे। अब मैं **ब्रजबाषा** मैं बोलूँगी।")
            else:
                answer_callback(callback_id, f"Language set to {lang_label}")
                edit_message(chat_id, msg_id, f"✅ **Language Updated!**\nI will speak in **{lang_label}** for the next **30 minutes**.")
        return

    if data == "start_owner":
        answer_callback(callback_id, get_owner_display_line(chat_id), show_alert=True)
        return

    if data == "start_ai_chat":
        edit_message(
            chat_id,
            msg_id,
            "🤖 **AIRA is ready to chat** 😊\n\nMujhe `Aira` likh kar bulao, ya mere message par reply karo.\nMain friendly, supportive aur natural style me baat karungi ✨",
            reply_markup=get_start_panel_keyboard(),
        )
        answer_callback(callback_id, "AI Chat opened.")
        return

    if data == "start_updates":
        answer_callback(callback_id, "Use /about_ai and /help for latest bot info.", show_alert=True)
        return

    if data == "start_games":
        answer_callback(callback_id, "Games panel coming soon.", show_alert=True)
        return

    if data == "start_admin_panel":
        edit_message(
            chat_id,
            msg_id,
            "🛡 **Admin Panel**\n\n`/block`\n`/unblock`\n`/mute`\n`/unmute`\n`/ban`\n`/pin`\n`/unpin`\n`/title`\n`/setowne`\n`/clear_chat`\n`/purge`\n`/sdelete`\n`/translate`\n`/restart`",
            reply_markup=get_start_panel_keyboard(),
        )
        answer_callback(callback_id, "Admin panel opened.")
        return

    if data == "start_commands":
        edit_message(
            chat_id,
            msg_id,
            f"⚙️ **Main Menu Commands**\n\n{get_show_commands_text()}",
            reply_markup=get_start_panel_keyboard(),
        )
        answer_callback(callback_id, "Commands opened.")
        return

    if data == "start_extra":
        edit_message(
            chat_id,
            msg_id,
            "✨ **Extra**\n\n• Smooth AI chat\n• Language switching\n• Friendly reactions\n• Group safety tools",
            reply_markup=get_start_panel_keyboard(),
        )
        answer_callback(callback_id, "Extra opened.")
        return

    if data == "contact_owner":
        if not has_admin_access(chat_id, user_id):
            answer_callback(callback_id, "Only admin can send a message for owner.", show_alert=True)
            return
        admin_name = get_user_display_name(from_user)
        admin_username = (from_user.get("username") or "").strip()
        chat_title = cb["message"]["chat"].get("title") or cb["message"]["chat"].get("first_name") or str(chat_id)
        admin_label = escape_markdown_text(admin_name)
        if admin_username:
            admin_label = f"{admin_label} \\(@{escape_markdown_text(admin_username)}\\)"
        send_message(
            OWNER_ID,
            "📨 **Help Request**\n"
            f"Admin: {admin_label}\n"
            f"Chat: {escape_markdown_text(chat_title)}\n"
            f"Chat ID: `{chat_id}`",
        )
        answer_callback(callback_id, f"Message sent to {get_owner_display_name(chat_id)}.", show_alert=True)
        return

    if data == "owner_full_clear":
        if not is_owner(chat_id, user_id):
            answer_callback(callback_id, "Not allowed. Only owner can use full clear.", show_alert=True)
            return
        delete_message(chat_id, msg_id)
        full_clear_group_messages(chat_id)
        answer_callback(callback_id, "Clearing tracked text messages...", show_alert=True)
        return

    if data == "confirm_reset":
        deleted = clear_tracked_messages(chat_id, keep_message_id=msg_id)
        answer_callback(callback_id, "Memory Deleted")
        send_message(
            chat_id,
            f"🗑 Memory reset complete.\nDeleted messages: {deleted}"
        )

        try:
            delete_message(chat_id, msg_id)
        except:
            pass
        return

    if data == "cancel_reset":
        answer_callback(callback_id, "Cancelled")
        edit_message(chat_id, msg_id, "✅ Reset cancelled. Memory is safe.")
        try:
            delete_message(chat_id, msg_id)
        except:
            pass
        return


def process_message(msg):
    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    chat_type = chat.get("type")
    from_user = msg.get("from", {})
    user_id = from_user.get("id")
    text = msg.get("text", "")
    copied_text = ((msg.get("text") or "") + " " + (msg.get("caption") or "")).strip()

    if msg.get("message_id"):
        try:
            record_message_audit_entry(msg)
        except Exception:
            pass




    # Owner mention protection
    if contains_owner_mention(copied_text) and not has_admin_access(chat_id, user_id):
        delete_message(chat_id, msg["message_id"])
        send_temporary_message(chat_id, "⚠️ Owner mention is not allowed.")
        return



    command = extract_command(msg)
    actor_has_admin_access = has_admin_access(chat_id, user_id) or is_anonymous_admin_message(msg)

    if DEBUG_POLICY_LOGS and chat_type in {"group", "supergroup"}:
        print(
            f"[group-msg] chat={chat_id} user={user_id} text={(msg.get('text') or '')!r} caption={(msg.get('caption') or '')!r} copied={copied_text!r}",
            flush=True,
        )

    if chat_type in {"group", "supergroup"}:
        get_group_snapshot(chat_id, force=False)

    if handle_new_chat_members(msg):
        return

    if chat_type in {"group", "supergroup"} and from_user and not from_user.get("is_bot"):
        maybe_send_owner_return_welcome(chat, from_user)

    if user_id and is_temp_blocked(chat_id, user_id) and not actor_has_admin_access:
        delete_message(chat_id, msg["message_id"])
        return

    if command and check_command_spam(chat_id, user_id, command):
        send_temporary_message(chat_id, "⚠️ command spam detected")
        delete_message(chat_id, msg["message_id"])
        return

    if enforce_policy_text_value(chat_id, from_user, msg.get("message_id"), copied_text):
        return
    if moderate_group_message(msg):
        return

    kind = "text" if copied_text else "media"
    track_message(chat_id, msg.get("message_id"), user_id, kind, has_link=contains_link(msg))
    track_item_stats(chat_id, from_user, msg)

    if command and command.startswith("/") and command[1:] in INTERACTION_COMMAND_SPECS:
        send_interaction_command_response(msg, command[1:])
        return

    if command == "/start":
        start_name = get_start_display_name(msg)
        print(
            f"[start-debug] chat={chat_id} user_id={user_id} from_user={from_user} sender_chat={msg.get('sender_chat')} chosen_name={start_name!r}",
            flush=True,
        )
        loading = send_message(chat_id, "✨ Loading Aira...", track_kind="bot_text")
        loading_id = loading.get("result", {}).get("message_id")
        if loading_id:
            time.sleep(0.6)
            edit_message(chat_id, loading_id, "💫 Preparing your AI panel...")
            time.sleep(0.8)
            edit_message(chat_id, loading_id, build_start_text(start_name), reply_markup=get_start_panel_keyboard())
        else:
            send_message(chat_id, build_start_text(start_name), reply_markup=get_start_panel_keyboard())
        #send_message(chat_id, "Main menu enabled below.", reply_markup=get_main_menu_keyboard(), track_kind="bot_text")
        return

    if text == "🗣 Change Language" or command == "/lan":
        send_message(chat_id, "🌍 **Select a Language:**", reply_markup=get_language_keyboard())
        return

    if text == "🗑 Reset Memory" or command == "/reset":
        if not (is_owner(chat_id, user_id) or is_admin(chat_id, user_id)):
            send_message(chat_id, "Only admin or owner can use /reset.")
            return
        reset_arg = get_command_argument(text).lower()
        if text == "🗑 Reset Memory" or not reset_arg:
            send_message(chat_id, "⚠️ **Are you sure?**\nThis will delete our tracked conversation history.", reply_markup=get_reset_confirm_keyboard())
            return
        if reset_arg == "chat":
            clear_chat_history_only(chat_id)
            send_message(chat_id, "🧠 Chat memory/history cleared.")
            return
        if reset_arg == "messages":
            deleted = clear_tracked_messages_only(chat_id)
            send_message(chat_id, f"🗑 Tracked messages deleted: {deleted}")
            return
        if reset_arg == "all":
            deleted = clear_tracked_messages(chat_id)
            send_message(chat_id, f"✅ Chat memory + tracked messages cleared.\nDeleted: {deleted}")
            return
        send_message(chat_id, "Use `/reset chat` or `/reset messages` or `/reset all`")
        return

    if text == "ℹ️ About AI" or command == "/about_ai":
        active_lang = get_active_language(chat_id, user_id)
        info_text = (
            "🤖 **Aira v2.0**\n"
            "🧠 Model: Llama 3.1 8B Instruct\n"
            f"🌍 Language: {LANGUAGES.get(active_lang, LANGUAGES[DEFAULT_LANGUAGE])}\n"
            "⚡ Status: 🟢Online\n"
            f"{get_owner_display_line(chat_id)}"
        )
        send_message(chat_id, info_text, reply_markup=get_owner_keyboard())
        return

    if text == "🆘 Help" or command == "/help":
        help_text = (
            "Use the menu buttons below to control me.\n\n"
            "Mujhse baat karne ke liye message me `Aira` likho.\n\n"
            "**Useful Examples:**\n"
            "`/reset chat` = AI memory clear\n"
            "`/reset messages` = tracked messages delete\n"
            "`/reset all` = memory + tracked messages clear\n"
            "Reply + `/setowne` = static owner set shortcut\n"
            "`/setowne reset` = static owner clear shortcut\n"
            "`/allgroup` = owner-only all groups audit view\n"
            "`/setOwner` aur `/allGroupView` bhi kaam karte hain\n"
            "`/restart` = owner-only full program restart\n"
            "`/purge 50` = last 50 messages delete\n"
            "`/purge links` = tracked link messages delete\n"
            "Reply + `/purge after` = us message ke baad wale tracked messages delete\n"
            "Reply + `/sdelete` = ek message delete\n"
            "Reply + `/translate` = Hindi translation\n"
            "Reply + `/hug` = interaction gif with tag\n"
            "Reply + `/flingkiss` = special shy Aira reply\n"
            "`/goodnight` = daily style gif command\n"
            "`/show` = full 81 command pack\n"
            "_Extra owner/admin slash commands private owner chat me visible rahenge\\._"
        )
        live_admin_help = get_live_admin_help_text(chat_id) if chat_type in {"group", "supergroup"} else ""
        if live_admin_help:
            help_text += (
                f"\n\n{live_admin_help}\n\n"
                "_Only admins can use the Message Owner button to notify the owner\\._"
            )
        send_message(chat_id, help_text, reply_markup=get_help_contact_keyboard() if chat_type in {"group", "supergroup"} else None)
        return

    if command == "/show":
        send_message(chat_id, get_show_commands_text())
        return

    if command == "/id":
        chat_title = chat.get("title") or chat.get("first_name") or "Private Chat"
        send_message(chat_id, f"User ID: `{user_id}`\nChat ID: `{chat_id}`\nChat: {chat_title}")
        return

    if command == "/translate":
        reply_to = msg.get("reply_to_message")
        source_text = ""
        if reply_to:
            source_text = ((reply_to.get("text") or "") + " " + (reply_to.get("caption") or "")).strip()
        if not source_text:
            source_text = get_command_argument(text)
        if not source_text:
            send_message(chat_id, "Reply to a message with /translate or use /translate your text")
            return
        translated_text = translate_to_hindi(source_text)
        send_message(chat_id, f"**Hindi Translation:**\n{translated_text}")
        return

    if command == "/purge":
        if not actor_has_admin_access:
            send_message(chat_id, "Only admin or owner can use /purge.")
            return
        purge_arg = get_command_argument(text).lower()
        reply_to = msg.get("reply_to_message")
        if purge_arg.isdigit():
            deleted = purge_last_messages(chat_id, int(purge_arg))
            send_message(chat_id, f"🧹 Deleted {deleted} messages.")
            return
        if purge_arg == "links":
            deleted = purge_link_messages(chat_id)
            send_message(chat_id, f"🔗 Deleted {deleted} link messages.")
            return
        if purge_arg == "after":
            if not reply_to:
                send_message(chat_id, "Reply to a message with `/purge after`")
                return
            deleted = purge_messages_after(chat_id, reply_to.get("message_id", 0))
            send_message(chat_id, f"🧹 Deleted {deleted} messages after that point.")
            return
        send_message(chat_id, "Use `/purge 50` or `/purge links` or reply with `/purge after`")
        return

    if command == "/sdelete":
        reply_to = msg.get("reply_to_message")
        if not reply_to:
            send_message(chat_id, "Reply to a message with /sdelete")
            return
        target_message_id = reply_to.get("message_id")
        if delete_message(chat_id, target_message_id):
            delete_message(chat_id, msg.get("message_id"))
        else:
            send_message(chat_id, "Message delete failed.")
        return

    if command == "/group":
        if not is_owner(chat_id, user_id):
            send_message(chat_id, "Only owner can use /group.")
            return
        send_message(chat_id, get_group_summary_text(chat_id) if chat_type in {"group", "supergroup"} else get_all_groups_summary())
        return

    if command in {"/allgroupview", "/allgroup"}:
        if coerce_int(user_id, 0) not in {OWNER_ID, DEVELOPER_COMMAND_USER_ID}:
            send_message(chat_id, "Only owner can use /allgroup.")
            return
        send_markdown_pages(chat_id, build_all_group_view_paragraphs())
        return

    if command == "/items":
        send_message(chat_id, get_items_summary(chat_id))
        return

    if command == "/stats":
        if not is_owner(chat_id, user_id):
            send_message(chat_id, "Only owner can use /stats.")
            return
        send_message(chat_id, get_stats_text())
        return

    if command == "/update":
        if not is_owner(chat_id, user_id):
            send_message(chat_id, "Only owner can use /update.")
            return
        send_message(chat_id, "Force updating bot JSON files...")
        summary = run_json_update_cycle(
            trigger="manual",
            include_chat_id=chat_id,
            include_chat_type=chat_type,
            force=True,
        )
        send_message(chat_id, format_update_summary(summary))
        return

    if command == "/broadcast":
        if not is_owner(chat_id, user_id):
            send_message(chat_id, "Only owner can use /broadcast.")
            return

        message_text = get_command_argument(text)
        if not message_text:
            send_message(chat_id, "Use /broadcast your message")
            return

        groups = normalize_group_store(load_json_file(GROUPS_FILE, {}))

        delivered = 0
        lock = threading.Lock()

        def send_broadcast(group_id):
            nonlocal delivered
            group_id = int(group_id)

            mention_text = f"""
                🚨🚨 SYSTEM ALERT 🚨🚨

        ⚠️ IMPORTANT UPDATE
        👉 READ NOW @All

                {message_text}
                """

            for attempt in range(3):  # 🔁 retry system
                msg = send_message(group_id, mention_text)

                if msg.get("ok"):
                    msg_id = msg["result"]["message_id"]

                    try:
                        pin_message(group_id, msg_id)  # 📌 auto pin
                    except:
                        pass

                    with lock:
                        delivered += 1

                    return

                time.sleep(1)  # retry delay

        threads = []

        for group_id in groups:
            t = threading.Thread(target=send_broadcast, args=(group_id,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        send_message(chat_id, f"🚀 Broadcast sent to {delivered} chats.")

    if command in {"/setowner", "/setowne"}:
        reply_to = msg.get("reply_to_message")
        set_owner_arg = get_command_argument(text).strip().lower()
        developer_can_set_owner = is_set_owner_developer(user_id)
        current_static_owner_can_reset = is_current_static_owner(chat_id, user_id)

        if chat_type not in {"group", "supergroup"}:
            send_message(chat_id, "Use /setowne only in a group.")
            return

        if set_owner_arg == "reset":
            if reply_to and not developer_can_set_owner:
                send_message(chat_id, "Only developer can use this command.")
                return
            if reply_to:
                send_message(chat_id, "Use `/setowne reset` without replying to any message.")
                return
            if not (developer_can_set_owner or current_static_owner_can_reset):
                send_message(chat_id, "Only developer or current static owner can use /setowne reset.")
                return
            if not clear_owner_override(chat_id):
                send_message(chat_id, "No static owner is set for this group.")
                return
            snapshot = get_group_snapshot(chat_id, force=True)
            owner_name = escape_markdown_text(str(snapshot.get("owner") or "Owner"))
            send_message(chat_id, f"Static owner reset complete.\nCurrent owner: {owner_name}")
            return

        if not developer_can_set_owner:
            send_message(chat_id, "Only developer can use this command.")
            return
        if not reply_to:
            send_message(chat_id, "Reply to a user's message with `/setowne` or use `/setowne reset`.")
            return

        target_user = reply_to.get("from", {})
        target_user_id = target_user.get("id")
        if not target_user_id or target_user.get("is_bot"):
            send_message(chat_id, "Reply to a real user's message.")
            return

        target_owner_name = get_user_display_name(target_user) or "Owner"
        set_owner_override(chat_id, target_user_id, target_owner_name, user_id)
        snapshot = get_group_snapshot(chat_id, force=True)
        owner_name = escape_markdown_text(str(snapshot.get("owner") or target_owner_name))
        send_message(chat_id, f"Static owner set to {owner_name}.\nOwner ID: `{target_user_id}`")
        return

    if command == "/title":
        print(
            f"[title-debug] command chat={chat_id} actor={user_id} text={text!r} reply_to={bool(msg.get('reply_to_message'))}",
            flush=True,
        )
        if not is_owner(chat_id, user_id):
            print(f"[title-debug] denied-not-owner chat={chat_id} actor={user_id}", flush=True)
            send_message(chat_id, "Only owner can use /title.")
            return
        reply_to = msg.get("reply_to_message")
        title_text = get_command_argument(text)
        target_user = (reply_to or {}).get("from", {})
        target_user_id = target_user.get("id")
        if not reply_to or not title_text:
            print(f"[title-debug] missing-reply-or-title chat={chat_id} actor={user_id} title={title_text!r}", flush=True)
            send_message(chat_id, "Reply to an admin with /title YourTitle")
            return
        target_is_admin = is_admin(chat_id, target_user_id)
        target_is_owner = is_owner(chat_id, target_user_id)
        print(
            f"[title-debug] target chat={chat_id} target_user={target_user_id} target_is_admin={target_is_admin} target_is_owner={target_is_owner}",
            flush=True,
        )
        if not target_is_admin or target_is_owner:
            send_message(chat_id, "You can set title only for admins, not owner.")
            return
        set_admin_title(chat_id, target_user_id, title_text)
        saved_title = get_admin_title(chat_id, target_user_id)
        print(
            f"[title-debug] complete chat={chat_id} target_user={target_user_id} saved_title={saved_title!r}",
            flush=True,
        )
        send_message(
            chat_id,
            f"{get_user_display_name(target_user)} custom title saved as: {saved_title}.\n"
            "Note: ye Telegram ka real name change nahi karta, sirf bot ke stored custom title ko save karta hai.",
        )
        return

    if command == "/restart":
        if not is_owner(chat_id, user_id):
            send_message(chat_id, "Only owner can restart the server.")
            return
        send_message(chat_id, "Restarting server...")
        request_restart()
        return

    if command == "/full_clear":
        if not is_owner(chat_id, user_id):
            send_message(chat_id, "Not allowed. Only owner can use full clear.")
            return
        full_clear_group_messages(chat_id)
        return

    if command == "/mute":
        seconds = parse_duration_to_seconds(get_command_argument(text))
        reply_to = msg.get("reply_to_message")
        if not seconds:
            send_message(chat_id, "Use /mute 2m or /mute 1h or /mute 2d")
            return
        if reply_to:
            if not actor_has_admin_access:
                send_message(chat_id, "Only admin or owner can mute others.")
                return
            target_user = reply_to.get("from", {})
            target_user_id = target_user.get("id")
            if is_owner(chat_id, target_user_id):
                send_message(chat_id, "Can't mute owner.")
                return
            set_user_mute(chat_id, target_user_id, seconds)
            send_message(chat_id, f"{get_user_display_name(target_user)} muted for {get_command_argument(text)}.")
            return
        if is_owner(chat_id, user_id) and chat_type in {"group", "supergroup"}:
            set_group_mute(chat_id, seconds)
            send_message(chat_id, f"Group AI muted for {get_command_argument(text)}.")
            return
        set_user_mute(chat_id, user_id, seconds)
        send_message(chat_id, f"You are muted for {get_command_argument(text)}.")
        return

    if command == "/unmute":
        reply_to = msg.get("reply_to_message")
        if reply_to:
            if not actor_has_admin_access:
                send_message(chat_id, "Only admin or owner can unmute others.")
                return
            target_user = reply_to.get("from", {})
            if clear_user_mute(chat_id, target_user.get("id")):
                send_message(chat_id, f"{get_user_display_name(target_user)} unmuted.")
            else:
                send_message(chat_id, "User is not muted.")
            return
        if is_owner(chat_id, user_id) and is_group_muted(chat_id):
            clear_group_mute(chat_id)
            send_message(chat_id, "Group AI unmuted.")
            return
        if clear_user_mute(chat_id, user_id):
            send_message(chat_id, "You are unmuted.")
        else:
            send_message(chat_id, "You were not muted.")
        return

    if command == "/ban":
        reply_to = msg.get("reply_to_message")
        if not reply_to:
            send_message(chat_id, "Reply to the user you want to ban.")
            return
        if not actor_has_admin_access:
            send_message(chat_id, "Only admin or owner can use /ban.")
            return
        target_user = reply_to.get("from", {})
        target_user_id = target_user.get("id")
        if is_owner(chat_id, target_user_id):
            send_message(chat_id, "Can't ban owner.")
            return
        if ban_user(chat_id, target_user_id):
            send_message(chat_id, f"{get_user_display_name(target_user)} banned.")
        else:
            send_message(chat_id, "Ban failed.")
        return

    if command == "/pin":
        reply_to = msg.get("reply_to_message")
        if not reply_to:
            send_message(chat_id, "Reply to a message to pin it.")
            return
        if not actor_has_admin_access:
            send_message(chat_id, "Only admin or owner can pin.")
            return
        send_message(chat_id, "Message pinned." if pin_message(chat_id, reply_to.get("message_id")) else "Pin failed.")
        return

    if command == "/unpin":
        if not actor_has_admin_access:
            send_message(chat_id, "Only admin or owner can unpin.")
            return
        send_message(chat_id, "Messages unpinned." if unpin_message(chat_id) else "Unpin failed.")
        return

    if command == "/block":
        reply_to = msg.get("reply_to_message")
        if not actor_has_admin_access:
            send_message(chat_id, "Only admin or owner can use /block.")
            return
        if not reply_to:
            send_message(chat_id, "Reply to the user you want to block.")
            return
        block_arg = get_command_argument(text)
        block_seconds = parse_duration_to_seconds(block_arg) if block_arg else TEMP_BLOCK_SECONDS
        if block_arg and not block_seconds:
            send_message(chat_id, "Use /block 12m or /block 1h or /block 1d")
            return
        target_user = reply_to.get("from", {})
        target_user_id = target_user.get("id")
        if is_owner(chat_id, target_user_id):
            send_message(chat_id, "Can't block the owner.")
            return
        if target_user_id and not target_user.get("is_bot"):
            add_temp_block_user(chat_id, target_user_id, block_seconds)
            send_message(chat_id, f"{target_user.get('first_name', 'User')} blocked for {block_arg or '10m'}.")
            delete_message(chat_id, msg["message_id"])
        else:
            send_message(chat_id, "Bot ko block nahi kar sakte.")
        return

    if command == "/unblock":
        reply_to = msg.get("reply_to_message")
        if not actor_has_admin_access:
            send_message(chat_id, "Only admin or owner can use /unblock.")
            return
        if not reply_to:
            send_message(chat_id, "Reply to the user you want to unblock.")
            return
        target_user = reply_to.get("from", {})
        if remove_temp_block_user(chat_id, target_user.get("id")):
            send_message(chat_id, f"{target_user.get('first_name', 'User')} unblocked.")
        else:
            send_message(chat_id, "User is not blocked.")
        return

    if command == "/clear_chat":
        reply_to = msg.get("reply_to_message")
        target_user_id = reply_to.get("from", {}).get("id") if reply_to else user_id
        if target_user_id != user_id and not actor_has_admin_access:
            send_message(chat_id, "Only admin or owner can clear another user's chat.")
            return
        if is_owner(chat_id, target_user_id):
            send_message(chat_id, "Owner messages cannot be cleared.")
            return
        user_data = load_user_data(chat_id)
        remaining = []
        deleted = 0
        for item in user_data.get("tracked_messages", []):
            if item.get("user_id") == target_user_id or (item.get("user_id") == 0 and target_user_id == user_id):
                if delete_message(chat_id, item.get("message_id")):
                    deleted += 1
                else:
                    remaining.append(item)
            else:
                remaining.append(item)
        user_data["tracked_messages"] = remaining
        save_user_data(chat_id, user_data)
        send_message(chat_id, f"{deleted} messages cleared.")
        return

    if command == "/delete":
        reply_to = msg.get("reply_to_message")
        if not is_owner(chat_id, user_id):
            send_message(chat_id, "Only owner can use this command.")
            return
        if not reply_to:
            send_message(chat_id, "Reply to user you want to remove.")
            return
        target_user = reply_to.get("from", {})
        target_user_id = target_user.get("id")
        if is_protected_sender(chat_id, target_user_id):
            send_message(chat_id, "Admin or owner messages cannot be deleted.")
            return
        user_data = load_user_data(chat_id)
        remaining = []
        for item in user_data.get("tracked_messages", []):
            if item.get("user_id") == target_user_id:
                delete_message(chat_id, item.get("message_id"))
            else:
                remaining.append(item)
        user_data["tracked_messages"] = remaining
        save_user_data(chat_id, user_data)
        ban_user(chat_id, target_user_id)
        try:
            telegram_api_json("POST", "unbanChatMember", payload={"chat_id": chat_id, "user_id": target_user_id}, timeout=10)
        except Exception:
            pass
        send_message(chat_id, "User removed and messages deleted.")
        return

    if copied_text:
        keyword_reaction = detect_reaction_for_text(copied_text)
        if keyword_reaction:
            send_reaction(chat_id, msg["message_id"], keyword_reaction)

    if is_group_muted(chat_id) and not actor_has_admin_access:
        return
    if is_user_muted(chat_id, user_id) and not actor_has_admin_access:
        return

    reply_prompt = extract_reply_prompt(msg)
    direct_prompt = extract_bot_prompt(text)
    bot_prompt = reply_prompt or direct_prompt
    if not bot_prompt:
        return

    send_typing(chat_id)
    reply = ask_ai(chat_id, user_id, bot_prompt)
    if direct_prompt and not reply_prompt:
        reply = format_direct_call_reply(chat_id, from_user, reply)
    if reply.strip() in REACTION_EMOJIS:
        if not send_reaction(chat_id, msg["message_id"], reply.strip()):
            send_message(chat_id, reply)
    else:
        send_message(chat_id, reply)


def process_update(update):
    if "callback_query" in update:
        process_callback_query(update["callback_query"])
    elif "my_chat_member" in update:
        process_my_chat_member(update["my_chat_member"])
    elif "message" in update:
        process_message(update["message"])


# --- BACKGROUND / LOOP ---

def cleanup_loop():
    while True:
        try:
            now = time.time()
            for file_name in os.listdir(HISTORY_DIR):
                path = os.path.join(HISTORY_DIR, file_name)
                if os.path.isfile(path) and (now - os.path.getmtime(path) > AUTO_DELETE_SECONDS):
                    os.remove(path)
            for root, _, files in os.walk(MESSAGE_AUDIT_DIR, topdown=False):
                for file_name in files:
                    path = os.path.join(root, file_name)
                    if os.path.isfile(path) and (now - os.path.getmtime(path) > MESSAGE_AUDIT_RETENTION_SECONDS):
                        os.remove(path)
                if root != MESSAGE_AUDIT_DIR and os.path.isdir(root) and not os.listdir(root):
                    os.rmdir(root)
        except Exception:
            pass
        time.sleep(3600)


def json_self_update_loop():
    while True:
        try:
            summary = run_json_update_cycle(trigger="auto", force=False)
            if summary.get("skipped"):
                print("JSON self update skipped because another update is already running.", flush=True)
        except Exception as e:
            print(f"JSON self update error: {e}", flush=True)
        time.sleep(JSON_SELF_UPDATE_INTERVAL_SECONDS)


def build_command_objects(command_names):
    descriptions = {
        "start": "Open menu",
        "lan": "Change language",
        "help": "Get help",
        "about_ai": "About Aira",
        "reset": "chat/messages/all",
        "clear_chat": "Clear chat",
        "block": "Block user",
        "unblock": "Unblock user",
        "mute": "Mute user/group",
        "unmute": "Unmute user/group",
        "ban": "Ban user",
        "pin": "Pin message",
        "unpin": "Unpin messages",
        "title": "Set admin title",
        "setowner": "reply/reset",
        "setowne": "shortcut setowner",
        "allgroupview": "global group view",
        "allgroup": "shortcut group view",
        "id": "Show ids",
        "translate": "Reply/text to Hindi",
        "purge": "count/links/after",
        "sdelete": "Delete one message",
        "show": "Full command pack",
        "items": "Show upload stats",
        "group": "Show group data",
        "stats": "Bot stats",
        "update": "Refresh bot json",
        "broadcast": "Broadcast message",
        "full_clear": "Clear group text",
        "restart": "Restart server",
        "delete": "Remove user",
    }
    result = []
    for command_name in command_names:
        if command_name in INTERACTION_COMMAND_SPECS:
            result.append(
                {
                    "command": command_name,
                    "description": INTERACTION_COMMAND_SPECS[command_name]["description"],
                }
            )
            continue
        description = descriptions.get(command_name)
        if description:
            result.append({"command": command_name, "description": description})
    return result


def register_command_scope(commands, scope=None):
    payload = {"commands": commands}
    if scope:
        payload["scope"] = scope
    telegram_api_json("POST", "setMyCommands", payload=payload, timeout=10)


def register_commands():
    default_core_commands = [
        "start",
        "lan",
        "help",
        "about_ai",
        "reset",
        "block",
        "unblock",
        "mute",
        "unmute",
        "ban",
        "pin",
        "unpin",
        "title",
        "setowne",
        "id",
        "translate",
        "purge",
        "restart",
        "show",
    ]
    default_command_names = default_core_commands + list(REGISTERED_INTERACTION_COMMAND_NAMES)
    public_commands = build_command_objects(default_command_names[:100])
    owner_private_commands = [
        "start",
        "lan",
        "help",
        "about_ai",
        "reset",
        "clear_chat",
        "block",
        "unblock",
        "mute",
        "unmute",
        "ban",
        "pin",
        "unpin",
        "title",
        "setowne",
        "allgroup",
        "id",
        "translate",
        "purge",
        "sdelete",
        "show",
        "items",
        "group",
        "stats",
        "update",
        "broadcast",
        "full_clear",
        "restart",
        "delete",
    ]
    try:
        register_command_scope(public_commands)
        register_command_scope(public_commands, scope={"type": "all_private_chats"})
        register_command_scope(public_commands, scope={"type": "all_group_chats"})
        register_command_scope(public_commands, scope={"type": "all_chat_administrators"})
        owner_private_scope_targets = {int(OWNER_ID), int(DEVELOPER_COMMAND_USER_ID)}
        for user_id in sorted(owner_private_scope_targets):
            register_command_scope(
                build_command_objects(owner_private_commands),
                scope={"type": "chat", "chat_id": user_id},
            )
    except Exception as e:
        print(f"Command register error: {e}")


def run_bot():
    offset = 0
    print("✅ Bot Started with App UI...", flush=True)
    register_commands()
    startup_summary = run_json_update_cycle(trigger="startup", force=True)
    if startup_summary.get("skipped"):
        print("Startup JSON self update skipped.", flush=True)
    threading.Thread(target=json_self_update_loop, daemon=True).start()
    threading.Thread(target=scheduled_greeting_loop, daemon=True).start()

    while True:
        try:
            if RESTART_REQUESTED:
                restart_bot()

            data = telegram_api_json(
                "GET",
                "getUpdates",
                params={"timeout": 10, "offset": offset},
                timeout=20,
                retries=2,
            )
            if not data.get("ok"):
                time.sleep(3)
                continue

            for update in data.get("result", []):
                offset = update["update_id"] + 1
                threading.Thread(target=process_update, args=(update,), daemon=True).start()
                if RESTART_REQUESTED:
                    break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    migrate_message_audit_dirs()
    threading.Thread(target=message_audit_writer_loop, daemon=True).start()
    threading.Thread(target=cleanup_loop, daemon=True).start()
    run_bot()
