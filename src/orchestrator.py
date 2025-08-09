import os
import json
import asyncio
from google import genai
from google.genai import types
from dotenv import load_dotenv
from .hardware_controller import HardwareManager, trigger_diorama_scene_declaration, move_robotic_arm_declaration

# --- Modular Functions for Core Logic ---

async def _execute_tool_calls(tool_calls, hardware_manager):
    """Executes a list of tool calls suggested by the model."""
    if not tool_calls:
        return
    
    # Create a list of tasks to run concurrently
    tasks = []
    for tool_call in tool_calls:
        function_name = tool_call.name
        function_to_call = getattr(hardware_manager, function_name, None)
        if callable(function_to_call):
            function_args = dict(tool_call.args)
            print(f"[ORCHESTRATOR] ---> Executing tool call: {function_name}({function_args})")
            tasks.append(function_to_call(**function_args))
        else:
            print(f"[ORCHESTRATOR] ERROR: Model suggested unknown tool '{function_name}'")
    
    # Run all hardware tasks concurrently
    if tasks:
        await asyncio.gather(*tasks)

async def _get_model_response(client, system_prompt, prompt):
    """Sends a single, intelligent request to the Gemini API."""
    print("[ORCHESTRATOR] ---> Calling Gemini API.")
    tools = types.Tool(function_declarations=[
        trigger_diorama_scene_declaration,
        move_robotic_arm_declaration
    ])
    # The generate_content call is synchronous, so we run it in a thread
    return await asyncio.to_thread(
        client.models.generate_content,
        model='gemini-2.5-flash',
        contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=[tools],
            candidate_count=1,
            temperature=0.7,
        )
    )

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
        self.client = genai.Client()
        self.hardware = HardwareManager()
        with open("prompts/AUM_ORCHESTRATOR.md", "r") as f:
            self.system_prompt = f.read()
        self.current_scene = "AWAITING_MODE_SELECTION"
        print(f"[ORCHESTRATOR] Initialized. Start scene: {self.current_scene}")

    async def process_user_command(self, user_text: str):
        """Processes user text, executes tools, and returns a narrative in a single step."""
        print(f"[ORCHESTRATOR] ---> Received command: \"{user_text}\" | Current Scene: {self.current_scene}")
        prompt = f"Current Scene: {self.current_scene}\nUser Speech: \"{user_text}\""
        
        try:
            # 1. Get the model's combined response (tools + text)
            response = await _get_model_response(self.client, self.system_prompt, prompt)
            candidate = response.candidates[0]

            # 2. Execute any hardware actions suggested by the model
            tool_calls = []
            if candidate.content and candidate.content.parts:
                tool_calls = [part.function_call for part in candidate.content.parts if part.function_call]
            
            print(f"[ORCHESTRATOR] <--- Received {len(tool_calls)} tool call(s) from API.")
            await _execute_tool_calls(tool_calls, self.hardware)

            # 3. Extract and parse the JSON narrative
            text_part = "".join(part.text for part in candidate.content.parts if part.text).strip()
            response_data = _parse_json_from_text(text_part)
            
            # If there's no JSON data but there were tool calls, create a default response.
            if not response_data and tool_calls:
                print("[ORCHESTRATOR] WARNING: No narrative returned with tool calls. Creating a default response.")
                response_data = {
                    "narrative": "On it.",
                    "next_scene": self.current_scene 
                }

            if not response_data:
                print("[ORCHESTRATOR] ERROR: Failed to get a valid JSON narrative. Using fallback.")
                return "I'm not sure what to say next.", self.current_scene

            # 4. Update state and return the narrative
            narrative = response_data.get("narrative", "I'm speechless.")
            self.current_scene = response_data.get("next_scene", self.current_scene)

            print(f"[ORCHESTRATOR] <--- Updated scene to \"{self.current_scene}\". Returning narrative to Director.")
            return narrative, self.current_scene

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