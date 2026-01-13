import os
import json
import telebot
from telebot import types
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import logging

# ================= CONFIG =================
BOT_TOKEN = "8271928754:AAHcymB4lNx0xSdkoWQuS3bZosDlSuOvAdk"
WEB_URL = "https://hdhdhsjsjsjdjsjshdjdhdjdjdjdu.netlify.app/"

ADMIN_ID = 8226637107  # 🔴 Apna Telegram ID
AUTHORIZED_FILE = "authorized.json"

TELEGRAM_CHANNEL = "@NEET_JEE_GUJ"
WHATSAPP_LINK = "https://t.me/NEET_JEE_GUJ"

bot = telebot.TeleBot(BOT_TOKEN)

# ================= LOAD DATA =================
with open("data.json", "r") as f:
    DATA = json.load(f)

# ================= AUTH STORAGE =================
if not os.path.exists(AUTHORIZED_FILE):
    with open(AUTHORIZED_FILE, "w") as f:
        json.dump([], f)

def load_auth():
    with open(AUTHORIZED_FILE, "r") as f:
        return json.load(f)

def save_auth(data):
    with open(AUTHORIZED_FILE, "w") as f:
        json.dump(data, f)

# ================= HEALTH SERVER =================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_server():
    HTTPServer(("0.0.0.0", 8000), HealthHandler).serve_forever()

threading.Thread(target=run_health_server, daemon=True).start()

# ================= START COMMAND =================
@bot.message_handler(commands=['start'])
def start_menu(msg):
    user_id = msg.from_user.id
    auth_users = load_auth()

    if user_id not in auth_users:
        bot.send_message(
            msg.chat.id,
            "🚫 **ACCESS DENIED** 🚫\n\n"
            "💰 Pay ₹50 for **Permanent Access**\n"
            "📩 Contact Admin: @xdsonic\n\n"
            "⛔ Without payment you cannot use this bot.",
            parse_mode="Markdown"
        )
        return

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(
        "✅ Join Telegram Channel",
        url=f"https://t.me/{TELEGRAM_CHANNEL.lstrip('@')}"
    ))
    kb.add(types.InlineKeyboardButton(
        "✅ Join WhatsApp Group",
        url=WHATSAPP_LINK
    ))
    kb.add(types.InlineKeyboardButton(
        "➡️ Continue",
        callback_data="CONTINUE"
    ))

    bot.send_message(
        msg.chat.id,
        "✅ **Access Granted!**\n\nJoin & Continue:",
        parse_mode="Markdown",
        reply_markup=kb
    )

# ================= ADD USER =================
@bot.message_handler(commands=['add'])
def add_user(msg):
    if msg.from_user.id != ADMIN_ID:
        return

    try:
        user_id = int(msg.text.split()[1])
        auth = load_auth()

        if user_id not in auth:
            auth.append(user_id)
            save_auth(auth)
            bot.send_message(msg.chat.id, f"✅ User {user_id} authorized")
        else:
            bot.send_message(msg.chat.id, "⚠️ User already authorized")
    except:
        bot.send_message(msg.chat.id, "❌ Usage: /add USER_ID")

# ================= REMOVE USER =================
@bot.message_handler(commands=['remove'])
def remove_user(msg):
    if msg.from_user.id != ADMIN_ID:
        return

    try:
        user_id = int(msg.text.split()[1])
        auth = load_auth()

        if user_id in auth:
            auth.remove(user_id)
            save_auth(auth)
            bot.send_message(
                msg.chat.id,
                f"❌ User {user_id} ka access REMOVE kar diya gaya"
            )
        else:
            bot.send_message(
                msg.chat.id,
                "⚠️ Ye user authorized list me nahi hai"
            )
    except:
        bot.send_message(
            msg.chat.id,
            "❌ Usage: /remove USER_ID"
        )

# ================= CALLBACK HANDLER =================
@bot.callback_query_handler(func=lambda c: True)
def callback_handler(call):
    parts = call.data.split("|")

    # Continue
    if call.data == "CONTINUE":
        kb = types.InlineKeyboardMarkup()
        for cls in DATA.keys():
            kb.add(types.InlineKeyboardButton(
                text=cls,
                callback_data=f"STD|{cls}"
            ))
        bot.edit_message_text(
            "📘 Select Class:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb
        )

    # Class
    elif parts[0] == "STD":
        cls = parts[1]
        kb = types.InlineKeyboardMarkup()
        for sub in DATA[cls]:
            kb.add(types.InlineKeyboardButton(
                text=sub,
                callback_data=f"SUBJECT|{cls}|{sub}"
            ))
        kb.add(types.InlineKeyboardButton(
            "⬅️ Back",
            callback_data="BACK_MAIN"
        ))
        bot.edit_message_text(
            f"📘 {cls} → Select Subject:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb
        )

    # Subject
    elif parts[0] == "SUBJECT":
        cls, sub = parts[1], parts[2]
        kb = types.InlineKeyboardMarkup()
        for t in DATA[cls][sub]:
            kb.add(types.InlineKeyboardButton(
                text=t["label"],
                web_app=types.WebAppInfo(WEB_URL + t["path"])
            ))
        kb.add(types.InlineKeyboardButton(
            "⬅️ Back",
            callback_data=f"STD|{cls}"
        ))
        bot.edit_message_text(
            f"🧪 {cls} → {sub} → Select Test:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb
        )

    # Back Main
    elif call.data == "BACK_MAIN":
        kb = types.InlineKeyboardMarkup()
        for cls in DATA.keys():
            kb.add(types.InlineKeyboardButton(
                text=cls,
                callback_data=f"STD|{cls}"
            ))
        bot.edit_message_text(
            "📘 Select Class:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb
        )

# ================= RUN BOT =================
logging.basicConfig(level=logging.INFO)
logging.info("🤖 Paid Access Test Bot Started")
bot.infinity_polling()