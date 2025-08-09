# Project Plan & Debugging Log

This document outlines the key challenges encountered and the solutions implemented during the development of the Aum's Journey interactive experience.

## 1. Initial Architecture & Core Problem

- **Problem:** The initial implementation had a confused architecture. The `live_director` (voice interface) was trying to interpret user intent and was sending pre-formatted tool calls as text to the `orchestrator`. The `orchestrator` was not executing hardware commands and would often crash.
- **Solution:** A major refactoring was undertaken to establish a clear separation of concerns:
  - The `live_director` was simplified to be a pure voice-to-text/text-to-speech layer. Its only job is to pass the user's raw speech to the orchestrator.
  - The `orchestrator` was made the single "brain" of the operation, responsible for all story logic, state management, and hardware control.

## 2. Environment Configuration (`dev` vs. `prod`)

- **Problem:** The application was not reliably detecting the local development environment, causing it to try and connect to real hardware ports instead of the hardware emulator. This resulted in no hardware logs and the system running in a silent "mock" mode.
- **Solution:**
  - **Explicit Environment Variable:** An `AUM_ENVIRONMENT` variable was introduced to explicitly switch between `dev` and `prod` modes.
  - **`.env.example`:** A `.env.example` file was created to provide clear instructions for setting up the local development environment.
  - **Robust Port Selection:** The `HardwareManager` was updated to read the `AUM_ENVIRONMENT` variable and select the correct set of serial ports.

## 3. Gemini API Integration & Logic

- **Problem:** There were numerous bugs related to the interaction with the Gemini API.
  - The model would return tool calls but no narrative text, causing the orchestrator to crash or give a generic, unhelpful response.
  - The application was attempting to use structured JSON output (`response_mime_type`) in combination with function calling, which is an unsupported feature of the API.
  - The model was not intelligently inferring user intent from conversational language.
- **Solution:**
  - **Intelligent Single-Prompt Architecture:** The logic was refactored to use a single, unified prompt (`AUM_ORCHESTRATOR.md`) and a single API call.
  - **Smarter Prompt Engineering:** The orchestrator's prompt was significantly enhanced to instruct the model to infer user intent, handle conversational filler, and _always_ return both tool calls and a JSON narrative in the same turn.
  - **Robust Code:** The Python code was updated to correctly parse the mixed response of tool calls and text from the model, making the system resilient to variations in the API's output.

## 4. Code Quality & Modularity

- **Problem:** The initial Python scripts had monolithic functions and used global variables, making them difficult to test and debug.
- **Solution:**
  - **`hardware_controller.py`:** Refactored to use a `HardwareManager` class, encapsulating all hardware logic and removing global variables.
  - **`orchestrator.py`:** Refactored to break down the main processing logic into smaller, single-purpose helper functions, improving readability and maintainability.
  - **Unit Tests:** The old, broken unit tests were completely rewritten to be compatible with the new, modular, class-based architecture.
