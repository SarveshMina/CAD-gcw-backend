import unittest
import requests
import os
import logging
from dotenv import load_dotenv

# Load environment variables (so we can get AZURE_FUNC_URL, etc.)
load_dotenv()

# Configure logging for the test
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TestGroupCalendar(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        Runs once before all tests.
        We'll store base URLs in class variables.
        """
        cls.base_url = os.getenv("AZURE_FUNC_URL", "http://localhost:7071/api/")
        logging.info("Using base URL: %s", cls.base_url)

        # We'll also store IDs as we go
        cls.user1_id = None
        cls.user2_id = None
        cls.user3_id = None
        cls.group_calendar_id = None

    def test_01_register_user1(self):
        """
        Registers user1. Expects 201 and extracts userId.
        """
        url = f"{self.base_url}register"
        payload = {
            "username": "user1",
            "password": "Password12!"
        }
        r = requests.post(url, json=payload)
        logging.info("Register user1 response: %s %s", r.status_code, r.text)
        self.assertEqual(r.status_code, 201, "Expected user1 to be created with 201")
        
        body = r.json()
        self.assertIn("userId", body, "Response should contain userId")
        # Save user1_id for future tests
        TestGroupCalendar.user1_id = body["userId"]

    def test_02_register_user2(self):
        """
        Registers user2. Expects 201 and extracts userId.
        """
        url = f"{self.base_url}register"
        payload = {
            "username": "user2",
            "password": "Password12!"
        }
        r = requests.post(url, json=payload)
        logging.info("Register user2 response: %s %s", r.status_code, r.text)
        self.assertEqual(r.status_code, 201, "Expected user2 to be created with 201")
        
        body = r.json()
        self.assertIn("userId", body, "Response should contain userId")
        # Save user2_id for future tests
        TestGroupCalendar.user2_id = body["userId"]

    def test_03_create_group_calendar(self):
        """
        Creates a group calendar with user1 as owner.
        """
        url = f"{self.base_url}group-calendar/create"
        payload = {
            "ownerId": TestGroupCalendar.user1_id,
            "name": "Group Calendar for Testing",
            "members": []  # We can add user2 later
        }
        r = requests.post(url, json=payload)
        logging.info("Create group calendar response: %s %s", r.status_code, r.text)
        self.assertEqual(r.status_code, 201, "Expected group calendar creation to return 201")
        
        body = r.json()
        self.assertIn("calendarId", body, "Response should contain calendarId")
        TestGroupCalendar.group_calendar_id = body["calendarId"]

    def test_04_add_user2_to_group(self):
        """
        Add user2 to the newly created group calendar. Must pass adminId = user1_id.
        """
        url = f"{self.base_url}group-calendar/{TestGroupCalendar.group_calendar_id}/add-user"
        payload = {
            "adminId": TestGroupCalendar.user1_id,
            "userId": TestGroupCalendar.user2_id
        }
        r = requests.post(url, json=payload)
        logging.info("Add user2 to group response: %s %s", r.status_code, r.text)
        self.assertEqual(r.status_code, 200, "Expected user2 to be added with 200")

    def test_05_remove_user2_from_group(self):
        """
        Remove user2 from the group calendar.
        """
        url = f"{self.base_url}group-calendar/{TestGroupCalendar.group_calendar_id}/remove-user"
        payload = {
            "adminId": TestGroupCalendar.user1_id,
            "userId": TestGroupCalendar.user2_id
        }
        r = requests.post(url, json=payload)
        logging.info("Remove user2 from group response: %s %s", r.status_code, r.text)
        self.assertEqual(r.status_code, 200, "Expected user2 to be removed with 200")

    def test_06_register_user3(self):
        """
        Registers user3 for demonstration. Expects 201 and extracts userId.
        """
        url = f"{self.base_url}register"
        payload = {
            "username": "user3",
            "password": "Password12!"
        }
        r = requests.post(url, json=payload)
        logging.info("Register user3 response: %s %s", r.status_code, r.text)
        self.assertEqual(r.status_code, 201, "Expected user3 to be created with 201")
        
        body = r.json()
        self.assertIn("userId", body, "Response should contain userId")
        # Save user3_id
        TestGroupCalendar.user3_id = body["userId"]

    def test_07_add_user3_to_group(self):
        """
        Finally, add user3 to the group calendar. Admin is still user1.
        """
        url = f"{self.base_url}group-calendar/{TestGroupCalendar.group_calendar_id}/add-user"
        payload = {
            "adminId": TestGroupCalendar.user1_id,
            "userId": TestGroupCalendar.user3_id
        }
        r = requests.post(url, json=payload)
        logging.info("Add user3 to group response: %s %s", r.status_code, r.text)
        self.assertEqual(r.status_code, 200, "Expected user3 to be added with 200")


if __name__ == '__main__':
    unittest.main()
