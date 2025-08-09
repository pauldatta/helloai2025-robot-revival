import os
import json
import asyncio
from google import genai
from google.genai import types
from dotenv import load_dotenv
from .hardware_controller import HardwareManager

# --- Scene to Action Mapping ---
# This dictionary maps a scene name to a list of hardware actions.
# This makes it easy to add new actions (like video) without changing the core logic.
SCENE_ACTIONS = {
    "AUMS_HOME": [
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 2}},
        {"action": "move_robotic_arm", "params": {"p1": 2468, "p2": 68, "p3": 3447}},
        {"action": "play_video", "params": {"video_file": "part1_lost_in_the_city.mp4"}},
    ],
    "PARK_AND_CITY": [
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 4}},
        {"action": "move_robotic_arm", "params": {"p1": 2457, "p2": 79, "p3": 3447}},
        {"action": "play_video", "params": {"video_file": "part2_glimmer_of_hope.mp4"}},
    ],
    "ROAD_TO_HUA_HIN": [
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 6}},
        {"action": "move_robotic_arm", "params": {"p1": 2457, "p2": 68, "p3": 3436}},
    ],
    "INTERNET_CAFE": [
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 8}},
        {"action": "move_robotic_arm", "params": {"p1": 2446, "p2": 68, "p3": 3436}},
        {"action": "play_video", "params": {"video_file": "part3_the_search.mp4"}},
    ],
    "MAP_VISUAL": [
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 10}},
        {"action": "move_robotic_arm", "params": {"p1": 4000, "p2": 1500, "p3": 3800}},
        {"action": "play_video", "params": {"video_file": "part4_the_path_home.mp4"}},
    ],
    "ROAD_TO_BANGKOK": [
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 12}},
        {"action": "move_robotic_arm", "params": {"p1": 3800, "p2": 1300, "p3": 3700}},
        {"action": "play_video", "params": {"video_file": "part5_the_reunion.mp4"}},
    ],
    # Guided mode scenes just reference the free-roam scenes
    "GUIDED_MODE_AUMS_HOME": "AUMS_HOME",
    "GUIDED_MODE_PARK_AND_CITY": "PARK_AND_CITY",
    "GUIDED_MODE_ROAD_TO_HUA_HIN": "ROAD_TO_HUA_HIN",
    "GUIDED_MODE_INTERNET_CAFE": "INTERNET_CAFE",
    "GUIDED_MODE_MAP_VISUAL": "MAP_VISUAL",
    "GUIDED_MODE_ROAD_TO_BANGKOK": "ROAD_TO_BANGKOK",
}


# --- Modular Functions for Core Logic ---

async def _execute_scene_actions(scene_name, hardware_manager):
    """Looks up a scene in the SCENE_ACTIONS map and executes all actions."""
    actions_to_run = SCENE_ACTIONS.get(scene_name)

    # Handle scene aliases (e.g., for guided mode)
    if isinstance(actions_to_run, str):
        actions_to_run = SCENE_ACTIONS.get(actions_to_run)

    if not actions_to_run:
        print(f"[ORCHESTRATOR] No actions defined for scene: {scene_name}")
        return

    tasks = []
    for item in actions_to_run:
        action_name = item.get("action")
        params = item.get("params", {})
        function_to_call = getattr(hardware_manager, action_name, None)

        if callable(function_to_call):
            print(f"[ORCHESTRATOR] ---> Queuing action: {action_name}({params})")
            tasks.append(function_to_call(**params))
        else:
            print(f"[ORCHESTRATOR] ERROR: Unknown action '{action_name}' in scene '{scene_name}'")

    # Run all hardware tasks concurrently with a timeout
    if tasks:
        try:
            print(f"[ORCHESTRATOR] ---> Executing {len(tasks)} action(s) for scene '{scene_name}'...")
            await asyncio.wait_for(asyncio.gather(*tasks), timeout=10.0)
        except asyncio.TimeoutError:
            print("[ORCHESTRATOR] ERROR: A hardware operation timed out.")


async def _get_model_response(client, system_prompt, prompt):
    """Sends a single, intelligent request to the Gemini API."""
    print("[ORCHESTRATOR] ---> Calling Gemini API.")
    # The model's only job is to return JSON, so no tools are needed.
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        candidate_count=1,
        temperature=0.7,
        thinking_config=types.ThinkingConfig(thinking_budget=0), # Disable thinking for lower latency
        system_instruction=system_prompt
    )
    # The generate_content call is synchronous, so we run it in a thread
    # and wrap it with asyncio.wait_for to apply a timeout.
    api_call = asyncio.to_thread(
        client.models.generate_content,
        model='gemini-2.5-flash',
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
        print(f"[ORCHESTRATOR] ERROR: Could not decode JSON from model response: {text}")
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
        print(f"[ORCHESTRATOR] Initialized. Start scene: {self.current_scene}")

    async def process_user_command(self, user_text: str):
        """
        Processes user text, determines the next scene, returns the narrative immediately,
        and executes hardware actions in the background.
        """
        print(f"[ORCHESTRATOR] ---> Received command: \"{user_text}\" | Current Scene: {self.current_scene}")
        prompt = f"Current Scene: {self.current_scene}\nUser Speech: \"{user_text}\""
        
        try:
            # 1. Get the model's response (narrative + next_scene)
            response = await _get_model_response(self.client, self.system_prompt, prompt)
            
            # 2. Extract and parse the JSON narrative
            raw_text = response.text
            response_data = _parse_json_from_text(raw_text)
            
            if not response_data:
                print("[ORCHESTRATOR] ERROR: Failed to get a valid JSON narrative. Using fallback.")
                return "I'm not sure what to say next.", self.current_scene

            # 3. Update state and get narrative
            narrative = response_data.get("narrative", "I'm speechless.")
            next_scene = response_data.get("next_scene", self.current_scene)

            # 4. If the scene has changed, start the hardware actions in the background.
            if next_scene != self.current_scene:
                task = asyncio.create_task(_execute_scene_actions(next_scene, self.hardware))
                self.background_tasks.add(task)
                task.add_done_callback(self.background_tasks.discard)

            self.current_scene = next_scene
            print(f"[ORCHESTRATOR] <--- Updated scene to \"{self.current_scene}\". Returning narrative immediately.")
            return narrative, self.current_scene

        except asyncio.TimeoutError:
            print("[ORCHESTRATOR] CRITICAL_ERROR: Gemini API call timed out.")
            return "I took too long to think. Could you please try that again?", self.current_scene
        except Exception as e:
            print(f"[ORCHESTRATOR] CRITICAL_ERROR: {e}")
            return "I seem to have gotten my wires crossed. Could you try that again?", self.current_scene

async def main():
    """A simple async main function for smoke testing."""
    orchestrator = StatefulOrchestrator()
    await orchestrator.hardware.connect_all()
    print("\n--- Orchestrator Smoke Test ---")
    narrative, _ = await orchestrator.process_user_command("Hello")
    print(f"Narrative Output: {narrative}")
    await orchestrator.hardware.close_all_ports()

if __name__ == '__main__':
    asyncio.run(main())