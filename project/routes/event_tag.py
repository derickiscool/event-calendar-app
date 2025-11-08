# routes/event_tag.py
from flask import Blueprint, request, jsonify
from project.models import db, EventTag

event_tag_bp = Blueprint("event_tag", __name__)

# GET all event-tags
@event_tag_bp.route("/event-tags", methods=["GET"])
def get_event_tags():
    tags = EventTag.query.all()
    return jsonify([t.as_dict() for t in tags])

# POST create event-tag
@event_tag_bp.route("/event-tags", methods=["POST"])
def create_event_tag():
    data = request.get_json()

    # Check that exactly one of event_id or event_identifier is provided
    if ("event_id" in data) == ("event_identifier" in data):
        return jsonify({"error": "Exactly one of event_id or event_identifier must be provided"}), 400

    # Duplicate check
    existing = EventTag.query.filter(
        (EventTag.tag_id == data["tag_id"]) &
        (EventTag.event_id == data.get("event_id")) &
        (EventTag.event_identifier == data.get("event_identifier"))
    ).first()
    if existing:
        return jsonify({"message": "EventTag already exists"}), 400

    et = EventTag(
        tag_id=data["tag_id"],
        event_id=data.get("event_id"),
        event_identifier=data.get("event_identifier")
    )
    db.session.add(et)
    db.session.commit()
    return jsonify(et.as_dict()), 201

# DELETE event-tag
@event_tag_bp.route("/event-tags/event/<int:event_id>/tag/<int:tag_id>", methods=["DELETE"])
def delete_event_tag(event_id, tag_id):
    et = EventTag.query.filter_by(event_id=event_id, tag_id=tag_id).first()
    if not et:
        return jsonify({"error": "EventTag not found"}), 404
    db.session.delete(et)
    db.session.commit()
    return jsonify({"message": "EventTag deleted"})
