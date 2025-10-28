# routes/tag.py
from flask import Blueprint, request, jsonify
from project.models import db, Tag

tag_bp = Blueprint("tag", __name__)

# GET all tags
@tag_bp.route("/tags", methods=["GET"])
def get_tags():
    tags = Tag.query.all()
    return jsonify([t.as_dict() for t in tags])

# POST create tag
@tag_bp.route("/tags", methods=["POST"])
def create_tag():
    data = request.get_json()

    # Duplicate check
    if Tag.query.filter_by(tag_name=data.get("tag_name")).first():
        return jsonify({"message": "Tag already exists"}), 400

    tag = Tag(tag_name=data.get("tag_name"))
    db.session.add(tag)
    db.session.commit()
    return jsonify(tag.as_dict()), 201


# PUT update tag
@tag_bp.route("/tags/<int:tag_id>", methods=["PUT"])
def update_tag(tag_id):
    tag = Tag.query.get(tag_id)
    if not tag:
        return jsonify({"error": "Tag not found"}), 404
    data = request.get_json()
    
    if "tag_name" in data:
        tag.tag_name = data["tag_name"]
    
    db.session.commit()
    return jsonify(tag.as_dict())

# DELETE tag
@tag_bp.route("/tags/<int:tag_id>", methods=["DELETE"])
def delete_tag(tag_id):
    tag = Tag.query.get(tag_id)
    if not tag:
        return jsonify({"error": "Tag not found"}), 404
    db.session.delete(tag)
    db.session.commit()
    return jsonify({"message": "Tag deleted"})
