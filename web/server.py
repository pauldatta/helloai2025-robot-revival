import asyncio
import aiofiles
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import logging
from typing import List, Set
from websockets.exceptions import ConnectionClosed

app = FastAPI()

# --- WebSocket Connection Management ---
# A more robust way to handle different client types.
log_clients: List[WebSocket] = []
director_socket: WebSocket = None
ui_control_sockets: Set[WebSocket] = set()

# Mount a static directory to serve images, CSS, etc.
app.mount("/static", StaticFiles(directory="context"), name="static")

html_path = "web/index.html"
log_file_path = "app.log"


@app.get("/")
async def get_main():
    with open(html_path) as f:
        return HTMLResponse(f.read())


async def log_sender(websocket: WebSocket):
    """Tails the log file and sends new lines to all connected log clients."""
    log_clients.append(websocket)
    try:
        async with aiofiles.open(log_file_path, mode="r") as f:
            await f.seek(0, 2)  # Go to the end of the file
            while True:
                line = await f.readline()
                if not line:
                    await asyncio.sleep(0.1)
                    continue
                # Use a copy of the list to avoid issues with concurrent modification
                current_clients = list(log_clients)
                for client in current_clients:
                    await client.send_text(line.strip())
    except asyncio.CancelledError:
        pass  # Task was cancelled, expected behavior
    except Exception as e:
        logging.error(f"[WEB_SERVER] Error reading log file: {e}")
    finally:
        if websocket in log_clients:
            log_clients.remove(websocket)


@app.websocket("/ws/logs")
async def websocket_logs_endpoint(websocket: WebSocket):
    await websocket.accept()
    sender_task = asyncio.create_task(log_sender(websocket))
    try:
        while True:
            # Keep the connection alive, but we don't expect messages from the client
            await websocket.receive_text()
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
    """
    Manages control commands. A client is initially treated as a UI.
    If it sends an 'identify' message, it's re-classified as the director.
    """
    global director_socket
    await websocket.accept()

    # Initially, treat every connection as a potential UI client
    client_socket = websocket
    ui_control_sockets.add(client_socket)
    logging.info(
        f"[WEB_SERVER] A control client connected. Total UIs: {len(ui_control_sockets)}"
    )

    try:
        while True:
            data = await client_socket.receive_text()

            try:
                message = json.loads(data)
                # Check for the special identification message
                if (
                    message.get("type") == "identify"
                    and message.get("client") == "director"
                ):
                    if director_socket is not None and director_socket != client_socket:
                        logging.warning(
                            "[WEB_SERVER] A second director tried to identify. Ignoring."
                        )
                        continue  # Don't process further

                    # This is the director. Register it and remove from UI list.
                    director_socket = client_socket
                    if client_socket in ui_control_sockets:
                        ui_control_sockets.remove(client_socket)
                    logging.info("[WEB_SERVER] Director identified and registered.")
                    # The director doesn't send other messages, so we just wait for disconnect
                    # by continuing the loop but not processing other message types from it.
                    continue

                # --- New QR Code Logic ---
                # If the director sends a 'display_qr' command, broadcast it to all UIs
                if (
                    client_socket == director_socket
                    and message.get("type") == "display_qr"
                ):
                    logging.info(
                        "[WEB_SERVER] Received 'display_qr' command from director. Broadcasting to all UIs."
                    )
                    qr_message = json.dumps({"type": "display_qr"})
                    # Create a copy of the set to safely iterate over it
                    for ui_socket in list(ui_control_sockets):
                        try:
                            await ui_socket.send_text(qr_message)
                        except ConnectionClosed:
                            # Handle case where UI client disconnected between iterations
                            ui_control_sockets.remove(ui_socket)
                    continue  # Don't forward this message back to the director

                if message.get("type") == "reset_conversation":
                    logging.info(
                        "[WEB_SERVER] Received 'reset_conversation' command from UI. Forwarding to director."
                    )
                    if director_socket:
                        try:
                            await director_socket.send_text(data)
                        except ConnectionClosed:
                            logging.error(
                                "[WEB_SERVER] Director is not connected. Command not sent."
                            )
                            director_socket = None
                    else:
                        logging.warning(
                            "[WEB_SERVER] No director connected to forward command to."
                        )
                    continue

            except json.JSONDecodeError:
                # Not a json message, treat as legacy or ignore
                pass

            # If we're here, it's a command from a UI client. Forward it.
            if director_socket and director_socket != client_socket:
                logging.info(f"[WEB_CONTROL] Forwarding UI command to director: {data}")
                try:
                    await director_socket.send_text(data)
                except ConnectionClosed:
                    logging.error(
                        "[WEB_CONTROL] Director is not connected. Command not sent."
                    )
                    director_socket = None  # Clear stale socket
            elif not director_socket:
                logging.warning(
                    "[WEB_CONTROL] No director connected to forward command to."
                )

    except WebSocketDisconnect:
        logging.info("[WEB_SERVER] Control client disconnected.")
    finally:
        # Clean up on disconnect
        if client_socket == director_socket:
            director_socket = None
            logging.info("[WEB_SERVER] Director disconnected.")
        if client_socket in ui_control_sockets:
            ui_control_sockets.remove(client_socket)
            logging.info(
                f"[WEB_SERVER] UI client disconnected. Total UIs: {len(ui_control_sockets)}"
            )
