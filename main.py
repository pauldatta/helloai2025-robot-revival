import asyncio
import os
from dotenv import load_dotenv

# Import the main application class
from live_director import AumDirectorApp

def main():
    """
    Main entry point for the Aum's Journey application.
    Loads configuration, reads the director's persona, and starts the app.
    """
    # Load environment variables from .env file
    load_dotenv()

    # Check for the API key before proceeding
    if 'GEMINI_API_KEY' not in os.environ:
        print("Error: The GEMINI_API_KEY environment variable is not set.")
        print("Please create a .env file and set the key.")
        return

    # Read the director's persona from the markdown file
    try:
        with open('AUM_DIRECTOR.md', 'r') as f:
            director_persona = f.read()
    except FileNotFoundError:
        print("Error: AUM_DIRECTOR.md not found. Please ensure the file is in the same directory.")
        return

    # Create and run the application
    app = AumDirectorApp(director_persona=director_persona)
    
    try:
        asyncio.run(app.run())
    except RuntimeError as e:
        print(f"Error running the application: {e}")

if __name__ == "__main__":
    main()