# Project "Bob the Curious Robot" - Phase 1 TODO (Multi-Turn Conversation)

This list outlines the steps to implement the new multi-turn conversational experience with Bob.

## Core Implementation Plan

1.  **Redefine AI Personas for Multi-Turn Conversation:**
    *   [x] **`BOB_STORYTELLER.md` (Conversation Engine):** Rewrite the prompt to make the AI the driver of a 3-5 turn conversation. It will receive the conversation history and its goal will be to generate the next question, select a relevant diorama scene, and decide when the conversation is complete.
    *   [x] **`BOB_DIRECTOR.md` (Conversational Guide):** Simplify the prompt to focus on facilitating the turn-by-turn interaction. It will ask the initial question, relay user answers, speak the next question from the Storyteller, and deliver the final QR code line.

2.  **Re-architect the Orchestrator for State Management:**
    *   [x] **State Tracking:** Refactor `StatefulOrchestrator` to manage `conversation_history` and `turn_number`.
    *   [x] **Implement `process_user_input` Method:** Create a new primary method in the orchestrator that:
        *   Checks for "stop commands" (e.g., "stop," "I'm done") to gracefully end the conversation.
        *   Appends the user's response to the `conversation_history`.
        *   Calls the `BOB_STORYTELLER` AI with the full history.
        *   Parses the AI's response (`next_question`, `scene_to_trigger`, `is_finished`).
        *   Triggers the hardware actions for the specified scene.
        *   Triggers the QR code display if the `is_finished` flag is true.
        *   Returns the result to the `LiveDirector`.
    *   [x] **Remove Single-Turn Logic:** Delete the now-obsolete `process_user_response` method.

3.  **Update the Live Director for Multi-Turn Flow:**
    *   [x] Modify the `AumDirectorApp` in `live_director.py` to manage the conversational loop, calling the orchestrator's `process_user_input` method repeatedly until the `is_finished` flag is received from the orchestrator.

4.  **Update Documentation and Housekeeping:**
    *   [ ] Ensure the `README.md` reflects the multi-turn conversational architecture.

5.  **Future Implementation (Post-Phase 1):**
    *   [ ] Implement a mechanism to save the captured `conversation_history` for each session.
    *   [ ] Create a new test suite to validate the multi-turn logic.
