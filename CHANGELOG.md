# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2025-08-22

### Added
- **New Persona: "Bob the Curious Robot"**
  - Introduced a new central character, Bob, a curious robot who engages users in a multi-turn conversation to learn about their world.
  - Created new AI prompts (`BOB_DIRECTOR.md`, `BOB_STORYTELLER.md`) to define Bob's persona and drive the conversation.
- **Multi-Turn Conversational Architecture**
  - Implemented a stateful orchestrator that manages conversation history and turn numbers.
  - The AI now asks 3-5 follow-up questions based on the user's previous answers.
  - Added "stop commands" to allow users to gracefully end the conversation.
- **Web-Based QR Code Transition**
  - Integrated a web-based QR code display at the end of each conversation to transition the user to a digital experience.
  - Updated the web server and UI to handle WebSocket commands for displaying the QR code.
- **Refined Mission Control UI**
  - Rebranded the UI for "Bob the Curious Robot."
  - Added a "Conversation State" panel to monitor the turn number and conversation history.
  - Implemented a "Reset Conversation" button to allow for easy testing and debugging.

### Changed
- **Project Pivot from "Aum's Journey"**
  - The project's core concept has been pivoted from a linear narrative about Aum to an interactive, curious conversation with Bob.
- **Simplified Orchestrator Logic**
  - Refactored the orchestrator to a single `process_user_input` method, removing the previous story-based logic.
- **Updated Live Director**
  - The `LiveDirector` has been updated to handle the new multi-turn conversational flow and kick off the conversation automatically.

### Removed
- Removed the diorama map from the Mission Control UI as it was no longer needed.
- Removed obsolete video files and test suites related to the previous "Aum's Journey" narrative.

## [Unreleased] - 2025-08-08

### Added
- **Hardware Emulator and Controller Refactor**
  - Implemented a high-fidelity hardware emulator (`hardware_emulator.py`) to simulate both the main scene and robotic arm controllers, allowing for development without physical hardware.
  - Added `Procfile.dev` to manage the emulator and director processes concurrently using Foreman.
  - Updated the `README.md` to include instructions for running the emulator and an example of the expected log output.

### Changed
- **Improved Testability and Robustness**
  - Refactored `hardware_controller.py` to use lazy initialization for serial connections, preventing the test suite from hanging on import.
  - Updated `test_hardware_controller.py` with comprehensive mocks to isolate the controller from file system and serial port dependencies, ensuring reliable and fast unit tests.
  - Corrected the serial data reading method in the emulator to reliably process incoming commands.

### Fixed
- Resolved an issue where the hardware emulator was not displaying received commands in the logs.
- Fixed a bug where unit tests would hang due to immediate serial port initialization.

---

### Previous Changes

### Added
- **Initial Implementation of Aum's Journey Director**
  - Created the core Python application for controlling the interactive diorama.
  - Implemented a real-time, full-duplex audio loop using the Gemini Live API for voice interaction.
  - Developed a modular hardware controller (`hardware_controller.py`) with validated tool functions to interface with serial ports.
  - Established a robust system prompt (`AUM_DIRECTOR.md`) with detailed story context, a scene-to-command map, and parameter validation rules.
  - Integrated configuration management using a `.env` file for API keys and serial port paths.
  - Added comprehensive unit tests for the hardware controller and an integration test for the live Gemini API.
  - Updated all documentation (`README.md`, `.gemini/GEMINI.md`, `context/CodeContext.md`) to reflect the new architecture and setup instructions.