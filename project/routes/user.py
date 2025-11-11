# routes/user.py
from flask import Blueprint, request, jsonify, session
from project.models import db, User, UserProfile, Event
from werkzeug.security import generate_password_hash
import os

user_bp = Blueprint("user", __name__)

# Commented out because these routes are not currently used.
# using user_profile.py and auth.py routes instead for user management.

# # GET all users
# @user_bp.route("/users", methods=["GET"])
# def get_users():
#     users = User.query.all()
#     return jsonify([u.as_dict() for u in users])

# # GET single user
# @user_bp.route("/users/<int:user_id>", methods=["GET"])
# def get_user(user_id):
#     user = User.query.get(user_id)
#     if not user:
#         return jsonify({"error": "User not found"}), 404
#     return jsonify(user.as_dict())

# # POST create user + profile
# @user_bp.route("/users", methods=["POST"])
# def create_user():
#     data = request.get_json()

#     # Check uniqueness
#     if User.query.filter_by(email=data.get("email")).first():
#         return jsonify({"error": "Email already exists"}), 400
#     if User.query.filter_by(username=data.get("username")).first():
#         return jsonify({"error": "Username already exists"}), 400

#     # Hash password
#     password_hashed = generate_password_hash(data.get("password_hash"))

#     new_user = User(
#         username=data.get("username"),
#         email=data.get("email"),
#         password_hash=password_hashed
#     )
#     db.session.add(new_user)
#     db.session.commit()  # generate user id

#     # default profile
#     profile = UserProfile(
#         user_id=new_user.id,
#         fname=data.get("fname", ""),
#         lname=data.get("lname", "")
#     )
#     db.session.add(profile)
#     db.session.commit()

#     return jsonify(new_user.as_dict()), 201

# # PUT update user
# @user_bp.route("/users/<int:user_id>", methods=["PUT"])
# def update_user(user_id):
#     user = User.query.get(user_id)
#     if not user:
#         return jsonify({"error": "User not found"}), 404
#     data = request.get_json()

#     user.username = data.get("username", user.username)
#     user.email = data.get("email", user.email)
#     if "password_hash" in data:
#         user.password_hash = generate_password_hash(data["password_hash"])

#     db.session.commit()
#     return jsonify(user.as_dict())

# # DELETE user (cascades handled automatically)
# @user_bp.route("/users/<int:user_id>", methods=["DELETE"])
# def delete_user(user_id):
#     user = User.query.get(user_id)
#     if not user:
#         return jsonify({"error": "User not found"}), 404

#     db.session.delete(user)
#     db.session.commit()
#     return jsonify({"message": "User and all related data deleted"})

# DELETE current user account with file cleanup
@user_bp.route("/delete-account", methods=["DELETE"])
def delete_account():
    """Delete the current user's account and all associated data."""
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Not authenticated"}), 401
    
    user_id = session['user_id']
    
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"status": "error", "message": "User not found"}), 404
        
        # Step 1: Delete all event images for user's events
        user_events = Event.query.filter_by(user_id=user_id).all()
        for event in user_events:
            if event.image_url:
                delete_event_image(event.image_url)
        
        # Step 2: Delete user's avatar
        if user.profile and user.profile.avatar_url:
            delete_user_avatar(user_id)
        
        # Step 3: Delete user (cascades will handle all related records)
        db.session.delete(user)
        db.session.commit()
        
        # Step 4: Clear session
        session.clear()
        
        return jsonify({
            "status": "success",
            "message": "Account deleted successfully"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": f"Failed to delete account: {str(e)}"
        }), 500

def delete_event_image(image_url):
    """Delete event image file from disk."""
    try:
        if not image_url or image_url.startswith('http'):
            return
        
        # Extract filename from URL path
        filename = image_url.split('/')[-1]
        filepath = os.path.join('project', 'static', 'assets', 'images', 'events', filename)
        
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"Deleted event image: {filepath}")
    except Exception as e:
        print(f"Error deleting event image {image_url}: {str(e)}")

def delete_user_avatar(user_id):
    """Delete user avatar file from disk."""
    try:
        avatar_dir = os.path.join('project', 'static', 'assets', 'images', 'avatars')
        
        # Check if directory exists
        if not os.path.exists(avatar_dir):
            return
        
        # Find and delete avatar file with any extension
        for filename in os.listdir(avatar_dir):
            if filename.startswith(f'user_{user_id}.'):
                filepath = os.path.join(avatar_dir, filename)
                os.remove(filepath)
                print(f"Deleted avatar: {filepath}")
                break
    except Exception as e:
        print(f"Error deleting avatar for user {user_id}: {str(e)}")
