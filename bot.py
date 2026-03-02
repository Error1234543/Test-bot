import os
import json
import telebot
from telebot import types
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import logging

# ---------------- CONFIG ----------------
# ⚠️ WARNING: Apna naya token yahan quotes ke andar daalein
BOT_TOKEN = "8585007953:AAEqP3K3_5y43YRoYc4h99Lzlg9uE-1rAHo"
WEB_URL = "https://oldxhdj.netlify.app/" # <-- Fixed quote here
OWNER_ID = 8226637107  

TELEGRAM_CHANNEL = "@NEET_JEE_GUJ"
WHATSAPP_LINK = "https://t.me/NEET_JEE_GUJ"

bot = telebot.TeleBot(BOT_TOKEN)

# ---------------- DATA PERSISTENCE ----------------
def load_allowed_users():
    if os.path.exists("users.json"):
        try:
            with open("users.json", "r") as f:
                return set(json.load(f))
        except:
            return {OWNER_ID}
    return {OWNER_ID}

def save_allowed_users(users_set):
    with open("users.json", "w") as f:
        json.dump(list(users_set), f)

ALLOWED_USERS = load_allowed_users()

try:
    with open("data.json", "r") as f:
        DATA = json.load(f)
except Exception:
    DATA = {}

# ---------------- ADMIN COMMANDS ----------------

@bot.message_handler(commands=['add'])
def add_user(msg):
    if msg.from_user.id != OWNER_ID:
        return
    try:
        new_id = int(msg.text.split()[1])
        ALLOWED_USERS.add(new_id)
        save_allowed_users(ALLOWED_USERS)
        bot.reply_to(msg, f"✅ User {new_id} added.")
    except:
        bot.reply_to(msg, "Format: `/add 12345`")

@bot.message_handler(commands=['remove'])
def remove_user(msg):
    if msg.from_user.id != OWNER_ID:
        return
    try:
        target_id = int(msg.text.split()[1])
        if target_id in ALLOWED_USERS:
            ALLOWED_USERS.remove(target_id)
            save_allowed_users(ALLOWED_USERS)
            bot.reply_to(msg, f"🗑️ User {target_id} removed.")
    except:
        bot.reply_to(msg, "Format: `/remove 12345`")

# ---------------- MAIN LOGIC ----------------

@bot.message_handler(commands=['start'])
def start_menu(msg):
    user_id = msg.from_user.id
    if user_id not in ALLOWED_USERS:
        bot.send_message(user_id, "🚫 No Access! Contact Admin.")
        return

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🚀 Start Mock Test", callback_data="SHOW_CLASSES"))
    bot.send_message(user_id, "👋 Welcome!", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: True)
def callback_handler(call):
    user_id = call.from_user.id
    if user_id not in ALLOWED_USERS:
        bot.answer_callback_query(call.id, "No Access", show_alert=True)
        return

    parts = call.data.split("|")
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    if call.data == "SHOW_CLASSES" or call.data == "BACK_MAIN":
        kb = types.InlineKeyboardMarkup()
        for cls in DATA.keys():
            kb.add(types.InlineKeyboardButton(text=cls, callback_data=f"STD|{cls}"))
        bot.edit_message_text("📘 Select Class:", chat_id, message_id, reply_markup=kb)

    elif parts[0] == "STD":
        cls = parts[1]
        subjects = DATA.get(cls, {})
        kb = types.InlineKeyboardMarkup()
        for sub in subjects.keys():
            kb.add(types.InlineKeyboardButton(text=sub, callback_data=f"SUB|{cls}|{sub}"))
        kb.add(types.InlineKeyboardButton("⬅️ Back", callback_data="BACK_MAIN"))
        bot.edit_message_text(f"📘 {cls} → Subject:", chat_id, message_id, reply_markup=kb)

    elif parts[0] == "SUB":
        cls, sub = parts[1], parts[2]
        tests = DATA[cls][sub]
        kb = types.InlineKeyboardMarkup()
        for i, t in enumerate(tests):
            kb.add(types.InlineKeyboardButton(text=f"📝 {t['label']}", callback_data=f"OPEN|{cls}|{sub}|{i}"))
        kb.add(types.InlineKeyboardButton("⬅️ Back", callback_data=f"STD|{cls}"))
        bot.edit_message_text(f"🧪 {cls} → {sub}:", chat_id, message_id, reply_markup=kb)

    elif parts[0] == "OPEN":
        cls, sub, idx = parts[1], parts[2], int(parts[3])
        full_url = f"{WEB_URL}{DATA[cls][sub][idx]['path']}"
        bot.answer_callback_query(call.id, url=full_url)

# ---------------- HEALTH SERVER ----------------
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"OK")

threading.Thread(target=lambda: HTTPServer(("0.0.0.0", 8000), HealthHandler).serve_forever(), daemon=True).start()

logging.basicConfig(level=logging.INFO)
bot.infinity_polling()
