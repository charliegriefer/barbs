import os

import flask
from dotenv import load_dotenv
from flask import Flask
from flask_wtf.csrf import CSRFProtect

from app.extensions import cache

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(dotenv_path=dotenv_path, verbose=True)

csrf = CSRFProtect()

def create_app():
    application = Flask(__name__)

    application.config.from_object(os.environ["CONFIG_TYPE"])

    cache.init_app(application)
    csrf.init_app(application)

    # register blueprints
    from app.main import main_blueprint
    application.register_blueprint(main_blueprint)

    return application
