import os
import json
import telebot
from telebot import types
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import logging

# ---------------- CONFIG ----------------
BOT_TOKEN = "8510670200:AAGN0wkvB8yYOOvsU3Jrf4pWAS5q0zR3CGI"
WEB_URL = "https://hdhdhsjsjsjdjsjshdjdhdjdjdjdu.netlify.app/"  # GitHub Pages URL

bot = telebot.TeleBot(BOT_TOKEN)

# Load data.json
with open("data.json", "r") as f:
    DATA = json.load(f)

# ---------------- HEALTH CHECK SERVER ----------------
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")  # Simple response for health check

def run_health_server():
    server = HTTPServer(("0.0.0.0", 8000), HealthHandler)
    logging.info("Health-check server running on port 8000")
    server.serve_forever()

# Start health server in a separate thread
threading.Thread(target=run_health_server, daemon=True).start()

# ---------------- TELEGRAM BOT ----------------
@bot.message_handler(commands=['start'])
def start_menu(msg):
    kb = types.InlineKeyboardMarkup()
    for cls in DATA.keys():
        kb.add(types.InlineKeyboardButton(text=cls, callback_data=f"STD|{cls}"))
    bot.send_message(msg.chat.id, "📘 Select Class:", reply_markup=kb)


@bot.callback_query_handler(func=lambda c: True)
def callback_handler(call):
    parts = call.data.split("|")

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
logging.info("🤖 Bot started. Health server running on port 8000.")
bot.infinity_polling()