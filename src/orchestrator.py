import asyncio
import json
import logging
import os
from google import genai
from google.genai import types
from .hardware_controller import HardwareManager

# --- Scene to Action Mapping ---
SCENE_ACTIONS = {
    "HOME": [
        {"action": "play_video", "params": {"video_file": "05Talking.mp4"}},
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 2}},
        {"action": "move_robotic_arm", "params": {"p1": 2900, "p2": 2600, "p3": 130}},
    ],
    "REFLECTION_POOL": [
        {"action": "play_video", "params": {"video_file": "06Sad.mp4"}},
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 4}},
        {"action": "move_robotic_arm", "params": {"p1": 2500, "p2": 2600, "p3": 550}},
    ],
    "SPORTS_GROUND": [
        {"action": "play_video", "params": {"video_file": "08Excited.mp4"}},
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 5}},
        {"action": "move_robotic_arm", "params": {"p1": 1950, "p2": 2900, "p3": 4000}},
    ],
    "MARKET": [
        {"action": "play_video", "params": {"video_file": "02Thoughtful.mp4"}},
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 3}},
        {"action": "move_robotic_arm", "params": {"p1": 3413, "p2": 2700, "p3": 3605}},
    ],
    "STALL": [
        {"action": "play_video", "params": {"video_file": "03Empathy_talk.mp4"}},
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 6}},
        {"action": "move_robotic_arm", "params": {"p1": 1700, "p2": 2800, "p3": 1075}},
    ],
    "TELEPHONE": [
        {"action": "play_video", "params": {"video_file": "05Talking.mp4"}},
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 8}},
        {"action": "move_robotic_arm", "params": {"p1": 600, "p2": 600, "p3": 305}},
    ],
    "INTERNET_CAFE": [
        {"action": "play_video", "params": {"video_file": "05Talking.mp4"}},
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 9}},
        {"action": "move_robotic_arm", "params": {"p1": 1367, "p2": 0, "p3": 145}},
    ],
    "SCENIC_OVERLOOK": [
        {"action": "play_video", "params": {"video_file": "05Talking.mp4"}},
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 10}},
        {"action": "move_robotic_arm", "params": {"p1": 800, "p2": 200, "p3": 500}},
    ],
    "CITY_ENTRANCE": [
        {"action": "play_video", "params": {"video_file": "05Talking.mp4"}},
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 11}},
        {"action": "move_robotic_arm", "params": {"p1": 4095, "p2": 900, "p3": 600}},
    ],
    "IDLE": [
        {"action": "play_video", "params": {"video_file": "02Thoughtful.mp4"}},
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 0}},
        {"action": "move_robotic_arm", "params": {"p1": 2390, "p2": 3751, "p3": 3505}},
    ],
}


# --- Helper Functions ---
async def _execute_scene_actions(scene_name, hardware_manager):
    actions_to_run = SCENE_ACTIONS.get(scene_name)
    if not actions_to_run:
        logging.info(f"[ORCHESTRATOR] No actions defined for scene: {scene_name}")
        return
    logging.info(f"[ORCHESTRATOR] ---> Executing actions for scene '{scene_name}'...")
    for item in actions_to_run:
        action_name = item.get("action")
        params = item.get("params", {})
        function_to_call = getattr(hardware_manager, action_name, None)
        if callable(function_to_call):
            try:
                await function_to_call(**params)
            except Exception as e:
                logging.error(f"[ORCHESTRATOR] ERROR during action {action_name}: {e}")


async def _execute_end_scene(hardware_manager):
    logging.info("[ORCHESTRATOR] ---> Executing end scene ...")
    action_name = "trigger_diorama_scene"
    params = {"scene_command_id": 12}
    function_to_call = getattr(hardware_manager, action_name, None)
    if callable(function_to_call):
        try:
            await function_to_call(**params)
        except Exception as e:
            logging.error(f"[ORCHESTRATOR] ERROR during action {action_name}: {e}")


async def _get_model_response(client, system_prompt, history):
    logging.info("[ORCHESTRATOR] ---> Calling Gemini API.")
    prompt = json.dumps({"conversation_history": history})

    # Pass the system prompt inside the generation configuration
    config = types.GenerateContentConfig(
        response_mime_type="application/json", system_instruction=system_prompt
    )

    contents = [types.Part(text=prompt)]

    api_call = asyncio.to_thread(
        client.models.generate_content,
        model="gemini-2.5-flash",
        contents=contents,
        config=config,
    )
    return await asyncio.wait_for(api_call, timeout=8.0)


def _parse_json_from_text(text: str):
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        logging.error(f"[ORCHESTRATOR] ERROR: Could not decode JSON: {text}")
        return None


# --- Main Orchestrator Class ---
class StatefulOrchestrator:
    """Manages the multi-turn conversation, state, and hardware orchestration."""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        self.client = genai.Client(api_key=api_key)
        self.hardware = HardwareManager()
        with open("prompts/BOB_STORYTELLER.md", "r") as f:
            self.system_prompt = f.read()
        self.background_tasks = set()
        self.conversation_history = []
        self.turn_number = 0
        self.stop_commands = [
            "stop",
            "i want to stop",
            "i'm done",
            "that's enough",
            "end conversation",
        ]
        logging.info("[ORCHESTRATOR] Initialized for multi-turn conversation.")

    def _reset_conversation(self):
        self.conversation_history = []
        self.turn_number = 0
        logging.info("[ORCHESTRATOR] Conversation has been reset.")

    async def process_user_input(self, user_prompt: str, director):
        """
        Processes user input, manages conversation state, and triggers all actions.
        """
        # 1. Handle the special command to start the conversation
        if user_prompt == "START_CONVERSATION":
            self._reset_conversation()
            logging.info("[ORCHESTRATOR] Starting new conversation.")
            return {
                "narrative": "Hello! I'm Bob. I live here in this town, but I'm so curious about your world. Can you tell me about a place that makes you happy?",
                "is_story_finished": False,
            }

        logging.info(
            f'[ORCHESTRATOR] Turn {self.turn_number} | User said: "{user_prompt}"'
        )

        # 2. Check for stop commands
        if user_prompt.lower().strip() in self.stop_commands:
            logging.info("[ORCHESTRATOR] Stop command detected. Ending conversation.")
            await director.send_qr_command_to_web()
            await _execute_end_scene(self.hardware)
            self._reset_conversation()
            return {
                "narrative": "Thank you for sharing your world with me!",
                "is_story_finished": True,
            }

        # 3. Append to history and increment turn
        self.conversation_history.append(user_prompt)
        self.turn_number += 1

        # 4. Call the AI to get the next step
        try:
            response = await _get_model_response(
                self.client, self.system_prompt, self.conversation_history
            )
            ai_response = _parse_json_from_text(response.text)

            if not ai_response:
                raise ValueError("AI response was not valid JSON.")

            scene = ai_response.get("scene_to_trigger")
            question = ai_response.get("next_question", "What do you think of that?")
            is_finished = ai_response.get("is_finished", False)

            # 5. Trigger hardware actions
            task = asyncio.create_task(_execute_scene_actions(scene, self.hardware))
            self.background_tasks.add(task)
            task.add_done_callback(self.background_tasks.discard)

            # 6. Check for end of conversation
            if is_finished or self.turn_number >= 5:
                logging.info(
                    "[ORCHESTRATOR] Conversation finished. Triggering QR code."
                )
                # await director.send_qr_command_to_web()
                await _execute_end_scene(self.hardware)
                self._reset_conversation()
                return {"narrative": question, "is_story_finished": True}
            else:
                return {"narrative": question, "is_story_finished": False}

        except Exception as e:
            logging.error(f"[ORCHESTRATOR] CRITICAL_ERROR: {e}")
            # await director.send_qr_command_to_web()
            self._reset_conversation()
            return {
                "narrative": "I seem to have gotten my wires crossed! Let's try again later.",
                "is_story_finished": True,
            }

    async def execute_scene_by_name(self, scene_name: str):
        """A direct method to execute a scene's actions, bypassing the AI."""
        task = asyncio.create_task(_execute_scene_actions(scene_name, self.hardware))
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)

    async def execute_manual_arm_move(self, p1: int, p2: int, p3: int):
        """A direct method to move the robotic arm."""
        await self.hardware.move_robotic_arm(p1=p1, p2=p2, p3=p3)
