import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
from google.genai import types

# The module we are testing
from orchestrator import StatefulOrchestrator, _parse_json_from_text

class TestOrchestrator(unittest.TestCase):

    # Use setUp to patch dependencies that are common across tests
    def setUp(self):
        # Patch the file open call used for the system prompt
        self.mock_file_patcher = patch('builtins.open', mock_open(read_data="Mock System Prompt"))
        self.mock_file = self.mock_file_patcher.start()

        # Patch the HardwareManager to prevent real hardware calls
        self.mock_hw_manager_patcher = patch('orchestrator.HardwareManager')
        self.mock_hw_manager_class = self.mock_hw_manager_patcher.start()
        self.mock_hw_manager_instance = self.mock_hw_manager_class.return_value

        # Patch the genai Client
        self.mock_genai_client_patcher = patch('orchestrator.genai.Client')
        self.mock_genai_client_class = self.mock_genai_client_patcher.start()
        self.mock_genai_client_instance = self.mock_genai_client_class.return_value

        # Instantiate the orchestrator for use in tests
        self.orchestrator = StatefulOrchestrator()
        # Ensure the orchestrator uses our mocked client
        self.orchestrator.client = self.mock_genai_client_instance
        # Ensure the orchestrator uses our mocked hardware manager
        self.orchestrator.hardware = self.mock_hw_manager_instance

    # Use tearDown to stop the patchers
    def tearDown(self):
        self.mock_file_patcher.stop()
        self.mock_hw_manager_patcher.stop()
        self.mock_genai_client_patcher.stop()

    def test_initialization(self):
        """Tests that the orchestrator initializes correctly."""
        self.assertEqual(self.orchestrator.system_prompt, "Mock System Prompt")
        self.assertEqual(self.orchestrator.current_scene, "AWAITING_MODE_SELECTION")
        self.mock_hw_manager_class.assert_called_once()
        self.mock_genai_client_class.assert_called_once()
        print("\n[TEST] Initialization successful.")

    def test_process_user_command_with_tool_call(self):
        """Tests a successful command that results in a tool call and a narrative."""
        # 1. Setup the mock response from the Gemini API
        mock_response = MagicMock()
        
        # Create a mock function call part
        mock_function_call = types.FunctionCall(name='move_robotic_arm', args={'p1': 1, 'p2': 2, 'p3': 3})
        
        # Create a mock text part with the JSON payload
        response_payload = {"narrative": "Moving the arm!", "next_scene": "ARM_MOVED"}
        mock_text_part = types.Part(text=f"```json\n{json.dumps(response_payload)}\n```")

        # Structure the mock response object as the real API would
        mock_candidate = MagicMock()
        mock_candidate.content.parts = [
            types.Part(function_call=mock_function_call), 
            mock_text_part
        ]
        mock_response.candidates = [mock_candidate]
        
        self.mock_genai_client_instance.models.generate_content.return_value = mock_response

        # 2. Call the method under test
        narrative, next_scene = self.orchestrator.process_user_command("Move the arm")

        # 3. Assert the results
        self.assertEqual(narrative, "Moving the arm!")
        self.assertEqual(next_scene, "ARM_MOVED")
        self.assertEqual(self.orchestrator.current_scene, "ARM_MOVED")
        
        # Assert that the hardware method was called correctly
        self.mock_hw_manager_instance.move_robotic_arm.assert_called_once_with(p1=1, p2=2, p3=3)
        print("\n[TEST] Command with tool call and narrative works.")

    def test_process_user_command_no_tool_call(self):
        """Tests a successful command that results in only a narrative (e.g., a question)."""
        # 1. Setup the mock response
        mock_response = MagicMock()
        response_payload = {"narrative": "Aum is a person.", "next_scene": "AWAITING_MODE_SELECTION"}
        mock_text_part = types.Part(text=json.dumps(response_payload))
        
        mock_candidate = MagicMock()
        # Note: The parts list only contains a text part, no function call
        mock_candidate.content.parts = [mock_text_part]
        mock_response.candidates = [mock_candidate]
        
        self.mock_genai_client_instance.models.generate_content.return_value = mock_response

        # 2. Call the method
        narrative, next_scene = self.orchestrator.process_user_command("Who is Aum?")

        # 3. Assert the results
        self.assertEqual(narrative, "Aum is a person.")
        self.assertEqual(next_scene, "AWAITING_MODE_SELECTION")
        
        # Assert that no hardware methods were called
        self.mock_hw_manager_instance.move_robotic_arm.assert_not_called()
        self.mock_hw_manager_instance.trigger_diorama_scene.assert_not_called()
        print("\n[TEST] Command with narrative only (no tool call) works.")

    def test_process_user_command_api_error(self):
        """Tests the fallback mechanism when the Gemini API call fails."""
        self.mock_genai_client_instance.models.generate_content.side_effect = Exception("API Failure")

        narrative, next_scene = self.orchestrator.process_user_command("This will fail")

        self.assertEqual(narrative, "I seem to have gotten my wires crossed. Could you try that again?")
        # The scene should not change on a critical error
        self.assertEqual(next_scene, "AWAITING_MODE_SELECTION")
        print("\n[TEST] API error handling is correct.")

    def test_process_user_command_malformed_json(self):
        """Tests the fallback mechanism when the API returns a malformed JSON."""
        # 1. Setup a mock response with invalid JSON
        mock_response = MagicMock()
        mock_text_part = types.Part(text="This is not valid JSON")
        mock_candidate = MagicMock()
        mock_candidate.content.parts = [mock_text_part]
        mock_response.candidates = [mock_candidate]
        
        self.mock_genai_client_instance.models.generate_content.return_value = mock_response

        # 2. Call the method
        narrative, next_scene = self.orchestrator.process_user_command("Malformed")

        # 3. Assert the results
        self.assertEqual(narrative, "I'm not sure what to say next.")
        # The scene should not change on a parsing error
        self.assertEqual(next_scene, "AWAITING_MODE_SELECTION")
        print("\n[TEST] Malformed JSON response handling is correct.")

    def test_parse_json_from_text(self):
        """Tests the helper function for parsing JSON."""
        # Test with markdown wrapping
        md_json = '```json\n{"key": "value"}\n```'
        self.assertEqual(_parse_json_from_text(md_json), {"key": "value"})
        
        # Test with plain json
        plain_json = '{"key": "value"}'
        self.assertEqual(_parse_json_from_text(plain_json), {"key": "value"})
        
        # Test with invalid json
        self.assertIsNone(_parse_json_from_text("not json"))
        
        # Test with empty string
        self.assertIsNone(_parse_json_from_text(""))
        print("\n[TEST] JSON parsing helper works correctly.")

if __name__ == '__main__':
    unittest.main()
