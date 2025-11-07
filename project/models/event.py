# models/event.py
from . import db

class Event(db.Model):
    __tablename__ = "event"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    start_datetime = db.Column(db.DateTime, nullable=False)
    end_datetime = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(255))
    image_url = db.Column(db.String(255))
    venue_id = db.Column(db.Integer, db.ForeignKey("venue.id"), nullable=False)

    tags = db.relationship("EventTag", backref="event", cascade="all, delete")
    registered_users = db.relationship("RegisteredEvent", backref="event", cascade="all, delete")
    reviews = db.relationship("Review", backref="event", cascade="all, delete")

    def as_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "start_datetime": self.start_datetime.isoformat() if self.start_datetime else None,
            "end_datetime": self.end_datetime.isoformat() if self.end_datetime else None,
            "location": self.location,
            "image_url": self.image_url,
            "venue_id": self.venue_id,
            "venue": self.venue.as_dict() if self.venue else None
        }
