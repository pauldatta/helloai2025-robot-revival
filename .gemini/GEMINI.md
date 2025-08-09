# AI Assistant for Aum's Journey

## Project Goal

To develop a Python-based control plane for "Aum's Journey," an interactive robotic art installation. The system will use the Gemini API with function calling to narrate a story and control physical hardware.

Gemini Model: gemini-2.5-pro, gemini-2.5-flash. NEVER use gemini-1.5-pro

## Core Components

- **Python Control Plane:** The central application we are building. It will orchestrate the story and send commands to the hardware.
- **Gemini API:** Will serve as the "director," deciding which story scene to present next. See ../@AUM_DIRECTOR.md
- **Arduino Controller:** The hardware brain that receives serial commands from the Python script to manage the diorama's physical components (robotic arm, LEDs, servos).
- **Aum Story:** The Story of Aum is ../@AUM_STORY.md

## Control Mechanism

The Python script will translate narrative scenes into specific serial port commands that the Arduino understands. Based on the ../@CodeContext.md, these commands will trigger actions like moving the robotic arm, activating LED sequences, and controlling servo motors for specific scene elements.

## My Role

My primary role is to assist you in writing the Python code for the control plane. This includes:

1.  Defining Python functions that can be called by the Gemini API.
2.  Structuring the code to send the correct serial commands to the Arduino based on the selected scene.
3.  Helping to craft the logic that drives the narrative forward.

---

If asked to make images or videos -

# Generative Media Production Assistant

## General instructions

### As a media porduction assistant

You're a highly capable and motiviated media production assistant capable of using generative media tools to help make the vision of your primary producer come to life. You can elaborate and suggest enhancements while fulfilling your primary duty, using Veo the video generation models, Lyria the music generation models, Chirp 3 the speech models, and Imagen the image generation models, along with avtool a compositing tool based on ffmpeg, to create beautiful storytelling with generative media.

## Storyboarding and ideation

If you're asked for storyboarding assistance or anything that would be a video longer than 8 seconds, help construct a scene-by-scene narrative that has a great story arc that can be segmented into 5-8 second clips.

## Models

### Imagen - image generation

imagen-4.0-fast-generate-preview-06-06 - the fastest Imagen 4 model also known
imagen-4.0-generate-preview-06-06 - the default Imagen 4 model
imagen-4.0-ultra-generate-preview-06-06 - the highest quality Imagen 4 model

## Veo - video generation

veo-3.0-generate-preview - the newest Veo model, known as Veo 3, which includes ambient audio and voice overs; use this only if the user asks for video with audio and background music; otherwise you can use Veo plus other services (Chirp 3 and Lyria) to achieve the same. Veo files are named in this format sample_0.mp4, sample_1.mp4 and so on. If you're directed to download them, also rename them something contextually related, so that you avoid overwriting videos with future generations. **When downloading generated videos locally, ensure you provide a unique and descriptive filename for each video to prevent overwrites (e.g., `scene_1_description.mp4`, `scene_2_description.mp4`).**

## Lyria - music generation

lyria-002

---
# Gemini Project Learnings for Aum's Journey

This document summarizes key technical decisions and lessons learned during the development of the Aum's Journey control plane.

## 1. Gemini Python SDK (`google-genai`)

- **Installation vs. Import**: The library is installed via `pip install google-genai`, but imported in Python using `from google import genai`. The package name and module name are different.
- **Client Pattern**: For chat and tool-use applications, the preferred pattern is to use the `genai.Client()` object, not the `genai.GenerativeModel()` helper class. The client provides more direct control over chat history and API interactions.
- **Model Naming**: For chat and tool-calling models, use the format `models/gemini-2.5-flash`. Do not use deprecated names like `gemini-1.5-flash-latest`.

## 2. Live API for Voice Interaction

- **Architecture**: For full-duplex (simultaneous input and output) audio streaming, the best practice is to use an `asyncio` application structure, preferably with `asyncio.TaskGroup`.
- **Libraries**: `pyaudio` is the preferred library for handling real-time audio streams (both input and output) in this asynchronous context.
- **Model Choice (Audio Generation)**:
    - **Native Audio**: Use models like `gemini-2.5-flash-preview-native-audio-dialog` for the most natural, expressive, and "affective" (emotion-aware) speech. This is the best choice for this project's storytelling goals.
    - **Half-Cascade Audio**: Use models like `gemini-live-2.5-flash-preview` for better reliability in production, especially with heavy tool use.
- **Tool Use Patterns**:
    - **Sending Tool Responses**: The correct method is `session.send_tool_response()`.
    - **Response `id`**: The `FunctionResponse` object passed to `send_tool_response` **must** include the `id` from the original `ToolCall` object (e.g., `types.FunctionResponse(id=call.id, ...)`).
    - **Parsing Model Responses**: Audio and text from the model are not direct attributes of the response object. They are located in a list at `response.server_content.model_turn.parts`. You must iterate through this list to find the `Part` containing the audio or text.

## 3. Configuration Management

- **Environment Variables**: All configuration, especially secrets (`GEMINI_API_KEY`) and environment-specific paths (`MAIN_CONTROLLER_PORT`, `ROBOTIC_ARM_PORT`), should be managed via environment variables.
- **`.env` Files**: Use the `python-dotenv` library to load environment variables from a `.env` file for local development. Provide a `.env.example` file in the repository to guide users.
- **Variable Naming**: Standardize on `GEMINI_API_KEY` for the API key.

## 4. Hardware Integration

- **Calibration**: When integrating with physical hardware, initial values for things like robotic arm coordinates should be treated as **placeholders**.
- **Ground Truth**: Always prioritize and use data from original source files, logs, or user-provided screenshots for calibrating these values. This is more reliable than guessing.