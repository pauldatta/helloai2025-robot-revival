import asyncio
import pyaudio
import traceback
from exceptiongroup import ExceptionGroup
from google import genai
from google.genai import types

# Import the new orchestrator and the hardware controller for closing ports
from orchestrator import StatefulOrchestrator
from hardware_controller import close_all_ports, trigger_diorama_scene, move_robotic_arm

# --- Audio Configuration ---
FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024

class AumDirectorApp:
    def __init__(self):
        # The director_persona is now handled by the orchestrator's prompt
        self.orchestrator = StatefulOrchestrator()
        self.pya = pyaudio.PyAudio()
        self.audio_in_queue = asyncio.Queue()
        self.session = None
        self.final_transcript = ""

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
        """Receives responses from Gemini, plays audio, and delegates decisions to the orchestrator."""
        while True:
            if not self.session:
                await asyncio.sleep(0.1)
                continue

            turn = self.session.receive()
            async for response in turn:
                # Handle audio output
                if response.server_content and response.server_content.model_turn:
                    for part in response.server_content.model_turn.parts:
                        if audio_data := getattr(part, 'inline_data', None):
                            if audio_data.mime_type.startswith('audio/pcm'):
                                self.audio_in_queue.put_nowait(audio_data.data)
                
                # Handle transcription and delegation
                if response.speech_to_text and (stt := response.speech_to_text.result):
                    if stt.is_final:
                        self.final_transcript += stt.text
                        print(f"User (final): {self.final_transcript}")

                        # --- DELEGATION POINT ---
                        # Once we have a final transcript, send it to the orchestrator
                        if self.final_transcript.strip():
                            narrative, _ = self.orchestrator.process_user_command(self.final_transcript)
                            
                            # Send the narrative back to the live API to be spoken
                            print(f"--> Speaking Narrative: {narrative}")
                            await self.session.send_text_input(narrative)
                        
                        self.final_transcript = "" # Reset for the next utterance
                    else:
                        print(f"User (interim): {stt.text}")


    async def run(self):
        """Main entry point to run the director application."""
        client = genai.Client()
        # Tools are now managed by the orchestrator, not the live director
        tools = [trigger_diorama_scene, move_robotic_arm]

        print("Starting Aum's Journey Director...")
        print("Use headphones to prevent audio feedback loops.")
        print("Press Ctrl+C to exit.")

        try:
            # The system prompt is now managed by the orchestrator.
            # The live model is only for speech-to-text and text-to-speech.
            async with client.aio.live.connect(
                model="models/gemini-live-2.5-flash-preview",
                config=types.LiveConnectConfig(
                    response_modalities=["AUDIO", "TEXT"],
                )
            ) as session, asyncio.TaskGroup() as tg:
                self.session = session
                # Send an initial empty text input to start the session
                await self.session.send_text_input(" ")
                
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