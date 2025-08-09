import asyncio
import sys
import aiofiles
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

app = FastAPI()
html_path = "web/index.html"
log_file_path = "app.log"


@app.get("/")
async def get():
    with open(html_path) as f:
        return HTMLResponse(f.read())


async def log_sender(websocket: WebSocket):
    """Tails the log file and sends new lines to the client."""
    try:
        async with aiofiles.open(log_file_path, mode="r") as f:
            await f.seek(0, 2)  # Go to the end of the file
            while True:
                line = await f.readline()
                if not line:
                    await asyncio.sleep(0.1)
                    continue
                # Send the raw JSON line
                await websocket.send_text(line.strip())
    except asyncio.CancelledError:
        print("[WEB_SERVER] Log sender task cancelled.")
    except Exception as e:
        print(f"[WEB_SERVER] Error reading log file: {e}")
    finally:
        await websocket.close()


@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    sender_task = asyncio.create_task(log_sender(websocket))
    try:
        while True:
            # Keep the connection open and wait for the client to disconnect
            await websocket.receive_text()
    except Exception:
        print("[WEB_SERVER] Client disconnected.")
    finally:
        sender_task.cancel()
        # In Python 3.9+ we can use an optional message
        if sys.version_info >= (3, 9):
            sender_task.cancel("Client disconnected")
        else:
            sender_task.cancel()
        try:
            await sender_task
        except asyncio.CancelledError:
            pass  # Expected
