Event Calendar Web Application
A hybrid SQL + NoSQL event discovery platform.

Quick Setup Guide (using submitted zip file)
- Run: pip install -r requirements.txt
- Ensure .env is present and ready
- Run: run.py
- Open localhost (127.0.0.1) once set up



Overview

The Event Calendar App allows users to:
- Browse community events created within the platform
- Discover official events from external sources (data.gov.sg, ArtsRepublic, EventFinda)
- Bookmark events
- View arts-related statistics
- Manage personal profiles and preferences
The system integrates:
- Flask Backend
- Responsive Frontend (HTML, CSS, JS, Jinja)
- MariaDB (SQL — users, community events, tags, bookmarks)
- MongoDB (NoSQL — official events, statistics)
- Custom Python ETL Pipeline (scraping & ingestion)

Prerequisites - Ensure the following are installed:
- Python 3.9+
- pip (Python package manager)
- MariaDB Server
- MongoDB Server or MongoDB Atlas
- Git (optional but recommended)

Supported OS
- Windows 10/11
- macOS
- Ubuntu/Linux

Install Dependencies stated in requirements.txt
Flask
pymongo
mysql-connector-python
python-dotenv
requests
beautifulsoup4

Install all required packages: pip install -r requirements.txt

Environment Variables: The .env should be present in the zip folder

Running the Application
- From the project root, run: python run.py
- This will start the Flask development server: http://127.0.0.1:5000/
- Your application is now running locally.
