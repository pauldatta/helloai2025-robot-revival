# main.py
import asyncio
from dotenv import load_dotenv
from .live_director import AumDirectorApp

# Load environment variables from .env file at the very start
load_dotenv()


async def main():
    """The main entry point for the application."""
    app = AumDirectorApp()
    await app.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting application.")
