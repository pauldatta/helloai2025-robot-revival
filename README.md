# Aum's Journey: An Interactive Robotic Art Installation

This project is the control plane for "Aum's Journey," an interactive robotic art installation that tells the true story of Aum, a man who found his way home after being lost for 15 years, using Google's voice search. The system uses a Python-based application to interpret narrative scenes directed by the Gemini API and sends serial commands to an Arduino controller to manipulate the physical diorama.

## Core Components

- **Python Control Plane:** The central application that orchestrates the story and sends commands to the hardware.
- **Gemini API:** Serves as the "director," deciding which story scene to present next based on user interaction.
- **Arduino Controller:** The hardware brain that receives serial commands from the Python script to manage the diorama's physical components, including a robotic arm, LEDs, and servos.

## The Story: Aum's Journey Home

The story is divided into five key parts, each corresponding to a scene on the diorama:

- **Part 1: Lost in the City (S3 & S2):** Aum runs away from his childhood home and spends 15 years lost and alone on the streets of Bangkok.
- **Part 2: A Glimmer of Hope (S11a & S12a):** Aum discovers Google voice search in an internet cafe, giving him a new sense of hope.
- **Part 3: The Search (S13):** Using voice search and Google Earth, Aum pieces together fragmented memories of his childhood neighborhood.
- **Part 4: The Path Home (S4a):** Aum identifies his home and contacts The Mirror Foundation to help him return.
- **Part 5: The Reunion:** Aum is emotionally reunited with his father.

## Project Structure

- **`AUM_DIRECTOR.md`**: Contains the persona and instructions for the AI director, defining the logic for both sequential and exploratory story modes.
- **`AUM_STORY.md`**: The complete narrative of Aum's journey, serving as the source material for the AI.
- **`context/`**: This directory holds all the assets for the story, including video clips and images.
- **`main.py`**: The main entry point for the Python application.
- **`*.ino`**: Arduino sketches for the microcontrollers can be found in the `context/OriginalSoftware/` subdirectories.
