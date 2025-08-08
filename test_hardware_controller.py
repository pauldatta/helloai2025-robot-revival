import unittest
from unittest.mock import patch, MagicMock
import serial
import os
import hardware_controller

# Import the classes and functions to be tested
from hardware_controller import SerialCommunicator, trigger_diorama_scene, move_robotic_arm, close_all_ports, get_main_scene_controller, get_robotic_arm_controller

class TestSerialCommunicator(unittest.TestCase):
    """Tests for the SerialCommunicator class."""

    @patch('os.path.exists', return_value=True)
    @patch('serial.Serial')
    def test_successful_connection(self, mock_serial, mock_exists):
        """Test that the communicator initializes successfully with a valid port."""
        mock_instance = MagicMock()
        mock_serial.return_value = mock_instance
        
        comm = SerialCommunicator(port="/dev/testport", baudrate=9600, name="Test")
        
        mock_exists.assert_called_with("/dev/testport")
        mock_serial.assert_called_with("/dev/testport", 9600, timeout=1)
        self.assertIsNotNone(comm.ser)
        comm.close()

    @patch('os.path.exists', return_value=True)
    @patch('serial.Serial')
    def test_failed_connection(self, mock_serial, mock_exists):
        """Test that the communicator handles a connection failure gracefully."""
        mock_serial.side_effect = serial.SerialException("Port not found")
        
        comm = SerialCommunicator(port="/dev/nonexistent", baudrate=9600, name="Test")
        
        mock_exists.assert_called_with("/dev/nonexistent")
        self.assertIsNone(comm.ser)

    @patch('os.path.exists', return_value=True)
    @patch('serial.Serial')
    def test_send_command_adds_newline(self, mock_serial, mock_exists):
        """Test that send_command appends a newline character."""
        mock_instance = MagicMock()
        mock_instance.is_open = True
        mock_serial.return_value = mock_instance

        comm = SerialCommunicator(port="/dev/testport", baudrate=9600, name="Test")
        comm.send_command("TEST_CMD")
        
        mock_instance.write.assert_called_with(b'TEST_CMD\n')
        comm.close()

    @patch('time.sleep')
    @patch('os.path.exists', side_effect=[False, False, True])
    @patch('serial.Serial')
    def test_waits_for_port(self, mock_serial, mock_exists, mock_sleep):
        """Test that the communicator waits for the port to become available."""
        mock_instance = MagicMock()
        mock_serial.return_value = mock_instance
        
        comm = SerialCommunicator(port="/dev/waitport", baudrate=9600, name="Test")
        
        self.assertEqual(mock_exists.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)
        self.assertIsNotNone(comm.ser)
        comm.close()


class TestHardwareToolsWithValidation(unittest.TestCase):
    """Tests for the hardware control tool functions, including validation logic."""

    def setUp(self):
        """Reset the controller singletons before each test."""
        # This is important to prevent tests from interfering with each other
        hardware_controller.main_scene_controller = None
        hardware_controller.robotic_arm_controller = None

    @patch('hardware_controller.get_main_scene_controller')
    def test_trigger_diorama_scene_valid_id(self, mock_get_controller):
        """Test that a valid scene ID is sent to the controller."""
        mock_controller = MagicMock()
        mock_get_controller.return_value = mock_controller
        trigger_diorama_scene(15)
        mock_controller.send_command.assert_called_with("15")

    @patch('hardware_controller.get_main_scene_controller')
    def test_trigger_diorama_scene_invalid_id_too_high(self, mock_get_controller):
        """Test that an invalid scene ID (too high) is rejected."""
        mock_controller = MagicMock()
        mock_get_controller.return_value = mock_controller
        result = trigger_diorama_scene(99)
        self.assertIn("Error: Invalid scene_command_id '99'", result)
        mock_controller.send_command.assert_not_called()

    @patch('hardware_controller.get_main_scene_controller')
    def test_trigger_diorama_scene_invalid_id_zero(self, mock_get_controller):
        """Test that an invalid scene ID (zero) is rejected."""
        mock_controller = MagicMock()
        mock_get_controller.return_value = mock_controller
        result = trigger_diorama_scene(0)
        self.assertIn("Error: Invalid scene_command_id '0'", result)
        mock_controller.send_command.assert_not_called()

    @patch('hardware_controller.get_robotic_arm_controller')
    def test_move_robotic_arm_valid_params(self, mock_get_controller):
        """Test that valid parameters are sent to the arm controller."""
        mock_controller = MagicMock()
        mock_get_controller.return_value = mock_controller
        move_robotic_arm(p1=0, p2=2048, p3=4095, velocity=100, acceleration=50)
        expected_command = "3 100 100 100 50 50 50 0 2048 4095"
        mock_controller.send_command.assert_called_with(expected_command)

    @patch('hardware_controller.get_robotic_arm_controller')
    def test_move_robotic_arm_invalid_position(self, mock_get_controller):
        """Test that an out-of-range position is rejected."""
        mock_controller = MagicMock()
        mock_get_controller.return_value = mock_controller
        result = move_robotic_arm(p1=5000, p2=2048, p3=4095)
        self.assertIn("Error: Invalid position", result)
        mock_controller.send_command.assert_not_called()

    @patch('hardware_controller.get_robotic_arm_controller')
    def test_move_robotic_arm_invalid_velocity(self, mock_get_controller):
        """Test that an out-of-range velocity is rejected."""
        mock_controller = MagicMock()
        mock_get_controller.return_value = mock_controller
        result = move_robotic_arm(p1=1, p2=1, p3=1, velocity=2000)
        self.assertIn("Error: Invalid velocity '2000'", result)
        mock_controller.send_command.assert_not_called()

    @patch('hardware_controller.get_robotic_arm_controller')
    def test_move_robotic_arm_invalid_acceleration(self, mock_get_controller):
        """Test that an out-of-range acceleration is rejected."""
        mock_controller = MagicMock()
        mock_get_controller.return_value = mock_controller
        result = move_robotic_arm(p1=1, p2=1, p3=1, acceleration=300)
        self.assertIn("Error: Invalid acceleration '300'", result)
        mock_controller.send_command.assert_not_called()

if __name__ == '__main__':
    unittest.main()
