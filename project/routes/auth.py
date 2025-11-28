# project/routes/auth.py
from flask import Blueprint, request, jsonify, session
from werkzeug.security import check_password_hash
from project.models import db, User, UserProfile
import re

auth_bp = Blueprint("auth", __name__)

def validate_username(username):
    """Validate username format and length."""
    if not username or not isinstance(username, str):
        return "Username is required"
    username = username.strip()
    if len(username) < 3:
        return "Username must be at least 3 characters"
    if len(username) > 50:
        return "Username must be less than 50 characters"
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return "Username can only contain letters, numbers, and underscores"
    return None

def validate_email(email):
    """Validate email format and length."""
    if not email or not isinstance(email, str):
        return "Email is required"
    email = email.strip()
    if len(email) > 255:
        return "Email must be less than 255 characters"
    # Basic email regex
    if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
        return "Please enter a valid email address"
    return None

def validate_password(password):
    """Validate password strength."""
    if not password or not isinstance(password, str):
        return "Password is required"
    if len(password) < 8:
        return "Password must be at least 8 characters"
    if len(password) > 128:
        return "Password must be less than 128 characters"
    if not re.search(r'[a-zA-Z]', password):
        return "Password must contain at least one letter"
    if not re.search(r'[0-9]', password):
        return "Password must contain at least one number"
    return None

def validate_name(name, field_name):
    """Validate optional name fields."""
    if not name:
        return None  # Optional field
    if not isinstance(name, str):
        return f"{field_name} must be text"
    name = name.strip()
    if len(name) > 100:
        return f"{field_name} must be less than 100 characters"
    if not re.match(r'^[a-zA-Z\s\'-]+$', name):
        return f"{field_name} can only contain letters, spaces, hyphens, and apostrophes"
    return None

@auth_bp.route("/auth/register", methods=["POST"])
def register():
    """Register a new user account with validation."""
    data = request.get_json()
    
    # Extract and sanitize inputs
    username = data.get("username", "").strip() if isinstance(data.get("username"), str) else ""
    email = data.get("email", "").strip().lower() if isinstance(data.get("email"), str) else ""
    password = data.get("password_hash", "")
    fname = data.get("fname", "").strip() if isinstance(data.get("fname"), str) else ""
    lname = data.get("lname", "").strip() if isinstance(data.get("lname"), str) else ""
    
    # Validate all fields
    username_error = validate_username(username)
    if username_error:
        return jsonify({"error": username_error}), 400
    
    email_error = validate_email(email)
    if email_error:
        return jsonify({"error": email_error}), 400
    
    password_error = validate_password(password)
    if password_error:
        return jsonify({"error": password_error}), 400
    
    fname_error = validate_name(fname, "First name")
    if fname_error:
        return jsonify({"error": fname_error}), 400
    
    lname_error = validate_name(lname, "Last name")
    if lname_error:
        return jsonify({"error": lname_error}), 400
    
    # Check if user already exists (case-insensitive for email)
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already taken"}), 400
    
    # Create new user with validated data
    new_user = User(
        username=username,
        email=email
    )
    new_user.set_password(password)  # Use the model's set_password method
    
    db.session.add(new_user)
    db.session.commit()
    
    # Create default profile with validated names
    profile = UserProfile(
        user_id=new_user.id,
        fname=fname,
        lname=lname
    )
    db.session.add(profile)
    db.session.commit()
    
    # Auto-login after registration
    session["user_id"] = new_user.id
    session["username"] = new_user.username
    
    return jsonify({
        "message": "Registration successful",
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email
        }
    }), 201


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    """Authenticate user and create session."""
    data = request.get_json()
    
    if not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email and password are required"}), 400
    
    # Find user by email
    user = User.query.filter_by(email=data["email"]).first()
    
    if not user or not user.check_password(data["password"]):
        return jsonify({"error": "Invalid email or password"}), 401
    
    # Create session
    session["user_id"] = user.id
    session["username"] = user.username
    if user.profile:
        session["avatar_url"] = user.profile.avatar_url
    else:
        session["avatar_url"] = None
    
    return jsonify({
        "message": "Login successful",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }), 200


@auth_bp.route("/auth/logout", methods=["POST"])
def logout():
    """Clear user session."""
    session.clear()
    return jsonify({"message": "Logout successful"}), 200


@auth_bp.route("/auth/status", methods=["GET"])
def auth_status():
    """Check if user is authenticated."""
    if "user_id" in session:
        user = User.query.get(session["user_id"])
        if user:
            return jsonify({
                "authenticated": True,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email
                }
            }), 200
    
    return jsonify({"authenticated": False}), 200
