import asyncio
import logging
import sys
from .hardware_controller import HardwareManager

# from .live_director import SCENE_ACTIONS

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format="[TEST] %(asctime)s - %(message)s",
    datefmt="%H:%M:%S",
)

SCENE_ACTIONS = {
    # --- Main Story Scenes ---
    "AUMS_HOME": [
        # Corresponds to S3: Story of Aum | Aum's Home and S4: Aum's Home - zoom in
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 2}},
        {"action": "move_robotic_arm", "params": {"p1": 2468, "p2": 68, "p3": 2980}},
        {
            "action": "play_video",
            "params": {"video_file": "part1_lost_in_the_city.mp4"},
        },
    ],
    "AUM_CRYING": [
        # Corresponds to S5: Aum Crying
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 4}},
        {"action": "move_robotic_arm", "params": {"p1": 2457, "p2": 79, "p3": 3447}},
    ],
    "BUS_SOCCER": [
        # Corresponds to S6a: Bus and S6b: Bus - Soccer
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 5}},
        {
            "action": "move_robotic_arm",
            "params": {"p1": 2457, "p2": 79, "p3": 3447},
        },  # Same as AUM_CRYING
    ],
    "MARKET": [
        # Corresponds to S9: Market
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 3}},
        {
            "action": "move_robotic_arm",
            "params": {"p1": 2457, "p2": 68, "p3": 3436},
        },  # Same as ROAD_TO_HUA_HIN
        {"action": "play_video", "params": {"video_file": "part2_glimmer_of_hope.mp4"}},
    ],
    "AUM_GROWS_UP": [
        # Corresponds to S10: Aum Grew Up
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 7}},
        {
            "action": "move_robotic_arm",
            "params": {"p1": 2457, "p2": 68, "p3": 3436},
        },  # Same as ROAD_TO_HUA_HIN
    ],
    "ROAD_TO_HUA_HIN": [
        # Corresponds to S11a: Aum to Hua Hin and S11b: Aum reach Hua Hin
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 6}},
        {"action": "move_robotic_arm", "params": {"p1": 2457, "p2": 68, "p3": 3436}},
    ],
    "INTERNET_CAFE": [
        # Corresponds to S12a: Cafe and S12b: Cafe
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 8}},
        {"action": "move_robotic_arm", "params": {"p1": 2446, "p2": 68, "p3": 3436}},
        {"action": "play_video", "params": {"video_file": "part3_the_search.mp4"}},
    ],
    "GOOGLE_MAP": [
        # Corresponds to S13: Google Map
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 10}},
        {"action": "move_robotic_arm", "params": {"p1": 4000, "p2": 1500, "p3": 3800}},
        {"action": "play_video", "params": {"video_file": "part4_the_path_home.mp4"}},
    ],
    "ROAD_TO_BANGKOK": [
        # Corresponds to S14a: Aum back to BK and S14b: Aum back to BK
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 11}},
        {"action": "move_robotic_arm", "params": {"p1": 3800, "p2": 1300, "p3": 3700}},
        {"action": "play_video", "params": {"video_file": "part5_the_reunion.mp4"}},
    ],
    # --- System & Utility Scenes ---
    "IDLE": [
        # Corresponds to S0: Rest
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 0}},
        {
            "action": "move_robotic_arm",
            "params": {"p1": 2048, "p2": 0, "p3": 3960},
        },  # Default position
    ],
    "FINDING_BOY": [
        # Corresponds to S2: Finding Boy (likely an intro/attract scene)
        {"action": "trigger_diorama_scene", "params": {"scene_command_id": 1}},
        {
            "action": "move_robotic_arm",
            "params": {"p1": 2048, "p2": 0, "p3": 3960},
        },  # Default position
    ],
    # --- Guided Mode ---
    # References the main story scenes
    "GUIDED_MODE_AUMS_HOME": "AUMS_HOME",
    "GUIDED_MODE_BUS_SOCCER": "BUS_SOCCER",
    "GUIDED_MODE_AUM_CRYING": "AUM_CRYING",
    "GUIDED_MODE_MARKET": "MARKET",
    "GUIDED_MODE_AUM_GROWS_UP": "AUM_GROWS_UP",
    "GUIDED_MODE_ROAD_TO_HUA_HIN": "ROAD_TO_HUA_HIN",
    "GUIDED_MODE_INTERNET_CAFE": "INTERNET_CAFE",
    "GUIDED_MODE_GOOGLE_MAP": "GOOGLE_MAP",
    "GUIDED_MODE_ROAD_TO_BANGKOK": "ROAD_TO_BANGKOK",
}


async def execute_scene(scene_name: str):
    """
    Executes all actions for a given scene using the HardwareManager.
    """
    logging.info(f"Initializing HardwareManager for scene: {scene_name}...")
    hm = HardwareManager()

    logging.info("Connecting to all hardware controllers...")
    await hm.connect_all()

    # Get actions for the specified scene
    actions_to_run = SCENE_ACTIONS.get(scene_name)

    # Handle scene aliases (e.g., for guided mode)
    if isinstance(actions_to_run, str):
        actions_to_run = SCENE_ACTIONS.get(actions_to_run)

    if not actions_to_run:
        logging.error(
            f"ERROR: No actions defined for scene '{scene_name}' or scene does not exist."
        )
        return

    tasks = []
    for item in actions_to_run:
        action_name = item.get("action")
        params = item.get("params", {})
        function_to_call = getattr(hm, action_name, None)

        if callable(function_to_call):
            logging.info(f"---> Queuing action: {action_name}({params})")
            tasks.append(function_to_call(**params))
        else:
            logging.error(
                f"ERROR: Unknown action '{action_name}' in scene '{scene_name}'"
            )

    if tasks:
        logging.info(f"Executing {len(tasks)} action(s) for scene '{scene_name}'...")
        await asyncio.gather(*tasks)

    logging.info("Closing all serial ports...")
    await hm.close_all_ports()
    logging.info("Test complete.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_scene.py <scene_name>")
        print("\nAvailable scenes:")
        # Filter out aliases and only show primary scenes
        for scene in sorted(
            [s for s in SCENE_ACTIONS if isinstance(SCENE_ACTIONS[s], list)]
        ):
            print(f"- {scene}")
    else:
        scene_to_test = sys.argv[1].strip()
        asyncio.run(execute_scene(scene_to_test))
