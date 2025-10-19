# project/db.py

import os
import pymongo
import mysql.connector
from mysql.connector import Error

def get_mongo_client():
    """Establishes a connection to MongoDB and returns the client object."""
    try:
        mongo_uri = os.getenv("MONGO_URI")
        client = pymongo.MongoClient(mongo_uri)
        client.admin.command('ping')
        print("MongoDB connection successful.")
        return client
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None


def get_mongo_status():
    """Pings the MongoDB Atlas cluster to check the connection."""
    client = get_mongo_client()
    if client:
        client.close()
        return "connected"
    return "disconnected"


def get_mariadb_connection():
    """Establishes and returns a connection to the MariaDB database."""
    try:
        db_port_str = os.getenv("MARIADB_PORT")
        ssl_ca_path = "ca.pem"

        connection = mysql.connector.connect(
            host=os.getenv("MARIADB_HOST"),
            user=os.getenv("MARIADB_USER"),
            password=os.getenv("MARIADB_PASSWORD"),
            database=os.getenv("MARIADB_DATABASE"),
            port=int(db_port_str),
            ssl_ca=ssl_ca_path
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"MariaDB connection failed: {e}")
        return None
    return None

def get_mariadb_status():
    """Checks the connection to the MariaDB database."""
    connection = get_mariadb_connection()
    if connection and connection.is_connected():
        connection.close()
        return "connected"
    return "disconnected"