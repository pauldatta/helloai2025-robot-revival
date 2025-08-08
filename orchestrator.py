import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv
import hardware_controller as hw

# Load environment variables
load_dotenv()

class StatefulOrchestrator:
    """
    Manages the story state and interacts with the Gemini API to decide on
    hardware actions. This is the "brain" of the operation.
    """
    def __init__(self):
        # The Client automatically uses the GOOGLE_API_KEY or GEMINI_API_KEY from the environment
        self.client = genai.Client()
        
        # Load the system prompt
        with open("AUM_ORCHESTRATOR.md", "r") as f:
            self.system_prompt = f.read()
        
        # Initialize story state
        self.current_scene = "AWAITING_MODE_SELECTION"
        print(f"[ORCHESTRATOR] Initialized. Current scene: {self.current_scene}")

    def process_user_command(self, user_text: str):
        """
        Processes the user's text, sends it to the Gemini model, handles tool calls,
        and returns the narrative response.
        """
        print(f"[ORCHESTRATOR] Processing command. Scene: '{self.current_scene}', Input: '{user_text}'")

        # Construct the full prompt for the model for this specific turn
        prompt = f"Current Scene: {self.current_scene}\nUser Speech: \"{user_text}\""
        
        try:
            # Make a single, non-streaming call to the model
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part(text=prompt)]
                    )
                ],
                system_instruction=self.system_prompt,
                tools=[hw.trigger_diorama_scene, hw.move_robotic_arm]
            )

            # The SDK's automatic function calling handles the tool loop.
            # The final response will contain the text after tools have been called.
            final_response_text = response.text.strip()
            
            if final_response_text.startswith("```json"):
                final_response_text = final_response_text[7:]
            if final_response_text.endswith("```"):
                final_response_text = final_response_text[:-3]
            
            response_data = json.loads(final_response_text)
            
            narrative = response_data.get("narrative")
            next_scene = response_data.get("next_scene")

            self.current_scene = next_scene
            print(f"[ORCHESTRATOR] <--- Response: '{narrative}'. New scene: {self.current_scene}")
            
            return narrative, self.current_scene

        except Exception as e:
            print(f"[ORCHESTRATOR] An error occurred: {e}")
            return "I'm having a little trouble connecting. Could you try that again?", self.current_scene

if __name__ == '__main__':
    orchestrator = StatefulOrchestrator()
    
    print("\n--- Simulating Initial Greeting ---")
    narrative, _ = orchestrator.process_user_command("Hello, please give me the introduction.")
    print(f"Spoken to user: {narrative}")

    print("\n--- Simulating User Choice: Guided Mode ---")
    narrative, _ = orchestrator.process_user_command("Guide me through the story.")
    print(f"Spoken to user: {narrative}")

    print("\n--- Simulating User Action: Continue ---")
    narrative, _ = orchestrator.process_user_command("Okay, what happens next?")
    print(f"Spoken to user: {narrative}")

    print("\n--- Simulating User Choice: Unguided Jump ---")
    narrative, _ = orchestrator.process_user_command("Take me to the internet cafe.")
    print(f"Spoken to user: {narrative}")