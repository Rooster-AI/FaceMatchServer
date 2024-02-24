# pylint: disable=C0413,W0718,E0401
"""
    This is the root for all endpoints, and is the file to be ran on the server
"""

import datetime
import os
import sys
from flask import Flask, request, jsonify, send_file
import app as Funcs
from app import DEVICE_ID

MAIN_DIR = os.path.dirname(__file__)
# Parent imports
PAR_DIR = os.path.dirname(MAIN_DIR)
sys.path.append(PAR_DIR)
from models.banned_person import BannedPerson
from models.logging import Logging
from supabase_dao import add_banned_person, database_log


flask_server = Flask(__name__)


@flask_server.route("/upload-images", methods=["POST"])
def upload_images_endpoint():
    """
    Endpoint for client to send images to server
    """
    success, result = Funcs.upload_images(request.json)
    if success:
        return jsonify(result), 200
    return jsonify(result), 400


@flask_server.route("/add-banned-person", methods=["POST"])
def add_banned_person_endpoint():
    """
    Add a new banned person
    """
    data = request.json
    person = BannedPerson(
        full_name=data.get("full_name"),
        drivers_license=data.get("drivers_license"),
        est_value_stolen=data.get("est_value_stolen"),
        reporting_store_id=data.get("reporting_store_id"),
        report_date=datetime.datetime.now(),
        is_private=data.get("is_private"),
        description=data.get("description"),
    )
    add_banned_person(person, data.get("image_encoding"))
    # success, result = Funcs
    return jsonify({"message": "success"}), 200


@flask_server.route("/latest_database", methods=["GET"])
def get_latest_database_pkl():
    """
    Endpoint for client to get new pkl file
    """
    filepath = Funcs.get_latest_database(request.args)
    if filepath:
        return send_file(filepath, as_attachment=True)

    return jsonify({"message": "Server Failed, check logs"}), 400


@flask_server.route("/logging", methods=["POST"])
def log():
    """
    Adds a row in the logging database
    """
    try:
        data = request.json
        this_log = Logging(
            device_id=data.get("device_id"),
            severity=data.get("severity"),
            message=data.get("message"),
        )
        database_log(this_log)
        return jsonify({"message": "success"}), 200
    except ValueError:
        return jsonify({"message", "Failed, possibly missing values"}), 400


def on_stop_server(exception=None):
    """
    Runs when the flask server crashes, or ctrl c is pressed
    """
    Funcs.send_warning_email("Rooster-Server Down, check database for error")
    database_log(
        Logging(DEVICE_ID, "ERROR", f"Rooster-Server Down on error: {exception}")
    )
    sys.exit(1)  # End the process with a non-zero to end in an error (for Docker)


if __name__ == "__main__":
    try:
        database_log(Logging(DEVICE_ID, "INFO", "Started Rooster-Server"))
        flask_server.run(debug=True, threaded=True, host="0.0.0.0", port=5000)
    except (Exception, KeyboardInterrupt) as e:
        on_stop_server(e)
