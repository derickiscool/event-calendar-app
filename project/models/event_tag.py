# models/event_tag.py
from . import db

class EventTag(db.Model):
    __tablename__ = "event_tag"
    id = db.Column(db.Integer, primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey("tag.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=True)
    event_identifier = db.Column(db.String(45), nullable=True)
    tag = db.relationship("Tag", backref="event_tags") 

    def as_dict(self):
        return {
            "id": self.id,
            "tag_id": self.tag_id,
            "event_id": self.event_id,
            "event_identifier": self.event_identifier
        }
