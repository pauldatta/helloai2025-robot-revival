# Project "Bob the Curious Robot" - Phase 1 TODO

This list outlines the steps to implement the new project direction as defined in the PRD.

## Core Implementation Plan

1.  **Establish Bob's AI Personas (Prompt Engineering):**
    *   [x] Rename `prompts/AUM_DIRECTOR.md` to `prompts/BOB_DIRECTOR.md` and rewrite the prompt to create Bob's "curious robot" persona, including his initial hook question and conversational logic.
    *   [x] Rename `prompts/AUM_STORYTELLER.md` to `prompts/BOB_STORYTELLER.md` and update its instructions to creatively link external user concepts (e.g., "hiking") to existing diorama scenes with a "Pixar-style" narrative, driven by curiosity.

2.  **Implement Narrative Branching in the Orchestrator (`orchestrator.py`):**
    *   [x] Modify the `StatefulOrchestrator` to handle the two main narrative branches.
    *   [x] Implement an "Activity Branch" using keyword matching for user responses that directly relate to diorama scenes.
    *   [x] Implement a "Generative Scene Branch" that invokes the `BOB_STORYTELLER` for external concepts.

3.  **Integrate the Digital Transition (Web-Based QR Code):**
    *   [x] **Web Server (`web/server.py`):** Update the WebSocket handler to broadcast a `display_qr` message to all connected browser clients.
    *   [x] **Web Page (`web/index.html`):** Add a hidden QR code element and the JavaScript logic to make it visible when a `display_qr` message is received via WebSocket.
    *   [x] **Orchestrator (`orchestrator.py`):** At the end of a story, call a method in the `LiveDirector` to send the QR code command to the web server.
    *   [x] **Live Director (`live_director.py`):** Implement the method that sends the `display_qr` JSON command over its existing WebSocket connection.

4.  **Refactor to Single-Turn Conversation:**
    *   [x] Simplify the `StatefulOrchestrator` to a single-turn model, removing `advance_story` and related state.
    *   [x] Simplify the `AumDirectorApp` to match the single-turn flow.
    *   [x] Remove obsolete "GUIDED_MODE" aliases from `SCENE_ACTIONS`.

## Documentation and Housekeeping

5.  **Update README.md:**
    *   [ ] Update the project's `README.md` to reflect the new premise, goals, and architecture centered around "Bob the Curious Robot."

## Development Approach

6.  **Mindful Changes:**
    *   [x] Throughout this process, I will be mindful of the existing architecture. I will adapt and rename files and components logically rather than performing destructive deletions, ensuring a smooth transition to the new project direction.
