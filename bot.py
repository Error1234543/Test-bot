
import os
import json
import telebot
from telebot import types
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import logging

# ---------------- CONFIG ----------------
BOT_TOKEN = "YOUR_BOT_TOKEN"
WEB_URL = "https://oldxhdjshshshs.netlify.app/"
OWNER_ID = 8226637107

TELEGRAM_LINK = "https://t.me/+NGUSfa7ns8c4OTll"

bot = telebot.TeleBot(BOT_TOKEN)

# ---------------- STORAGE ----------------
def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r") as f:
            return set(json.load(f))
    return set(default)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(list(data), f)

verified_users = load_json("verified.json", set())
banned_users = load_json("banned.json", set())

# ---------------- DATA ----------------
try:
    with open("data.json", "r") as f:
        DATA = json.load(f)
except:
    DATA = {}

# ---------------- BAN ----------------
@bot.message_handler(commands=['ban'])
def ban_user(msg):
    if msg.from_user.id != OWNER_ID:
        return
    try:
        uid = int(msg.text.split()[1])
        banned_users.add(uid)
        save_json("banned.json", banned_users)
        bot.reply_to(msg, f"🚫 User {uid} banned")
    except:
        bot.reply_to(msg, "Usage: /ban USER_ID")

# ---------------- UNBAN ----------------
@bot.message_handler(commands=['unban'])
def unban_user(msg):
    if msg.from_user.id != OWNER_ID:
        return
    try:
        uid = int(msg.text.split()[1])
        banned_users.discard(uid)
        save_json("banned.json", banned_users)
        bot.reply_to(msg, f"✅ User {uid} unbanned")
    except:
        bot.reply_to(msg, "Usage: /unban USER_ID")

# ---------------- START (IMAGE MESSAGE) ----------------
@bot.message_handler(commands=['start'])
def start_menu(msg):
    uid = msg.from_user.id

    if uid in banned_users:
        bot.send_message(msg.chat.id, "🚫 You are banned from this bot.")
        return

    # already verified → direct menu
    if uid in verified_users:
        show_main_menu(msg.chat.id)
        return

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("📢 Join Channel", url=TELEGRAM_LINK))
    kb.add(types.InlineKeyboardButton("✔️ I Have Joined", callback_data="VERIFY"))

    caption = (
        "🎯 *NEET Gujarati Test Bot 2026*\n\n"
        "📚 Yaha aapko milenge:\n\n"
        "🧪 NEET 2026 Mock Tests\n"
        "📘 Board Based Tests\n"
        "📖 Subject Wise Tests\n"
        "📊 Chapter Wise 5+ Tests\n"
        "🔥 Har Subject me 200+ Practice Tests\n\n"
        "💡 Perfect preparation for NEET (Gujarati Medium)\n\n"
        "👇 Pehle channel join karo aur verify karo\n\n"
        "https://t.me/+NGUSfa7ns8c4OTll\n\n"
        "✔️ Verify joined you 👇"
    )

    with open("image.jpg", "rb") as img:
        bot.send_photo(
            msg.chat.id,
            img,
            caption=caption,
            reply_markup=kb,
            parse_mode="Markdown"
        )

# ---------------- VERIFY ----------------
@bot.callback_query_handler(func=lambda c: c.data == "VERIFY")
def verify_user(call):
    uid = call.from_user.id

    if uid in banned_users:
        bot.answer_callback_query(call.id, "You are banned!")
        return

    verified_users.add(uid)
    save_json("verified.json", verified_users)

    bot.answer_callback_query(call.id, "Verified!")
    show_main_menu(call.message.chat.id)

# ---------------- MAIN MENU ----------------
def show_main_menu(chat_id):
    kb = types.InlineKeyboardMarkup()
    for cls in DATA.keys():
        kb.add(types.InlineKeyboardButton(cls, callback_data=f"STD|{cls}"))
    bot.send_message(chat_id, "📘 Select Class:", reply_markup=kb)

# ---------------- CALLBACK ----------------
@bot.callback_query_handler(func=lambda c: True)
def callback_handler(call):
    uid = call.from_user.id

    if uid in banned_users:
        bot.answer_callback_query(call.id, "Banned")
        return

    parts = call.data.split("|")
    chat_id = call.message.chat.id
    mid = call.message.message_id

    if call.data == "BACK_MAIN":
        show_main_menu(chat_id)

    elif parts[0] == "STD":
        cls = parts[1]
        kb = types.InlineKeyboardMarkup()
        for sub in DATA.get(cls, {}).keys():
            kb.add(types.InlineKeyboardButton(sub, callback_data=f"SUB|{cls}|{sub}"))
        kb.add(types.InlineKeyboardButton("⬅️ Back", callback_data="BACK_MAIN"))
        bot.edit_message_text(f"📘 {cls} → Select Subject:", chat_id, mid, reply_markup=kb)

    elif parts[0] == "SUB":
        cls, sub = parts[1], parts[2]
        kb = types.InlineKeyboardMarkup()
        for i, t in enumerate(DATA[cls][sub]):
            kb.add(types.InlineKeyboardButton(
                f"📝 {t['label']}",
                callback_data=f"OPEN|{cls}|{sub}|{i}"
            ))
        kb.add(types.InlineKeyboardButton("⬅️ Back", callback_data=f"STD|{cls}"))
        bot.edit_message_text(f"🧪 {cls} → {sub}:", chat_id, mid, reply_markup=kb)

    elif parts[0] == "OPEN":
        cls, sub, idx = parts[1], parts[2], int(parts[3])
        test = DATA[cls][sub][idx]
        url = f"{WEB_URL}{test['path']}"

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(
            f"🚀 Open {test['label']}",
            web_app=types.WebAppInfo(url=url)
        ))

        bot.send_message(chat_id, f"✅ {test['label']} ready!", reply_markup=kb)
        bot.answer_callback_query(call.id)

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