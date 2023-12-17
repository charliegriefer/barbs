import os
import logging
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(dotenv_path=dotenv_path, verbose=True)
basedir = os.path.abspath(os.path.dirname(__file__))

class BaseConfig:
    SECRET_KEY = os.environ["SECRET_KEY"]

    # PETSTABLISHED API
    PETSTABLISHED_BASE_URL = "https://petstablished.com/api/v2/public/pets"
    PETSTABLISHED_PUBLIC_KEY = os.environ["PETSTABLISHED_PUBLIC_KEY"]

    # LOGGING
    LOG_LEVEL = logging.DEBUG
    LOG_BACKTRACE = False

    @staticmethod
    def init_app(app):
        pass


class DevConfig(BaseConfig):
    DEBUG = os.environ["DEBUG"]


class ProdConfig(BaseConfig):
    # LOGGING
    LOG_LEVEL = logging.INFO
    LOG_BACKTRACE = True
