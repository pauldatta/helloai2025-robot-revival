import asyncio
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
            # Go to the end of the file
            await f.seek(0, 2)
            while True:
                line = await f.readline()
                if not line:
                    await asyncio.sleep(0.1)
                    continue
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
        # Keep the connection open and wait for the client to disconnect
        while True:
            await websocket.receive_text()
    except Exception:
        print("[WEB_SERVER] Client disconnected.")
    finally:
        sender_task.cancel()
        await sender_task
