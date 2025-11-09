# bot.py — Telegram Inline Study Bot (JSON Sync Version)
# Created for auto folder/test menu from data.json hosted on web.

import os
import time
import json
import logging
import requests
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import telebot
from telebot import types

# ---------------- BASIC CONFIG ----------------
logging.basicConfig(level=logging.INFO)
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@YOUR_CHANNEL")  # optional, or leave blank
DATA_URL = os.getenv("DATA_URL", "https://hdhdhsjsjsjdjsjshdjdhdjdjdjdu.netlify.app/data.json")
WEB_URL = os.getenv("WEB_URL", "https://hdhdhsjsjsjdjsjshdjdhdjdjdjdu.netlify.app")
OWNER_ID = int(os.getenv("OWNER_ID", "8226637107"))  # your Telegram ID

bot = telebot.TeleBot(BOT_TOKEN)
# ------------------------------------------------


# ---------- HEALTH SERVER for Koyeb -------------
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
# ------------------------------------------------


# ---------- DATA FETCHER ------------------------
def load_data():
    """Fetch JSON data (subjects/tests) from DATA_URL"""
    try:
        r = requests.get(DATA_URL, timeout=10)
        data = r.json()
        logging.info("✅ Data loaded successfully from JSON.")
        return data
    except Exception as e:
        logging.error(f"❌ Error loading data.json: {e}")
        return {}
# ------------------------------------------------


# ---------- INLINE MENU SYSTEM ------------------
@bot.message_handler(commands=['start', 'refresh'])
def start_menu(msg):
    data = load_data()
    if not data:
        bot.reply_to(msg, "⚠️ Unable to load data.json from server.")
        return

    kb = types.InlineKeyboardMarkup()
    for std in data.keys():
        kb.add(types.InlineKeyboardButton(text=std, callback_data=f"STD|{std}"))
    bot.send_message(msg.chat.id, "📘 Select your class:", reply_markup=kb)


@bot.callback_query_handler(func=lambda c: True)
def callback_handler(call):
    try:
        data = load_data()
        parts = call.data.split("|")

        if parts[0] == "STD":  # Level 1 → Show subjects
            std = parts[1]
            if std not in data:
                bot.answer_callback_query(call.id, "No data found.")
                return
            kb = types.InlineKeyboardMarkup()
            for subject in data[std].keys():
                kb.add(types.InlineKeyboardButton(
                    text=subject, callback_data=f"SUBJECT|{std}|{subject}"))
            kb.add(types.InlineKeyboardButton("⬅️ Back", callback_data="BACK_MAIN"))
            bot.edit_message_text(f"📚 {std}\nSelect Subject:",
                                  call.message.chat.id, call.message.message_id, reply_markup=kb)

        elif parts[0] == "SUBJECT":  # Level 2 → Show tests
            std, subject = parts[1], parts[2]
            tests = data.get(std, {}).get(subject, [])
            kb = types.InlineKeyboardMarkup()
            for t in tests:
                label, path = t["label"], t["path"]
                kb.add(types.InlineKeyboardButton(
                    text=label, web_app=types.WebAppInfo(WEB_URL + path)))
            kb.add(types.InlineKeyboardButton("⬅️ Back", callback_data=f"STD|{std}"))
            bot.edit_message_text(f"🧪 {std} → {subject}\nSelect Test:",
                                  call.message.chat.id, call.message.message_id, reply_markup=kb)

        elif parts[0] == "BACK_MAIN":  # Back to class list
            kb = types.InlineKeyboardMarkup()
            for std in data.keys():
                kb.add(types.InlineKeyboardButton(
                    text=std, callback_data=f"STD|{std}"))
            bot.edit_message_text("📘 Select your class:",
                                  call.message.chat.id, call.message.message_id, reply_markup=kb)

        else:
            bot.answer_callback_query(call.id, "Unknown action")

    except Exception as e:
        logging.error(f"Callback error: {e}")
        bot.answer_callback_query(call.id, "⚠️ Something went wrong.")


# ---------- HELP / OWNER COMMANDS ---------------
@bot.message_handler(commands=['help'])
def help_cmd(m):
    text = (
        "📚 *Study Bot Help*\n\n"
        "• /start - Show main menu\n"
        "• /refresh - Reload JSON from GitHub\n"
        "• Update your tests by editing data.json in your GitHub repo.\n\n"
        "Bot auto-syncs changes automatically 🔄"
    )
    bot.send_message(m.chat.id, text, parse_mode="Markdown")
# ------------------------------------------------


# ---------- POLLING LOOP ------------------------
if __name__ == '__main__':
    logging.info("🤖 Bot started. Using long polling...")
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=50)
        except Exception as e:
            logging.error(f"Polling error: {e}")
            time.sleep(5)