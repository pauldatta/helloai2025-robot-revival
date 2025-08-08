
import asyncio
import pyaudio
import traceback
from exceptiongroup import ExceptionGroup
from google import genai
from google.genai import types

# Import the hardware control functions
from hardware_controller import trigger_diorama_scene, move_robotic_arm, close_all_ports

# --- Audio Configuration ---
FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024

class AumDirectorApp:
    def __init__(self, director_persona: str):
        self.director_persona = director_persona
        self.pya = pyaudio.PyAudio()
        self.audio_in_queue = asyncio.Queue()
        self.session = None

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
        print("Microphone is open. Start speaking.")
        while True:
            data = await asyncio.to_thread(stream.read, CHUNK_SIZE, exception_on_overflow=False)
            if self.session:
                await self.session.send_realtime_input(audio={"data": data, "mime_type": "audio/pcm"})

    async def play_audio(self):
        """Plays audio from a queue to the speakers."""
        stream = self.pya.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RECEIVE_SAMPLE_RATE,
            output=True,
        )
        while True:
            chunk = await self.audio_in_queue.get()
            await asyncio.to_thread(stream.write, chunk)

    async def receive_and_process(self):
        """Receives responses from Gemini, plays audio, and handles function calls."""
        while True:
            if not self.session:
                await asyncio.sleep(0.1)
                continue

            turn = self.session.receive()
            async for response in turn:
                if response.server_content and response.server_content.model_turn:
                    for part in response.server_content.model_turn.parts:
                        if audio_data := getattr(part, 'inline_data', None):
                            if audio_data.mime_type.startswith('audio/pcm'):
                                self.audio_in_queue.put_nowait(audio_data.data)
                        if text := getattr(part, 'text', None):
                            print(f"Director (transcribed/text): {text}")

                if response.tool_call and (function_calls := response.tool_call.function_calls):
                    for call in function_calls:
                        # Log the intended tool call
                        args_str = ', '.join(f'{k}={v}' for k, v in call.args.items())
                        print(f"--> Calling Tool: {call.name}({args_str})")

                        if call.name == "trigger_diorama_scene":
                            result = await asyncio.to_thread(trigger_diorama_scene, **call.args)
                        elif call.name == "move_robotic_arm":
                            result = await asyncio.to_thread(move_robotic_arm, **call.args)
                        else:
                            result = f"Error: Unknown function '{call.name}' called by model."
                            print(result)
                            continue
                        
                        # Log the result of the tool call
                        print(f"<-- Tool Result: {result}")
                        
                        await self.session.send_tool_response(
                            function_responses=[types.FunctionResponse(id=call.id, name=call.name, response={"content": result})]
                        )

    async def run(self):
        """Main entry point to run the director application."""
        client = genai.Client()
        tools = [trigger_diorama_scene, move_robotic_arm]

        print("Starting Aum's Journey Director...")
        print("Use headphones to prevent audio feedback loops.")
        print("Press Ctrl+C to exit.")

        try:
            async with client.aio.live.connect(
                model="models/gemini-live-2.5-flash-preview",
                config=types.LiveConnectConfig(
                    system_instruction=types.Content(parts=[types.Part.from_text(text=self.director_persona)]),
                    response_modalities=["AUDIO"],
                    tools=tools
                )
            ) as session, asyncio.TaskGroup() as tg:
                self.session = session
                tg.create_task(self.listen_and_send_audio())
                tg.create_task(self.play_audio())
                tg.create_task(self.receive_and_process())

        except asyncio.CancelledError:
            pass
        except ExceptionGroup as eg:
            print(f"An unexpected error occurred: {eg.message}")
            for error in eg.exceptions:
                print("--- Sub-exception ---")
                traceback.print_exception(error)
                print("---------------------")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            traceback.print_exc()
        finally:
            self.pya.terminate()
            close_all_ports()
            print("Application shut down gracefully.")
