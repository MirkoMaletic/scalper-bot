import os
import json
import time
import threading
from datetime import datetime
from flask import Flask, request
from dotenv import load_dotenv
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, Dispatcher

# Učitaj .env
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Flask aplikacija
app = Flask(__name__)
bot = Bot(token=TOKEN)

state = {
    "live": False,
    "paused": False,
    "positions": []
}

STATE_FILE = "state.json"

# Učitaj prethodno stanje
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        state.update(json.load(f))

def save_state():
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

# Telegram funkcije
async def start_live(update: Update, context):
    state["live"] = True
    save_state()
    await update.message.reply_text("✅ Live režim uključen.")

async def pause(update: Update, context):
    state["paused"] = True
    save_state()
    await update.message.reply_text("⏸ Bot pauziran.")

async def resume(update: Update, context):
    state["paused"] = False
    save_state()
    await update.message.reply_text("▶ Bot nastavlja rad.")

async def stop(update: Update, context):
    state["live"] = False
    save_state()
    await update.message.reply_text("🛑 Bot isključen.")

async def status(update: Update, context):
    await update.message.reply_text(
        f"📊 Status:\nLive: {state['live']}\nPaused: {state['paused']}\nOtvorene pozicije: {len(state['positions'])}"
    )

async def reset(update: Update, context):
    state["positions"] = []
    save_state()
    await update.message.reply_text("🔁 Reset pozicija.")

async def close_all(update: Update, context):
    for p in state["positions"]:
        p["status"] = "closed"
    save_state()
    await update.message.reply_text("🚫 Sve pozicije zatvorene (simulacija).")

# Aplikacija i dispatcher
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start_live", start_live))
application.add_handler(CommandHandler("pause", pause))
application.add_handler(CommandHandler("resume", resume))
application.add_handler(CommandHandler("stop", stop))
application.add_handler(CommandHandler("status", status))
application.add_handler(CommandHandler("reset", reset))
application.add_handler(CommandHandler("close_all", close_all))

@app.route("/")
def root():
    return "✅ Bot je aktivan."

@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    application.update_queue.put(update)
    return "OK"

def start_flask():
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    threading.Thread(target=start_flask).start()
    application.run_polling()
