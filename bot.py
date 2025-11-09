# bot.py
# Telegram WebApp Bot (Entry point)
# Placeholders: BOT_TOKEN, CHANNEL_ID, WEB_URL should be provided as environment variables.
# For Koyeb, set these in the service environment variables.

import os
import telebot
from telebot import types
import logging
import time

logging.basicConfig(level=logging.INFO)
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@YOUR_CHANNEL")  # include @ for username
WEB_URL = os.getenv("WEB_URL", "https://hdhdhsjsjsjdjsjshdjdhdjdjdjdu.netlify.app")

if BOT_TOKEN.startswith("YOUR_"):
    logging.warning("BOT_TOKEN not set. Replace the placeholder or set BOT_TOKEN env var.")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

def check_joined(user_id):
    """Return True if the user is member/admin/creator of the configured channel."""
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        # If channel is private or bot not in channel, fallback to False
        logging.info(f"check_joined: Exception while checking membership: {e}")
        return False

@bot.message_handler(commands=['start'])
def start(msg):
    chat_id = msg.chat.id
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    # Join Channel button (opens channel link)
    channel_username = CHANNEL_ID.lstrip('@')
    join_url = f"https://t.me/{channel_username}"
    keyboard.add(types.InlineKeyboardButton("📢 Join Channel", url=join_url))
    # Done button to verify membership
    keyboard.add(types.InlineKeyboardButton("✅ Done", callback_data="check_join"))
    bot.send_message(chat_id, "Please join our channel to continue:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda c: True)
def callback_handler(call):
    data = call.data or ''
    uid = call.from_user.id
    if data == 'check_join':
        bot.answer_callback_query(call.id, text="Checking membership...")
        if check_joined(uid):
            bot.send_message(uid, "✅ Verified. Opening website below...")
            send_open_button(uid)
        else:
            bot.send_message(uid, "❌ You are not a member yet. Please join the channel and press Done again.")
            # Optionally re-show join and done buttons
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            channel_username = CHANNEL_ID.lstrip('@')
            join_url = f"https://t.me/{channel_username}"
            keyboard.add(types.InlineKeyboardButton("📢 Join Channel", url=join_url))
            keyboard.add(types.InlineKeyboardButton("✅ Done", callback_data="check_join"))
            bot.send_message(uid, "Join channel and press Done:", reply_markup=keyboard)
    elif data == 'open_website':
        # Not used — webapp button uses web_app param
        bot.answer_callback_query(call.id)
    else:
        bot.answer_callback_query(call.id, text="Unknown action")

def send_open_button(chat_id):
    kb = types.InlineKeyboardMarkup()
    webapp = types.WebAppInfo(WEB_URL)
    kb.add(types.InlineKeyboardButton(text="🚀 OPEN WEBSITE", web_app=webapp))
    bot.send_message(chat_id, "Tap below to open the site inside Telegram:", reply_markup=kb)

@bot.message_handler(commands=['help'])
def help_cmd(m):
    bot.reply_to(m, "This bot opens your hosted website inside Telegram. Set BOT_TOKEN, CHANNEL_ID and WEB_URL environment variables before running.")

@bot.message_handler(func=lambda m: True)
def fallback(m):
    bot.reply_to(m, "Use /start to begin.")

if __name__ == '__main__':
    logging.info('Bot starting (long polling).')
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=120)
        except Exception as e:
            logging.error(f"Polling error: {e}")
            time.sleep(5)
