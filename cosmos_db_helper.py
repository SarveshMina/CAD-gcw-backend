import os
import logging
from azure.cosmos import CosmosClient, exceptions

def get_cosmos_container():
    """Gets the Cosmos DB container client."""
    cosmos_connection_string = os.environ.get("CosmosDbConnectionString")
    database_name = os.environ.get("DatabaseName")
    container_name = os.environ.get("UsersContainer")

    if not all([cosmos_connection_string, database_name, container_name]):
        logging.error("Missing Cosmos DB environment variables.")
        return None

    try:
        client = CosmosClient.from_connection_string(cosmos_connection_string)
        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)
        return container
    except exceptions.CosmosHttpResponseError as e:
        logging.error(f"Cosmos DB connection error: {e}")
        return None

def query_users(container, username):
    """Queries the UsersContainer for a user by username."""
    if container is None:
        return None
    query = "SELECT * FROM c WHERE c.username=@username"
    params = [{"name": "@username", "value": username}]
    try:
        users = list(container.query_items(query=query, parameters=params, enable_cross_partition_query=True))
        return users
    except exceptions.CosmosHttpResponseError as e:
        logging.error(f"Cosmos DB query error: {e}")
        return None