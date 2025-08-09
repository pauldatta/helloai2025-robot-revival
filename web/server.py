import asyncio
import aiofiles
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import logging

app = FastAPI()

# In-memory list of connected clients for broadcasting
log_clients = []
control_clients = []

# Mount a static directory to serve images, CSS, etc.
app.mount("/static", StaticFiles(directory="context"), name="static")

html_path = "web/index.html"
log_file_path = "app.log"


@app.get("/")
async def get_main():
    with open(html_path) as f:
        return HTMLResponse(f.read())


async def log_sender(websocket: WebSocket):
    """Tails the log file and sends new lines to the client."""
    log_clients.append(websocket)
    try:
        async with aiofiles.open(log_file_path, mode="r") as f:
            await f.seek(0, 2)
            while True:
                line = await f.readline()
                if not line:
                    await asyncio.sleep(0.1)
                    continue
                # Broadcast to all connected clients
                for client in log_clients:
                    await client.send_text(line.strip())
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logging.error(f"[WEB_SERVER] Error reading log file: {e}")
    finally:
        log_clients.remove(websocket)


@app.websocket("/ws/logs")
async def websocket_logs_endpoint(websocket: WebSocket):
    await websocket.accept()
    sender_task = asyncio.create_task(log_sender(websocket))
    try:
        while True:
            await websocket.receive_text()  # Keep connection open
    except WebSocketDisconnect:
        logging.info("[WEB_SERVER] Log client disconnected.")
    finally:
        sender_task.cancel()
        try:
            await sender_task
        except asyncio.CancelledError:
            pass


@app.websocket("/ws/control")
async def websocket_control_endpoint(websocket: WebSocket):
    """Handles incoming control commands from the web UI."""
    await websocket.accept()
    control_clients.append(websocket)
    logging.info("[WEB_SERVER] Control client connected.")
    try:
        while True:
            data = await websocket.receive_text()
            # For now, we just log the command.
            # In the future, this would call the orchestrator.
            logging.info(f"[WEB_CONTROL] Received command: {data}")
    except WebSocketDisconnect:
        logging.info("[WEB_SERVER] Control client disconnected.")
    finally:
        control_clients.remove(websocket)
