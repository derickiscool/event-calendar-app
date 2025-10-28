from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import models to register with SQLAlchemy
from .user import User
from .user_profile import UserProfile
from .tag import Tag
from .user_preference import UserPreference
from .venue import Venue
from .event import Event
from .event_tag import EventTag
from .registered_event import RegisteredEvent
from .review import Review
