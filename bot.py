import os
import json
import telebot
from telebot import types
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import logging

# ---------------- CONFIG ----------------
BOT_TOKEN = "8585007953:AAEqP3K3_5y43YRoYc4h99Lzlg9uE-1rAHo"
WEB_URL = "https://oldxhdjshshshs.netlify.app/"
OWNER_ID = 8226637107  

TELEGRAM_CHANNEL = "@NEET_JEE_GUJ"
WHATSAPP_LINK = "https://t.me/NEET_JEE_GUJ"

bot = telebot.TeleBot(BOT_TOKEN)

# ---------------- DATA LOADING ----------------
# Users list load karna
def load_allowed_users():
    if os.path.exists("users.json"):
        with open("users.json", "r") as f:
            return set(json.load(f))
    return {OWNER_ID}

def save_allowed_users(users_set):
    with open("users.json", "w") as f:
        json.dump(list(users_set), f)

ALLOWED_USERS = load_allowed_users()

# data.json se tests load karna
try:
    with open("data.json", "r") as f:
        DATA = json.load(f)
except Exception as e:
    logging.error(f"Error loading data.json: {e}")
    DATA = {}

# ---------------- ADMIN COMMANDS ----------------
@bot.message_handler(commands=['add'])
def add_user(msg):
    if msg.from_user.id != OWNER_ID: return
    try:
        new_id = int(msg.text.split()[1])
        ALLOWED_USERS.add(new_id)
        save_allowed_users(ALLOWED_USERS)
        bot.reply_to(msg, f"✅ User {new_id} added successfully!")
    except: bot.reply_to(msg, "Usage: `/add USER_ID`")

@bot.message_handler(commands=['remove'])
def remove_user(msg):
    if msg.from_user.id != OWNER_ID: return
    try:
        uid = int(msg.text.split()[1])
        if uid in ALLOWED_USERS:
            ALLOWED_USERS.remove(uid)
            save_allowed_users(ALLOWED_USERS)
            bot.reply_to(msg, f"🗑️ User {uid} access removed.")
    except: bot.reply_to(msg, "Usage: `/remove USER_ID`")

# ---------------- MAIN BOT LOGIC ----------------
@bot.message_handler(commands=['start'])
def start_menu(msg):
    user_id = msg.from_user.id
    if user_id not in ALLOWED_USERS:
        bot.send_message(msg.chat.id, "🚫 **Access Denied!**\nContact Admin for access.")
        return

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{TELEGRAM_CHANNEL.lstrip('@')}"))
    kb.add(types.InlineKeyboardButton("🚀 Start Mock Test", callback_data="BACK_MAIN"))
    
    bot.send_message(msg.chat.id, "👋 Welcome! Press the button to see classes.", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: True)
def callback_handler(call):
    if call.from_user.id not in ALLOWED_USERS:
        bot.answer_callback_query(call.id, "No Access", show_alert=True)
        return

    parts = call.data.split("|")
    chat_id = call.message.chat.id
    mid = call.message.message_id

    # 1. Main Classes (data.json ki keys)
    if call.data == "BACK_MAIN":
        kb = types.InlineKeyboardMarkup()
        for cls in DATA.keys():
            kb.add(types.InlineKeyboardButton(text=cls, callback_data=f"STD|{cls}"))
        bot.edit_message_text("📘 Select Class:", chat_id, mid, reply_markup=kb)

    # 2. Subjects
    elif parts[0] == "STD":
        cls = parts[1]
        kb = types.InlineKeyboardMarkup()
        for sub in DATA.get(cls, {}).keys():
            kb.add(types.InlineKeyboardButton(text=sub, callback_data=f"SUB|{cls}|{sub}"))
        kb.add(types.InlineKeyboardButton("⬅️ Back", callback_data="BACK_MAIN"))
        bot.edit_message_text(f"📘 {cls} → Select Subject:", chat_id, mid, reply_markup=kb)

    # 3. Test List
    elif parts[0] == "SUB":
        cls, sub = parts[1], parts[2]
        kb = types.InlineKeyboardMarkup()
        for i, t in enumerate(DATA[cls][sub]):
            # Yahan hum direct URL nahi daal rahe, sirf callback trigger kar rahe hain
            kb.add(types.InlineKeyboardButton(text=f"📝 {t['label']}", callback_data=f"OPEN|{cls}|{sub}|{i}"))
        kb.add(types.InlineKeyboardButton("⬅️ Back", callback_data=f"STD|{cls}"))
        bot.edit_message_text(f"🧪 {cls} → {sub}:", chat_id, mid, reply_markup=kb)

    # 4. WebApp Opening (Hidden Link Method)
    elif parts[0] == "OPEN":
        cls, sub, idx = parts[1], parts[2], int(parts[3])
        test_data = DATA[cls][sub][idx]
        full_url = f"{WEB_URL}{test_data['path']}"
        
        # Ek naya message bhejenge jisme real WebApp button hoga
        # Isse long press par purana URL leak nahi hoga
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text=f"🚀 Open {test_data['label']}", web_app=types.WebAppInfo(url=full_url)))
        
        bot.send_message(chat_id, f"✅ Test Ready: **{test_data['label']}**\nClick below to start:", reply_markup=kb)
        bot.answer_callback_query(call.id)

# ---------------- HEALTH SERVER ----------------
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK")

threading.Thread(target=lambda: HTTPServer(("0.0.0.0", 8000), H).serve_forever(), daemon=True).start()

logging.basicConfig(level=logging.INFO)
bot.infinity_polling()
