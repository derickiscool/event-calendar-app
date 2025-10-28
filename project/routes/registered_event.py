# routes/registered_event.py
from flask import Blueprint, request, jsonify
from project.models import db, RegisteredEvent
from datetime import datetime

registered_event_bp = Blueprint("registered_event", __name__)

# GET all registered events
@registered_event_bp.route("/registered-events", methods=["GET"])
def get_registered_events():
    regs = RegisteredEvent.query.all()
    return jsonify([r.as_dict() for r in regs])

# POST registered event
@registered_event_bp.route("/registered-events", methods=["POST"])
def create_registered_event():
    data = request.get_json()

    # Convert ISO 8601 string to MySQL-compatible datetime
    try:
        registered_at = datetime.fromisoformat(data["registered_at"].replace("Z", "+00:00"))
    except Exception:
        return jsonify({"error": "Invalid datetime format"}), 400

    # ===== Add this duplicate check here =====
    existing = RegisteredEvent.query.filter_by(
        user_id=data["user_id"], event_id=data["event_id"]
    ).first()
    if existing:
        return jsonify({"message": "User already registered for this event"}), 400

    # Only create if it doesn't exist
    reg = RegisteredEvent(
        user_id=data["user_id"],
        event_id=data["event_id"],
        registered_at=registered_at
    )

    db.session.add(reg)
    db.session.commit()
    return jsonify(reg.as_dict()), 201

# DELETE registered event
@registered_event_bp.route("/registered-events/user/<int:user_id>/event/<int:event_id>", methods=["DELETE"])
def delete_registered_event(user_id, event_id):
    reg = RegisteredEvent.query.filter_by(user_id=user_id, event_id=event_id).first()
    if not reg:
        return jsonify({"error": "Registration not found"}), 404
    db.session.delete(reg)
    db.session.commit()
    return jsonify({"message": "Registration deleted"})
