import unittest
import requests
import os
import logging
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

AZURE_FUNC_URL = os.getenv("AZURE_FUNC_URL", "http://localhost:7071/api/")

class TestCalendar(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Runs once before all tests in this class.
        We create a user and store the homeCalendarId for event tests.
        """
        cls.register_url = f"{AZURE_FUNC_URL}register"
        cls.calendar_id = None
        cls.test_user = {
            "username": "calendarTest2",
            "password": "CalendarPass1",
            "email": "calendar@example.com"
        }
        
        logging.info("Ensuring test user is created for calendar tests...")
        
        # Attempt to register user
        response = requests.post(cls.register_url, json=cls.test_user)
        logging.info("Register response: %d %s", response.status_code, response.text)
        
        if response.status_code == 201:
            # Successful creation
            json_body = response.json()
            cls.calendar_id = json_body.get("homeCalendarId")
            logging.info("Created user. Home calendar = %s", cls.calendar_id)
        elif response.status_code == 400 and "Username already exists" in response.text:
            logging.info("User already exists, proceeding to fetch their home calendar.")
            # If you need to fetch an existing homeCalendarId, do so here.
        else:
            logging.warning(
                "Unexpected response creating test user: %d %s",
                response.status_code,
                response.text
            )

    def setUp(self):
        """
        Runs before each individual test. We build the event endpoints using self.calendar_id.
        """
        self.event_base_url = None
        self.events_list_url = None

        if self.calendar_id:
            self.event_base_url = f"{AZURE_FUNC_URL}calendar/{self.calendar_id}/event"
            self.events_list_url = f"{AZURE_FUNC_URL}calendar/{self.calendar_id}/events"
        
        logging.info("Testing event endpoint: %s", self.event_base_url)
        logging.info("Testing list endpoint: %s", self.events_list_url)

    def test_01_create_event_success(self):
        """
        Create an event in the user's home calendar.
        """
        if not self.calendar_id:
            self.skipTest("No home calendar available for testing (registration may have failed).")

        start_time = datetime.utcnow() + timedelta(days=1)
        end_time = start_time + timedelta(hours=2)

        payload = {
            "calendarId": self.calendar_id,
            "title": "Movie Booking",
            "startTime": start_time.isoformat(),
            "endTime": end_time.isoformat(),
            "locked": True,
            "description": "Going to the cinema."
        }
        response = requests.post(self.event_base_url, json=payload)
        self.log_request_response(payload, response)

        self.assertEqual(response.status_code, 201)
        self.assertIn("Event created successfully", response.text)

    def test_02_list_events_success(self):
        """
        List events in the user's home calendar to confirm the created event is present.
        """
        if not self.calendar_id:
            self.skipTest("No home calendar available for testing (registration may have failed).")
        if not self.events_list_url:
            self.skipTest("No events_list_url built in setUp().")

        response = requests.get(self.events_list_url)
        self.log_request_response(None, response)

        self.assertEqual(response.status_code, 200)
        json_body = response.json()
        self.assertIn("events", json_body)
        events_list = json_body["events"]
        self.assertTrue(len(events_list) >= 1, "Expected at least one event in the calendar")

    def test_03_create_event_missing_title(self):
        """
        Attempt to create an event without a title, but still with calendarId.
        Expect a failure from the server (because 'title' is required).
        """
        if not self.calendar_id:
            self.skipTest("No home calendar available for testing.")

        payload = {
            "calendarId": self.calendar_id,
            "startTime": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "endTime": (datetime.utcnow() + timedelta(days=1, hours=1)).isoformat(),
            "locked": True
        }
        response = requests.post(self.event_base_url, json=payload)
        self.log_request_response(payload, response)

        self.assertNotEqual(
            response.status_code, 
            201, 
            "Expected to fail due to missing title, but got success."
        )
        self.assertTrue(response.status_code in [400, 422, 500])

    def log_request_response(self, payload, response):
        """
        Helper to log request payload and response details
        """
        logging.info("Request Payload: %s", payload)
        logging.info("Response Code: %s", response.status_code)
        logging.info("Response Text: %s", response.text)


if __name__ == '__main__':
    unittest.main()
