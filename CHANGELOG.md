# Changelog

All notable changes to this project will be documented in this file.

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