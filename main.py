import os
import uuid
import logging
import asyncio
import subprocess
import requests
from telegram import Update, InputFile
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# 🔐 Replace this with your @BotFather token
BOT_TOKEN = "8278977289:AAF8bSha4IXqIxx1Y6Tk-PV9AzMKVBPZoeU"

# 📁 Folder to store downloaded files
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# 🪵 Logging setup
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ✅ /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Ranajii Bot!\n\n"
        "📁 Send a `.txt` file containing links to videos or PDFs,\n"
        "or send a direct streaming link (`enc=` or `.m3u8`)\n"
        "📦 I’ll download & send them back to you!"
    )

# 🔗 Simple video downloader using FFmpeg
def download_video(url, output_path):
    cmd = [
        'ffmpeg', '-y',
        '-i', url,
        '-c', 'copy',
        '-bsf:a', 'aac_adtstoasc',
        output_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

# 📄 Simple PDF downloader
def download_pdf(url, output_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(response.content)
        return True
    return False

# 📩 Handler for .txt file upload
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if not document.file_name.endswith(".txt"):
        await update.message.reply_text("❌ Please upload a `.txt` file only.")
        return

    file_path = os.path.join(DOWNLOAD_DIR, f"{uuid.uuid4().hex}.txt")
    file_obj = await context.bot.get_file(document.file_id)
    await file_obj.download_to_drive(file_path)

    await update.message.reply_text("📥 Reading file and downloading...")

    with open(file_path, 'r') as f:
        links = [line.strip() for line in f if line.strip()]

    os.remove(file_path)

    for url in links:
        try:
            file_id = uuid.uuid4().hex
            if url.endswith(".pdf"):
                output_path = os.path.join(DOWNLOAD_DIR, f"{file_id}.pdf")
                success = download_pdf(url, output_path)
                if success:
                    await update.message.reply_document(InputFile(output_path), caption="📄 PDF Ready")
                    os.remove(output_path)
                else:
                    await update.message.reply_text(f"❌ Couldn't download PDF: {url}")
            elif "enc=" in url or url.endswith(".m3u8"):
                output_path = os.path.join(DOWNLOAD_DIR, f"{file_id}.mp4")
                download_video(url, output_path)
                await update.message.reply_video(InputFile(output_path), caption="🎬 Video Downloaded", timeout=300)
                os.remove(output_path)
            else:
                await update.message.reply_text(f"⚠️ Unknown format: {url}")
        except Exception as e:
            logging.error(f"Error with URL {url}: {e}")
            await update.message.reply_text(f"❌ Failed: {url}")

# 🌐 Handle plain text message input (links only)
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    file_id = uuid.uuid4().hex

    try:
        if url.endswith(".pdf"):
            output_path = os.path.join(DOWNLOAD_DIR, f"{file_id}.pdf")
            success = download_pdf(url, output_path)
            if success:
                await update.message.reply_document(InputFile(output_path), caption="📄 PDF Done")
                os.remove(output_path)
            else:
                await update.message.reply_text("❌ PDF Download Failed.")
        elif "enc=" in url or url.endswith(".m3u8"):
            output_path = os.path.join(DOWNLOAD_DIR, f"{file_id}.mp4")
            download_video(url, output_path)
            await update.message.reply_video(InputFile(output_path), caption="🎬 Video Ready", timeout=300)
            os.remove(output_path)
        else:
            await update.message.reply_text("❌ Invalid link. Please send a streaming or PDF link.")
    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("⚠️ Failed to process the link.")

# 🏁 Main function to run bot
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("🤖 Telegram Bot is Running...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
