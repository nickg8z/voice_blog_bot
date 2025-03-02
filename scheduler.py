import time
import schedule
import logging
import os
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filename="scheduler.log",
)
logger = logging.getLogger(__name__)


def run_bot():
    """Run the Telegram bot script."""
    try:
        logger.info("Starting Telegram bot...")
        subprocess.run(["python", "bot.py"])
    except Exception as e:
        logger.error(f"Error running bot: {str(e)}")


def check_bot_status():
    """Check if the bot is running and restart if needed."""
    # This is a simplistic approach - in production, you might want to use
    # a proper process manager like supervisord or systemd
    try:
        # Check if the bot is running (this is platform-dependent)
        bot_running = False
        if os.name == "posix":  # Linux/Mac
            result = subprocess.run(
                ["pgrep", "-f", "python bot.py"], capture_output=True, text=True
            )
            bot_running = result.returncode == 0
        else:  # Windows
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq python.exe"],
                capture_output=True,
                text=True,
            )
            bot_running = "bot.py" in result.stdout

        if not bot_running:
            logger.warning("Bot not running. Restarting...")
            run_bot()
        else:
            logger.info("Bot is running normally.")

    except Exception as e:
        logger.error(f"Error checking bot status: {str(e)}")


if __name__ == "__main__":
    # Schedule regular health checks
    schedule.every(30).minutes.do(check_bot_status)

    # Run the bot initially
    run_bot()

    # Keep the scheduler running
    while True:
        schedule.run_pending()
        time.sleep(60)
