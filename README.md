# Aum's Journey: An Interactive Robotic Art Installation

This project is the control plane for "Aum's Journey," an interactive robotic art installation that tells the true story of Aum, a man who found his way home after being lost for 15 years, using Google's voice search.

The system uses a two-tiered AI architecture powered by the Gemini API. A voice-activated **Live Director** handles real-time conversation, while a stateful **Orchestrator** interprets user intent, manages the story's progression, and controls the physical hardware.

## System Architecture

The application's logic is separated into a voice interface and a control plane. The **Live Director** captures the user's speech and passes it to the **Orchestrator**. The Orchestrator then uses the Gemini API to decide which hardware actions to take and what narrative to speak, passing the narrative back to the Director to be spoken aloud.

![System Architecture Diagram](context/new_architecture_diagram.svg)

## Project Structure

The project is organized into the following directories:
-   `src/`: Contains all the core Python source code for the application.
-   `prompts/`: Holds the system prompts that define the behavior of the AI director and orchestrator.
-   `tests/`: Contains the unit tests for the application.
-   `context/`: Contains story context, diagrams, and original hardware code.

## Getting Started

### 1. First-Time Setup
- **Install `socat`** (Required for Emulator Mode):
  - **macOS:** `brew install socat`
  - **Linux:** `sudo apt-get install socat`
- **Install Audio & Python Dependencies:**
  - **macOS:** `brew install portaudio`
  - **Linux:** `sudo apt-get install libportaudio2`
  - Then, install Python packages: `pip install -r requirements.txt`
- **Configure API Key:**
  - Copy `.env.example` to a new file named `.env`.
  - Edit `.env` and add your `GEMINI_API_KEY`.

### 2. Running in Emulator Mode (for Development)
- The application runs in **emulator mode** by default when you use `foreman`.
  ```bash
  source venv/bin/activate
  foreman start -f Procfile.dev
  ```

### 3. Running in Production Mode (with Hardware)
1.  **Find Your Port Names:** Connect your hardware and find the device paths (e.g., by running `ls /dev/tty.*`).
2.  **Configure `.env`:**
    - Open your `.env` file.
    - Set the environment to production: `AUM_ENVIRONMENT="prod"`
    - Set the correct port paths for your hardware (e.g., `MAIN_CONTROLLER_PORT="/dev/tty.usbmodem12345"`).
3.  **Run the Application:**
    - Start the main application directly as a module from the project root.
      ```bash
      source venv/bin/activate
      python -m src.main
      ```

### Example Log Output
The standardized logs clearly show the flow of information between the components.

```
[DIRECTOR] ---> User speech detected: "Show me his home."
[DIRECTOR] ---> Calling Orchestrator with command: "Show me his home."
[ORCHESTRATOR] ---> Received command: "Show me his home." | Current Scene: AWAITING_MODE_SELECTION
[ORCHESTRATOR] ---> Calling Gemini API.
[ORCHESTRATOR] <--- Received 1 tool call(s) from API.
[ORCHESTRATOR] ---> Executing tool call: move_robotic_arm({'p1': 2468, 'p2': 68, 'p3': 3447})
[HARDWARE] ---> Sent to Robotic Arm Controller: "3 50 50 50 5 5 5 2468 68 3447"
[ARM_EMU] <--- Received command: "3 50 50 50 5 5 5 2468 68 3447"
[ARM_EMU] ---> State updated. New position: [2468, 68, 3447]
[HARDWARE] <--- Received from Robotic Arm Controller: "angle:2468|68|3447"
[ORCHESTRATOR] <--- Updated scene to "AUMS_HOME". Returning narrative to Director.
[DIRECTOR] <--- Received narrative: "Aum ran away from this home when he was just seven years old." | New Scene: AUMS_HOME
```

### 4. Running Tests
- To verify the application's logic, run the unit tests:
  ```bash
  source venv/bin/activate
  python -m unittest discover tests
  ```