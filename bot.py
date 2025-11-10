# bot.py — My Study Bot (Inline JSON + Channel Join)
import os
import time
import logging
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import telebot
from telebot import types
import requests

# ---------------- CONFIG ----------------
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@YourChannelUsername")  # channel for join
DATA_JSON = os.getenv("DATA_JSON", "data.json")  # local JSON file
WEB_URL = os.getenv("WEB_URL", "https://hdhdhsjsjsjdjsjshdjdhdjdjdjdu.netlify.app/")

bot = telebot.TeleBot(BOT_TOKEN)
OWNER_ID = int(os.getenv("OWNER_ID", "7447651332"))
# ---------------------------------------

# ---------- HEALTH CHECK SERVER ----------
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type","text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_server():
    server = HTTPServer(("0.0.0.0", 8000), HealthHandler)
    logging.info("✅ Health check server running on port 8000")
    server.serve_forever()

threading.Thread(target=run_health_server, daemon=True).start()
# ---------------------------------------

# ---------- LOAD JSON DATA --------------
def load_data():
    try:
        with open(DATA_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        logging.info("✅ JSON data loaded")
        return data
    except Exception as e:
        logging.error(f"❌ Failed to load data.json: {e}")
        return {}
# ---------------------------------------

# ---------- START / MENU HANDLER ----------
@bot.message_handler(commands=['start'])
def start_menu(msg):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_ID.strip('@')}"))
    data = load_data()
    for std in data.keys():
        kb.add(types.InlineKeyboardButton(text=std, callback_data=f"STD|{std}"))
    bot.send_message(msg.chat.id, "📘 Select Class:", reply_markup=kb)

# ---------- CALLBACK HANDLER ----------
@bot.callback_query_handler(func=lambda c: True)
def callback_handler(call):
    try:
        data = load_data()
        parts = call.data.split("|")

        if parts[0] == "STD":
            std = parts[1]
            kb = types.InlineKeyboardMarkup()
            for subject in data[std].keys():
                kb.add(types.InlineKeyboardButton(
                    text=subject, callback_data=f"SUBJECT|{std}|{subject}"))
            kb.add(types.InlineKeyboardButton("⬅️ Back", callback_data="BACK_MAIN"))
            bot.edit_message_text(f"📚 {std} → Select Subject:",
                                  call.message.chat.id,
                                  call.message.message_id,
                                  reply_markup=kb)

        elif parts[0] == "SUBJECT":
            std, subject = parts[1], parts[2]
            tests = data[std][subject]
            kb = types.InlineKeyboardMarkup()
            for t in tests:
                label = t["label"]
                path = t["path"].replace(".html","")  # remove extension for Netlify
                folder = t["path"].split("/")[0]
                url = f"{WEB_URL}{folder}/{path.split('/')[-1]}"
                kb.add(types.InlineKeyboardButton(text=label, web_app=types.WebAppInfo(url)))
            kb.add(types.InlineKeyboardButton("⬅️ Back", callback_data=f"STD|{std}"))
            bot.edit_message_text(f"🧪 {std} → {subject} → Select Test:",
                                  call.message.chat.id,
                                  call.message.message_id,
                                  reply_markup=kb)

        elif parts[0] == "BACK_MAIN":
            kb = types.InlineKeyboardMarkup()
            for std in data.keys():
                kb.add(types.InlineKeyboardButton(text=std, callback_data=f"STD|{std}"))
            kb.add(types.InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_ID.strip('@')}"))
            bot.edit_message_text("📘 Select Class:",
                                  call.message.chat.id,
                                  call.message.message_id,
                                  reply_markup=kb)
        else:
            bot.answer_callback_query(call.id, "⚠️ Unknown action")
    except Exception as e:
        logging.error(f"Callback error: {e}")
        bot.answer_callback_query(call.id, "⚠️ Something went wrong")

# ---------- HELP ----------
@bot.message_handler(commands=['help'])
def help_cmd(msg):
    text = (
        "📚 *My Study Bot Help*\n\n"
        "• /start - Show main menu\n"
        "• /help - This help message\n"
        "• Click 'Join Channel' to get updates\n"
        "• Tests open directly in Web App via JSON paths"
    )
    bot.send_message(msg.chat.id, text, parse_mode="Markdown")

# ---------- BOT POLLING ----------
if __name__ == "__main__":
    logging.info("🤖 Bot started, polling...")
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=50)
        except Exception as e:
            logging.error(f"Polling error: {e}")
            time.sleep(5)