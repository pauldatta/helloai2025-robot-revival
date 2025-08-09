# main.py
import asyncio
import logging
import sys
from dotenv import load_dotenv
from pythonjsonlogger import jsonlogger
from .live_director import AumDirectorApp

# Load environment variables from .env file at the very start
load_dotenv()


def setup_logging():
    """Configures logging to file and console."""
    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Create a handler for the file
    file_handler = logging.FileHandler("app.log")

    # Create a JSON formatter
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s"
    )
    file_handler.setFormatter(formatter)

    # Clear existing handlers and add the new one
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.addHandler(file_handler)

    # Also log to the console for local debugging
    logger.addHandler(logging.StreamHandler(sys.stdout))


async def main():
    """The main entry point for the application."""
    setup_logging()
    app = AumDirectorApp()
    await app.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("\nExiting application.")
