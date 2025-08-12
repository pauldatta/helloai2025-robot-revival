import serial.tools.list_ports


def list_serial_ports():
    """
    Lists serial ports using the pyserial list_ports module.
    Each port is identified by its device, name, and description.
    """
    print("Listing available serial ports...")

    # Use the list_ports.comports() function to get a list of all serial port objects.
    ports = serial.tools.list_ports.comports()

    if not ports:
        print("No serial ports found.")
        return

    # Iterate through the list of ports and print their details.
    for port, desc, hwid in sorted(ports):
        print(f"Device: {port}")
        print(f"Description: {desc}")
        print(f"Hardware ID: {hwid}")
        print("-" * 20)


if __name__ == "__main__":
    list_serial_ports()
