import asyncio
import os
from dotenv import load_dotenv

# Import the main application class
from live_director import AumDirectorApp

def main():
    """
    Main entry point for the Aum's Journey application.
    Loads configuration and starts the director application.
    """
    # Load environment variables from .env file
    load_dotenv()

    # Check for the API key before proceeding
    # Note: The orchestrator now handles the API key directly.
    if 'GEMINI_API_KEY' not in os.environ and 'GOOGLE_API_KEY' not in os.environ:
        print("Error: GEMINI_API_KEY or GOOGLE_API_KEY environment variable is not set.")
        print("Please create a .env file and set the key.")
        return

    app = AumDirectorApp()
    
    try:
        asyncio.run(app.run())
    except RuntimeError as e:
        print(f"Error running the application: {e}")

if __name__ == "__main__":
    main()
