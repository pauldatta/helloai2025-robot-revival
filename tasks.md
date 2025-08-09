# Aum's Journey Refactoring Tasks

This file tracks the necessary changes to fix the control flow between the `live_director` and the `orchestrator`.

## Core Architectural Refactoring
- [x] **Fix Orchestrator's Response Handling:** The orchestrator was updated to correctly parse responses from the Gemini API, handling cases where the model returned only tool calls, only text, or a mix of both. This resolved numerous `'NoneType'` and `TypeError` exceptions.

- [x] **Simplify the Live Director:** The `live_director`'s role was clarified. Its prompts and code were simplified to ensure it acts as a pure voice interface, passing the user's raw speech to the orchestrator without trying to interpret intent.

- [x] **Enhance the Orchestrator's Logic:** The orchestrator was completely refactored into a modular, single-API-call architecture. It now uses a single, intelligent prompt to infer user intent, execute hardware commands, and generate a narrative in one step.

- [x] **Verify the Corrected Flow:** The end-to-end flow is now working correctly. The `live_director` captures speech, the `orchestrator` controls the hardware and story, and the `hardware_emulator` shows the corresponding actions.

## Additional Refinements & Fixes
- [x] **Modular Code:** Both `orchestrator.py` and `hardware_controller.py` were refactored from monolithic scripts into clean, modular, class-based modules that are easier to read, test, and maintain.

- [x] **Robust Environment Handling:** A clear `dev` vs. `prod` environment switch was implemented using an `AUM_ENVIRONMENT` variable in the `.env` file. This ensures the application correctly connects to the hardware emulator during local development.

- [x] **Advanced Prompt Engineering:** The orchestrator's prompt (`AUM_ORCHESTRATOR.md`) was significantly improved to provide the model with the full story context, enabling it to handle conversational filler and answer questions that don't have a direct hardware action.

- [x] **Unit Tests:** The out-of-date `test_hardware_controller.py` was completely rewritten to be compatible with the new `HardwareManager` class.

## Project Status
All major architectural issues have been resolved. The application is now in a stable, feature-complete, and robust state.