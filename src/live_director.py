import asyncio
import logging
import os
import pyaudio
import traceback
import json
import websockets
from google import genai
from google.genai import types

from .orchestrator import StatefulOrchestrator

# --- Audio Configuration ---
FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024


class AumDirectorApp:
    def __init__(self):
        self.orchestrator = StatefulOrchestrator()
        self.pya = pyaudio.PyAudio()
        self.audio_in_queue = asyncio.Queue()
        self.session = None
        self.web_socket = None

    async def send_qr_command_to_web(self):
        """Sends the display_qr command to the web server via WebSocket."""
        if self.web_socket and self.web_socket.open:
            logging.info("[DIRECTOR] ---> Sending 'display_qr' command to web server.")
            try:
                await self.web_socket.send(json.dumps({"type": "display_qr"}))
            except websockets.exceptions.ConnectionClosed:
                logging.error("[DIRECTOR] WebSocket connection is closed.")
                self.web_socket = None

    async def listen_for_web_commands(self):
        """Connects to the web server's control WebSocket and listens for commands."""
        uri = "ws://localhost:8000/ws/control"
        while True:
            try:
                async with websockets.connect(uri) as websocket:
                    self.web_socket = websocket
                    await websocket.send(
                        json.dumps({"type": "identify", "client": "director"})
                    )
                    logging.info("[DIRECTOR] Connected to web control WebSocket.")
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            if data.get("type") == "trigger_scene":
                                await self.orchestrator.execute_scene_by_name(
                                    data.get("scene_name")
                                )
                            elif data.get("type") == "move_robotic_arm":
                                await self.orchestrator.execute_manual_arm_move(
                                    **data.get("params", {{}})
                                )
                        except (json.JSONDecodeError, TypeError) as e:
                            logging.error(
                                f"[DIRECTOR] Error processing web command: {e}"
                            )
            except (OSError, websockets.exceptions.ConnectionClosedError) as e:
                logging.warning(
                    f"[DIRECTOR] WebSocket connection failed: {e}. Retrying..."
                )
                self.web_socket = None
                await asyncio.sleep(3)

    async def listen_and_send_audio(self):
        """Captures and sends audio to the Gemini API."""
        stream = self.pya.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=SEND_SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE,
        )
        logging.info("[DIRECTOR] Microphone is open.")
        while True:
            data = await asyncio.to_thread(
                stream.read, CHUNK_SIZE, exception_on_overflow=False
            )
            if self.session:
                await self.session.send_realtime_input(
                    audio={"data": data, "mime_type": "audio/pcm"}
                )

    async def play_audio(self):
        """Plays audio from the incoming queue."""
        stream = self.pya.open(
            format=FORMAT, channels=CHANNELS, rate=RECEIVE_SAMPLE_RATE, output=True
        )
        logging.info("[DIRECTOR] Audio output is open.")
        while True:
            chunk = await self.audio_in_queue.get()
            await asyncio.to_thread(stream.write, chunk)

    async def receive_and_process(self):
        """Handles responses from Gemini, including tool calls and audio."""
        while True:
            if not self.session:
                await asyncio.sleep(0.1)
                continue

            turn = self.session.receive()
            async for response in turn:
                if audio_data := response.server_content.model_turn.parts[
                    0
                ].inline_data:
                    self.audio_in_queue.put_nowait(audio_data.data)

                if response.tool_call:
                    for call in response.tool_call.function_calls:
                        if call.name == "process_user_command":
                            command = call.args["command"]
                            logging.info(
                                f'[DIRECTOR] ---> User speech detected: "{command}"'
                            )
                            result = await self.orchestrator.process_user_input(
                                command, self
                            )
                            await self.session.send_tool_response(
                                function_responses=[
                                    types.FunctionResponse(
                                        id=call.id, name=call.name, response=result
                                    )
                                ]
                            )

    async def run(self):
        """Main entry point to run the director application."""
        api_key = os.getenv("GEMINI_API_KEY")
        client = genai.Client(api_key=api_key)
        with open("prompts/BOB_DIRECTOR.md", "r") as f:
            system_prompt = f.read()

        tools = [
            {
                "function_declarations": [
                    {
                        "name": "process_user_command",
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {"command": {"type": "STRING"}},
                            "required": ["command"],
                        },
                    }
                ]
            }
        ]

        logging.info("--- Bob the Curious Robot ---")
        try:
            await self.orchestrator.hardware.connect_all()
            async with (
                client.aio.live.connect(
                    model="models/gemini-2.5-flash-preview-native-audio-dialog",
                    config={
                        "system_instruction": system_prompt,
                        "response_modalities": ["AUDIO"],
                        "input_audio_transcription": {{}},
                        "realtime_input_config": {"automatic_activity_detection": {{}}},
                        "tools": tools,
                    },
                ) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session
                tg.create_task(self.listen_and_send_audio())
                tg.create_task(self.play_audio())
                tg.create_task(self.receive_and_process())
                tg.create_task(self.listen_for_web_commands())
        except Exception as e:
            logging.error(f"[DIRECTOR] CRITICAL_ERROR: {e}\n{traceback.format_exc()}")
        finally:
            self.pya.terminate()
            if self.orchestrator and hasattr(self.orchestrator, "hardware"):
                await self.orchestrator.hardware.close_all_ports()
            logging.info("--- Application shut down ---")
