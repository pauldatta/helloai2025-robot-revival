# main.py
import asyncio
import logging
import sys
from dotenv import load_dotenv
from .live_director import AumDirectorApp

# Load environment variables from .env file at the very start
load_dotenv()


def setup_logging():
    """Configures logging to file and console."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler("app.log"), logging.StreamHandler(sys.stdout)],
    )


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
