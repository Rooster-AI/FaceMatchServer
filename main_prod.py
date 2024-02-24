# pylint: disable=C0413,E0401
"""
    This is the main file run from gunicorn
"""

import sys
import os

MAIN_DIR = os.path.dirname(__file__)

sys.path.append(os.path.join(MAIN_DIR, "facial_recognition_server"))
from server import flask_server


app = flask_server
