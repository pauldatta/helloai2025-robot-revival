import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import json
import sys
import os
import asyncio
import time

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# The module we are testing
from src.orchestrator import StatefulOrchestrator, _parse_json_from_text


class TestOrchestrator(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Patch the file open call
        self.mock_file_patcher = patch(
            "builtins.open", unittest.mock.mock_open(read_data="Mock System Prompt")
        )
        self.mock_file = self.mock_file_patcher.start()

        # Patch HardwareManager
        self.mock_hw_manager_patcher = patch("src.orchestrator.HardwareManager")
        self.mock_hw_manager_class = self.mock_hw_manager_patcher.start()
        self.mock_hw_manager_instance = self.mock_hw_manager_class.return_value

        # Patch genai Client
        self.mock_genai_client_patcher = patch("src.orchestrator.genai.Client")
        self.mock_genai_client_class = self.mock_genai_client_patcher.start()
        self.mock_genai_client_instance = self.mock_genai_client_class.return_value

        # The method we need to mock is synchronous, so we use MagicMock
        self.mock_genai_client_instance.models.generate_content = MagicMock()

        # Instantiate the orchestrator
        self.orchestrator = StatefulOrchestrator()
        self.orchestrator.client = self.mock_genai_client_instance
        self.orchestrator.hardware = self.mock_hw_manager_instance

    def tearDown(self):
        self.mock_file_patcher.stop()
        self.mock_hw_manager_patcher.stop()
        self.mock_genai_client_patcher.stop()

    async def test_initialization(self):
        """Tests that the orchestrator initializes correctly."""
        self.assertEqual(self.orchestrator.system_prompt, "Mock System Prompt")
        self.assertEqual(self.orchestrator.current_scene, "AWAITING_MODE_SELECTION")
        self.mock_hw_manager_class.assert_called_once()
        self.mock_genai_client_class.assert_called_once()
        print("\n[TEST] Initialization successful.")

    async def test_scene_change_triggers_actions(self):
        """Tests that a state change correctly triggers mapped hardware actions."""
        # 1. Setup the mock response
        mock_response = MagicMock()
        response_payload = {
            "narrative": "Let's go to Aum's home.",
            "next_scene": "AUMS_HOME",
        }
        mock_response.text = json.dumps(response_payload)
        self.orchestrator.client.models.generate_content.return_value = mock_response

        # Mock the hardware methods to be async
        self.orchestrator.hardware.trigger_diorama_scene = AsyncMock()
        self.orchestrator.hardware.move_robotic_arm = AsyncMock()
        self.orchestrator.hardware.play_video = AsyncMock()

        # 2. Call the method
        narrative, next_scene = await self.orchestrator.process_user_command(
            "Show me the house"
        )

        # 3. Assert immediate results
        self.assertEqual(narrative, "Let's go to Aum's home.")
        self.assertEqual(next_scene, "AUMS_HOME")

        # 4. Wait for background tasks to complete
        await asyncio.sleep(0.01)
        tasks = self.orchestrator.background_tasks
        if tasks:
            await asyncio.gather(*tasks)

        # 5. Assert that hardware actions were called
        self.orchestrator.hardware.trigger_diorama_scene.assert_called_once_with(
            scene_command_id=2
        )
        self.orchestrator.hardware.move_robotic_arm.assert_called_once_with(
            p1=2468, p2=68, p3=2980
        )
        self.orchestrator.hardware.play_video.assert_called_once_with(
            video_file="part1_lost_in_the_city.mp4"
        )
        print("\n[TEST] Scene change correctly triggers mapped hardware actions.")

    async def test_no_scene_change_no_actions(self):
        """Tests that if the scene does not change, no hardware actions are triggered."""
        mock_response = MagicMock()
        response_payload = {
            "narrative": "Aum is a person.",
            "next_scene": "AWAITING_MODE_SELECTION",
        }
        mock_response.text = json.dumps(response_payload)
        self.orchestrator.client.models.generate_content.return_value = mock_response

        self.orchestrator.hardware.trigger_diorama_scene = AsyncMock()
        self.orchestrator.hardware.move_robotic_arm = AsyncMock()

        narrative, next_scene = await self.orchestrator.process_user_command(
            "Who is Aum?"
        )

        self.assertEqual(narrative, "Aum is a person.")
        self.assertEqual(next_scene, "AWAITING_MODE_SELECTION")
        self.orchestrator.hardware.move_robotic_arm.assert_not_called()
        self.orchestrator.hardware.trigger_diorama_scene.assert_not_called()
        print("\n[TEST] No scene change results in no hardware actions.")

    async def test_api_timeout_error(self):
        """Tests the fallback mechanism when the Gemini API call times out."""

        # This synchronous mock will sleep, causing the asyncio.wait_for in the
        # main code to raise a TimeoutError.
        def timeout_mock(*args, **kwargs):
            time.sleep(9)  # Sleep longer than the 8s timeout

        self.orchestrator.client.models.generate_content.side_effect = timeout_mock

        narrative, next_scene = await self.orchestrator.process_user_command(
            "This will fail"
        )

        self.assertEqual(
            narrative, "I took too long to think. Could you please try that again?"
        )
        self.assertEqual(next_scene, "AWAITING_MODE_SELECTION")
        print("\n[TEST] API timeout error handling is correct.")

    def test_parse_json_from_text(self):
        """Tests the helper function for parsing JSON."""
        md_json = '```json\n{"key": "value"}\n```'
        self.assertEqual(_parse_json_from_text(md_json), {"key": "value"})
        plain_json = '{"key": "value"}'
        self.assertEqual(_parse_json_from_text(plain_json), {"key": "value"})
        self.assertIsNone(_parse_json_from_text("not json"))
        self.assertIsNone(_parse_json_from_text(""))
        print("\n[TEST] JSON parsing helper works correctly.")


if __name__ == "__main__":
    unittest.main()
