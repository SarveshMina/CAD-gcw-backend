# tests/test_register.py

import unittest
import requests
import os
import logging
from dotenv import load_dotenv

# Load env
load_dotenv()

# Configure logging (for the test itself)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# e.g., http://localhost:7071/api/
AZURE_FUNC_URL = os.getenv("AZURE_FUNC_URL", "http://localhost:7071/api/")

class TestRegisterUser(unittest.TestCase):

    def setUp(self):
        """Setup before each test"""
        self.base_url = f"{AZURE_FUNC_URL}register"
        logging.info("Testing register endpoint: %s", self.base_url)

    def log_request_response(self, payload, response):
        """Helper to log request payload and response details"""
        logging.info("Request Payload: %s", payload)
        logging.info("Response Code: %d", response.status_code)
        logging.info("Response Text: %s", response.text)

    # 1) Successful registration with a unique username
    def test_01_register_success(self):
        """Test successful user registration"""
        payload = {
            "username": "uniqueUser123",
            "password": "ValidPass1",
            "email": "test@example.com"
        }
        response = requests.post(self.base_url, json=payload)
        self.log_request_response(payload, response)
        self.assertEqual(response.status_code, 201)
        self.assertIn("User registered successfully", response.text)

    # 2) Register the same username again => should fail with 400
    def test_02_register_duplicate_username(self):
        """Test duplicate username registration"""
        payload = {
            "username": "uniqueUser123",  # same as test_01
            "password": "ValidPass1",
            "email": "test@example.com"
        }
        response = requests.post(self.base_url, json=payload)
        self.log_request_response(payload, response)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Username already exists", response.text)

    # 3) Username too short
    def test_03_register_short_username(self):
        """Test username too short"""
        payload = {
            "username": "usr",
            "password": "Password123",
            "email": "test@example.com"
        }
        response = requests.post(self.base_url, json=payload)
        self.log_request_response(payload, response)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Username must be between 5 and 15 characters", response.text)

    # 4) Username too long
    def test_04_register_long_username(self):
        """Test username too long"""
        payload = {
            "username": "thisisaverylongusername",
            "password": "Password123",
            "email": "test@example.com"
        }
        response = requests.post(self.base_url, json=payload)
        self.log_request_response(payload, response)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Username must be between 5 and 15 characters", response.text)

    # 5) Password too short
    def test_05_register_short_password(self):
        """Test password too short"""
        payload = {
            "username": "validUser",
            "password": "short",
            "email": "test@example.com"
        }
        response = requests.post(self.base_url, json=payload)
        self.log_request_response(payload, response)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Password must be between 8 and 15 characters", response.text)

    # 6) Password too long
    def test_06_register_long_password(self):
        """Test password too long"""
        payload = {
            "username": "validUser2",
            "password": "thispasswordiswaytoolong123",
            "email": "test@example.com"
        }
        response = requests.post(self.base_url, json=payload)
        self.log_request_response(payload, response)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Password must be between 8 and 15 characters", response.text)

if __name__ == '__main__':
    unittest.main()
