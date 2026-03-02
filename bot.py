import os
import json
import telebot
from telebot import types
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import logging

# ---------------- CONFIG ----------------
# ⚠️ WARNING: Naya token yahan daalein!
BOT_TOKEN = "8585007953:AAEqP3K3_5y43YRoYc4h99Lzlg9uE-1rAHo"
WEB_URL = https://oldxhdj.netlify.app/"
OWNER_ID = 8226637107  # Aapki ID

TELEGRAM_CHANNEL = "@NEET_JEE_GUJ"
WHATSAPP_LINK = "https://t.me/NEET_JEE_GUJ"

bot = telebot.TeleBot(BOT_TOKEN)

# ---------------- DATA PERSISTENCE ----------------
# Allowed users load/save karne ke liye
def load_allowed_users():
    if os.path.exists("users.json"):
        with open("users.json", "r") as f:
            return set(json.load(f))
    return {OWNER_ID}  # By default owner allowed hai

def save_allowed_users(users_set):
    with open("users.json", "w") as f:
        json.dump(list(users_set), f)

ALLOWED_USERS = load_allowed_users()

# Load data.json (Tests data)
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
        bot.reply_to(msg, f"✅ User {new_id} ko access de diya gaya hai.")
    except (IndexError, ValueError):
        bot.reply_to(msg, "❌ Sahi format use karein: `/add 123456789`")

@bot.message_handler(commands=['remove'])
def remove_user(msg):
    if msg.from_user.id != OWNER_ID:
        return
    
    try:
        target_id = int(msg.text.split()[1])
        if target_id == OWNER_ID:
            bot.reply_to(msg, "❌ Aap khud ko remove nahi kar sakte!")
            return
            
        if target_id in ALLOWED_USERS:
            ALLOWED_USERS.remove(target_id)
            save_allowed_users(ALLOWED_USERS)
            bot.reply_to(msg, f"🗑️ User {target_id} ka access hata diya gaya hai.")
        else:
            bot.reply_to(msg, "❌ Ye user list mein nahi hai.")
    except (IndexError, ValueError):
        bot.reply_to(msg, "❌ Sahi format use karein: `/remove 123456789`")

@bot.message_handler(commands=['list'])
def list_users(msg):
    if msg.from_user.id != OWNER_ID:
        return
    users_list = "\n".join([str(u) for u in ALLOWED_USERS])
    bot.reply_to(msg, f"👥 **Allowed Users:**\n{users_list}")

# ---------------- TELEGRAM BOT LOGIC ----------------

@bot.message_handler(commands=['start'])
def start_menu(msg):
    user_id = msg.from_user.id
    
    # Access Check
    if user_id not in ALLOWED_USERS:
        bot.send_message(user_id, "🚫 **Access Denied!**\nAapko ye bot use karne ki permission nahi hai. Admin se contact karein.")
        return

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✅ Join Telegram", url=f"https://t.me/{TELEGRAM_CHANNEL.lstrip('@')}"))
    kb.add(types.InlineKeyboardButton("✅ Join WhatsApp", url=WHATSAPP_LINK))
    kb.add(types.InlineKeyboardButton("🚀 Start Mock Test", callback_data="SHOW_CLASSES"))

    bot.send_message(user_id, "👋 Welcome back! Niche diye gaye button se test shuru karein.", reply_markup=kb)

# ---------------- CALLBACK HANDLER ----------------

@bot.callback_query_handler(func=lambda c: True)
def callback_handler(call):
    user_id = call.from_user.id
    
    # Security Check: Har click par check karega user allowed hai ya nahi
    if user_id not in ALLOWED_USERS:
        bot.answer_callback_query(call.id, "❌ Access Revoked!", show_alert=True)
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
        bot.edit_message_text(f"📘 {cls} → Select Subject:", chat_id, message_id, reply_markup=kb)

    elif parts[0] == "SUB":
        cls, sub = parts[1], parts[2]
        tests = DATA[cls][sub]
        kb = types.InlineKeyboardMarkup()
        for i, t in enumerate(tests):
            kb.add(types.InlineKeyboardButton(text=f"📝 {t['label']}", callback_data=f"OPEN|{cls}|{sub}|{i}"))
        kb.add(types.InlineKeyboardButton("⬅️ Back", callback_data=f"STD|{cls}"))
        bot.edit_message_text(f"🧪 {cls} → {sub} → Select Test:", chat_id, message_id, reply_markup=kb)

    elif parts[0] == "OPEN":
        cls, sub, idx = parts[1], parts[2], int(parts[3])
        full_url = f"{WEB_URL}{DATA[cls][sub][idx]['path']}"
        # URL Protection method
        bot.answer_callback_query(call.id, url=full_url)

# ---------------- HEALTH CHECK & START ----------------
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"OK")

def run_health_server():
    HTTPServer(("0.0.0.0", 8000), HealthHandler).serve_forever()

threading.Thread(target=run_health_server, daemon=True).start()
logging.basicConfig(level=logging.INFO)
print("🤖 Admin Bot is running...")
bot.infinity_polling()
