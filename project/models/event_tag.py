# project/models/event_tag.py
from . import db

class EventTag(db.Model):
    __tablename__ = "event_tag"
    id = db.Column(db.Integer, primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey("tag.id"), nullable=False)
    
    event_identifier = db.Column(db.String(255), db.ForeignKey("event_cache.event_identifier"), nullable=False)
    
    cached_event = db.relationship("EventCache", backref="tags")
    tag = db.relationship("Tag", backref="event_tags") 

    def as_dict(self):
        return {
            "id": self.id,
            "tag_id": self.tag_id,
            "event_identifier": self.event_identifier,
            "tag_name": self.tag.tag_name if self.tag else None
        }