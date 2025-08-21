# Bob the Curious Robot: An Interactive Diorama Experience

This project is the control plane for "Bob the Curious Robot," an interactive robotic art installation. Bob is a curious robot who lives in a small diorama town and longs to learn about the world outside. Through a voice-driven, conversational experience, Bob asks users about their world and connects their answers to the scenes in his own.

The system uses a voice-activated AI architecture powered by the Gemini API. A **Live Director** handles real-time conversation, passing the user's speech to a stateful **Orchestrator**. The Orchestrator processes the user's response, determines the appropriate scene in the diorama, generates a creative narrative, and triggers all corresponding hardware actions. At the end of the interaction, it presents a QR code to transition the user to a digital experience.

## System Architecture

The application is built on a stateful, multi-turn conversational architecture designed to create a natural, curious interaction with Bob.

1.  **Live Director (`live_director.py`):** The voice interface. It captures the user's speech, relays it to the Orchestrator, and speaks the next question that the AI generates. It is responsible for the turn-by-turn flow of the conversation.
2.  **Orchestrator (`orchestrator.py`):** The "brain" of the operation. It maintains the `conversation_history` and `turn_number`. With each user response, it calls the Gemini API, providing the full conversation history as context.
3.  **Conversation Engine (`prompts/BOB_STORYTELLER.md`):** This is the core creative AI. It receives the conversation history and generates the next logical question for Bob to ask, chooses a relevant diorama scene to trigger, and determines when the conversation has reached a natural conclusion (after 3-5 turns).
4.  **Scene-to-Action Mapping (`orchestrator.py`):** A simple Python dictionary (`SCENE_ACTIONS`) maps scene names to a list of hardware commands, decoupling the AI's creative decisions from the physical hardware execution.

![System Architecture Diagram](context/new_architecture_diagram.svg)

## Mission Control Web Interface

The project includes a real-time web interface for monitoring and control, accessible at `http://localhost:8000`. It provides a live log stream, a parsed conversation transcript, and a system status panel. The interface also includes manual controls for triggering scenes and moving the robotic arm, which is essential for calibration.

At the end of each interaction, the web interface will display a QR code, allowing the user to continue their journey on a digital platform.

![Mission Control Web Interface](context/aums_web_admin.png)

## Project Structure

-   `src/`: Contains all the core Python source code.
-   `prompts/`: Holds the system prompts that define the AI personas for Bob.
-   `web/`: Contains the FastAPI web server and the HTML/JS for the Mission Control interface.
-   `context/`: Contains project context, diagrams, and original hardware code.

## Customizing Scenes and Actions

The core of the installation's physical behavior is defined in the `SCENE_ACTIONS` dictionary, located at the top of the `src/orchestrator.py` file. This dictionary maps a narrative scene name to a sequence of hardware actions, making it easy to customize the experience without altering the core logic.

### Structure

Each scene is a key in the dictionary. Its value is a list of action objects, where each object has an `action` and `params` key.

```python
"SCENE_NAME": [
    {"action": "action_type_1", "params": {"param_a": "value_1"}},
    {"action": "action_type_2", "params": {"param_b": 123}},
]
```

### Available Actions

| Action                    | Description                                                                                                     | Parameters                                                              |
| ------------------------- | --------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| `trigger_diorama_scene`   | Sends a numeric ID to the main Arduino controller to trigger a specific, pre-programmed light and motor sequence. | `scene_command_id` (integer): The ID for the scene in the Arduino code. |
| `move_robotic_arm`        | Moves the robotic arm to a specific coordinate.                                                                 | `p1`, `p2`, `p3` (integers): The coordinates for the arm's position.      |
| `play_video`              | Plays a video file on the connected tablet. Video files are located in the `context/` directory.                  | `video_file` (string): The name of the video file.                      |

## Development Workflow with Gemini CLI

This project includes custom commands for the Gemini CLI to accelerate common development tasks. These commands are defined in the `.gemini/commands/` directory.

| Command                         | Description                                                                                                                                                  |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `/context:refresh`              | Reloads the Gemini API and project convention documents from the `context/` directory. Use this if the assistant seems to be forgetting project-specific details. |
| `/dev:test`                     | Runs the complete Python unit test suite using the virtual environment.                                                                                      |
| `/git:commit_and_push [message]` | Initiates an interactive commit and push. It will analyze staged changes and generate a Conventional Commit message if one isn't provided.                   |

## Getting Started

### 1. Initial Setup

- **Install `socat`** (Required for Emulator Mode on macOS/Linux):
  - **macOS:** `brew install socat`
- **Install Audio & Python Dependencies:**
  - **macOS:** `brew install portaudio`
  - Then, install Python packages: `pip install -r requirements.txt`
- **Install Git Hooks:**
  - `pre-commit install`
- **Configure API Key:**
  - Copy `.env.example` to `.env` and add your `GEMINI_API_KEY`.

### 2. Running the Application

#### Development (Emulator Mode)

For local development without physical hardware.

1.  **Activate Virtual Environment:**
    ```bash
    source venv/bin/activate
    ```
2.  **Start Services with Foreman:**
    ```bash
    foreman start -f Procfile.dev
    ```
    The web interface will be available at `http://localhost:8000`.

#### Production (with Hardware)

1.  **Configure Environment:**
    - In your `.env` file, set `AUM_ENVIRONMENT="prod"`.
    - Set the correct serial port paths for your hardware. The production Mac mini uses the following:
      - **Main Controller (OpenCR Board):** `MAIN_CONTROLLER_PORT="/dev/cu.usbmodem1421"`
      - **Robotic Arm (IOUSBHostDevice):** `ROBOTIC_ARM_PORT="/dev/cu.usbmodem1461"`
2.  **Run with Foreman:**
    ```bash
    source ven/bin/activate
    foreman start -f Procfile.prod
    ```


## Getting Started

### 1. Initial Setup

- **Install `socat`** (Required for Emulator Mode on macOS/Linux):
  - **macOS:** `brew install socat`
- **Install Audio & Python Dependencies:**
  - **macOS:** `brew install portaudio`
  - Then, install Python packages: `pip install -r requirements.txt`
- **Install Git Hooks:**
  - `pre-commit install`
- **Configure API Key:**
  - Copy `.env.example` to `.env` and add your `GEMINI_API_KEY`.

### 2. Running the Application

#### Development (Emulator Mode)

For local development without physical hardware.

1.  **Activate Virtual Environment:**
    ```bash
    source venv/bin/activate
    ```
2.  **Start Services with Foreman:**
    ```bash
    foreman start -f Procfile.dev
    ```
    The web interface will be available at `http://localhost:8000`.

#### Production (with Hardware)

1.  **Configure Environment:**
    - In your `.env` file, set `AUM_ENVIRONMENT="prod"`.
    - Set the correct serial port paths for your hardware (e.g., `MAIN_CONTROLLER_PORT` and `ROBOTIC_ARM_PORT`).
2.  **Run with Foreman:**
    ```bash
    source venv/bin/activate
    foreman start -f Procfile.prod
    ```