import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set dummy environment variables for testing before importing the module
os.environ['AUM_ENVIRONMENT'] = 'dev'
os.environ['MAIN_CONTROLLER_PORT_EMULATOR'] = './test_main_port'
os.environ['ROBOTIC_ARM_PORT_EMULATOR'] = './test_arm_port'

from src.hardware_controller import HardwareManager

class TestHardwareManager(unittest.TestCase):

    @patch('src.hardware_controller.SerialCommunicator')
    def setUp(self, MockSerialCommunicator):
        """Set up a new HardwareManager instance before each test."""
        # Create mock instances for the two controllers
        self.mock_main_controller = MagicMock()
        self.mock_arm_controller = MagicMock()

        # Configure the mock to return our specific mocks when called
        def side_effect(port, baudrate, name):
            if name == "Main Scene Controller":
                return self.mock_main_controller
            if name == "Robotic Arm Controller":
                return self.mock_arm_controller
            return MagicMock()

        MockSerialCommunicator.side_effect = side_effect
        
        # Instantiate the class we are testing
        self.hardware_manager = HardwareManager()

    def test_initialization(self):
        """Tests that the HardwareManager initializes both controllers."""
        self.assertIsNotNone(self.hardware_manager.main_scene_controller)
        self.assertIsNotNone(self.hardware_manager.robotic_arm_controller)
        print("\n[TEST] HardwareManager initialization successful.")

    def test_trigger_diorama_scene_valid(self):
        """Tests a valid call to trigger_diorama_scene."""
        scene_id = 5
        self.hardware_manager.trigger_diorama_scene(scene_id)
        # Check that the send_command method was called on the correct controller with the correct argument
        self.mock_main_controller.send_command.assert_called_once_with(str(scene_id))
        print("\n[TEST] Valid diorama scene trigger works.")

    def test_trigger_diorama_scene_invalid(self):
        """Tests an invalid call to trigger_diorama_scene."""
        scene_id = 99 # Invalid ID
        result = self.hardware_manager.trigger_diorama_scene(scene_id)
        # Check that send_command was NOT called
        self.mock_main_controller.send_command.assert_not_called()
        # Check that an error message was returned
        self.assertIn("[HARDWARE] VALIDATION_ERROR: Invalid scene_command_id", result)
        print("\n[TEST] Invalid diorama scene trigger is handled correctly.")

    def test_move_robotic_arm_valid(self):
        """Tests a valid call to move_robotic_arm."""
        p1, p2, p3 = 1000, 2000, 3000
        self.hardware_manager.move_robotic_arm(p1, p2, p3)
        # Check that the send_command method was called on the arm controller
        self.mock_arm_controller.send_command.assert_called_once()
        # Check that the command string was formatted correctly
        called_command = self.mock_arm_controller.send_command.call_args[0][0]
        self.assertTrue(called_command.startswith('3 '))
        self.assertIn(str(p1), called_command)
        self.assertIn(str(p2), called_command)
        self.assertIn(str(p3), called_command)
        print("\n[TEST] Valid robotic arm move works.")

    def test_move_robotic_arm_invalid_position(self):
        """Tests an invalid position call to move_robotic_arm."""
        p1, p2, p3 = 5000, 2000, 3000 # Invalid p1
        result = self.hardware_manager.move_robotic_arm(p1, p2, p3)
        # Check that send_command was NOT called
        self.mock_arm_controller.send_command.assert_not_called()
        # Check that an error message was returned
        self.assertIn("[HARDWARE] VALIDATION_ERROR: Invalid p1 position", result)
        print("\n[TEST] Invalid robotic arm position is handled correctly.")

    def test_close_all_ports(self):
        """Tests that close_all_ports calls close on both controllers."""
        self.hardware_manager.close_all_ports()
        self.mock_main_controller.close.assert_called_once()
        self.mock_arm_controller.close.assert_called_once()
        print("\n[TEST] close_all_ports works correctly.")

if __name__ == '__main__':
    unittest.main()