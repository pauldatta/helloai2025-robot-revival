# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2025-08-08

### Added
- **Initial Implementation of Aum's Journey Director**
  - Created the core Python application for controlling the interactive diorama.
  - Implemented a real-time, full-duplex audio loop using the Gemini Live API for voice interaction.
  - Developed a modular hardware controller (`hardware_controller.py`) with validated tool functions to interface with serial ports.
  - Established a robust system prompt (`AUM_DIRECTOR.md`) with detailed story context, a scene-to-command map, and parameter validation rules.
  - Integrated configuration management using a `.env` file for API keys and serial port paths.
  - Added comprehensive unit tests for the hardware controller and an integration test for the live Gemini API.
  - Updated all documentation (`README.md`, `.gemini/GEMINI.md`, `context/CodeContext.md`) to reflect the new architecture and setup instructions.
