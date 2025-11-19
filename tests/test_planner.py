import unittest
from src.agent.planner.planner import create_plan

class TestPlanner(unittest.TestCase):

    def test_create_plan_valid_input(self):
        user_request = "Create a backup of the documents folder"
        expected_output = {
            "action": "backup",
            "target": "documents"
        }
        result = create_plan(user_request)
        self.assertEqual(result, expected_output)

    def test_create_plan_invalid_input(self):
        user_request = ""
        expected_output = {}
        result = create_plan(user_request)
        self.assertEqual(result, expected_output)

    def test_create_plan_edge_case(self):
        user_request = "Delete all files in the downloads folder"
        expected_output = {
            "action": "delete",
            "target": "downloads"
        }
        result = create_plan(user_request)
        self.assertEqual(result, expected_output)

if __name__ == '__main__':
    unittest.main()