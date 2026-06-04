import logging
import sys
import os
import asyncio
import hashlib
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Force stdout/stderr to flush instantly so logs appear immediately on Render
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Helper function to generate hashes
def generate_hashes(data_bytes: bytes) -> str:
    md5_hash = hashlib.md5(data_bytes).hexdigest()
    sha1_hash = hashlib.sha1(data_bytes).hexdigest()
    sha256_hash = hashlib.sha256(data_bytes).hexdigest()
    
    return (
        f"🔐 **Cryptographic Hashes Generated:**\n\n"
        f"🔹 **MD5:**\n`{md5_hash}`\n\n"
        f"🔹 **SHA-1:**\n`{sha1_hash}`\n\n"
        f"🔹 **SHA-256:**\n`{sha256_hash}`"
    )

# Command: /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 **Welcome to CryptoHash Utility Bot!**\n\n"
        "Send me any **text message** or upload any **file/document**, and I will instantly generate its secure MD5, SHA-1, and SHA-256 checksums.\n\n"
        "🔒 *Everything is processed entirely in memory; nothing is saved.*"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

# Handler for Text Messages
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_bytes = update.message.text.encode('utf-8')
    result = generate_hashes(text_bytes)
    await update.message.reply_text(result, parse_mode="Markdown")

# Handler for Files/Documents
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_message = await update.message.reply_text("📥 Processing file and calculating hashes... please wait.")
    
    try:
        # Fetch file metadata from Telegram
        file_id = update.message.document.file_id
        tg_file = await context.bot.get_file(file_id)
        
        # Download the file completely into memory as a bytearray
        file_bytes = await tg_file.download_as_bytearray()
        
        # Calculate hashes
        result = generate_hashes(bytes(file_bytes))
        
        # Edit status message with results
        await status_message.edit_text(result, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error handling file: {e}")
        await status_message.edit_text("❌ Failed to process file. Make sure it is under 20MB.")

# Async Lifecycle Wrapper to handle Python 3.14+ loop compliance
async def run_bot_lifecycle():
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        logger.error("CRITICAL: BOT_TOKEN environment variable is missing!")
        return

    logger.info("Building Telegram application framework...")
    application = Application.builder().token(BOT_TOKEN).build()

    # Register bot handlers
    application.add_handler(CommandHandler("start", start_command))
    # Handles text inputs
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    # Handles file/document uploads
    application.add_handler(filters = MessageHandler(filters.Document.ALL, handle_document))

    # Explicitly initialize components within the running event loop
    logger.info("Initializing application components...")
    await application.initialize()
    await application.updater.start_polling()
    await application.start()

    logger.info("🚀 CryptoHash Bot is successfully running and polling for updates!")

    # Keep the background worker thread alive infinitely 
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Stopping bot service gracefully...")
    finally:
        # Proper cleanup structure to prevent open hanging loops on exit
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

def main():
    # asyncio.run handles loop creation safely across environments without RuntimeError
    asyncio.run(run_bot_lifecycle())

if __name__ == '__main__':
    main()
