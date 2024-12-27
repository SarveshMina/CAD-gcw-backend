# app/database.py

import os
from azure.cosmos import CosmosClient
from dotenv import load_dotenv

# Load environment variables from .env (if needed locally)
load_dotenv()

COSMOS_CONNECTION_STRING = os.getenv("COSMOS_CONNECTION_STRING")
DATABASE_NAME = "CalendarDB"
USERS_CONTAINER = "Users"

# Initialize Cosmos DB client
client = CosmosClient.from_connection_string(COSMOS_CONNECTION_STRING)
database = client.get_database_client(DATABASE_NAME)
user_container = database.get_container_client(USERS_CONTAINER)
