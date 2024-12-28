import unittest
import requests
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
AZURE_FUNC_URL = os.getenv("AZURE_FUNC_URL", "http://localhost:7071/api/")

class TestGroupCalendar(unittest.TestCase):

    # Store the calendar ID at the class level
    test_group_calendar_id = None  # so all methods see it

    @classmethod
    def setUpClass(cls):
        """Runs once for the entire TestGroupCalendar suite."""
        logging.info("Setting up TestGroupCalendar suite")

        # We can set up data that might persist across all tests if needed
        # but typically we do it in the test_01 itself.

    def setUp(self):
        """Runs before each test method (a fresh instance every time)."""
        self.create_group_url = f"{AZURE_FUNC_URL}group-calendar/create"
        self.owner_id = "owner-1234"
        self.user1_id = "user-5678"
        self.user2_id = "user-9999"

    def log_request_response(self, desc, url, payload, response):
        logging.info("===== %s =====", desc)
        logging.info("Request URL: %s", url)
        logging.info("Payload: %s", payload)
        logging.info("Response Code: %d", response.status_code)
        logging.info("Response Text: %s", response.text)

    def test_01_create_group_calendar(self):
        """
        Create a group calendar, store the calendarId in TestGroupCalendar.test_group_calendar_id
        so that subsequent tests can access it.
        """
        payload = {
            "ownerId": self.owner_id,
            "name": "CAD Project Group",
            "members": [self.user1_id]
        }
        response = requests.post(self.create_group_url, json=payload)
        self.log_request_response("Create Group", self.create_group_url, payload, response)

        self.assertEqual(response.status_code, 201)
        resp_data = response.json()
        # Store ID at the class level
        TestGroupCalendar.test_group_calendar_id = resp_data["calendarId"]

        self.assertIn("Group calendar created successfully", resp_data["message"])

    def test_02_add_user_to_group(self):
        """We trust test_01 ran first and set the class-level test_group_calendar_id."""
        if not TestGroupCalendar.test_group_calendar_id:
            self.fail("No group calendar from previous tests.")

        url = f"{AZURE_FUNC_URL}group-calendar/{TestGroupCalendar.test_group_calendar_id}/add-user"
        payload = {
            "adminId": self.owner_id,
            "userId":  self.user2_id
        }
        response = requests.post(url, json=payload)
        self.log_request_response("Add User to Group", url, payload, response)

        self.assertEqual(response.status_code, 200)
        self.assertIn("User added successfully", response.text)

    def test_03_add_existing_user(self):
        """Try adding the same user again."""
        if not TestGroupCalendar.test_group_calendar_id:
            self.fail("No group calendar from previous tests.")

        url = f"{AZURE_FUNC_URL}group-calendar/{TestGroupCalendar.test_group_calendar_id}/add-user"
        payload = {
            "adminId": self.owner_id,
            "userId":  self.user2_id
        }
        response = requests.post(url, json=payload)
        self.log_request_response("Add Existing User", url, payload, response)

        # Could be 200 or 409, depending on your logic. We'll assume 200 with a message:
        self.assertEqual(response.status_code, 200)
        self.assertIn("User already in group calendar", response.text)

    def test_04_remove_user_from_group(self):
        """Remove the user from the group."""
        if not TestGroupCalendar.test_group_calendar_id:
            self.fail("No group calendar from previous tests.")

        url = f"{AZURE_FUNC_URL}group-calendar/{TestGroupCalendar.test_group_calendar_id}/remove-user"
        payload = {
            "adminId": self.owner_id,
            "userId":  self.user2_id
        }
        response = requests.post(url, json=payload)
        self.log_request_response("Remove User from Group", url, payload, response)

        self.assertEqual(response.status_code, 200)
        self.assertIn("User removed successfully", response.text)

    def test_05_remove_non_member(self):
        """Try removing a user who isn't in the group anymore."""
        if not TestGroupCalendar.test_group_calendar_id:
            self.fail("No group calendar from previous tests.")

        url = f"{AZURE_FUNC_URL}group-calendar/{TestGroupCalendar.test_group_calendar_id}/remove-user"
        payload = {
            "adminId": self.owner_id,
            "userId":  self.user2_id
        }
        response = requests.post(url, json=payload)
        self.log_request_response("Remove Non-Member", url, payload, response)

        self.assertEqual(response.status_code, 200)
        self.assertIn("User not in group calendar", response.text)

    def test_06_add_user_not_admin(self):
        """Try adding a user with a 'fake' admin who is not the real owner."""
        if not TestGroupCalendar.test_group_calendar_id:
            self.fail("No group calendar from previous tests.")

        url = f"{AZURE_FUNC_URL}group-calendar/{TestGroupCalendar.test_group_calendar_id}/add-user"
        payload = {
            "adminId": "fakeAdmin",
            "userId":  "someUser"
        }
        response = requests.post(url, json=payload)
        self.log_request_response("Add User Not Admin", url, payload, response)

        self.assertEqual(response.status_code, 403)
        self.assertIn("Only the calendar owner can add members", response.text)

if __name__ == '__main__':
    unittest.main()
