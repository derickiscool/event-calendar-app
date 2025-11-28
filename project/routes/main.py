from flask import Blueprint, render_template, jsonify
from project.db import get_mongo_status, get_mariadb_status

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def index():
    """Render the main index page with dark theme."""
    return render_template('index.html')

@main_bp.route("/login")
def login():
    """Render the login page."""
    return render_template('login.html')

@main_bp.route("/register")
def register():
    """Render the register page."""
    return render_template('register.html')

@main_bp.route("/profile")
def profile():
    """Render the profile page."""
    return render_template('profile.html')

@main_bp.route("/event-new")
def event_new():
    """Render the create event page."""
    return render_template('event-new.html')

@main_bp.route("/event-edit")
def event_edit():
    """Render the edit event page."""
    return render_template('event-edit.html')

@main_bp.route("/manage-events")
def manage_events():
    """Render the manage events page."""
    return render_template('manage-events.html')

@main_bp.route("/event-detail")
def event_detail():
    """Render the event detail page."""
    return render_template('event-detail.html')

@main_bp.route("/bookmarks")
def bookmarks():
    """Render the bookmarks page."""
    return render_template('bookmarks.html')

