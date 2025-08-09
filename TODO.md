# Project TODO List

This file tracks planned improvements and bug fixes for the Aum's Journey project.

## High Priority

### 1. Implement Robust Speech Processing Lock in `live_director.py`

-   **Problem:** The system sometimes processes the same user speech twice (double speech detection), likely due to echo or VAD re-triggering on the system's own audio output. This disrupts the conversational flow.
-   **Proposed Solution:** Implement a robust, event-driven locking mechanism using `asyncio.Event`.
    -   Create an `asyncio.Event` named `can_process_speech`, initially set to `True`.
    -   When user speech is detected and a command is sent to the orchestrator, immediately clear the event (`can_process_speech.clear()`).
    -   Monitor the audio playback queue. When the queue is empty and the last audio chunk has been played, set the event (`can_process_speech.set()`).
    -   This will ensure new speech is only processed after the system has completely finished speaking its response.

## Medium Priority

### 2. Improve Conversational AI for Filler Text

-   **Problem:** The AI currently defaults to a fallback message ("I didn't catch that") when the user provides short, conversational filler like "Um," "Okay," or "Wow."
-   **Proposed Solution:** Enhance the `AUM_ORCHESTRATOR.md` prompt with more specific instructions and examples for how to handle this kind of conversational input gracefully, perhaps by offering a gentle prompt for the next action (e.g., "It's quite a story. What would you like to see next?").

## Completed

-   **FIXED:** Hardware operations were timing out because the `MainSceneEmulator` and `RoboticArmEmulator` were not sending confirmation messages back to the `HardwareManager`. This has been resolved by adding immediate `write()` calls in the emulators after a command is received.
