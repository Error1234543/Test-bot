import os
import json
import telebot
from telebot import types
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import logging

# ---------------- CONFIG ----------------
BOT_TOKEN = "YOUR_BOT_TOKEN"
WEB_URL = "https://i.ibb.co/7tShY3Z7/x.jpg"
OWNER_ID = 8226637107  

CHANNEL_LINK = "https://t.me/+NGUSfa7ns8c4OTll"
CHANNEL_USERNAME = "@NEET_JEE_GUJ"  # verify ke liye

START_IMAGE = "https://i.ibb.co/your-image.jpg"  # 🔁 baad me replace kar dena

bot = telebot.TeleBot(BOT_TOKEN)

# ---------------- DATA ----------------
try:
    with open("data.json", "r") as f:
        DATA = json.load(f)
except:
    DATA = {}

# ---------------- START ----------------
@bot.message_handler(commands=['start'])
def start_menu(msg):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK))
    kb.add(types.InlineKeyboardButton("✅ Verify Joined", callback_data="VERIFY"))

    caption = """🎯 **NEET Gujarati Test Bot 2026**

📚 Yaha aapko milenge:

🧪 NEET 2026 Mock Tests  
📘 Board Based Tests  
📖 Subject Wise Tests  
📊 Chapter Wise 5+ Tests  
🔥 Har Subject me 200+ Practice Tests  

💡 Perfect preparation for NEET aspirants (Gujarati Medium)

👇 Pehle channel join karo aur verify karo fir tests access karo."""

    bot.send_photo(msg.chat.id, START_IMAGE, caption=caption, reply_markup=kb)

# ---------------- VERIFY ----------------
@bot.callback_query_handler(func=lambda c: c.data == "VERIFY")
def verify_user(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ["member", "administrator", "creator"]:
            bot.answer_callback_query(call.id, "✅ Verified Successfully!")

            show_main_menu(chat_id, call.message.message_id)

        else:
            bot.answer_callback_query(call.id, "❌ Join Channel First!", show_alert=True)

    except:
        bot.answer_callback_query(call.id, "⚠️ Error checking membership", show_alert=True)

# ---------------- MAIN MENU ----------------
def show_main_menu(chat_id, mid):
    kb = types.InlineKeyboardMarkup()
    for cls in DATA.keys():
        kb.add(types.InlineKeyboardButton(text=cls, callback_data=f"STD|{cls}"))

    bot.edit_message_caption(
        "📘 Select Your Category:",
        chat_id,
        mid,
        reply_markup=kb
    )

# ---------------- CALLBACK ----------------
@bot.callback_query_handler(func=lambda c: True)
def callback_handler(call):
    parts = call.data.split("|")
    chat_id = call.message.chat.id
    mid = call.message.message_id

    if call.data.startswith("STD"):
        cls = parts[1]
        kb = types.InlineKeyboardMarkup()
        for sub in DATA.get(cls, {}).keys():
            kb.add(types.InlineKeyboardButton(text=sub, callback_data=f"SUB|{cls}|{sub}"))
        kb.add(types.InlineKeyboardButton("⬅️ Back", callback_data="BACK_MAIN"))

        bot.edit_message_caption(f"📘 {cls} → Select Subject:", chat_id, mid, reply_markup=kb)

    elif call.data.startswith("SUB"):
        cls, sub = parts[1], parts[2]
        kb = types.InlineKeyboardMarkup()
        for i, t in enumerate(DATA[cls][sub]):
            kb.add(types.InlineKeyboardButton(text=f"📝 {t['label']}", callback_data=f"OPEN|{cls}|{sub}|{i}"))
        kb.add(types.InlineKeyboardButton("⬅️ Back", callback_data=f"STD|{cls}"))

        bot.edit_message_caption(f"🧪 {cls} → {sub}:", chat_id, mid, reply_markup=kb)

    elif call.data.startswith("OPEN"):
        cls, sub, idx = parts[1], parts[2], int(parts[3])
        test_data = DATA[cls][sub][idx]
        full_url = f"{WEB_URL}{test_data['path']}"

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(
            text=f"🚀 Open {test_data['label']}",
            web_app=types.WebAppInfo(url=full_url)
        ))

        bot.send_message(chat_id, f"✅ Test Ready: **{test_data['label']}**\nClick below to start:", reply_markup=kb)
        bot.answer_callback_query(call.id)

    elif call.data == "BACK_MAIN":
        show_main_menu(chat_id, mid)

# ---------------- SERVER ----------------
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

threading.Thread(
    target=lambda: HTTPServer(("0.0.0.0", 8000), H).serve_forever(),
    daemon=True
).start()

logging.basicConfig(level=logging.INFO)
bot.infinity_polling()