# Aum's Journey - Hardware Control Context

This document provides a precise summary of the original software found in the `context/OriginalSoftware/` directory. It details the functionality of each microcontroller, the serial commands they accept, and the communication protocols they use. This information is critical for developing the Python-based control plane that will direct the diorama.

--- 

## System Architecture Overview

The installation is controlled by three distinct microcontrollers:

1.  **Robotic Arm Controller (`26_AllMotor_JointMode.ino`)**: An OpenCR board that manages a 3-axis robotic arm using Dynamixel motors. It receives high-level commands to control the arm's position, velocity, and acceleration.
2.  **Main Scene Controller (`29_MainMega.ino`)**: An Arduino Mega (or Teensy) that acts as the central orchestrator for the diorama's scenes. It controls various LEDs and servos and responds to simple integer-based commands.
3.  **Secondary LED Controller (`22_SecMega.ino`)**: An Arduino Mega that acts as a slave to the Main Scene Controller, responsible for animating the large front-facing logo. It does not accept direct serial commands.

--- 

## Controller Details

### 1. Robotic Arm Controller (`26_AllMotor_JointMode.ino`)

This controller is responsible for all movements of the robotic arm holding the tablet.

-   **Device**: OpenCR board
-   **Motors**: 3 x Dynamixel Servos (ID10: Primary, ID11: Secondary, ID21: Tablet Rotate)
-   **Communication**: Serial
-   **Baud Rate**: `57600`

#### Serial Commands

The controller accepts string-based commands terminated by a newline character (`\n`).

| Command String                                                                                               |
| :----------------------------------------------------------------------------------------------------------- |
| `1`                                                                                                          |
| `2`                                                                                                          |
| `3 <v1> <v2> <v3> <a1> <a2> <a3> <p1> <p2> <p3>`                                                               |
| `4 <p1> <p2> <p3>`                                                                                           |

*   `<v>`: Velocity (0-1023)
*   `<a>`: Acceleration (0-254)
*   `<p>`: Position (0-4095)

#### Serial Feedback

The controller continuously streams the current position of all three motors back over the serial port at a 10ms interval.

-   **Format**: `angle:<pos1>|<pos2>|<pos3>\n`
-   **Example**: `angle:2048|1950|3960`

--- 

### 2. Main Scene Controller (`29_MainMega.ino`)

This is the master controller for the diorama's narrative elements, including lighting and small mechanical movements.

-   **Device**: Arduino Mega or Teensy
-   **Components**:
    -   Multiple LED strips via `FastLED` (Artwork, Google Map, Logo Back, G-tail)
    -   5 Servos via `Pololu Maestro` (Home Sign, Aum Cry, Market Aunty, Phone, BK Market)
    -   Distance Sensor for person detection
-   **Communication**: Serial
-   **Baud Rate**: `9600`

#### Serial Commands

The controller uses a state machine and accepts simple integer commands followed by a newline.

| Command (int) |
| :------------ |
| `1`           |
| `2`           |
| `3`           |
| `4`           |
| `5`           |
| `6`           |
| `7`           |
| `8`           |
| `9`           |
| `10`          |
| `11`          |
| `12`          |
| `13`          |
| `14`          |
| `15`          |

--- 

### 3. Secondary LED Controller (`22_SecMega.ino`)

This controller manages the large, 1080-pixel front logo animation. It is a slave device and does not accept serial commands.

-   **Device**: Arduino Mega
-   **Components**: 1080-pixel WS2812B LED strip (`FastLED`)
-   **Communication**: Digital Pins (Slave to Main Scene Controller)

#### Trigger Mechanism

The animation is triggered by state changes on two digital pins connected to the Main Scene Controller:

-   **`ledfront_datapinIn_Show` (Pin 3)**: When this pin goes HIGH, the controller begins a multi-color fill animation for the front logo.
-   **`ledfront_datapinIn_Hide` (Pin 4)**: When this pin goes HIGH, the controller immediately turns off all front logo LEDs and resets its animation state.