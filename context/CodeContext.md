The @OriginalSoftware/ folder contains over 227 files, mostly unknown file types, folders, and language files. Based on a review of 25 files, this folder appears to contain source code and configuration files for various software projects, likely related to embedded systems, web development, and Adobe AIR applications.

### Folder Structure Overview:

- **\_Web**: This subfolder contains PHP and text files, suggesting web-related functionalities, potentially for data logging or dynamic content.
- **\_MainController**: This subfolder, along with its `_old_` subfolder, holds XML configuration files for Adobe AIR applications (MainController). These files define application properties like ID, version, filename, and initial window settings.
- **\_MainTablet**: This subfolder, specifically its `_old_` subfolder, contains an XML configuration for an Adobe AIR application named "23-MainTablet," which appears to be a full-screen tablet application with various Android permissions.
- **\_MainRobotis**: This subfolder contains `.ino` files, indicating Arduino or similar microcontroller code, specifically for controlling Dynamixel motors.
- **\_MainMega**: This subfolder contains `.ino` files, also suggesting Arduino or microcontroller code, likely for controlling LEDs and servos, and managing sensor input.

### Detailed Analysis by Topic:

**1. Adobe AIR Applications (MainController & MainTablet)**

Several `.xml` files define Adobe AIR applications. These files outline the core properties of the applications, including:

- **Application ID**: Unique identifier for the application.
- **Version Number**: Current version of the application.
- **Filename**: The executable name of the application.
- **Initial Window Settings**: Configurations for the application's main window, such as content (SWF file), system chrome, transparency, visibility, fullscreen mode, aspect ratio, and resizability.

Here's a comparison of the `MainController` application configurations:

| File Title                 | ID                | Version | Filename           | Content SWF            | Supported Lang |
| :------------------------- | :---------------- | :------ | :----------------- | :--------------------- | :------------- |
| 028_MainController-app.xml | 028-MainControll. | 1.0     | 028_MainController | 028_MainController.swf |                |
| 030_MainController-app.xml | MainController    | 1.0     | MainController     | 030_MainController.swf |                |
| 031_MainController-app.xml | MainController    | 1.0     | MainController     | 031_MainController.swf |                |
| 032_MainController-app.xml | MainController    | 1.0     | MainController     | 032_MainController.swf |                |
| 035_MainController-app.xml | MainController    | 1.0     | MainController     | 035_MainController.swf | en             |
| 037_MainController-app.xml | MainController    | 1.0     | MainController     | 037_MainController.swf | en             |
| 038_MainController-app.xml | MainController    | 1.0     | MainController     | 038_MainController.swf | en             |
| 039_MainController-app.xml | MainController    | 1.0     | MainController     | 039_MainController.swf | en             |

The `23-MainTablet-app.xml` file indicates a tablet-specific application with full-screen capability and Android permissions, including internet access, external storage write access, phone state reading, fine location access, wake lock, network state access, and Wi-Fi state access.

**2. Web Scripts for Data Handling**

The `_Web` subfolder contains PHP files (`lightstate.php`, `finder.php`) and associated text files (`lightstate.txt`, `found.txt`). These scripts appear to handle simple GET requests, write the received data to text files, and then echo the data. This suggests a basic logging or data transfer mechanism, possibly for receiving status updates or commands from an external source.

- `lightstate.php` and `finder.php` both take a `lightstate` or `data` parameter from a GET request and write it to `lightstate.txt` or `found.txt` respectively.

**3. Microcontroller Firmware (Arduino/Teensy)**

The `.ino` files (Arduino sketches) in `_MainRobotis` and `_MainMega` detail the logic for controlling hardware components.

- **26_AllMotor_JointMode.ino**: This file is an Arduino sketch for controlling Dynamixel motors (DXL_ID10, DXL_ID11, DXL_ID21). It initializes the motors in joint mode, sets their initial positions, and provides functionalities for:

  - Torque enable/disable.
  - Setting motor velocity and acceleration profiles.
  - Setting goal positions for each motor.
  - Reading back present motor positions at regular intervals.
  - Processing serial commands to control motor actions.

- **29_MainMega.ino**: This Arduino sketch seems to be for a "Main Teensy / Mega" controller, managing various LEDs and servos. Key functionalities include:

  - Control of multiple FastLED-driven LED strips (artwork, Google Map, logo back, G-tail).
  - Control of Pololu Maestro servos for mechanical scenes (Home Sign, Aum Cry, Market Aunty, Phone, BK Market).
  - Sensor input processing (distance sensor with averaging).
  - Implementing various "scenes" (e.g., `HOME_SIGN_SHOW`, `LED_MAP_SHOW`, `PHONE_RING`) that involve coordinated movements of servos and LED animations.
  - Serial communication for receiving commands to trigger these scenes.

- **22_SecMega.ino**: This is likely a "Secondary Mega" controller, working in conjunction with `29_MainMega.ino`. Its primary role is to control the "LOGO FRONT" LEDs. It reads digital pin states from the Main Mega to determine when to show or hide the front LEDs and animates color filling for the logo.

**4. Command and Configuration Files**

- **command.txt**: Lists commands, mostly "show" and "hide" actions, for various elements like `ledmap`, `ledlogo`, `homesign`, `aunty`, and `bkmarketsign`. These commands are likely intended for serial communication with the microcontrollers.
- **textfiles.txt**: Contains a mix of information, including:
  - A link to a RealtimeBoard (Miro) board.
  - Robot arm default and scene positions, likely for the Dynamixel motors.
  - More serial commands for the "MT" (Main Teensy/Mega) controller.
  - Network and login credentials for router Wi-Fi, router admin, Gmail, Stringify, sureMDM, and a Mac Mini. **It is highly recommended to review and secure any sensitive credentials found in plain text.**

### Interconnections and Flow:

It appears there is a system with:

1.  **Web Interface**: PHP scripts potentially receive data or commands from a web source.
2.  **Main Controller (Adobe AIR)**: Applications running on a desktop or tablet might serve as user interfaces or control panels.
3.  **Microcontrollers (MainMega, SecMega, Robotis)**: These devices handle the physical interactions:
    - **MainMega (`29_MainMega.ino`)** seems to be the central orchestrator for LED animations, servo movements, and sensor input, reacting to serial commands (possibly from the Adobe AIR app or another control system).
    - **SecMega (`22_SecMega.ino`)** acts as a slave controller for the front logo LEDs, triggered by signals from the MainMega.
    - **Robotis (`26_AllMotor_JointMode.ino`)** controls a robotic arm with Dynamixel motors, likely receiving commands to adjust its position, velocity, and acceleration.

The `command.txt` and `textfiles.txt` files likely provide the vocabulary of commands used to communicate with the microcontroller systems.
