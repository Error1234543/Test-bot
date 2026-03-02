import os
import json
import telebot
from telebot import types
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import logging

# ---------------- CONFIG ----------------
BOT_TOKEN = "8585007953:AAEqP3K3_5y43YRoYc4h99Lzlg9uE-1rAHo"
OWNER_ID = 7447651332  # <-- Apna Telegram ID

WEB_URL = "https://hdhdhsjsjsjdjsjshdjdhdjdjdjdu.netlify.app/"

TELEGRAM_CHANNEL = "@NEET_JEE_GUJ"
WHATSAPP_LINK = "https://t.me/NEET_JEE_GUJ"

bot = telebot.TeleBot(BOT_TOKEN)

# ---------------- ACCESS STORAGE ----------------
ACCESS_FILE = "access.json"

if not os.path.exists(ACCESS_FILE):
    with open(ACCESS_FILE, "w") as f:
        json.dump([], f)

def load_access():
    with open(ACCESS_FILE, "r") as f:
        return json.load(f)

def save_access(data):
    with open(ACCESS_FILE, "w") as f:
        json.dump(data, f)

def has_access(user_id):
    access_list = load_access()
    return user_id in access_list or user_id == OWNER_ID

# ---------------- LOAD DATA ----------------
with open("data.json", "r") as f:
    DATA = json.load(f)

# ---------------- HEALTH CHECK SERVER ----------------
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_server():
    server = HTTPServer(("0.0.0.0", 8000), HealthHandler)
    logging.info("Health-check server running on port 8000")
    server.serve_forever()

threading.Thread(target=run_health_server, daemon=True).start()

# ---------------- START COMMAND ----------------
@bot.message_handler(commands=['start'])
def start_menu(msg):
    user_id = msg.from_user.id
    chat_id = msg.chat.id

    if not has_access(user_id):
        bot.send_message(
            chat_id,
            "🚫 This Bot is Private!\n\n"
            "🔐 Get access for this bot contact with me:\n"
            "👉 t.me/spidy_x100\n\n"
            "💰 Price: 100 Rupees"
        )
        return

    # Original join system (same as before)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✅ Join Telegram Channel", url=f"https://t.me/{TELEGRAM_CHANNEL.lstrip('@')}"))
    kb.add(types.InlineKeyboardButton("✅ Join WhatsApp Group", url=WHATSAPP_LINK))
    kb.add(types.InlineKeyboardButton("❌ Continue", callback_data="DISMISS_JOIN"))

    bot.send_message(chat_id,
                     "📢 Join our Channel/Group then press Continue:",
                     reply_markup=kb)

# ---------------- ADD USER ----------------
@bot.message_handler(commands=['add'])
def add_user(msg):
    if msg.from_user.id != OWNER_ID:
        return

    try:
        user_id = int(msg.text.split()[1])
        access_list = load_access()

        if user_id not in access_list:
            access_list.append(user_id)
            save_access(access_list)
            bot.reply_to(msg, f"✅ User {user_id} Added Successfully!")
        else:
            bot.reply_to(msg, "⚠️ User Already Has Access.")

    except:
        bot.reply_to(msg, "❌ Usage:\n/add user_id")

# ---------------- REMOVE USER ----------------
@bot.message_handler(commands=['remove'])
def remove_user(msg):
    if msg.from_user.id != OWNER_ID:
        return

    try:
        user_id = int(msg.text.split()[1])
        access_list = load_access()

        if user_id in access_list:
            access_list.remove(user_id)
            save_access(access_list)
            bot.reply_to(msg, f"❌ User {user_id} Removed!")
        else:
            bot.reply_to(msg, "⚠️ User Not Found.")

    except:
        bot.reply_to(msg, "❌ Usage:\n/remove user_id")

# ---------------- CALLBACK HANDLER ----------------
@bot.callback_query_handler(func=lambda c: True)
def callback_handler(call):

    if not has_access(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ You don't have access!")
        return

    parts = call.data.split("|")

    if call.data == "DISMISS_JOIN":
        kb = types.InlineKeyboardMarkup()
        for cls in DATA.keys():
            kb.add(types.InlineKeyboardButton(text=cls, callback_data=f"STD|{cls}"))
        bot.edit_message_text("📘 Select Class:", call.message.chat.id,
                              call.message.message_id, reply_markup=kb)
        return

    if parts[0] == "STD":
        cls = parts[1]
        subjects = DATA.get(cls, {})
        kb = types.InlineKeyboardMarkup()
        for sub in subjects.keys():
            kb.add(types.InlineKeyboardButton(
                text=sub, callback_data=f"SUBJECT|{cls}|{sub}"
            ))
        kb.add(types.InlineKeyboardButton("⬅️ Back", callback_data="BACK_MAIN"))
        bot.edit_message_text(f"📘 {cls} → Select Subject:",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=kb)

    elif parts[0] == "SUBJECT":
        cls, sub = parts[1], parts[2]
        tests = DATA[cls][sub]
        kb = types.InlineKeyboardMarkup()
        for t in tests:
            kb.add(types.InlineKeyboardButton(
                text=t["label"],
                web_app=types.WebAppInfo(WEB_URL + t["path"])
            ))
        kb.add(types.InlineKeyboardButton("⬅️ Back", callback_data=f"STD|{cls}"))
        bot.edit_message_text(f"🧪 {cls} → {sub} → Select Test:",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=kb)

    elif parts[0] == "BACK_MAIN":
        kb = types.InlineKeyboardMarkup()
        for cls in DATA.keys():
            kb.add(types.InlineKeyboardButton(text=cls, callback_data=f"STD|{cls}"))
        bot.edit_message_text("📘 Select Class:",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=kb)

# ---------------- START BOT ----------------
logging.basicConfig(level=logging.INFO)
logging.info("🤖 Private Bot Started")
bot.infinity_polling()