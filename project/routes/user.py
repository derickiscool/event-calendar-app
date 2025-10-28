# routes/user.py
from flask import Blueprint, request, jsonify
from project.models import db, User, UserProfile
from werkzeug.security import generate_password_hash

user_bp = Blueprint("user", __name__)

# GET all users
@user_bp.route("/users", methods=["GET"])
def get_users():
    users = User.query.all()
    return jsonify([u.as_dict() for u in users])

# GET single user
@user_bp.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user.as_dict())

# POST create user + profile
@user_bp.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()

    # Check uniqueness
    if User.query.filter_by(email=data.get("email")).first():
        return jsonify({"error": "Email already exists"}), 400
    if User.query.filter_by(username=data.get("username")).first():
        return jsonify({"error": "Username already exists"}), 400

    # Hash password
    password_hashed = generate_password_hash(data.get("password_hash"))

    new_user = User(
        username=data.get("username"),
        email=data.get("email"),
        password_hash=password_hashed
    )
    db.session.add(new_user)
    db.session.commit()  # generate user id

    # default profile
    profile = UserProfile(
        user_id=new_user.id,
        fname=data.get("fname", ""),
        lname=data.get("lname", "")
    )
    db.session.add(profile)
    db.session.commit()

    return jsonify(new_user.as_dict()), 201

# PUT update user
@user_bp.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    data = request.get_json()

    user.username = data.get("username", user.username)
    user.email = data.get("email", user.email)
    if "password_hash" in data:
        user.password_hash = generate_password_hash(data["password_hash"])

    db.session.commit()
    return jsonify(user.as_dict())

# DELETE user (cascades handled automatically)
@user_bp.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User and all related data deleted"})
