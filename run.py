# run.py
from project import create_app  # Import the app factory function

app = create_app()  # Call the factory function to create the app instance

if __name__ == "__main__":
    app.run(debug=True)  # Run the app
