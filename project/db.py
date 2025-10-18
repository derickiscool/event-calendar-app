# project/db.py

import os
import pymongo
import mysql.connector
from mysql.connector import Error

def get_mongo_status():
    """Pings the MongoDB Atlas cluster to check the connection."""
    try:
        mongo_uri = os.getenv("MONGO_URI")
        client = pymongo.MongoClient(mongo_uri)
        client.admin.command('ping')
        return "connected"
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        return "disconnected"

def get_mariadb_status():
    """Connects to the Aiven (MySQL/MariaDB) database to check the connection."""
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
            connection.close()
            return "connected"
        else:
            return "disconnected"
    except Error as e:
        print(f"MariaDB connection failed: {e}")
        return "disconnected"