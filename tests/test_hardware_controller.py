import unittest
from unittest.mock import patch, AsyncMock
import os
import sys
from src.hardware_controller import HardwareManager

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set dummy environment variables for testing before importing the module
os.environ["AUM_ENVIRONMENT"] = "dev"
os.environ["MAIN_CONTROLLER_PORT_EMULATOR"] = "./test_main_port"
os.environ["ROBOTIC_ARM_PORT_EMULATOR"] = "./test_arm_port"


class TestHardwareManager(unittest.IsolatedAsyncioTestCase):
    @patch("src.hardware_controller.SerialCommunicator")
    def setUp(self, MockSerialCommunicator):
        """Set up a new HardwareManager instance before each test."""
        # Create mock instances for the two controllers
        self.mock_main_controller = AsyncMock()
        self.mock_arm_controller = AsyncMock()

        # Configure the mock to return our specific mocks when called
        def side_effect(port, baudrate, name):
            if name == "Main Scene Controller":
                return self.mock_main_controller
            if name == "Robotic Arm Controller":
                return self.mock_arm_controller
            return AsyncMock()

        MockSerialCommunicator.side_effect = side_effect

        # Instantiate the class we are testing
        self.hardware_manager = HardwareManager()

    async def test_initialization(self):
        """Tests that the HardwareManager initializes both controllers."""
        self.assertIsNotNone(self.hardware_manager.main_scene_controller)
        self.assertIsNotNone(self.hardware_manager.robotic_arm_controller)
        print("\n[TEST] HardwareManager initialization successful.")

    async def test_trigger_diorama_scene_valid(self):
        """Tests a valid call to trigger_diorama_scene."""
        scene_id = 5
        await self.hardware_manager.trigger_diorama_scene(scene_id)
        self.mock_main_controller.send_command.assert_called_once_with(str(scene_id))
        print("\n[TEST] Valid diorama scene trigger works.")

    async def test_trigger_diorama_scene_invalid(self):
        """Tests an invalid call to trigger_diorama_scene."""
        scene_id = 99  # Invalid ID
        result = await self.hardware_manager.trigger_diorama_scene(scene_id)
        self.mock_main_controller.send_command.assert_not_called()
        self.assertIn("[HARDWARE] VALIDATION_ERROR: Invalid scene_command_id", result)
        print("\n[TEST] Invalid diorama scene trigger is handled correctly.")

    async def test_move_robotic_arm_valid(self):
        """Tests a valid call to move_robotic_arm."""
        p1, p2, p3 = 1000, 2000, 3000
        await self.hardware_manager.move_robotic_arm(p1, p2, p3)
        self.mock_arm_controller.send_command.assert_called_once()
        called_command = self.mock_arm_controller.send_command.call_args[0][0]
        self.assertTrue(called_command.startswith("3 "))
        self.assertIn(str(p1), called_command)
        self.assertIn(str(p2), called_command)
        self.assertIn(str(p3), called_command)
        # Check the exact command format
        expected_command = f"3 50 50 50 5 5 5 {p1} {p2} {p3}"
        self.assertEqual(called_command, expected_command)
        print("\n[TEST] Valid robotic arm move works.")

    async def test_move_robotic_arm_invalid_position(self):
        """Tests an invalid position call to move_robotic_arm."""
        p1, p2, p3 = 5000, 2000, 3000  # Invalid p1
        result = await self.hardware_manager.move_robotic_arm(p1, p2, p3)
        self.mock_arm_controller.send_command.assert_not_called()
        self.assertIn("[HARDWARE] VALIDATION_ERROR: Invalid p1 position", result)
        print("\n[TEST] Invalid robotic arm position is handled correctly.")

    async def test_close_all_ports(self):
        """Tests that close_all_ports calls close on both controllers."""
        await self.hardware_manager.close_all_ports()
        self.mock_main_controller.close.assert_called_once()
        self.mock_arm_controller.close.assert_called_once()
        print("\n[TEST] close_all_ports works correctly.")


class TestHardwareManagerValidation(unittest.TestCase):
    def setUp(self):
        """Set up a new HardwareManager instance for validation tests."""
        # We don't need mocks for this, just the instance
        self.hardware_manager = HardwareManager()

    def test_validate_params_all_valid(self):
        """Test _validate_params with a set of all valid parameters."""
        result = self.hardware_manager._validate_params(
            p1=100, p2=200, p3=300, velocity=50, acceleration=10, scene_command_id=1
        )
        self.assertIsNone(result)
        print("\n[TEST] _validate_params handles all valid inputs.")

    def test_validate_params_invalid_scene_id(self):
        """Test _validate_params with an invalid scene_command_id."""
        result = self.hardware_manager._validate_params(scene_command_id=99)
        self.assertIn("Invalid scene_command_id", result)
        print("\n[TEST] _validate_params catches invalid scene_id.")

    def test_validate_params_invalid_p1(self):
        """Test _validate_params with an invalid p1 position."""
        result = self.hardware_manager._validate_params(p1=9999)
        self.assertIn("Invalid p1 position", result)
        print("\n[TEST] _validate_params catches invalid p1.")

    def test_validate_params_invalid_velocity(self):
        """Test _validate_params with an invalid velocity."""
        result = self.hardware_manager._validate_params(velocity=2000)
        self.assertIn("Invalid velocity", result)
        print("\n[TEST] _validate_params catches invalid velocity.")

    def test_validate_params_invalid_acceleration(self):
        """Test _validate_params with an invalid acceleration."""
        result = self.hardware_manager._validate_params(acceleration=300)
        self.assertIn("Invalid acceleration", result)
        print("\n[TEST] _validate_params catches invalid acceleration.")

    def test_validate_params_only_some_params(self):
        """Test _validate_params with a subset of parameters."""
        result = self.hardware_manager._validate_params(p1=100, velocity=50)
        self.assertIsNone(result)
        print("\n[TEST] _validate_params handles a subset of valid inputs.")


if __name__ == "__main__":
    unittest.main()
