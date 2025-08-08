import os
import serial
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class SerialCommunicator:
    """A class to handle serial communication with a microcontroller."""
    def __init__(self, port, baudrate, name="Controller"):
        self.port = port
        self.baudrate = baudrate
        self.name = name
        self.ser = None

        # Wait for the serial port to be created by socat
        print(f"[{name}] Waiting for serial port '{port}' to become available...")
        start_time = time.time()
        while not os.path.exists(port):
            if time.time() - start_time > 30: # 30-second timeout
                print(f"[{name}] Error: Timed out waiting for port '{port}'.")
                break
            time.sleep(0.5)

        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            print(f"Successfully connected to {self.name} on port: {self.port}")
        except serial.SerialException as e:
            print(f"Error: Could not open serial port for {self.name} on {self.port}: {e}")
            print(f"Proceeding without serial communication for {self.name}. Commands will be mocked.")

    def send_command(self, command: str):
        """Sends a command to the serial port. This is a blocking call."""
        if self.ser and self.ser.is_open:
            try:
                full_command = command + '\n'
                self.ser.write(full_command.encode('utf-8'))
                print(f"DIRECTOR ACTION: Sent to {self.name}: {full_command.strip()}")
                time.sleep(0.1)
                return f"Command '{command}' sent to {self.name}."
            except serial.SerialException as e:
                return f"Failed to send command '{command}' to {self.name}."
        else:
            print(f"DIRECTOR ACTION (Mock): Serial port for {self.name} not available. Mock command: {command}")
            return f"Mock command '{command}' executed for {self.name}."

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            print(f"Serial connection for {self.name} closed.")

# --- Controller Initialization ---

main_scene_controller = None
robotic_arm_controller = None

def get_main_scene_controller():
    """Initializes and returns the main scene controller singleton."""
    global main_scene_controller
    if main_scene_controller is None:
        port = os.getenv('MAIN_CONTROLLER_PORT', './main_controller_app_port')
        main_scene_controller = SerialCommunicator(port=port, baudrate=9600, name="Main Scene Controller")
    return main_scene_controller

def get_robotic_arm_controller():
    """Initializes and returns the robotic arm controller singleton."""
    global robotic_arm_controller
    if robotic_arm_controller is None:
        port = os.getenv('ROBOTIC_ARM_PORT', './robotic_arm_app_port')
        robotic_arm_controller = SerialCommunicator(port=port, baudrate=57600, name="Robotic Arm Controller")
    return robotic_arm_controller

# --- Tool Definitions with Validation ---

VALID_SCENE_IDS = set(range(1, 16))
VALID_POSITION_RANGE = range(0, 4096)
VALID_VELOCITY_RANGE = range(0, 1024)
VALID_ACCELERATION_RANGE = range(0, 255)

def trigger_diorama_scene(scene_command_id: int):
    """
    Triggers a scene on the diorama. Validates the scene ID before sending.
    """
    if scene_command_id not in VALID_SCENE_IDS:
        error_msg = f"Error: Invalid scene_command_id '{scene_command_id}'. Must be an integer between 1 and 15."
        print(error_msg)
        return error_msg
    
    controller = get_main_scene_controller()
    return controller.send_command(str(scene_command_id))

def move_robotic_arm(p1: int, p2: int, p3: int, velocity: int = 50, acceleration: int = 5):
    """
    Moves the robotic arm to a specific position. Validates all parameters before sending.
    """
    if p1 not in VALID_POSITION_RANGE or p2 not in VALID_POSITION_RANGE or p3 not in VALID_POSITION_RANGE:
        error_msg = f"Error: Invalid position. All positions (p1, p2, p3) must be between 0 and 4095."
        print(error_msg)
        return error_msg
    
    if velocity not in VALID_VELOCITY_RANGE:
        error_msg = f"Error: Invalid velocity '{velocity}'. Must be between 0 and 1023."
        print(error_msg)
        return error_msg

    if acceleration not in VALID_ACCELERATION_RANGE:
        error_msg = f"Error: Invalid acceleration '{acceleration}'. Must be between 0 and 254."
        print(error_msg)
        return error_msg

    command = f"3 {velocity} {velocity} {velocity} {acceleration} {acceleration} {acceleration} {p1} {p2} {p3}"
    controller = get_robotic_arm_controller()
    return controller.send_command(command)

def close_all_ports():
    """A helper function to close all serial connections."""
    global main_scene_controller, robotic_arm_controller
    if main_scene_controller:
        main_scene_controller.close()
    if robotic_arm_controller:
        robotic_arm_controller.close()
