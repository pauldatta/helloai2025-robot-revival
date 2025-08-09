Here is the MD file with the Python code and documentation examples from [the provided URL.](https://ai.google.dev/gemini-api/docs/live-guide)

`````markdown
# Gemini API Live API Capabilities Guide

This guide covers the capabilities and configurations available with the Gemini Live API.

## Establishing a connection

The following example shows how to create a connection with an API key.

```python
import asyncio
from google import genai

# Note: Replace with your actual API key
client = genai.Client()

model = "gemini-live-2.5-flash-preview"
config = {"response_modalities": ["TEXT"]}

async def main():
    async with client.aio.live.connect(model=model, config=config) as session:
        print("Session started")

if __name__ == "__main__":
    asyncio.run(main())
```

**Note:** You can only set one modality in the `response_modalities` field. This means that you can configure the model to respond with either text or audio, but not both in the same session.

## Interaction modalities

The following sections provide examples and supporting context for the different input and output modalities available in Live API.

### Sending and receiving text

Here's how you can send and receive text:

```python
import asyncio
from google import genai

client = genai.Client()
model = "gemini-live-2.5-flash-preview"
config = {"response_modalities": ["TEXT"]}

async def main():
    async with client.aio.live.connect(model=model, config=config) as session:
        message = "Hello, how are you?"
        await session.send_client_content(
            turns={"role": "user", "parts": [{"text": message}]},
            turn_complete=True
        )
        async for response in session.receive():
            if response.text is not None:
                print(response.text, end="")

if __name__ == "__main__":
    asyncio.run(main())
```

### Incremental content updates

Use incremental updates to send text input, establish session context, or restore session context. For short contexts you can send turn-by-turn interactions to represent the exact sequence of events:

```python
import asyncio
from google import genai

client = genai.Client()
model = "gemini-live-2.5-flash-preview"
config = {"response_modalities": ["TEXT"]}

async def main():
    async with client.aio.live.connect(model=model, config=config) as session:
        turns = [
            {"role": "user", "parts": [{"text": "What is the capital of France?"}]},
            {"role": "model", "parts": [{"text": "Paris"}]},
        ]
        await session.send_client_content(turns=turns, turn_complete=False)

        turns = [{"role": "user", "parts": [{"text": "What is the capital of Germany?"}]}]
        await session.send_client_content(turns=turns, turn_complete=True)

        async for response in session.receive():
            if response.text is not None:
                print(response.text, end="")

if __name__ == "__main__":
    asyncio.run(main())
```

For longer contexts it's recommended to provide a single message summary to free up the context window for subsequent interactions.

### Sending and receiving audio

Here's an audio-to-text example that reads a WAV file, sends it in the correct format and receives text output:

```python
# Test file: https://storage.googleapis.com/generativeai-downloads/data/16000.wav
# Install helpers for converting files: pip install librosa soundfile
import asyncio
import io
from pathlib import Path
from google import genai
from google.genai import types
import soundfile as sf
import librosa

client = genai.Client()
model = "gemini-live-2.5-flash-preview"
config = {"response_modalities": ["TEXT"]}

async def main():
    async with client.aio.live.connect(model=model, config=config) as session:
        buffer = io.BytesIO()
        y, sr = librosa.load("sample.wav", sr=16000)
        sf.write(buffer, y, sr, format='RAW', subtype='PCM_16')
        buffer.seek(0)
        audio_bytes = buffer.read()

        # If already in correct format, you can use this:
        # audio_bytes = Path("sample.pcm").read_bytes()

        await session.send_realtime_input(
            audio=types.Blob(data=audio_bytes, mime_type="audio/pcm;rate=16000")
        )

        async for response in session.receive():
            if response.text is not None:
                print(response.text)

if __name__ == "__main__":
    asyncio.run(main())
```

And here is a text-to-audio example. You can receive audio by setting `AUDIO` as response modality. This example saves the received data as WAV file:

```python
import asyncio
import wave
from google import genai

client = genai.Client()
model = "gemini-live-2.5-flash-preview"
config = {"response_modalities": ["AUDIO"]}

async def main():
    async with client.aio.live.connect(model=model, config=config) as session:
        with wave.open("audio.wav", "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)

            message = "Hello how are you?"
            await session.send_client_content(
                turns={"role": "user", "parts": [{"text": message}]},
                turn_complete=True
            )

            async for response in session.receive():
                if response.data is not None:
                    wf.writeframes(response.data)

if __name__ == "__main__":
    asyncio.run(main())
```

### Audio transcriptions

You can enable transcription of the model's audio output by sending `output_audio_transcription` in the setup config.

```python
import asyncio
from google import genai
from google.genai import types

client = genai.Client()
model = "gemini-live-2.5-flash-preview"
config = {
    "response_modalities": ["AUDIO"],
    "output_audio_transcription": {}
}

async def main():
    async with client.aio.live.connect(model=model, config=config) as session:
        message = "Hello? Gemini are you there?"
        await session.send_client_content(
            turns={"role": "user", "parts": [{"text": message}]},
            turn_complete=True
        )
        async for response in session.receive():
            if response.server_content.model_turn:
                print("Model turn:", response.server_content.model_turn)
            if response.server_content.output_transcription:
                print("Transcript:", response.server_content.output_transcription.text)

if __name__ == "__main__":
    asyncio.run(main())
```

You can enable transcription of the audio input by sending `input_audio_transcription` in setup config.

````python
import asyncio
from pathlib import Path
from google import genai
from google.genai import types

client = genai.Client()
model = "gemini-live-2.5-flash-preview"
config = {
    "response_modalities": ["TEXT"],
    "input_audio_transcription": {},
}

async def main():
    async with client.aio.live.connect(model=model, config=config) as session:
        audio_data = Path("16000.pcm").read_bytes()
        await session.send_realtime_input(
            audio=types.Blob(data=audio_data, mime_type='audio/pcm;rate=16000')
        )
        async for msg in session.receive():
            if msg.server_content.input_transcription:
                print('Transcript:', msg.server_content.input_transcription.text)

if __name__ == "__main__":
    asyncio.run(main())```

## Voice Activity Detection (VAD)

Voice Activity Detection (VAD) allows the model to recognize when a person is speaking. This is essential for creating natural conversations, as it allows a user to interrupt the model at any time.

When VAD detects an interruption, the ongoing generation is canceled and discarded.

### Automatic VAD

By default, the model automatically performs VAD on a continuous audio input stream.

```python
import asyncio
from pathlib import Path
from google import genai
from google.genai import types

client = genai.Client()
model = "gemini-live-2.5-flash-preview"
config = {"response_modalities": ["TEXT"]}

async def main():
    async with client.aio.live.connect(model=model, config=config) as session:
        audio_bytes = Path("sample.pcm").read_bytes()
        await session.send_realtime_input(
            audio=types.Blob(data=audio_bytes, mime_type="audio/pcm;rate=16000")
        )
        # if stream gets paused, send:
        # await session.send_realtime_input(audio_stream_end=True)
        async for response in session.receive():
            if response.text is not None:
                print(response.text)

if __name__ == "__main__":
    asyncio.run(main())
````
`````

### Automatic VAD configuration

For more control over the VAD activity, you can configure the following parameters.

```python
from google.genai import types

config = {
    "response_modalities": ["TEXT"],
    "realtime_input_config": {
        "automatic_activity_detection": {
            "disabled": False,  # default
            "start_of_speech_sensitivity": types.StartSensitivity.START_SENSITIVITY_LOW,
            "end_of_speech_sensitivity": types.EndSensitivity.END_SENSITIVITY_LOW,
            "prefix_padding_ms": 20,
            "silence_duration_ms": 100,
        }
    }
}
```

### Disable automatic VAD

Alternatively, the automatic VAD can be disabled by setting `realtimeInputConfig.automaticActivityDetection.disabled` to `True` in the setup message.

```python
config = {
    "response_modalities": ["TEXT"],
    "realtime_input_config": {"automatic_activity_detection": {"disabled": True}},
}

async with client.aio.live.connect(model=model, config=config) as session:
    # ...
    await session.send_realtime_input(activity_start=types.ActivityStart())
    await session.send_realtime_input(
        audio=types.Blob(data=audio_bytes, mime_type="audio/pcm;rate=16000")
    )
    await session.send_realtime_input(activity_end=types.ActivityEnd())
    # ...
```

## Token count

You can find the total number of consumed tokens in the `usageMetadata` field of the returned server message.

```python
async for message in session.receive():
    # The server will periodically send messages that include UsageMetadata.
    if message.usage_metadata:
        usage = message.usage_metadata
        print(f"Used {usage.total_token_count} tokens in total. Response token breakdown:")
        for detail in usage.response_tokens_details:
            match detail:
                case types.ModalityTokenCount(modality=modality, token_count=count):
                    print(f"{modality}: {count}")
```

```

```
