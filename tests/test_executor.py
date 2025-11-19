import unittest
from src.agent.executor.executor import execute_command

class TestExecutor(unittest.TestCase):

    def test_execute_command_valid(self):
        command_json = {
            "action": "list_files",
            "path": "C:\\Users\\Public"
        }
        result = execute_command(command_json)
        self.assertIn("files", result)
        self.assertIsInstance(result["files"], list)

    def test_execute_command_invalid_action(self):
        command_json = {
            "action": "invalid_action",
            "path": "C:\\Users\\Public"
        }
        with self.assertRaises(ValueError):
            execute_command(command_json)

    def test_execute_command_missing_action(self):
        command_json = {
            "path": "C:\\Users\\Public"
        }
        with self.assertRaises(KeyError):
            execute_command(command_json)

    def test_execute_command_invalid_path(self):
        command_json = {
            "action": "list_files",
            "path": "C:\\InvalidPath"
        }
        result = execute_command(command_json)
        self.assertEqual(result["error"], "Invalid path specified.")

if __name__ == '__main__':
    unittest.main()