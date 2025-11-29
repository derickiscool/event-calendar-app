from . import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # Relationships with cascade
    profile = db.relationship("UserProfile", backref="user", uselist=False, cascade="all, delete")
    events = db.relationship("Event", backref="creator", cascade="all, delete")
    reviews = db.relationship("Review", backref="user", cascade="all, delete")
    # FIX: Renamed attribute to 'bookmarks' and target to "Bookmark"
    bookmarks = db.relationship("Bookmark", backref="user", cascade="all, delete")
    preferences = db.relationship("UserPreference", backref="user", cascade="all, delete")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def as_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "profile": self.profile.as_dict() if self.profile else None
        }