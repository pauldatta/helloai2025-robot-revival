# Gemini Live API Best Practices

This document summarizes key learnings and best practices for implementing the Gemini Live API, based on both official documentation and successful real-world implementations.

## 1. Configuration (`live.connect`)

-   **Use `types.LiveConnectConfig`:** Instead of a plain dictionary, use the `google.genai.types.LiveConnectConfig` object to define the session configuration. This provides better type safety and clarity.
-   **Model Selection:** For real-time, spoken conversation with tool use, `gemini-2.5-flash-preview-native-audio-dialog` is the preferred model.
-   **System Prompt:** The system prompt should be passed via the `system_instruction` field within the `LiveConnectConfig`.
-   **Speech & Voice Configuration:** For more natural-sounding speech, use the `speech_config` parameter to specify a `language_code` and a pre-built `voice_name`.

## 2. Voice Activity Detection (VAD)

-   **Enable by Default:** Automatic VAD is essential for a natural, interruptible conversation. It should be enabled by default (`disabled=False`).
-   **Tune Sensitivity and Timings:** The default VAD settings can be too sensitive. It is a best practice to fine-tune the following parameters within the `automatic_activity_detection` block:
    -   `start_of_speech_sensitivity`: `START_SENSITIVITY_LOW` is a good starting point to avoid triggering on background noise.
    -   `end_of_speech_sensitivity`: `END_SENSITIVITY_LOW` can also help.
    -   `silence_duration_ms`: Increase this value (e.g., to `1200`) to give the user more time to pause and think without the system cutting them off.
-   **Turn Coverage:** Set `turn_coverage` to `TURN_INCLUDES_ALL_INPUT` to ensure the model receives the complete user utterance, even if it's long.

## 3. Denoising and Audio Quality

-   **Denoising:** The Gemini Live API has built-in denoising capabilities. To enable it, you must include the `denoise` flag in the `input_audio` configuration.
-   **Sample Rate:** Ensure the audio you are sending matches the expected sample rate of the model (typically 16000 Hz).

## 4. Session Management

-   **Kick-off Message:** To start a conversation, send an initial, empty user turn immediately after the session is established. This prompts the AI to speak its first line based on its system instructions.
    ```python
    await session.send_client_content(
        turns={"role": "user", "parts": []}, turn_complete=True
    )
    ```

-   **Tool Responses:** When responding to a tool call, use `session.send_tool_response` and ensure the `id` of the `FunctionResponse` matches the `id` from the original `ToolCall`.
