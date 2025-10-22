# models/venue.py
from . import db

class Venue(db.Model):
    __tablename__ = "venue"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    address = db.Column(db.String(255), nullable=False)
    postal_code = db.Column(db.String(6), nullable=False)

    events = db.relationship("Event", backref="venue", cascade="all, delete")

    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address,
            "postal_code": self.postal_code
        }
