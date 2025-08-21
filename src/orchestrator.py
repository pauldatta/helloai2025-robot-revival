import asyncio
import json
import logging
import os
import re
from google import genai
from google.genai import types
from .hardware_controller import HardwareManager

# --- Scene to Action Mapping ---
# This dictionary maps a scene name to a list of hardware actions.
# This makes it easy to add new actions (like video) without changing the core logic.
SCENE_ACTIONS = {
    # --- Main Story Scenes ---
    "AUMS_HOME": [
        # Corresponds to S3: Story of Aum | Aum's Home and S4: Aum's Home - zoom in
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 2}},
        {"action": "move_robotic_arm", "params": {"p1": 2468, "p2": 68, "p3": 2980}},
        {
            "action": "play_video",
            "params": {"video_file": "part1_lost_in_the_city.mp4"},
        },
    ],
    "AUM_CRYING": [
        # Corresponds to S5: Aum Crying
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 4}},
        {"action": "move_robotic_arm", "params": {"p1": 2457, "p2": 79, "p3": 3447}},
    ],
    "BUS_SOCCER": [
        # Corresponds to S6a: Bus and S6b: Bus - Soccer
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 5}},
        {
            "action": "move_robotic_arm",
            "params": {"p1": 2457, "p2": 79, "p3": 3447},  # Same as AUM_CRYING
        },
    ],
    "MARKET": [
        # Corresponds to S9: Market
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 3}},
        {
            "action": "move_robotic_arm",
            "params": {"p1": 2457, "p2": 68, "p3": 3436},  # Same as ROAD_TO_HUA_HIN
        },
        {"action": "play_video", "params": {"video_file": "part2_glimmer_of_hope.mp4"}},
    ],
    "AUM_GROWS_UP": [
        # Corresponds to S10: Aum Grew Up
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 7}},
        {
            "action": "move_robotic_arm",
            "params": {"p1": 2457, "p2": 68, "p3": 3436},  # Same as ROAD_TO_HUA_HIN
        },
    ],
    "ROAD_TO_HUA_HIN": [
        # Corresponds to S11a: Aum to Hua Hin and S11b: Aum reach Hua Hin
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 6}},
        {"action": "move_robotic_arm", "params": {"p1": 2457, "p2": 68, "p3": 3436}},
    ],
    "INTERNET_CAFE": [
        # Corresponds to S12a: Cafe and S12b: Cafe
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 8}},
        {"action": "move_robotic_arm", "params": {"p1": 2446, "p2": 68, "p3": 3436}},
        {"action": "play_video", "params": {"video_file": "part3_the_search.mp4"}},
    ],
    "GOOGLE_MAP": [
        # Corresponds to S13: Google Map
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 10}},
        {"action": "move_robotic_arm", "params": {"p1": 4000, "p2": 1500, "p3": 3800}},
        {"action": "play_video", "params": {"video_file": "part4_the_path_home.mp4"}},
    ],
    "ROAD_TO_BANGKOK": [
        # Corresponds to S14a: Aum back to BK and S14b: Aum back to BK
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 11}},
        {"action": "move_robotic_arm", "params": {"p1": 3800, "p2": 1300, "p3": 3700}},
        {"action": "play_video", "params": {"video_file": "part5_the_reunion.mp4"}},
    ],
    # --- System & Utility Scenes ---
    "IDLE": [
        # Corresponds to S0: Rest
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 0}},
        {
            "action": "move_robotic_arm",
            "params": {"p1": 2048, "p2": 0, "p3": 3960},  # Default position
        },
    ],
    "FINDING_BOY": [
        # Corresponds to S2: Finding Boy (likely an intro/attract scene)
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 1}},
        {
            "action": "move_robotic_arm",
            "params": {"p1": 2048, "p2": 0, "p3": 3960},  # Default position
        },
    ],
}


# --- Modular Functions for Core Logic ---
async def _execute_scene_actions(scene_name, hardware_manager):
    """Looks up a scene and executes its actions sequentially."""
    actions_to_run = SCENE_ACTIONS.get(scene_name)

    # Handle scene aliases
    if isinstance(actions_to_run, str):
        actions_to_run = SCENE_ACTIONS.get(actions_to_run)

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
                logging.info(
                    f"[ORCHESTRATOR] ---> Running action: {action_name}({params})"
                )
                # Execute each action and wait for it to complete.
                await function_to_call(**params)
            except Exception as e:
                logging.error(f"[ORCHESTRATOR] ERROR during action {action_name}: {e}")
        else:
            logging.error(
                f"[ORCHESTRATOR] ERROR: Unknown action '{action_name}' in scene '{scene_name}'"
            )


async def _get_model_response(client, system_prompt, prompt):
    """Sends a single, intelligent request to the Gemini API."""
    logging.info("[ORCHESTRATOR] ---> Calling Gemini API.")
    # The model's only job is to return JSON, so no tools are needed.
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        candidate_count=1,
        temperature=0.7,
        thinking_config=types.ThinkingConfig(
            thinking_budget=0
        ),  # Disable thinking for lower latency
        system_instruction=system_prompt,
    )
    # The generate_content call is synchronous, so we run it in a thread
    # and wrap it with asyncio.wait_for to apply a timeout.
    api_call = asyncio.to_thread(
        client.models.generate_content,
        model="gemini-2.5-flash",
        contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
        config=config,
    )
    return await asyncio.wait_for(api_call, timeout=8.0)


def _parse_json_from_text(text: str):
    """Cleans and parses a JSON string that might be wrapped in markdown."""
    if not text:
        return None
    if text.startswith("```json"):
        text = text[7:-3].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logging.error(
            f"[ORCHESTRATOR] ERROR: Could not decode JSON from model response: {text}"
        )
        return None


# --- Main Orchestrator Class ---
class StatefulOrchestrator:
    """Manages the conversational flow, hardware actions, and AI interaction."""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        self.client = genai.Client(api_key=api_key)
        self.hardware = HardwareManager()
        with open("prompts/BOB_STORYTELLER.md", "r") as f:
            self.system_prompt = f.read()
        self.background_tasks = set()
        logging.info("[ORCHESTRATOR] Initialized.")

    async def process_user_response(self, user_prompt: str, director):
        """
        Processes the user's response, triggers the appropriate hardware and AI actions,
        and returns a single narrative response.
        """
        logging.info(f'[ORCHESTRATOR] ---> Processing user prompt: "{user_prompt}"')

        # --- Activity Branch Logic ---
        activity_keywords = {
            "home": "AUMS_HOME",
            "house": "AUMS_HOME",
            "market": "MARKET",
            "train": "ROAD_TO_HUA_HIN",
            "bus": "BUS_SOCCER",
            "cafe": "INTERNET_CAFE",
            "map": "GOOGLE_MAP",
        }

        for keyword, scene in activity_keywords.items():
            if re.search(r"\b" + re.escape(keyword) + r"\b", user_prompt.lower()):
                logging.info(
                    f"[ORCHESTRATOR] Matched keyword '{keyword}'. Triggering Activity Branch."
                )

                narrative = f"Ah, the {keyword}. That reminds me of a place I know..."
                task = asyncio.create_task(_execute_scene_actions(scene, self.hardware))
                self.background_tasks.add(task)
                task.add_done_callback(self.background_tasks.discard)

                asyncio.create_task(director.send_qr_command_to_web())
                return {"narrative": narrative, "is_story_finished": True}

        # --- Generative Scene Branch Logic ---
        logging.info(
            "[ORCHESTRATOR] No keyword match. Triggering Generative Scene Branch."
        )
        try:
            response = await _get_model_response(
                self.client, self.system_prompt, user_prompt
            )
            response_data = _parse_json_from_text(response.text)

            if (
                not response_data
                or "story_plan" not in response_data
                or not response_data["story_plan"]
            ):
                raise ValueError("Invalid story plan from AI.")

            scene_name = response_data["story_plan"][0].get("scene_name")
            narrative = response_data["story_plan"][0].get(
                "narrative", "I'm speechless."
            )

            task = asyncio.create_task(
                _execute_scene_actions(scene_name, self.hardware)
            )
            self.background_tasks.add(task)
            task.add_done_callback(self.background_tasks.discard)

            asyncio.create_task(director.send_qr_command_to_web())
            return {"narrative": narrative, "is_story_finished": True}

        except Exception as e:
            logging.error(f"[ORCHESTRATOR] CRITICAL_ERROR in Generative Branch: {e}")
            asyncio.create_task(director.send_qr_command_to_web())
            return {
                "narrative": "That's a fascinating thought! It reminds me of the time...",
                "is_story_finished": True,
            }

    async def execute_scene_by_name(self, scene_name: str):
        """A direct method to execute a scene's actions, bypassing the AI."""
        logging.info(f"[ORCHESTRATOR] ---> Manually executing scene: {scene_name}")
        task = asyncio.create_task(_execute_scene_actions(scene_name, self.hardware))
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)

    async def execute_manual_arm_move(self, p1: int, p2: int, p3: int):
        """A direct method to move the robotic arm."""
        logging.info(
            f"[ORCHESTRATOR] ---> Manually moving arm to: p1={p1}, p2={p2}, p3={p3}"
        )
        await self.hardware.move_robotic_arm(p1=p1, p2=p2, p3=p3)
        logging.info("[ORCHESTRATOR] <--- Manual arm move complete.")


async def main():
    """A simple async main function for smoke testing."""
    logging.basicConfig(level=logging.INFO)
    orchestrator = StatefulOrchestrator()

    # This is a mock director for testing purposes.
    class MockDirector:
        async def send_qr_command_to_web(self):
            logging.info("[MOCK DIRECTOR] ---> QR command would be sent here.")

    mock_director = MockDirector()
    await orchestrator.hardware.connect_all()
    logging.info("\n--- Orchestrator Smoke Test ---")

    result = await orchestrator.process_user_response(
        "Tell me a story about a train.", mock_director
    )
    logging.info(f"Narrative: {result['narrative']}")

    await orchestrator.hardware.close_all_ports()


if __name__ == "__main__":
    asyncio.run(main())
