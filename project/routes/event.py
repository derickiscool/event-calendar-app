# routes/event.py
from flask import Blueprint, request, jsonify
from project.models import db, Event

event_bp = Blueprint("event", __name__)

# GET all events
@event_bp.route("/events", methods=["GET"])
def get_events():
    events = Event.query.all()
    return jsonify([e.as_dict() for e in events])

# GET single event
@event_bp.route("/events/<int:event_id>", methods=["GET"])
def get_event(event_id):
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404
    return jsonify(event.as_dict())

# POST create event
@event_bp.route("/events", methods=["POST"])
def create_event():
    data = request.get_json()
    event = Event(
        user_id=data.get("user_id"),
        title=data.get("title"),
        description=data.get("description"),
        start_datetime=data.get("start_datetime"),
        end_datetime=data.get("end_datetime"),
        location=data.get("location"),
        image_url=data.get("image_url"),
        venue_id=data.get("venue_id")
    )
    db.session.add(event)
    db.session.commit()
    return jsonify(event.as_dict()), 201

# PUT update event
@event_bp.route("/events/<int:event_id>", methods=["PUT"])
def update_event(event_id):
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404
    data = request.get_json()

    for field in ["title", "description", "start_datetime", "end_datetime", "location", "image_url", "venue_id"]:
        if field in data:
            setattr(event, field, data[field])

    db.session.commit()
    return jsonify(event.as_dict())

# DELETE event
@event_bp.route("/events/<int:event_id>", methods=["DELETE"])
def delete_event(event_id):
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404

    db.session.delete(event)
    db.session.commit()
    return jsonify({"message": "Event and all related data deleted"})
