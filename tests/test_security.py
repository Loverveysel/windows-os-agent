import unittest
from src.agent.security.policy import is_path_allowed, is_file_type_allowed

class TestSecurity(unittest.TestCase):

    def test_is_path_allowed(self):
        allowed_paths = ['/allowed/path', '/another/allowed/path']
        self.assertTrue(is_path_allowed('/allowed/path', allowed_paths))
        self.assertFalse(is_path_allowed('/disallowed/path', allowed_paths))

    def test_is_file_type_allowed(self):
        allowed_file_types = ['.txt', '.json']
        self.assertTrue(is_file_type_allowed('file.txt', allowed_file_types))
        self.assertFalse(is_file_type_allowed('file.exe', allowed_file_types))

if __name__ == '__main__':
    unittest.main()