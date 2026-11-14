import os, io, threading
from flask import Flask
from google import genai
from telegram import Update
from telegram.ext import (ApplicationBuilder, CommandHandler,
                          MessageHandler, ContextTypes, filters)

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
CHAT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "gemini-2.5-flash-image")
chats = {}  # har user ki alag chat history

# Render ko port chahiye, is liye chhota web server
web = Flask(__name__)
@web.route("/")
def home():
    return "OK"

def run_web():
    web.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Assalam o Alaikum! Mujh se chat karein.\n"
        "Image ke liye: /image aap ka prompt")

async def reply(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in chats:
        chats[uid] = client.aio.chats.create(model=CHAT_MODEL)
    try:
        r = await chats[uid].send_message(update.message.text)
        await update.message.reply_text(r.text or "Koi jawab nahi mila.")
    except Exception as e:
        print(e)
        await update.message.reply_text("Kuch gadbad ho gayi, dobara koshish karein.")

async def image(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(ctx.args)
    if not prompt:
        await update.message.reply_text("Aise likhein: /image ek sher pahaar par")
        return
    try:
        r = await client.aio.models.generate_content(
            model=IMAGE_MODEL, contents=prompt)
        sent = False
        for p in r.candidates[0].content.parts:
            if p.inline_data:
                await update.message.reply_photo(io.BytesIO(p.inline_data.data))
                sent = True
        if not sent:
            await update.message.reply_text("Image nahi bani, prompt badal kar dekhein.")
    except Exception as e:
        print(e)
        await update.message.reply_text("Image mein masla hua (shayad billing ya limit).")

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    app = ApplicationBuilder().token(os.environ["TELEGRAM_TOKEN"]).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("image", image))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))
    app.run_polling()
