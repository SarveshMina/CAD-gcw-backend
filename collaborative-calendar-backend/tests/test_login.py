import unittest
import requests
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

AZURE_FUNC_URL = os.getenv("AZURE_FUNC_URL", "http://localhost:7071/api/")

class TestLoginUser(unittest.TestCase):

    def setUp(self):
        """Setup before each test"""
        self.base_url = f"{AZURE_FUNC_URL}login"
        self.register_url = f"{AZURE_FUNC_URL}register"
        logging.info("Testing login endpoint: %s", self.base_url)
        self.test_user = {
            "username": "loginTest",
            "password": "LoginPass123",
            "email": "login@example.com"
        }
        self.ensure_user_created()

    def ensure_user_created(self):
        """Ensure the test user exists before login tests"""
        response = requests.post(self.register_url, json=self.test_user)
        if response.status_code == 201:
            logging.info("Test user created for login tests.")
        elif response.status_code == 400 and "Username already exists" in response.text:
            logging.info("Test user already exists. Proceeding with login tests.")
        else:
            logging.error("Failed to set up test user: %s", response.text)

    def log_request_response(self, payload, response):
        """Helper to log request payload and response details"""
        logging.info("Request Payload: %s", payload)
        logging.info("Response Code: %d", response.status_code)
        logging.info("Response Text: %s", response.text)

    # 1) Successful login with valid credentials
    def test_01_login_success(self):
        """Test successful login with correct credentials"""
        payload = {
            "username": self.test_user["username"],
            "password": self.test_user["password"]
        }
        response = requests.post(self.base_url, json=payload)
        self.log_request_response(payload, response)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Login successful", response.text)

    # 2) Login with invalid password
    def test_02_login_invalid_password(self):
        """Test login with an invalid password"""
        payload = {
            "username": self.test_user["username"],
            "password": "WrongPassword"
        }
        response = requests.post(self.base_url, json=payload)
        self.log_request_response(payload, response)
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid credentials", response.text)

    # 3) Login with non-existent user
    def test_03_login_non_existent_user(self):
        """Test login for a non-existent user"""
        payload = {
            "username": "fakeUser123",
            "password": "DoesNotMatter123"
        }
        response = requests.post(self.base_url, json=payload)
        self.log_request_response(payload, response)
        self.assertEqual(response.status_code, 404)
        self.assertIn("User not found", response.text)

    # 4) Login with missing username or password
    def test_04_login_missing_credentials(self):
        """Test login with missing credentials (no password)"""
        payload = {
            "username": self.test_user["username"]
        }
        response = requests.post(self.base_url, json=payload)
        self.log_request_response(payload, response)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Missing credentials", response.text)

        payload = {
            "password": self.test_user["password"]
        }
        response = requests.post(self.base_url, json=payload)
        self.log_request_response(payload, response)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Missing credentials", response.text)

if __name__ == '__main__':
    unittest.main()
