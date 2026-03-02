
import os
import json
import telebot
from telebot import types
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import logging

# ---------------- CONFIG ----------------
BOT_TOKEN = "8271928754:AAHcymB4lNx0xSdkoWQuS3bZosDlSuOvAdk"
WEB_URL = "https://hdhdhsjsjsjdjsjshdjdhdjdjdjdu.netlify.app/"

# Telegram channel & WhatsApp group links
TELEGRAM_CHANNEL = "@NEET_JEE_GUJ"
WHATSAPP_LINK = "https://t.me/NEET_JEE_GUJ"

# Owner ID (replace with your Telegram ID)
OWNER_ID = 
8226637107

bot = telebot.TeleBot(BOT_TOKEN)

# Load data.json
with open("data.json", "r") as f:
    DATA = json.load(f)

# ---------------- ACCESS CONTROL ----------------
ALLOWED_USERS = set()  # in-memory only

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

# ---------------- TELEGRAM BOT ----------------
@bot.message_handler(commands=['start'])
def start_menu(msg):
    chat_id = msg.chat.id

    if chat_id not in ALLOWED_USERS:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("✅ Join Telegram Channel", url=f"https://t.me/{TELEGRAM_CHANNEL.lstrip('@')}"))
        kb.add(types.InlineKeyboardButton("✅ Join WhatsApp Group", url=WHATSAPP_LINK))
        kb.add(types.InlineKeyboardButton("❌ Dismiss", callback_data="DISMISS_JOIN"))

        bot.send_message(chat_id,
                         "📢 You must join our Telegram Channel and/or WhatsApp Group to access the tests.\n\nAfter joining, press the button below:",
                         reply_markup=kb)
    else:
        send_class_menu(chat_id)

# ---------------- ACCESS MANAGEMENT ----------------
@bot.message_handler(commands=['add'])
def add_user(msg):
    if msg.from_user.id != OWNER_ID:
        bot.reply_to(msg, "❌ You are not allowed to add users.")
        return
    try:
        user_id = int(msg.text.split()[1])
        ALLOWED_USERS.add(user_id)
        bot.reply_to(msg, f"✅ User {user_id} added successfully!")
    except:
        bot.reply_to(msg, "Usage: /add <user_id>")

@bot.message_handler(commands=['remove'])
def remove_user(msg):
    if msg.from_user.id != OWNER_ID:
        bot.reply_to(msg, "❌ You are not allowed to remove users.")
        return
    try:
        user_id = int(msg.text.split()[1])
        ALLOWED_USERS.discard(user_id)
        bot.reply_to(msg, f"✅ User {user_id} removed successfully!")
    except:
        bot.reply_to(msg, "Usage: /remove <user_id>")

# ---------------- MENU HELPERS ----------------
def send_class_menu(chat_id, message_id=None):
    kb = types.InlineKeyboardMarkup()
    for cls in DATA.keys():
        kb.add(types.InlineKeyboardButton(text=cls, callback_data=f"STD|{cls}"))
    text = "📘 Select Class:"
    if message_id:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=kb)
    else:
        bot.send_message(chat_id, text, reply_markup=kb)

# ---------------- CALLBACK HANDLER ----------------
@bot.callback_query_handler(func=lambda c: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    if chat_id not in ALLOWED_USERS and call.data != "DISMISS_JOIN":
        bot.answer_callback_query(call.id, "❌ You don't have access.")
        return

    parts = call.data.split("|")

    # ---------------- Dismiss Join ----------------
    if call.data == "DISMISS_JOIN":
        send_class_menu(chat_id, call.message.message_id)
        return

    # ---------------- CLASS SELECTION ----------------
    if parts[0] == "STD":
        cls = parts[1]
        subjects = DATA.get(cls, {})
        kb = types.InlineKeyboardMarkup()
        for sub in subjects.keys():
            kb.add(types.InlineKeyboardButton(
                text=sub, callback_data=f"SUBJECT|{cls}|{sub}"
            ))
        kb.add(types.InlineKeyboardButton("⬅️ Back", callback_data="BACK_MAIN"))
        bot.edit_message_text(f"📘 {cls} → Select Subject:", chat_id,
                              call.message.message_id, reply_markup=kb)

    # ---------------- SUBJECT SELECTION ----------------
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
        bot.edit_message_text(f"🧪 {cls} → {sub} → Select Test:", chat_id,
                              call.message.message_id, reply_markup=kb)

    # ---------------- BACK TO MAIN ----------------
    elif parts[0] == "BACK_MAIN":
        send_class_menu(chat_id, call.message.message_id)

# ---------------- START BOT ----------------
logging.basicConfig(level=logging.INFO)
logging.info("🤖 Bot started. Health server running on port 8000.")
bot.infinity_polling()