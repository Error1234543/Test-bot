import os
import json
import telebot
from telebot import types
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import logging

# ---------------- CONFIG ----------------
BOT_TOKEN = "8510670200:AAGN0wkvB8yYOOvsU3Jrf4pWAS5q0zR3CGI"
WEB_URL = "https://hdhdhsjsjsjdjsjshdjdhdjdjdjdu.netlify.app/"
OWNER_ID = 7447651332  # Your Telegram ID
AUTHORIZED_USERS_FILE = "authorized.json"

# Telegram channel & WhatsApp group links
TELEGRAM_CHANNEL = "@NEET_JEE_GUJ"
WHATSAPP_LINK = "t.me/NEET_JEE_GUJ"

bot = telebot.TeleBot(BOT_TOKEN)

# Load data.json
with open("data.json", "r") as f:
    DATA = json.load(f)

# Load authorized users
if os.path.exists(AUTHORIZED_USERS_FILE):
    with open(AUTHORIZED_USERS_FILE, "r") as f:
        AUTH_USERS = json.load(f)
else:
    AUTH_USERS = []

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

# ---------------- AUTH HELPER ----------------
def is_authorized(user_id):
    return user_id in AUTH_USERS or user_id == OWNER_ID

def save_auth_users():
    with open(AUTHORIZED_USERS_FILE, "w") as f:
        json.dump(AUTH_USERS, f)

# ---------------- TELEGRAM BOT ----------------
@bot.message_handler(commands=['start'])
def start_menu(msg):
    chat_id = msg.chat.id
    user_id = msg.from_user.id

    if not is_authorized(user_id):
        bot.send_message(chat_id,
                         "🚫 Access Denied\n\nYou do not have permanent access.\nContact Owner: T.me/sonic8307")
        return

    # Show join buttons + dismiss
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✅ Join Telegram Channel", url=f"https://t.me/{TELEGRAM_CHANNEL.lstrip('@')}"))
    kb.add(types.InlineKeyboardButton("✅ Join WhatsApp Group", url=WHATSAPP_LINK))
    kb.add(types.InlineKeyboardButton("❌ Dismiss", callback_data="DISMISS_JOIN"))

    bot.send_message(chat_id,
                     "📢 You must join our Telegram Channel and/or WhatsApp Group to access the tests.\n\nAfter joining, press the button below:",
                     reply_markup=kb)

# ---------------- ADD/REMOVE USERS ----------------
@bot.message_handler(commands=['adduser'])
def add_user(msg):
    if msg.from_user.id != OWNER_ID:
        return
    parts = msg.text.split()
    if len(parts) != 2:
        bot.reply_to(msg, "Usage: /adduser <user_id>")
        return
    try:
        user_id = int(parts[1])
        if user_id not in AUTH_USERS:
            AUTH_USERS.append(user_id)
            save_auth_users()
            bot.reply_to(msg, f"✅ User {user_id} added successfully.")
        else:
            bot.reply_to(msg, "User already authorized.")
    except:
        bot.reply_to(msg, "Invalid user ID.")

@bot.message_handler(commands=['removeuser'])
def remove_user(msg):
    if msg.from_user.id != OWNER_ID:
        return
    parts = msg.text.split()
    if len(parts) != 2:
        bot.reply_to(msg, "Usage: /removeuser <user_id>")
        return
    try:
        user_id = int(parts[1])
        if user_id in AUTH_USERS:
            AUTH_USERS.remove(user_id)
            save_auth_users()
            bot.reply_to(msg, f"❌ User {user_id} removed successfully.")
        else:
            bot.reply_to(msg, "User not found in authorized list.")
    except:
        bot.reply_to(msg, "Invalid user ID.")

# ---------------- CALLBACK HANDLER ----------------
@bot.callback_query_handler(func=lambda c: True)
def callback_handler(call):
    if not is_authorized(call.from_user.id):
        bot.answer_callback_query(call.id, "🚫 Access Denied", show_alert=True)
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
        bot.edit_message_text(f"📘 {cls} → Select Subject:", call.message.chat.id,
                              call.message.message_id, reply_markup=kb)

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
        bot.edit_message_text(f"🧪 {cls} → {sub} → Select Test:", call.message.chat.id,
                              call.message.message_id, reply_markup=kb)

    elif parts[0] == "BACK_MAIN":
        kb = types.InlineKeyboardMarkup()
        for cls in DATA.keys():
            kb.add(types.InlineKeyboardButton(text=cls, callback_data=f"STD|{cls}"))
        bot.edit_message_text("📘 Select Class:", call.message.chat.id,
                              call.message.message_id, reply_markup=kb)

# ---------------- START BOT ----------------
logging.basicConfig(level=logging.INFO)
logging.info("🤖 Bot started. Health server running on port 8000.")
bot.infinity_polling()