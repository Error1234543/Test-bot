import os
import json
import telebot
from telebot import types

BOT_TOKEN = "8510670200:AAGN0wkvB8yYOOvsU3Jrf4pWAS5q0zR3CGI"
WEB_URL = "https://hdhdhsjsjsjdjsjshdjdhdjdjdjdu.netlify.app/"  # GitHub Pages URL

bot = telebot.TeleBot(BOT_TOKEN)

# Load data.json
with open("data.json", "r") as f:
    DATA = json.load(f)


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


bot.infinity_polling()