import asyncio
import json
import logging
import os
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
            "params": {"p1": 2457, "p2": 79, "p3": 3447},
        },  # Same as AUM_CRYING
    ],
    "MARKET": [
        # Corresponds to S9: Market
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 3}},
        {
            "action": "move_robotic_arm",
            "params": {"p1": 2457, "p2": 68, "p3": 3436},
        },  # Same as ROAD_TO_HUA_HIN
        {"action": "play_video", "params": {"video_file": "part2_glimmer_of_hope.mp4"}},
    ],
    "AUM_GROWS_UP": [
        # Corresponds to S10: Aum Grew Up
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 7}},
        {
            "action": "move_robotic_arm",
            "params": {"p1": 2457, "p2": 68, "p3": 3436},
        },  # Same as ROAD_TO_HUA_HIN
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
            "params": {"p1": 2048, "p2": 0, "p3": 3960},
        },  # Default position
    ],
    "FINDING_BOY": [
        # Corresponds to S2: Finding Boy (likely an intro/attract scene)
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 1}},
        {
            "action": "move_robotic_arm",
            "params": {"p1": 2048, "p2": 0, "p3": 3960},
        },  # Default position
    ],
    # --- Guided Mode ---
    # References the main story scenes
    "GUIDED_MODE_AUMS_HOME": "AUMS_HOME",
    "GUIDED_MODE_BUS_SOCCER": "BUS_SOCCER",
    "GUIDED_MODE_AUM_CRYING": "AUM_CRYING",
    "GUIDED_MODE_MARKET": "MARKET",
    "GUIDED_MODE_AUM_GROWS_UP": "AUM_GROWS_UP",
    "GUIDED_MODE_ROAD_TO_HUA_HIN": "ROAD_TO_HUA_HIN",
    "GUIDED_MODE_INTERNET_CAFE": "INTERNET_CAFE",
    "GUIDED_MODE_GOOGLE_MAP": "GOOGLE_MAP",
    "GUIDED_MODE_ROAD_TO_BANGKOK": "ROAD_TO_BANGKOK",
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
    """Manages story state via a single, intelligent API call."""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        self.client = genai.Client(api_key=api_key)
        self.hardware = HardwareManager()
        with open("prompts/AUM_ORCHESTRATOR.md", "r") as f:
            self.system_prompt = f.read()
        self.current_scene = "AWAITING_MODE_SELECTION"
        self.background_tasks = set()
        logging.info(f"[ORCHESTRATOR] Initialized. Start scene: {self.current_scene}")

    async def process_user_command(self, user_text: str):
        """
        Processes user text, determines the next scene, returns the narrative immediately,
        and executes hardware actions in the background.
        """
        logging.info(
            f'[ORCHESTRATOR] ---> Received command: "{user_text}" | Current Scene: {self.current_scene}'
        )
        prompt = f'Current Scene: {self.current_scene}\nUser Speech: "{user_text}"'

        try:
            # 1. Get the model's response (narrative + next_scene)
            response = await _get_model_response(
                self.client, self.system_prompt, prompt
            )

            # 2. Extract and parse the JSON narrative
            raw_text = response.text
            response_data = _parse_json_from_text(raw_text)

            if not response_data:
                logging.error(
                    "[ORCHESTRATOR] ERROR: Failed to get a valid JSON narrative. Using fallback."
                )
                return "I'm not sure what to say next.", self.current_scene

            # 3. Update state and get narrative
            narrative = response_data.get("narrative", "I'm speechless.")
            next_scene = response_data.get("next_scene", self.current_scene)

            # 4. If the scene has changed, start the hardware actions in the background.
            if next_scene != self.current_scene:
                task = asyncio.create_task(
                    _execute_scene_actions(next_scene, self.hardware)
                )
                self.background_tasks.add(task)
                task.add_done_callback(self.background_tasks.discard)

            self.current_scene = next_scene
            logging.info(
                f'[ORCHESTRATOR] <--- Updated scene to "{self.current_scene}". Returning narrative immediately.'
            )
            return narrative, self.current_scene

        except asyncio.TimeoutError:
            logging.error("[ORCHESTRATOR] CRITICAL_ERROR: Gemini API call timed out.")
            return (
                "I took too long to think. Could you please try that again?",
                self.current_scene,
            )
        except Exception as e:
            logging.error(f"[ORCHESTRATOR] CRITICAL_ERROR: {e}")
            return (
                "I seem to have gotten my wires crossed. Could you try that again?",
                self.current_scene,
            )

    async def execute_scene_by_name(self, scene_name: str):
        """A direct method to execute a scene's actions, bypassing the AI."""
        logging.info(f"[ORCHESTRATOR] ---> Manually executing scene: {scene_name}")
        task = asyncio.create_task(_execute_scene_actions(scene_name, self.hardware))
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
        self.current_scene = scene_name

    async def execute_manual_arm_move(self, p1: int, p2: int, p3: int):
        """A direct method to move the robotic arm, updating the scene state."""
        logging.info(
            f"[ORCHESTRATOR] ---> Manually moving arm to: p1={p1}, p2={p2}, p3={p3}"
        )
        await self.hardware.move_robotic_arm(p1=p1, p2=p2, p3=p3)
        self.current_scene = "MANUAL_OVERRIDE"
        logging.info(f'[ORCHESTRATOR] <--- Scene state is now "{self.current_scene}"')


async def main():
    """A simple async main function for smoke testing."""
    orchestrator = StatefulOrchestrator()
    await orchestrator.hardware.connect_all()
    logging.info("\n--- Orchestrator Smoke Test ---")
    narrative, _ = await orchestrator.process_user_command("Hello")
    logging.info(f"Narrative Output: {narrative}")
    await orchestrator.hardware.close_all_ports()


if __name__ == "__main__":
    asyncio.run(main())
