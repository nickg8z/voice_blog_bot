import os
import logging
from datetime import datetime, time
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from voice_processor import (
    download_voice_message,
    get_daily_transcriptions,
    clear_daily_files,
)
from blog_formatter import generate_blog_post, publish_to_blog

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get environment variables
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID"))


# Command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    user_id = update.effective_user.id
    if user_id != ALLOWED_USER_ID:
        await update.message.reply_text(
            "Sorry, you are not authorized to use this bot."
        )
        return

    await update.message.reply_text(
        "👋 Welcome to your Voice Blog Bot!\n\n"
        "Send me voice messages throughout the day, and I'll compile them into a blog post every evening.\n\n"
        "Commands:\n"
        "/start - Show this message\n"
        "/compile - Manually compile today's voice messages into a blog post\n"
        "/status - Check how many voice messages you've sent today"
    )


async def compile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manually trigger the compilation process."""
    user_id = update.effective_user.id
    if user_id != ALLOWED_USER_ID:
        await update.message.reply_text(
            "Sorry, you are not authorized to use this bot."
        )
        return

    await update.message.reply_text("Starting to compile today's voice messages...")
    await compile_and_post(context, update.effective_chat.id)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check the status of today's voice messages."""
    user_id = update.effective_user.id
    if user_id != ALLOWED_USER_ID:
        await update.message.reply_text(
            "Sorry, you are not authorized to use this bot."
        )
        return

    today = datetime.now().strftime("%Y-%m-%d")
    voice_files = get_daily_transcriptions(today, count_only=True)

    await update.message.reply_text(f"You've sent {voice_files} voice messages today.")


# Message handlers
async def voice_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages."""
    user_id = update.effective_user.id
    if user_id != ALLOWED_USER_ID:
        await update.message.reply_text(
            "Sorry, you are not authorized to use this bot."
        )
        return

    voice = update.message.voice
    if not voice:
        return

    await update.message.reply_text(
        "🎤 Received your voice message! I'll add it to today's compilation."
    )

    # Download and process the voice message
    voice_file = await context.bot.get_file(voice.file_id)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_path = f"temp_audio/{timestamp}.ogg"

    await download_voice_message(voice_file, file_path)
    logger.info(f"Voice message saved: {file_path}")


# Compilation function
async def compile_and_post(context, chat_id=None):
    """Compile the day's voice messages and create a blog post."""
    today = datetime.now().strftime("%Y-%m-%d")

    # Get all transcriptions for today
    transcriptions = get_daily_transcriptions(today)

    if not transcriptions:
        message = "No voice messages were recorded today."
        if chat_id:
            await context.bot.send_message(chat_id=chat_id, text=message)
        logger.info(message)
        return

        # Generate blog post using OpenRouter
    try:
        blog_post = await generate_blog_post(transcriptions)

        # Send the blog post to the user
        if chat_id:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"📝 Here's your blog post for {today}:\n\n{blog_post[:1000]}...\n\n(Processing for publishing...)",
            )

        # Publish to blog
        try:
            success, result = await publish_to_blog(blog_post, today)

            if success:
                message = f"✅ Blog post published successfully! {result}"
            else:
                message = f"❌ Failed to publish: {result}"
        except Exception as e:
            message = f"❌ Error during publishing: {str(e)}"
            logger.error(f"Publishing error: {str(e)}")

        if chat_id:
            await context.bot.send_message(chat_id=chat_id, text=message)

        logger.info(f"Blog compilation result: {message}")

        # Clear processed files (optional, depending on your retention policy)
        # clear_daily_files(today)

    except Exception as e:
        error_message = f"Error generating blog post: {str(e)}"
        if chat_id:
            await context.bot.send_message(chat_id=chat_id, text=error_message)
        logger.error(error_message)


# Schedule daily compilation
async def scheduled_compilation(context):
    """Run the compilation task at a scheduled time."""
    allowed_user_id = ALLOWED_USER_ID
    await compile_and_post(context, allowed_user_id)


def main():
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("compile", compile_command))
    application.add_handler(CommandHandler("status", status_command))

    # Add message handlers
    application.add_handler(MessageHandler(filters.VOICE, voice_message_handler))

    # Set up daily job at 9PM
    job_queue = application.job_queue
    if job_queue:
        job_queue.run_daily(scheduled_compilation, time=time(hour=21, minute=0))
        logger.info("Scheduled daily compilation at 9:00 PM")
    else:
        logger.warning(
            "Job queue not available. Install python-telegram-bot[job-queue] for scheduling"
        )

    # Start the Bot
    application.run_polling()


if __name__ == "__main__":
    main()
