# models/event_tag.py
from . import db

class EventTag(db.Model):
    __tablename__ = "event_tag"
    tag_id = db.Column(db.Integer, db.ForeignKey("tag.id"), primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), primary_key=True)

    def as_dict(self):
        return {
            "tag_id": self.tag_id,
            "event_id": self.event_id
        }
