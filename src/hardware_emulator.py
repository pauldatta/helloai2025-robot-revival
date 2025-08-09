import asyncio
import serial
import os
import sys
from dotenv import load_dotenv

# Load environment variables to get the port names
load_dotenv()

class RoboticArmEmulator:
    """Simulates the Robotic Arm Controller (OpenCR board)."""

    def __init__(self):
        # Initial position, mimicking the real device's startup
        self.position = [2048, 0, 3960]
        self.port_name = os.getenv('ROBOTIC_ARM_PORT_EMULATOR', './robotic_arm_emu_port')
        if not self.port_name:
            raise ValueError("ROBOTIC_ARM_PORT_EMULATOR not set in .env file")
        self.ser = serial.Serial(self.port_name, 57600, timeout=0.1)
        print(f"[ARM_EMU] Listening on {self.port_name}")
        sys.stdout.flush()

    async def listen_for_commands(self):
        """Waits for commands and updates the arm's state."""
        while True:
            try:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline()
                    if line:
                        line = line.decode('utf-8').strip()
                        print(f"[ARM_EMU] <--- Received command: \"{line}\"")
                        sys.stdout.flush()
                        parts = line.split()
                        command_id = int(parts[0])
                        if command_id == 3: # Move Full
                            self.position = [int(p) for p in parts[7:10]]
                        elif command_id == 4: # Move Position
                            self.position = [int(p) for p in parts[1:4]]
                        
                        # Send a confirmation/position update immediately after command
                        pos_str = f"angle:{self.position[0]}|{self.position[1]}|{self.position[2]}\n"
                        self.ser.write(pos_str.encode('utf-8'))
                        
                        print(f"[ARM_EMU] ---> State updated. New position: {self.position}")
                        sys.stdout.flush()
            except Exception as e:
                print(f"[ARM_EMU] ERROR: Could not process command: {e}")
                sys.stdout.flush()
            await asyncio.sleep(0.05)

    async def send_position_updates(self):
        """Continuously sends position feedback, like the real device."""
        while True:
            try:
                pos_str = f"angle:{self.position[0]}|{self.position[1]}|{self.position[2]}\n"
                self.ser.write(pos_str.encode('utf-8'))
            except Exception as e:
                print(f"[ARM_EMU] ERROR: Could not send position update: {e}")
                sys.stdout.flush()
            await asyncio.sleep(0.01) # 10ms interval from original code

    def close(self):
        self.ser.close()

class MainSceneEmulator:
    """Simulates the Main Scene Controller (Arduino Mega)."""

    def __init__(self):
        self.port_name = os.getenv('MAIN_CONTROLLER_PORT_EMULATOR', './main_controller_emu_port')
        if not self.port_name:
            raise ValueError("MAIN_CONTROLLER_PORT_EMULATOR not set in .env file")
        self.ser = serial.Serial(self.port_name, 9600, timeout=0.1)
        print(f"[SCENE_EMU] Listening on {self.port_name}")
        sys.stdout.flush()

    async def listen_for_commands(self):
        """Waits for commands and prints them."""
        while True:
            try:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline()
                    if line:
                        line = line.decode('utf-8').strip()
                        print(f"[SCENE_EMU] <--- Received command: \"{line}\"")
                        # Send a simple "OK" confirmation
                        self.ser.write(b"OK\n")
                        sys.stdout.flush()
            except Exception as e:
                print(f"[SCENE_EMU] ERROR: Could not process command: {e}")
                sys.stdout.flush()
            await asyncio.sleep(0.05)

    def close(self):
        self.ser.close()

async def main():
    """Runs both emulators concurrently."""
    print("--- Hardware Emulator ---")
    print("Simulating physical Arduino and OpenCR boards.")
    print("Press Ctrl+C to exit.")
    sys.stdout.flush()

    arm_emulator = None
    scene_emulator = None
    try:
        arm_emulator = RoboticArmEmulator()
        scene_emulator = MainSceneEmulator()

        await asyncio.gather(
            arm_emulator.listen_for_commands(),
            arm_emulator.send_position_updates(),
            scene_emulator.listen_for_commands()
        )
    except serial.SerialException as e:
        print(f"[EMULATOR] CRITICAL_ERROR: {e}")
        print("[EMULATOR] Is 'socat' running correctly? Check Procfile.dev.")
        sys.stdout.flush()
    except KeyboardInterrupt:
        print("\n--- Shutting down hardware emulator ---")
        sys.stdout.flush()
    finally:
        if arm_emulator:
            arm_emulator.close()
        if scene_emulator:
            scene_emulator.close()


if __name__ == "__main__":
    asyncio.run(main())