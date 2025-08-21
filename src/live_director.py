import asyncio
import logging
import os
import pyaudio
import traceback
import json
import websockets
from exceptiongroup import ExceptionGroup
from google import genai
from google.genai import types

# Import the new orchestrator and the hardware controller for closing ports
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
                logging.error(
                    "[DIRECTOR] WebSocket connection is closed. Cannot send QR command."
                )
                self.web_socket = None
        else:
            logging.warning("[DIRECTOR] No active web socket to send QR command.")

    async def process_user_response(self, command: str):
        """
        Processes the user's response by sending it to the orchestrator and
        returning the single-turn conversational result.
        """
        logging.info(f'[DIRECTOR] ---> Calling Orchestrator with command: "{command}"')
        result = await self.orchestrator.process_user_response(command, self)
        logging.info(f'[DIRECTOR] <--- Received narrative: "{result.get("narrative")}"')
        return result

    async def listen_for_web_commands(self):
        """Connects to the web server's control WebSocket and listens for commands."""
        uri = "ws://localhost:8000/ws/control"
        while True:
            try:
                async with websockets.connect(uri) as websocket:
                    self.web_socket = websocket  # Store the active websocket
                    # Identify this client as the director upon connecting
                    await websocket.send(
                        json.dumps({"type": "identify", "client": "director"})
                    )
                    logging.info(
                        "[DIRECTOR] Connected to web control WebSocket and identified."
                    )

                    while True:
                        message = await websocket.recv()
                        try:
                            data = json.loads(message)
                            command_type = data.get("type")

                            if command_type == "trigger_scene":
                                scene_name = data.get("scene_name")
                                logging.info(
                                    f"[DIRECTOR] Received web command to trigger scene: {scene_name}"
                                )
                                # In the new design, scene_name from the UI maps to a location
                                await self.orchestrator.execute_scene_by_name(
                                    scene_name
                                )

                            elif command_type == "move_robotic_arm":
                                params = data.get("params")
                                logging.info(
                                    f"[DIRECTOR] Received web command to move arm with params: {params}"
                                )
                                if params:
                                    # Create a background task to prevent blocking the receive loop
                                    asyncio.create_task(
                                        self.orchestrator.execute_manual_arm_move(
                                            **params
                                        )
                                    )

                        except json.JSONDecodeError:
                            logging.error(
                                f"[DIRECTOR] Invalid JSON received from web control: {message}"
                            )
                        except Exception as e:
                            logging.error(
                                f"[DIRECTOR] Error processing web command: {e}"
                            )
            except (OSError, websockets.exceptions.ConnectionClosedError) as e:
                logging.warning(
                    f"[DIRECTOR] WebSocket connection failed: {e}. Retrying in 3 seconds..."
                )
                self.web_socket = None  # Clear the socket on failure
                await asyncio.sleep(3)

    async def listen_and_send_audio(self):
        """Captures audio and sends it directly to the Gemini API."""
        mic_info = self.pya.get_default_input_device_info()
        stream = self.pya.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=SEND_SAMPLE_RATE,
            input=True,
            input_device_index=mic_info["index"],
            frames_per_buffer=CHUNK_SIZE,
        )
        logging.info("[DIRECTOR] Microphone is open. Start speaking.")
        while True:
            data = await asyncio.to_thread(
                stream.read, CHUNK_SIZE, exception_on_overflow=False
            )
            if self.session:
                await self.session.send_realtime_input(
                    audio={"data": data, "mime_type": "audio/pcm"}
                )

    async def play_audio(self):
        """Plays audio from a queue to the speakers."""
        stream = self.pya.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RECEIVE_SAMPLE_RATE,
            output=True,
        )
        logging.info("[DIRECTOR] Audio output stream is open.")
        while True:
            chunk = await self.audio_in_queue.get()
            await asyncio.to_thread(stream.write, chunk)

    async def receive_and_process(self):
        """Receives responses from Gemini, handles tool calls, and plays audio."""
        while True:
            if not self.session:
                await asyncio.sleep(0.1)
                continue

            turn = self.session.receive()
            async for response in turn:
                if response.server_content and response.server_content.model_turn:
                    for part in response.server_content.model_turn.parts:
                        if audio_data := getattr(part, "inline_data", None):
                            if audio_data.mime_type.startswith("audio/pcm"):
                                self.audio_in_queue.put_nowait(audio_data.data)

                if response.tool_call:
                    for call in response.tool_call.function_calls:
                        tool_name = call.name
                        if tool_name == "process_user_command":
                            # Simple debounce to avoid rapid-fire tool calls
                            await asyncio.sleep(0.25)
                            command = call.args["command"]
                            logging.info(
                                f'[DIRECTOR] ---> User speech detected: "{command}"'
                            )
                            result = await self.process_user_response(command)
                            await self.session.send_tool_response(
                                function_responses=[
                                    types.FunctionResponse(
                                        id=call.id, name=tool_name, response=result
                                    )
                                ]
                            )

                if response.server_content and (
                    it := response.server_content.input_transcription
                ):
                    if not it.finished:
                        logging.info(f'[DIRECTOR] Interim transcript: "{it.text}"')

    async def run(self):
        """Main entry point to run the director application."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        client = genai.Client(api_key=api_key)

        with open("prompts/BOB_DIRECTOR.md", "r") as f:
            system_prompt = f.read()

        tools = [
            {
                "name": "process_user_command",
                "description": "Processes the user's speech to either start a new story or advance the current one.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "command": {
                            "type": "STRING",
                            "description": "The verbatim transcribed text of the user's speech (e.g., 'Tell me a story about a brave mouse', or 'Yes, please continue').",
                        }
                    },
                    "required": ["command"],
                },
                "response": {
                    "type": "OBJECT",
                    "properties": {
                        "narrative": {
                            "type": "STRING",
                            "description": "The part of the story for the assistant to speak.",
                        },
                        "is_story_finished": {
                            "type": "BOOLEAN",
                            "description": "True if this is the last part of the story, False otherwise.",
                        },
                    },
                },
            }
        ]

        logging.info("--- Aum's Journey Director ---")
        logging.info("Initializing...")
        logging.info("Press Ctrl+C to exit.")

        try:
            await self.orchestrator.hardware.connect_all()

            async with (
                client.aio.live.connect(
                    model="models/gemini-2.5-flash-preview-native-audio-dialog",
                    config={
                        "system_instruction": system_prompt,
                        "response_modalities": ["AUDIO"],
                        "input_audio_transcription": {},
                        "realtime_input_config": {"automatic_activity_detection": {}},
                        "tools": [{"function_declarations": tools}],
                    },
                ) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session

                tg.create_task(self.listen_and_send_audio())
                tg.create_task(self.play_audio())
                tg.create_task(self.receive_and_process())
                tg.create_task(self.listen_for_web_commands())  # Add the new task here

        except asyncio.CancelledError:
            pass
        except ExceptionGroup as eg:
            logging.error(f"[DIRECTOR] CRITICAL_ERROR: {eg.message}")
            for error in eg.exceptions:
                logging.error("--- Sub-exception ---")
                # Create a dummy exception to pass to print_exception
                try:
                    raise error
                except Exception:
                    logging.error(traceback.format_exc())
                logging.error("---------------------")
        except Exception as e:
            logging.error(f"[DIRECTOR] CRITICAL_ERROR: {e}")
            logging.error(traceback.format_exc())
        finally:
            self.pya.terminate()
            if self.orchestrator and hasattr(self.orchestrator, "hardware"):
                await self.orchestrator.hardware.close_all_ports()
            logging.info("--- Application shut down gracefully ---")
