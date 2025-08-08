import unittest
from unittest.mock import patch, MagicMock
import serial

# Import the classes and functions to be tested
from hardware_controller import SerialCommunicator, trigger_diorama_scene, move_robotic_arm, close_all_ports

class TestSerialCommunicator(unittest.TestCase):
    """Tests for the SerialCommunicator class."""

    @patch('serial.Serial')
    def test_successful_connection(self, mock_serial):
        """Test that the communicator initializes successfully with a valid port."""
        mock_instance = MagicMock()
        mock_serial.return_value = mock_instance
        comm = SerialCommunicator(port="/dev/testport", baudrate=9600, name="Test")
        mock_serial.assert_called_with("/dev/testport", 9600, timeout=1)
        self.assertIsNotNone(comm.ser)
        comm.close()

    @patch('serial.Serial')
    def test_failed_connection(self, mock_serial):
        """Test that the communicator handles a connection failure gracefully."""
        mock_serial.side_effect = serial.SerialException("Port not found")
        comm = SerialCommunicator(port="/dev/nonexistent", baudrate=9600, name="Test")
        self.assertIsNone(comm.ser)

    @patch('serial.Serial')
    def test_send_command_adds_newline(self, mock_serial):
        """Test that send_command appends a newline character."""
        mock_instance = MagicMock()
        mock_instance.is_open = True
        mock_serial.return_value = mock_instance

        comm = SerialCommunicator(port="/dev/testport", baudrate=9600, name="Test")
        comm.ser = mock_instance
        comm.send_command("TEST_CMD")
        mock_instance.write.assert_called_with(b'TEST_CMD\n')
        comm.close()

class TestHardwareToolsWithValidation(unittest.TestCase):
    """Tests for the hardware control tool functions, including validation logic."""

    @patch('hardware_controller.main_scene_controller')
    def test_trigger_diorama_scene_valid_id(self, mock_scene_controller):
        """Test that a valid scene ID is sent to the controller."""
        trigger_diorama_scene(15)
        mock_scene_controller.send_command.assert_called_with("15")

    @patch('hardware_controller.main_scene_controller')
    def test_trigger_diorama_scene_invalid_id_too_high(self, mock_scene_controller):
        """Test that an invalid scene ID (too high) is rejected."""
        result = trigger_diorama_scene(99)
        self.assertIn("Error: Invalid scene_command_id '99'", result)
        mock_scene_controller.send_command.assert_not_called()

    @patch('hardware_controller.main_scene_controller')
    def test_trigger_diorama_scene_invalid_id_zero(self, mock_scene_controller):
        """Test that an invalid scene ID (zero) is rejected."""
        result = trigger_diorama_scene(0)
        self.assertIn("Error: Invalid scene_command_id '0'", result)
        mock_scene_controller.send_command.assert_not_called()

    @patch('hardware_controller.robotic_arm_controller')
    def test_move_robotic_arm_valid_params(self, mock_arm_controller):
        """Test that valid parameters are sent to the arm controller."""
        move_robotic_arm(p1=0, p2=2048, p3=4095, velocity=100, acceleration=50)
        expected_command = "3 100 100 100 50 50 50 0 2048 4095"
        mock_arm_controller.send_command.assert_called_with(expected_command)

    @patch('hardware_controller.robotic_arm_controller')
    def test_move_robotic_arm_invalid_position(self, mock_arm_controller):
        """Test that an out-of-range position is rejected."""
        result = move_robotic_arm(p1=5000, p2=2048, p3=4095)
        self.assertIn("Error: Invalid position", result)
        mock_arm_controller.send_command.assert_not_called()

    @patch('hardware_controller.robotic_arm_controller')
    def test_move_robotic_arm_invalid_velocity(self, mock_arm_controller):
        """Test that an out-of-range velocity is rejected."""
        result = move_robotic_arm(p1=1, p2=1, p3=1, velocity=2000)
        self.assertIn("Error: Invalid velocity '2000'", result)
        mock_arm_controller.send_command.assert_not_called()

    @patch('hardware_controller.robotic_arm_controller')
    def test_move_robotic_arm_invalid_acceleration(self, mock_arm_controller):
        """Test that an out-of-range acceleration is rejected."""
        result = move_robotic_arm(p1=1, p2=1, p3=1, acceleration=300)
        self.assertIn("Error: Invalid acceleration '300'", result)
        mock_arm_controller.send_command.assert_not_called()

if __name__ == '__main__':
    unittest.main()