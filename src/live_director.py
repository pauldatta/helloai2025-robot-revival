import asyncio
import pyaudio
import traceback
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

    def process_user_command(self, command: str):
        """
        Processes the user's command by sending it to the orchestrator and
        returning the structured response.
        """
        print(f"[DIRECTOR] ---> Calling Orchestrator with command: \"{command}\"")
        # The orchestrator now returns a tuple: (narrative, scene_name)
        narrative, scene_name = self.orchestrator.process_user_command(command)
        print(f"[DIRECTOR] <--- Received narrative: \"{narrative}\" | New Scene: {scene_name}")
        # We return a dictionary, which becomes the JSON response for the tool call
        return {"narrative": narrative, "scene_name": scene_name}

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
        print("[DIRECTOR] Microphone is open. Start speaking.")
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
        print("[DIRECTOR] Audio output stream is open.")
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
                # Handle audio output from the model
                if response.server_content and response.server_content.model_turn:
                    for part in response.server_content.model_turn.parts:
                        if audio_data := getattr(part, "inline_data", None):
                            if audio_data.mime_type.startswith("audio/pcm"):
                                self.audio_in_queue.put_nowait(audio_data.data)

                # Handle tool calls requested by the model
                if response.tool_call:
                    for call in response.tool_call.function_calls:
                        tool_name = call.name
                        if tool_name == "process_user_command":
                            command = call.args["command"]
                            print(f"[DIRECTOR] ---> User speech detected: \"{command}\"")
                            # Execute the tool and get the structured result
                            result = self.process_user_command(command)
                            # Send the entire structured result back to the model
                            await self.session.send_tool_response(
                                function_responses=[types.FunctionResponse(id=call.id, name=tool_name, response=result)]
                            )

                # Optional: Print interim transcripts for debugging
                if response.server_content and (it := response.server_content.input_transcription):
                    if not it.finished:
                        print(f"[DIRECTOR] Interim transcript: \"{it.text}\"")

    async def run(self):
        """Main entry point to run the director application."""
        client = genai.Client()

        # Load the system prompt for the Live Director
        with open("prompts/AUM_DIRECTOR.md", "r") as f:
            system_prompt = f.read()
        
        # Define the tool schema for the one and only tool the director uses.
        tools = [
            {
                "name": "process_user_command",
                "description": "Processes the user's transcribed speech. This is the primary way the user interacts with the story.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "command": {
                            "type": "STRING",
                            "description": "The verbatim transcribed text of the user's speech.",
                        }
                    },
                    "required": ["command"],
                },
            }
        ]

        print("--- Aum's Journey Director ---")
        print("Initializing...")
        print("Press Ctrl+C to exit.")

        try:
            async with client.aio.live.connect(
                model="models/gemini-2.5-flash-preview-native-audio-dialog",
                config={
                    "system_instruction": system_prompt,
                    "response_modalities": ["AUDIO"],
                    "input_audio_transcription": {},
                    "realtime_input_config": {"automatic_activity_detection": {}},
                    "tools": [{"function_declarations": tools}],
                },
            ) as session, asyncio.TaskGroup() as tg:
                self.session = session
                
                tg.create_task(self.listen_and_send_audio())
                tg.create_task(self.play_audio())
                tg.create_task(self.receive_and_process())

        except asyncio.CancelledError:
            pass
        except ExceptionGroup as eg:
            print(f"[DIRECTOR] CRITICAL_ERROR: {eg.message}")
            for error in eg.exceptions:
                print("--- Sub-exception ---")
                traceback.print_exception(error)
                print("---------------------")
        except Exception as e:
            print(f"[DIRECTOR] CRITICAL_ERROR: {e}")
            traceback.print_exc()
        finally:
            self.pya.terminate()
            if self.orchestrator and hasattr(self.orchestrator, 'hardware'):
                self.orchestrator.hardware.close_all_ports()
            print("--- Application shut down gracefully ---")
