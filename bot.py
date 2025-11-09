#!/usr/bin/env python3
# bot.py - Dynamic Telegram WebApp menu for subjects/tests + admin management
# Requires: pyTelegramBotAPI
# Persisted data: data.json (created next to this file)

import os
import json
import logging
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telebot import TeleBot, types

logging.basicConfig(level=logging.INFO)

# ---- Configuration via env vars ----
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@YOUR_CHANNEL")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))  # must be integer
WEB_URL = os.getenv("WEB_URL", "https://YOUR_WEBSITE_URL").rstrip("/")

DATA_FILE = "data.json"

if BOT_TOKEN.startswith("YOUR_"):
    logging.warning("BOT_TOKEN not set. Replace the placeholder or set BOT_TOKEN env var.")
if OWNER_ID == 0:
    logging.warning("OWNER_ID not set. Set OWNER_ID env var to your numeric Telegram id.")

bot = TeleBot(BOT_TOKEN, parse_mode=None)

# ---------- Health server for platforms (port 8000) ----------
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_server():
    server = HTTPServer(("0.0.0.0", 8000), HealthHandler)
    logging.info("Health-check HTTP server running on port 8000")
    server.serve_forever()

threading.Thread(target=run_health_server, daemon=True).start()

# ---------- Data management ----------
def load_data():
    if not os.path.exists(DATA_FILE):
        # default example
        default = {
            "subjects": {
                "STD 12 BOARDS TEST": [
                    # each entry is { "label": "Test 1", "path": "std12/physics/test1.html" }
                ]
            }
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2, ensure_ascii=False)
        return default
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)

data = load_data()

# ---------- Utilities ----------
def is_owner(user_id):
    return user_id == OWNER_ID

def check_joined(user_id):
    """Return True if user is member/admin/creator of configured channel.
       Owner bypass if OWNER_ID set."""
    if is_owner(user_id):
        return True
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logging.info(f"check_joined exception: {e}")
        return False

def build_subjects_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=1)
    for subj in data.get("subjects", {}).keys():
        cb = f"SUBJ|{subj}"
        kb.add(types.InlineKeyboardButton(f"📁 {subj}", callback_data=cb))
    # admin shortcuts
    kb.row(types.InlineKeyboardButton("🔄 Refresh", callback_data="REFRESH"),
           types.InlineKeyboardButton("❓ Help", callback_data="HELP"))
    return kb

def build_tests_keyboard(subject):
    tests = data.get("subjects", {}).get(subject, [])
    kb = types.InlineKeyboardMarkup(row_width=1)
    for idx, t in enumerate(tests):
        # callback contains subject and index
        cb = f"TEST|{subject}|{idx}"
        kb.add(types.InlineKeyboardButton(f"🧪 {t.get('label')}", callback_data=cb))
    kb.row(types.InlineKeyboardButton("🔙 Back", callback_data="BACK"))
    return kb

def open_test_via_webapp(chat_id, path, label):
    # path is relative on your hosted site, e.g. "std12/physics/test1.html"
    url = f"{WEB_URL}/{path.lstrip('/')}"
    kb = types.InlineKeyboardMarkup()
    webapp = types.WebAppInfo(url)
    kb.add(types.InlineKeyboardButton(f"🚀 Open: {label}", web_app=webapp))
    bot.send_message(chat_id, f"Opening: {label}", reply_markup=kb)

# ---------- Handlers ----------
@bot.message_handler(commands=['start'])
def start_cmd(m):
    chat_id = m.chat.id
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    channel_username = CHANNEL_ID.lstrip('@')
    join_url = f"https://t.me/{channel_username}"
    keyboard.add(types.InlineKeyboardButton("📢 Join Channel", url=join_url))
    keyboard.add(types.InlineKeyboardButton("✅ Done", callback_data="check_join"))
    bot.send_message(chat_id, "Please join our channel to continue:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda c: True)
def callback_handler(call):
    data_cb = (call.data or "")
    uid = call.from_user.id

    if data_cb == "check_join":
        bot.answer_callback_query(call.id, text="Checking membership...")
        if check_joined(uid):
            bot.send_message(uid, "✅ Verified. Choose a subject below:")
            kb = build_subjects_keyboard()
            bot.send_message(uid, "📂 Subjects:", reply_markup=kb)
        else:
            bot.send_message(uid, "❌ You are not a member yet. Please join the channel and press Done again.")
    elif data_cb.startswith("SUBJ|"):
        subject = data_cb.split("|",1)[1]
        kb = build_tests_keyboard(subject)
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=f"📂 {subject} — Select test:", reply_markup=kb)
        bot.answer_callback_query(call.id)
    elif data_cb.startswith("TEST|"):
        # format: TEST|subject|index
        parts = data_cb.split("|", 2)
        if len(parts) == 3:
            subject = parts[1]
            idx = int(parts[2])
            tests = data.get("subjects", {}).get(subject, [])
            if 0 <= idx < len(tests):
                t = tests[idx]
                path = t.get("path")
                label = t.get("label")
                # open as webapp
                open_test_via_webapp(call.message.chat.id, path, label)
                bot.answer_callback_query(call.id, text=f"Opening {label}...")
            else:
                bot.answer_callback_query(call.id, text="Test not found.")
        else:
            bot.answer_callback_query(call.id, text="Bad data.")
    elif data_cb == "BACK":
        try:
            bot.edit_message_text(chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  text="📂 Subjects:",
                                  reply_markup=build_subjects_keyboard())
        except Exception:
            bot.send_message(call.message.chat.id, "📂 Subjects:", reply_markup=build_subjects_keyboard())
        bot.answer_callback_query(call.id)
    elif data_cb == "REFRESH":
        bot.answer_callback_query(call.id, "Refreshed.")
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text="📂 Subjects:",
                              reply_markup=build_subjects_keyboard())
    elif data_cb == "HELP":
        bot.answer_callback_query(call.id)
        bot.send_message(call.from_user.id,
                         "Admin commands (owner only):\n"
                         "/add_subject <subject_name>\n"
                         "/remove_subject <subject_name>\n"
                         "/add_test <subject>|<label>|<relative_path>\n"
                         "/remove_test <subject>|<label>\n"
                         "/list")
    else:
        bot.answer_callback_query(call.id, "Unknown action.")

# ---------- Admin commands: only owner (OWNER_ID) ----------
def require_owner(func):
    def wrapper(m):
        uid = m.from_user.id
        if not is_owner(uid):
            bot.reply_to(m, "❌ Only the owner can use this command.")
            return
        return func(m)
    wrapper.__name__ = func.__name__
    return wrapper

@bot.message_handler(commands=['add_subject'])
@require_owner
def add_subject_cmd(m):
    text = m.text.strip()
    parts = text.split(" ", 1)
    if len(parts) < 2:
        bot.reply_to(m, "Usage: /add_subject <subject_name>")
        return
    subj = parts[1].strip()
    subjects = data.setdefault("subjects", {})
    if subj in subjects:
        bot.reply_to(m, f"Subject '{subj}' already exists.")
        return
    subjects[subj] = []
    save_data(data)
    bot.reply_to(m, f"✅ Subject '{subj}' added.")

@bot.message_handler(commands=['remove_subject'])
@require_owner
def remove_subject_cmd(m):
    text = m.text.strip()
    parts = text.split(" ", 1)
    if len(parts) < 2:
        bot.reply_to(m, "Usage: /remove_subject <subject_name>")
        return
    subj = parts[1].strip()
    subjects = data.get("subjects", {})
    if subj not in subjects:
        bot.reply_to(m, f"Subject '{subj}' not found.")
        return
    del subjects[subj]
    save_data(data)
    bot.reply_to(m, f"✅ Subject '{subj}' removed.")

@bot.message_handler(commands=['add_test'])
@require_owner
def add_test_cmd(m):
    text = m.text.strip()
    parts = text.split(" ", 1)
    if len(parts) < 2:
        bot.reply_to(m, "Usage: /add_test <subject>|<label>|<relative_path>")
        return
    body = parts[1].strip()
    try:
        subj, label, path = [p.strip() for p in body.split("|", 2)]
    except Exception:
        bot.reply_to(m, "Bad format. Use: /add_test <subject>|<label>|<relative_path>")
        return
    subjects = data.setdefault("subjects", {})
    if subj not in subjects:
        bot.reply_to(m, f"Subject '{subj}' not found. Use /add_subject first.")
        return
    # append
    subjects[subj].append({"label": label, "path": path})
    save_data(data)
    bot.reply_to(m, f"✅ Added test '{label}' to subject '{subj}'.\nPath: {path}")

@bot.message_handler(commands=['remove_test'])
@require_owner
def remove_test_cmd(m):
    text = m.text.strip()
    parts = text.split(" ", 1)
    if len(parts) < 2:
        bot.reply_to(m, "Usage: /remove_test <subject>|<label>")
        return
    body = parts[1].strip()
    try:
        subj, label = [p.strip() for p in body.split("|", 1)]
    except Exception:
        bot.reply_to(m, "Bad format. Use: /remove_test <subject>|<label>")
        return
    subjects = data.get("subjects", {})
    if subj not in subjects:
        bot.reply_to(m, f"Subject '{subj}' not found.")
        return
    tests = subjects[subj]
    new_tests = [t for t in tests if t.get("label") != label]
    if len(new_tests) == len(tests):
        bot.reply_to(m, f"Test '{label}' not found in subject '{subj}'.")
        return
    subjects[subj] = new_tests
    save_data(data)
    bot.reply_to(m, f"✅ Removed test '{label}' from subject '{subj}'.")

@bot.message_handler(commands=['list'])
@require_owner
def list_cmd(m):
    bot.reply_to(m, f"Current data:\n`{json.dumps(data, indent=2, ensure_ascii=False)}`")

# Fallback
@bot.message_handler(func=lambda m: True)
def fallback(m):
    bot.reply_to(m, "Use /start to begin. Owner can manage content with admin commands.")

# ---------- Main ----------
if __name__ == "__main__":
    logging.info("Bot starting (long polling).")
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=20)
        except Exception as e:
            logging.error(f"Polling error: {e}")
            time.sleep(3)