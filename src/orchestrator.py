import asyncio
import json
import logging
import os
from google import genai
from google.genai import types
from .hardware_controller import HardwareManager

# --- Location to Action Mapping ---
# This dictionary maps a generic location name to a list of hardware actions.
LOCATION_ACTIONS = {
    "HOME": [
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 2}},
        {"action": "move_robotic_arm", "params": {"p1": 2468, "p2": 68, "p3": 2980}},
    ],
    "REFLECTING_POOL": [
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 4}},
        {"action": "move_robotic_arm", "params": {"p1": 2457, "p2": 79, "p3": 3447}},
    ],
    "MARKET": [
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 3}},
        {"action": "move_robotic_arm", "params": {"p1": 2457, "p2": 68, "p3": 3436}},
    ],
    "INTERNET_CAFE": [
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 8}},
        {"action": "move_robotic_arm", "params": {"p1": 2446, "p2": 68, "p3": 3436}},
    ],
    "SCENIC_OVERLOOK": [
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 10}},
        {"action": "move_robotic_arm", "params": {"p1": 4000, "p2": 1500, "p3": 3800}},
    ],
    "CITY_ENTRANCE": [
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 11}},
        {"action": "move_robotic_arm", "params": {"p1": 3800, "p2": 1300, "p3": 3700}},
    ],
    "IDLE": [
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 0}},
        {
            "action": "move_robotic_arm",
            "params": {"p1": 2048, "p2": 0, "p3": 3960},
        },  # Default position
    ],
}


# --- Modular Functions for Core Logic ---
async def _execute_location_actions(location_name, hardware_manager):
    """Looks up a location and executes its actions sequentially."""
    actions_to_run = LOCATION_ACTIONS.get(location_name)

    if not actions_to_run:
        logging.info(f"[ORCHESTRATOR] No actions defined for location: {location_name}")
        return

    logging.info(
        f"[ORCHESTRATOR] ---> Executing actions for location '{location_name}'..."
    )
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
                f"[ORCHESTRATOR] ERROR: Unknown action '{action_name}' in location '{location_name}'"
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
    """Manages the story generation, state, and hardware orchestration."""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        self.client = genai.Client(api_key=api_key)
        self.hardware = HardwareManager()
        with open("prompts/AARON_STORYTELLER.md", "r") as f:
            self.system_prompt = f.read()
        self.current_story_plan = []
        self.current_story_step = -1
        self.background_tasks = set()
        logging.info("[ORCHESTRATOR] Initialized in storytelling mode.")

    async def request_new_story(self, user_prompt: str):
        """
        Calls the Gemini API to generate a new story plan based on the user's prompt.
        Returns the first part of the story.
        """
        logging.info(
            f'[ORCHESTRATOR] ---> Requesting new story with prompt: "{user_prompt}"'
        )
        try:
            # 1. Get the model's response (the story plan)
            response = await _get_model_response(
                self.client, self.system_prompt, user_prompt
            )
            raw_text = response.text
            response_data = _parse_json_from_text(raw_text)

            if not response_data or "story_plan" not in response_data:
                logging.error(
                    "[ORCHESTRATOR] ERROR: Failed to get a valid story plan. Using fallback."
                )
                return {
                    "narrative": "I'm sorry, I couldn't think of a story right now. Please ask me again!",
                    "is_story_finished": True,
                }

            # 2. Store the new story plan and start the first step
            self.current_story_plan = response_data["story_plan"]
            self.current_story_step = 0
            logging.info(
                f"[ORCHESTRATOR] <--- Received new story with {len(self.current_story_plan)} parts."
            )

            # 3. Execute the hardware actions for the first part in the background
            first_part = self.current_story_plan[0]
            location = first_part.get("location")
            task = asyncio.create_task(
                _execute_location_actions(location, self.hardware)
            )
            self.background_tasks.add(task)
            task.add_done_callback(self.background_tasks.discard)

            # 4. Return the first narrative
            return {
                "narrative": first_part.get("narrative"),
                "is_story_finished": len(self.current_story_plan) <= 1,
            }

        except asyncio.TimeoutError:
            logging.error("[ORCHESTRATOR] CRITICAL_ERROR: Gemini API call timed out.")
            return {
                "narrative": "I took too long to think. Could you please try that again?",
                "is_story_finished": True,
            }
        except Exception as e:
            logging.error(f"[ORCHESTRATOR] CRITICAL_ERROR: {e}")
            return {
                "narrative": "I seem to have gotten my wires crossed. Could you try that again?",
                "is_story_finished": True,
            }

    async def advance_story(self):
        """
        Advances the story to the next step and returns the corresponding narrative.
        """
        if not self.current_story_plan or self.current_story_step < 0:
            return {
                "narrative": "There is no story in progress. You can ask me to tell you one!",
                "is_story_finished": True,
            }

        self.current_story_step += 1
        if self.current_story_step >= len(self.current_story_plan):
            logging.info("[ORCHESTRATOR] Story finished.")
            self.current_story_plan = []
            self.current_story_step = -1
            return {
                "narrative": "And that's the end of the story! I hope you enjoyed it.",
                "is_story_finished": True,
            }

        logging.info(
            f"[ORCHESTRATOR] Advancing story to step {self.current_story_step}"
        )
        next_part = self.current_story_plan[self.current_story_step]
        location = next_part.get("location")

        # Execute hardware actions in the background
        task = asyncio.create_task(_execute_location_actions(location, self.hardware))
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)

        is_finished = self.current_story_step >= len(self.current_story_plan) - 1
        return {
            "narrative": next_part.get("narrative"),
            "is_story_finished": is_finished,
        }

    async def execute_location_by_name(self, location_name: str):
        """A direct method to execute a location's actions, bypassing the AI."""
        logging.info(
            f"[ORCHESTRATOR] ---> Manually executing location: {location_name}"
        )
        task = asyncio.create_task(
            _execute_location_actions(location_name, self.hardware)
        )
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
        # In the new design, manual triggers don't affect the story state.

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
    await orchestrator.hardware.connect_all()
    logging.info("\n--- Orchestrator Storytelling Smoke Test ---")

    # Test starting a new story
    result = await orchestrator.request_new_story(
        "Tell me a story about a lost kitten."
    )
    logging.info(f"Narrative 1: {result['narrative']}")

    # Test advancing the story
    if not result["is_story_finished"]:
        result = await orchestrator.advance_story()
        logging.info(f"Narrative 2: {result['narrative']}")

    await orchestrator.hardware.close_all_ports()


if __name__ == "__main__":
    asyncio.run(main())
