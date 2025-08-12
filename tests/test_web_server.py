import json
from fastapi.testclient import TestClient
from web.server import app


def test_websocket_ui_to_director_forwarding():
    """
    Tests the core WebSocket logic:
    1. A client identifies as the 'director'.
    2. A second 'ui' client sends a command.
    3. The director client receives the command from the ui client.
    """
    client = TestClient(app)
    with client.websocket_connect(
        "/ws/control"
    ) as director_ws, client.websocket_connect("/ws/control") as ui_ws:
        # 1. Director identifies itself
        director_ws.send_text(json.dumps({"type": "identify", "client": "director"}))

        # 2. UI sends a command
        command = {"type": "trigger_scene", "scene_name": "AUMS_HOME"}
        ui_ws.send_text(json.dumps(command))

        # 3. Verify director receives the command from the UI
        received_data = director_ws.receive_text()
        assert json.loads(received_data) == command
