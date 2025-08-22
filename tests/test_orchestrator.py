import asyncio
import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock, AsyncMock

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.orchestrator import StatefulOrchestrator


class TestOrchestratorConversation(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        """Set up a fresh orchestrator and mock dependencies for each test."""
        self.mock_file_patcher = patch(
            "builtins.open",
            unittest.mock.mock_open(read_data="You are Bob's storyteller."),
        )
        self.mock_file_patcher.start()

        self.mock_hw_manager_patcher = patch("src.orchestrator.HardwareManager")
        self.mock_hw_manager_class = self.mock_hw_manager_patcher.start()
        self.mock_hw_manager_instance = self.mock_hw_manager_class.return_value

        self.mock_genai_client_patcher = patch("src.orchestrator.genai.Client")
        self.mock_genai_client_class = self.mock_genai_client_patcher.start()
        self.mock_genai_client_instance = self.mock_genai_client_class.return_value
        self.mock_genai_client_instance.models.generate_content = MagicMock()

        self.orchestrator = StatefulOrchestrator()
        self.orchestrator.hardware = self.mock_hw_manager_instance
        self.orchestrator.hardware.trigger_diorama_scene = AsyncMock()
        self.orchestrator.hardware.move_robotic_arm = AsyncMock()

        self.mock_director = MagicMock()
        self.mock_director.send_qr_command_to_web = AsyncMock()

    def tearDown(self):
        patch.stopall()

    async def test_start_conversation(self):
        """Tests that the 'START_CONVERSATION' command returns the initial greeting."""
        result = await self.orchestrator.process_user_input(
            "START_CONVERSATION", self.mock_director
        )

        self.assertIn("Hello! I'm Bob.", result["narrative"])
        self.assertFalse(result["is_story_finished"])
        self.assertEqual(self.orchestrator.conversation_history, [])
        self.assertEqual(self.orchestrator.turn_number, 0)

    async def test_user_first_response(self):
        """Tests processing the first real user response after the conversation starts."""
        # Mock the AI's response
        ai_response_payload = {
            "scene_to_trigger": "MARKET",
            "next_question": "That sounds delicious! What's your favorite thing to eat there?",
            "is_finished": False,
        }
        mock_response = MagicMock()
        mock_response.text = json.dumps(ai_response_payload)
        self.mock_genai_client_instance.models.generate_content.return_value = (
            mock_response
        )

        user_input = "My favorite place is the local farmer's market."
        result = await self.orchestrator.process_user_input(
            user_input, self.mock_director
        )

        # Verify state and response
        self.assertEqual(self.orchestrator.conversation_history, [user_input])
        self.assertEqual(self.orchestrator.turn_number, 1)
        self.mock_genai_client_instance.models.generate_content.assert_called_once()

        # Allow the background task to run
        await asyncio.sleep(0)

        self.orchestrator.hardware.trigger_diorama_scene.assert_called_once_with(
            scene_command_id=3
        )
        self.assertEqual(
            result["narrative"],
            "That sounds delicious! What's your favorite thing to eat there?",
        )
        self.assertFalse(result["is_story_finished"])

    async def test_conversation_ends_at_turn_limit(self):
        """Tests that the conversation automatically ends after 5 turns."""
        # Manually set the state to be the 4th turn
        self.orchestrator.turn_number = 4
        self.orchestrator.conversation_history = [
            "response 1",
            "response 2",
            "response 3",
            "response 4",
        ]

        ai_response_payload = {
            "scene_to_trigger": "IDLE",
            "next_question": "Thanks for sharing!",
            "is_finished": False,
        }
        mock_response = MagicMock()
        mock_response.text = json.dumps(ai_response_payload)
        self.mock_genai_client_instance.models.generate_content.return_value = (
            mock_response
        )

        result = await self.orchestrator.process_user_input(
            "My final answer.", self.mock_director
        )

        # Verify the conversation ended
        self.assertTrue(result["is_story_finished"])
        self.mock_director.send_qr_command_to_web.assert_called_once()
        self.assertEqual(self.orchestrator.turn_number, 0)  # Should be reset

    async def test_stop_command(self):
        """Tests that a stop command immediately ends the conversation."""
        result = await self.orchestrator.process_user_input(
            "I'm done", self.mock_director
        )

        self.assertTrue(result["is_story_finished"])
        self.assertIn("Thank you for sharing", result["narrative"])
        self.mock_director.send_qr_command_to_web.assert_called_once()
        self.assertEqual(self.orchestrator.conversation_history, [])
        # Ensure the AI was not called for a stop command
        self.mock_genai_client_instance.models.generate_content.assert_not_called()


if __name__ == "__main__":
    unittest.main()
