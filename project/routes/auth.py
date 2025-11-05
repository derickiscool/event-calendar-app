# project/routes/auth.py
from flask import Blueprint, request, jsonify, session
from werkzeug.security import check_password_hash
from project.models import db, User, UserProfile

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/auth/register", methods=["POST"])
def register():
    """Register a new user account."""
    data = request.get_json()
    
    # Validation
    if not data.get("username") or not data.get("email") or not data.get("password_hash"):
        return jsonify({"error": "Username, email, and password are required"}), 400
    
    # Check if user already exists
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already registered"}), 400
    
    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "Username already taken"}), 400
    
    # Create new user
    new_user = User(
        username=data["username"],
        email=data["email"]
    )
    new_user.set_password(data["password_hash"])  # Use the model's set_password method
    
    db.session.add(new_user)
    db.session.commit()
    
    # Create default profile
    profile = UserProfile(
        user_id=new_user.id,
        fname=data.get("fname", ""),
        lname=data.get("lname", "")
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
