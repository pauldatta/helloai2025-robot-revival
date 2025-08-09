import os
import serial
import time
from dotenv import load_dotenv
from google.genai.types import FunctionDeclaration

# --- Constants for Hardware Validation ---
VALID_SCENE_IDS = set(range(1, 16))
VALID_POSITION_RANGE = range(0, 4096)
VALID_VELOCITY_RANGE = range(0, 1024)
VALID_ACCELERATION_RANGE = range(0, 255)

class SerialCommunicator:
    """A class to handle serial communication with a microcontroller."""
    def __init__(self, port, baudrate, name="Controller"):
        self.port = port
        self.baudrate = baudrate
        self.name = name
        self.ser = None
        self._connect()

    def _connect(self):
        """Waits for and establishes the serial connection."""
        print(f"[{self.name}] Waiting for serial port '{self.port}'...")
        start_time = time.time()
        while not os.path.exists(self.port):
            if time.time() - start_time > 10:  # 10-second timeout
                print(f"[{self.name}] Error: Timed out waiting for port '{self.port}'.")
                return
            time.sleep(0.5)
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            print(f"Successfully connected to {self.name} on port: {self.port}")
        except serial.SerialException as e:
            print(f"Error opening port for {self.name}: {e}. Commands will be mocked.")

    def send_command(self, command: str):
        """Sends a command to the serial port and reads a line if it's the arm."""
        if self.ser and self.ser.is_open:
            try:
                full_command = command + '\n'
                self.ser.write(full_command.encode('utf-8'))
                print(f"HARDWARE ACTION: Sent to {self.name}: {full_command.strip()}")
                
                # If this is the robotic arm, read the feedback to prevent blocking
                if self.name == "Robotic Arm Controller":
                    time.sleep(0.1) # Give the emulator a moment to respond
                    response = self.ser.readline().decode('utf-8').strip()
                    print(f"[{self.name} SAYS]: {response}")

                return f"Command '{command}' sent to {self.name}."
            except serial.SerialException as e:
                return f"Failed to send command to {self.name}: {e}"
        else:
            print(f"HARDWARE ACTION (Mock): Port for {self.name} not available. Mock command: {command}")
            return f"Mock command '{command}' executed for {self.name}."

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            print(f"Serial connection for {self.name} closed.")


class HardwareManager:
    """A centralized class to manage all hardware controllers and tool functions."""
    def __init__(self):
        env = os.getenv('AUM_ENVIRONMENT', 'prod') # Default to production
        
        if env == 'dev':
            print("[HardwareManager] Running in DEV mode. Connecting to EMULATOR ports.")
            main_port = os.getenv('MAIN_CONTROLLER_PORT_EMULATOR', './main_controller_emu_port')
            arm_port = os.getenv('ROBOTIC_ARM_PORT_EMULATOR', './robotic_arm_emu_port')
        else:
            print("[HardwareManager] Running in PROD mode. Connecting to REAL hardware ports.")
            main_port = os.getenv('MAIN_CONTROLLER_PORT')
            arm_port = os.getenv('ROBOTIC_ARM_PORT')

        if not main_port or not arm_port:
            print("[HardwareManager] ERROR: Serial ports not defined in environment. Halting.")
            # In a real app, you might raise an exception here.
            # For this project, we'll proceed with mock connections.
            main_port = main_port or './mock_main_port'
            arm_port = arm_port or './mock_arm_port'

        self.main_scene_controller = SerialCommunicator(port=main_port, baudrate=9600, name="Main Scene Controller")
        self.robotic_arm_controller = SerialCommunicator(port=arm_port, baudrate=57600, name="Robotic Arm Controller")

    def _validate_params(self, p1=None, p2=None, p3=None, velocity=None, acceleration=None, scene_command_id=None):
        """A single method to validate all possible hardware parameters."""
        if scene_command_id is not None and scene_command_id not in VALID_SCENE_IDS:
            return f"Error: Invalid scene_command_id '{scene_command_id}'."
        if p1 is not None and p1 not in VALID_POSITION_RANGE:
            return f"Error: Invalid p1 position '{p1}'."
        if p2 is not None and p2 not in VALID_POSITION_RANGE:
            return f"Error: Invalid p2 position '{p2}'."
        if p3 is not None and p3 not in VALID_POSITION_RANGE:
            return f"Error: Invalid p3 position '{p3}'."
        if velocity is not None and velocity not in VALID_VELOCITY_RANGE:
            return f"Error: Invalid velocity '{velocity}'."
        if acceleration is not None and acceleration not in VALID_ACCELERATION_RANGE:
            return f"Error: Invalid acceleration '{acceleration}'."
        return None

    def trigger_diorama_scene(self, scene_command_id: int):
        """Triggers a scene on the diorama after validating the ID."""
        error = self._validate_params(scene_command_id=scene_command_id)
        if error:
            print(error)
            return error
        return self.main_scene_controller.send_command(str(scene_command_id))

    def move_robotic_arm(self, p1: int, p2: int, p3: int, velocity: int = 50, acceleration: int = 5):
        """Moves the robotic arm to a specific position after validating parameters."""
        error = self._validate_params(p1=p1, p2=p2, p3=p3, velocity=velocity, acceleration=acceleration)
        if error:
            print(error)
            return error
        command = f"3 {velocity} {velocity} {velocity} {acceleration} {acceleration} {acceleration} {p1} {p2} {p3}"
        return self.robotic_arm_controller.send_command(command)

    def close_all_ports(self):
        """Closes all managed serial connections."""
        self.main_scene_controller.close()
        self.robotic_arm_controller.close()

# --- Function Declarations for Gemini API ---
# These remain at the module level as they are static definitions for the API.

trigger_diorama_scene_declaration = FunctionDeclaration(
    name="trigger_diorama_scene",
    description="Triggers a specific scene on the diorama by sending a command ID.",
    parameters={
        "type": "object",
        "properties": {
            "scene_command_id": {
                "type": "integer",
                "description": "The command ID (1-15) for the scene."
            }
        },
        "required": ["scene_command_id"]
    }
)

move_robotic_arm_declaration = FunctionDeclaration(
    name="move_robotic_arm",
    description="Moves the 6-axis robotic arm to a specified coordinate position.",
    parameters={
        "type": "object",
        "properties": {
            "p1": {"type": "integer", "description": "Position for axis 1 (0-4095)."},
            "p2": {"type": "integer", "description": "Position for axis 2 (0-4095)."},
            "p3": {"type": "integer", "description": "Position for axis 3 (0-4095)."},
            "velocity": {"type": "integer", "description": "Movement velocity (0-1023)."},
            "acceleration": {"type": "integer", "description": "Movement acceleration (0-254)."}
        },
        "required": ["p1", "p2", "p3"]
    }
)