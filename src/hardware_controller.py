import asyncio
import logging
import os
import serial
import time


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
        # The connection will now be established asynchronously.

    async def _connect(self):
        """Waits for and establishes the serial connection asynchronously."""
        logging.info(
            f"[HARDWARE] Waiting for serial port '{self.port}' for {self.name}..."
        )
        start_time = time.time()
        while not os.path.exists(self.port):
            if time.time() - start_time > 10:  # 10-second timeout
                logging.error(
                    f"[HARDWARE] ERROR: Timed out waiting for port '{self.port}'."
                )
                return
            await asyncio.sleep(0.5)
        try:
            # Run the blocking serial.Serial call in a separate thread
            self.ser = await asyncio.to_thread(
                serial.Serial, self.port, self.baudrate, timeout=1
            )
            logging.info(
                f"[HARDWARE] Successfully connected to {self.name} on port: {self.port}"
            )
        except serial.SerialException as e:
            logging.error(
                f"[HARDWARE] ERROR: Could not open port for {self.name}: {e}. Commands will be mocked."
            )

    async def send_command(self, command: str):
        """Sends a command to the serial port asynchronously."""
        if self.ser and self.ser.is_open:
            try:
                full_command = command + "\n"
                # Run the blocking write call in a separate thread
                await asyncio.to_thread(self.ser.write, full_command.encode("utf-8"))
                logging.info(
                    f'[HARDWARE] ---> Sent to {self.name}: "{full_command.strip()}"'
                )

                # Always read a line back to prevent the buffer from filling up and blocking.
                # The serial port has a timeout, so this won't block forever.
                await asyncio.sleep(0.1)
                response = await asyncio.to_thread(self.ser.readline)
                response_str = response.decode("utf-8").strip()
                if response_str:
                    logging.info(
                        f'[HARDWARE] <--- Received from {self.name}: "{response_str}"'
                    )

                return f"Command '{command}' sent to {self.name}."
            except serial.SerialException as e:
                return f"[HARDWARE] ERROR: Failed to send command to {self.name}: {e}"
        else:
            logging.info(
                f'[HARDWARE] MOCK_ACTION: Port for {self.name} not available. Mock command: "{command}"'
            )
            return f"Mock command '{command}' executed for {self.name}."

    async def close(self):
        if self.ser and self.ser.is_open:
            await asyncio.to_thread(self.ser.close)
            logging.info(f"[HARDWARE] Serial connection for {self.name} closed.")


class HardwareManager:
    """A centralized class to manage all hardware controllers and tool functions."""

    def __init__(self):
        env = os.getenv("AUM_ENVIRONMENT", "prod")  # Default to production

        if env == "dev":
            logging.info(
                "[HARDWARE] Running in DEV mode. Connecting to EMULATOR ports."
            )
            main_port = os.getenv(
                "MAIN_CONTROLLER_PORT_EMULATOR", "./main_controller_emu_port"
            )
            arm_port = os.getenv("ROBOTIC_ARM_PORT_EMULATOR", "./robotic_arm_emu_port")
        else:
            logging.info(
                "[HARDWARE] Running in PROD mode. Connecting to REAL hardware ports."
            )
            main_port = os.getenv("MAIN_CONTROLLER_PORT")
            arm_port = os.getenv("ROBOTIC_ARM_PORT")

        if not main_port or not arm_port:
            logging.error(
                "[HARDWARE] ERROR: Serial ports not defined in environment. Halting."
            )
            main_port = main_port or "./mock_main_port"
            arm_port = arm_port or "./mock_arm_port"

        self.main_scene_controller = SerialCommunicator(
            port=main_port, baudrate=9600, name="Main Scene Controller"
        )
        self.robotic_arm_controller = SerialCommunicator(
            port=arm_port, baudrate=57600, name="Robotic Arm Controller"
        )

    async def connect_all(self):
        """Connects to all serial devices concurrently."""
        await asyncio.gather(
            self.main_scene_controller._connect(),
            self.robotic_arm_controller._connect(),
        )

    def _validate_params(
        self,
        p1=None,
        p2=None,
        p3=None,
        velocity=None,
        acceleration=None,
        scene_command_id=None,
    ):
        """A single method to validate all possible hardware parameters."""
        if scene_command_id is not None and scene_command_id not in VALID_SCENE_IDS:
            return f"[HARDWARE] VALIDATION_ERROR: Invalid scene_command_id '{scene_command_id}'."
        if p1 is not None and p1 not in VALID_POSITION_RANGE:
            return f"[HARDWARE] VALIDATION_ERROR: Invalid p1 position '{p1}'."
        if p2 is not None and p2 not in VALID_POSITION_RANGE:
            return f"[HARDWARE] VALIDATION_ERROR: Invalid p2 position '{p2}'."
        if p3 is not None and p3 not in VALID_POSITION_RANGE:
            return f"[HARDWARE] VALIDATION_ERROR: Invalid p3 position '{p3}'."
        if velocity is not None and velocity not in VALID_VELOCITY_RANGE:
            return f"[HARDWARE] VALIDATION_ERROR: Invalid velocity '{velocity}'."
        if acceleration is not None and acceleration not in VALID_ACCELERATION_RANGE:
            return (
                f"[HARDWARE] VALIDATION_ERROR: Invalid acceleration '{acceleration}'."
            )
        return None

    async def trigger_diorama_scene(self, scene_command_id: int):
        """Triggers a scene on the diorama after validating the ID."""
        error = self._validate_params(scene_command_id=scene_command_id)
        if error:
            logging.error(error)
            return error
        return await self.main_scene_controller.send_command(str(scene_command_id))

    async def move_robotic_arm(
        self,
        p1: int,
        p2: int,
        p3: int,
        velocity: int = 50,
        acceleration: int = 5,
    ):
        """Moves the robotic arm to a specific position after validating parameters."""
        error = self._validate_params(
            p1=p1, p2=p2, p3=p3, velocity=velocity, acceleration=acceleration
        )
        if error:
            logging.error(error)
            return error
        command = f"3 {velocity} {velocity} {velocity} {acceleration} {acceleration} {acceleration} {p1} {p2} {p3}"
        return await self.robotic_arm_controller.send_command(command)

    async def play_video(self, video_file: str):
        """Plays a video file on the connected Android tablet using ADB."""
        # This command starts the default video player for a file in the Camera directory
        command = f"adb shell am start -a android.intent.action.VIEW -d file:///sdcard/DCIM/Camera/{video_file} -t video/*"
        logging.info(f"[HARDWARE] ---> Executing ADB command: {command}")

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await proc.communicate()

            if proc.returncode == 0:
                logging.info(
                    f"[HARDWARE] <--- ADB command successful: {stdout.decode().strip()}"
                )
                return f"Successfully started video '{video_file}'."
            else:
                error_message = stderr.decode().strip()
                logging.error(
                    f"[HARDWARE] ERROR: ADB command failed with code {proc.returncode}: {error_message}"
                )
                return f"Error playing video '{video_file}': {error_message}"

        except FileNotFoundError:
            logging.error(
                "[HARDWARE] ERROR: 'adb' command not found. Is the Android SDK Platform Tools installed and in your PATH?"
            )
            return "Error: 'adb' command not found."
        except Exception as e:
            logging.error(
                f"[HARDWARE] CRITICAL_ERROR: An unexpected error occurred while trying to play video: {e}"
            )
            return f"An unexpected error occurred: {e}"

    async def close_all_ports(self):
        """Closes all managed serial connections."""
        await asyncio.gather(
            self.main_scene_controller.close(), self.robotic_arm_controller.close()
        )
