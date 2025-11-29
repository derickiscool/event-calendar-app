from . import db
from datetime import datetime

class EventCache(db.Model):
    __tablename__ = "event_cache"

    event_identifier = db.Column(db.String(255), primary_key=True) 
    source = db.Column(db.Enum('official', 'community'), nullable=False)
    original_id = db.Column(db.String(255), nullable=False)        
    title = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    # Relationships
    reviews = db.relationship("Review", backref="cached_event", cascade="all, delete")
    bookmarks = db.relationship("Bookmark", backref="cached_event", cascade="all, delete")

    def as_dict(self):
        return {
            "event_identifier": self.event_identifier,
            "source": self.source,
            "title": self.title
        }