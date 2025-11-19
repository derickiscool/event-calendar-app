# routes/event_tag.py
from flask import Blueprint, request, jsonify
from project.models import db, EventTag

event_tag_bp = Blueprint("event_tag", __name__)

# GET event-tags (optionally filtered by event_id or event_identifier)
@event_tag_bp.route("/event-tags", methods=["GET"])
def get_event_tags():
    event_id = request.args.get("event_id")
    event_identifier = request.args.get("event_identifier")
    
    # Build query with filters if provided
    query = EventTag.query
    
    if event_id:
        query = query.filter_by(event_id=int(event_id))
    
    if event_identifier:
        query = query.filter_by(event_identifier=event_identifier)
    
    tags = query.all()
    return jsonify([t.as_dict() for t in tags])

# POST create event-tag
@event_tag_bp.route("/event-tags", methods=["POST"])
def create_event_tag():
    data = request.get_json()

    # Check that at least one of event_id or event_identifier is provided
    if not data.get("event_id") and not data.get("event_identifier"):
        return jsonify({"error": "At least one of event_id or event_identifier must be provided"}), 400

    # Require tag_id
    if not data.get("tag_id"):
        return jsonify({"error": "tag_id is required"}), 400

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
