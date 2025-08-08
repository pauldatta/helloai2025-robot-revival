import unittest
from unittest.mock import patch, MagicMock, mock_open

# Import the class to be tested
from orchestrator import StatefulOrchestrator

class TestStatefulOrchestrator(unittest.TestCase):
    """Tests for the StatefulOrchestrator class."""

    # This mock_open will simulate the AUM_ORCHESTRATOR.md file being present
    mock_prompt_file = mock_open(read_data="SYSTEM PROMPT")

    @patch('orchestrator.hw')
    @patch('orchestrator.genai.Client')
    @patch('builtins.open', mock_prompt_file)
    def setUp(self, mock_genai_client, mock_hw):
        """Set up a new orchestrator instance before each test."""
        # Mock the entire client and its nested attributes
        self.mock_client = MagicMock()
        self.mock_client.models.generate_content.return_value = self.create_mock_response(
            '{"narrative": "Initial response.", "next_scene": "SCENE_1"}'
        )
        mock_genai_client.return_value = self.mock_client
        
        # Create the orchestrator instance for testing
        self.orchestrator = StatefulOrchestrator()
        # Reset the mock call count before each test
        self.mock_client.models.generate_content.reset_mock()

    def create_mock_response(self, json_text):
        """Helper method to create a mock GenerateContentResponse."""
        mock_response = MagicMock()
        mock_response.text = json_text
        return mock_response

    def test_initialization(self):
        """Test that the orchestrator initializes in the correct state."""
        self.assertEqual(self.orchestrator.current_scene, "AWAITING_MODE_SELECTION")
        self.assertEqual(self.orchestrator.system_prompt, "SYSTEM PROMPT")
        # Verify that the prompt file was opened
        self.mock_prompt_file.assert_called_with("AUM_ORCHESTRATOR.md", "r")

    def test_process_user_command_updates_state(self):
        """Test that a successful command updates the internal state."""
        # Configure the mock response for this specific test
        self.mock_client.models.generate_content.return_value = self.create_mock_response(
            '{"narrative": "Moved to the park.", "next_scene": "PARK_AND_CITY"}'
        )
        
        # Initial state is AWAITING_MODE_SELECTION
        self.assertEqual(self.orchestrator.current_scene, "AWAITING_MODE_SELECTION")

        # Process a command
        narrative, next_scene = self.orchestrator.process_user_command("Go to the park")

        # Check the returned values
        self.assertEqual(narrative, "Moved to the park.")
        self.assertEqual(next_scene, "PARK_AND_CITY")

        # Check that the internal state of the orchestrator has been updated
        self.assertEqual(self.orchestrator.current_scene, "PARK_AND_CITY")

    def test_state_is_sent_in_prompt(self):
        """Test that the current state is correctly included in the prompt to the model."""
        # Set a specific state
        self.orchestrator.current_scene = "PARK_AND_CITY"
        
        # Process a command
        self.orchestrator.process_user_command("What's over there?")

        # Verify that the generate_content method was called
        self.mock_client.models.generate_content.assert_called_once()
        
        # Extract the arguments it was called with
        _, kwargs = self.mock_client.models.generate_content.call_args
        sent_contents = kwargs['contents']
        
        # Check that the prompt sent to the model contains the correct current scene
        expected_prompt = 'Current Scene: PARK_AND_CITY\nUser Speech: "What\'s over there?"'
        self.assertIn(expected_prompt, sent_contents[0].parts[0].text)

    def test_state_guard_prevents_repeated_actions(self):
        """Test that the orchestrator doesn't repeat an action if the state is already correct."""
        # --- First Call: Move to the park ---
        self.mock_client.models.generate_content.return_value = self.create_mock_response(
            '{"narrative": "Okay, moving to the park.", "next_scene": "PARK_AND_CITY"}'
        )
        self.orchestrator.process_user_command("Go to the park")
        self.assertEqual(self.orchestrator.current_scene, "PARK_AND_CITY")

        # --- Second Call: Ask to go to the park AGAIN ---
        # The model, now aware of the state, should respond differently
        self.mock_client.models.generate_content.return_value = self.create_mock_response(
            '{"narrative": "We are already at the park.", "next_scene": "PARK_AND_CITY"}'
        )
        narrative, next_scene = self.orchestrator.process_user_command("Go to the park")

        # Verify the prompt sent in this second call included the updated state
        _, kwargs = self.mock_client.models.generate_content.call_args
        sent_prompt = kwargs['contents'][0].parts[0].text
        self.assertIn("Current Scene: PARK_AND_CITY", sent_prompt)
        
        # Verify the narrative reflects the new context
        self.assertEqual(narrative, "We are already at the park.")
        # Verify the state remains the same
        self.assertEqual(self.orchestrator.current_scene, "PARK_AND_CITY")

    def test_handles_json_with_markdown_fences(self):
        """Test that it correctly parses JSON wrapped in markdown code fences."""
        json_with_fences = '```json\n{"narrative": "Cleaned.", "next_scene": "CLEANED_SCENE"}\n```'
        self.mock_client.models.generate_content.return_value = self.create_mock_response(
            json_with_fences
        )
        
        narrative, next_scene = self.orchestrator.process_user_command("test")
        
        self.assertEqual(narrative, "Cleaned.")
        self.assertEqual(next_scene, "CLEANED_SCENE")
        self.assertEqual(self.orchestrator.current_scene, "CLEANED_SCENE")

    def test_handles_api_exception_gracefully(self):
        """Test that a fallback message is returned if the API call fails."""
        # Configure the mock to raise an exception
        self.mock_client.models.generate_content.side_effect = Exception("API Error")
        
        # The state before the call
        initial_state = self.orchestrator.current_scene

        narrative, next_scene = self.orchestrator.process_user_command("test")

        self.assertEqual(narrative, "I'm having a little trouble connecting. Could you try that again?")
        # Ensure the state did not change on error
        self.assertEqual(next_scene, initial_state)
        self.assertEqual(self.orchestrator.current_scene, initial_state)


if __name__ == '__main__':
    unittest.main()
