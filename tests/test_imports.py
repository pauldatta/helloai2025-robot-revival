import unittest
import sys
import os

# Add the src directory to the Python path to allow for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestModuleImports(unittest.TestCase):
    """
    A simple test suite that attempts to import all Python modules
    from the 'src' directory to ensure there are no circular dependencies
    or broken paths after the project reorganization.
    """

    def test_import_main(self):
        """Test that src.main can be imported."""
        try:
            from src import main
            self.assertIsNotNone(main)
        except ImportError as e:
            self.fail(f"Failed to import src.main: {e}")

    def test_import_live_director(self):
        """Test that src.live_director can be imported."""
        try:
            from src import live_director
            self.assertIsNotNone(live_director)
        except ImportError as e:
            self.fail(f"Failed to import src.live_director: {e}")

    def test_import_orchestrator(self):
        """Test that src.orchestrator can be imported."""
        try:
            from src import orchestrator
            self.assertIsNotNone(orchestrator)
        except ImportError as e:
            self.fail(f"Failed to import src.orchestrator: {e}")

    def test_import_hardware_controller(self):
        """Test that src.hardware_controller can be imported."""
        try:
            from src import hardware_controller
            self.assertIsNotNone(hardware_controller)
        except ImportError as e:
            self.fail(f"Failed to import src.hardware_controller: {e}")

    def test_import_hardware_emulator(self):
        """Test that src.hardware_emulator can be imported."""
        try:
            from src import hardware_emulator
            self.assertIsNotNone(hardware_emulator)
        except ImportError as e:
            self.fail(f"Failed to import src.hardware_emulator: {e}")

if __name__ == '__main__':
    unittest.main()
