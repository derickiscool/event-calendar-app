import os
from flask import Flask, jsonify
from dotenv import load_dotenv
import pymongo
import mysql.connector
from mysql.connector import Error

# --- 1. Initialization and Configuration ---
# Load all the environment variables from the .env file
load_dotenv()

# Create the Flask application object
app = Flask(__name__)

# --- 2. Database Connection Logic ---

def get_mongo_status():
    """
    Pings the MongoDB Atlas cluster to check the connection.
    Returns a string: "connected" or "disconnected".
    """
    try:
        # Get the connection string from environment variables
        mongo_uri = os.getenv("MONGO_URI")
        
        # This is all you need to confirm a connection
        client = pymongo.MongoClient(mongo_uri)
        client.admin.command('ping') # The ping command is lightweight and fast
        
        return "connected"
    except Exception as e:
        # Print the error for debugging purposes
        print(f"MongoDB connection failed: {e}")
        return "disconnected"


def get_mariadb_status():
    """
    Connects to the Railway (MySQL/MariaDB) database to check the connection.
    Returns a string: "connected" or "disconnected".
    """
    try:
        # Get all required credentials from environment variables
        db_port_str = os.getenv("MARIADB_PORT")
        
        # Establish the connection, making sure to convert the port to an integer
        ssl_ca_path = "ca.pem"

        connection = mysql.connector.connect(
            host=os.getenv("MARIADB_HOST"),
            user=os.getenv("MARIADB_USER"),
            password=os.getenv("MARIADB_PASSWORD"),
            database=os.getenv("MARIADB_DATABASE"),
            port=int(db_port_str), 
            # --- ADD THIS SSL ARGUMENT ---
            ssl_ca=ssl_ca_path
        )
        # If the connection object is created and is_connected() is true, it's a success
        if connection.is_connected():
            connection.close() # Close the connection immediately after checking
            return "connected"
        else:
            return "disconnected"
            
    except Error as e:
        # Print the error for debugging purposes
        print(f"MariaDB connection failed: {e}")
        return "disconnected"

# --- 3. API Endpoint Definition ---

@app.route("/")
def index():
    """A simple root endpoint to show the server is running."""
    return "<h1>Event Calendar Backend is Running!</h1>"


@app.route("/health")
def health_check():
    """
    This is the health check endpoint.
    It calls the status functions for each database and returns a JSON response.
    """
    mongo_status = get_mongo_status()
    mariadb_status = get_mariadb_status()
    
    # Determine the overall HTTP status code
    if mongo_status == "connected" and mariadb_status == "connected":
        # If both are good, return a 200 OK
        status_code = 200
    else:
        # If any database is down, return a 500 Internal Server Error
        status_code = 500
        
    # Return the status of each database in a JSON format
    return jsonify({
        "mongodb_status": mongo_status,
        "mariadb_status": mariadb_status
    }), status_code

# This is the standard entry point for a Python script
if __name__ == "__main__":
    # The debug=True flag is useful for development.
    # It automatically reloads the server when you save changes.
    app.run(debug=True)