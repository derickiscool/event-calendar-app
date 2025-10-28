
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

from project import routes

from .api import api_bp
app.register_blueprint(api_bp)