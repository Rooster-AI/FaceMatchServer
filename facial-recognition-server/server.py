"""
    This is the root for all endpoints, and is the file to be ran on the server
"""

import datetime
from flask import Flask, request, jsonify, send_file
import app as Funcs
import os
from models.banned_person import BannedPerson
from supabase_dao import add_banned_person

os.chdir(os.path.dirname(__file__))

app = Flask(__name__)


@app.route("/upload-images", methods=["POST"])
def upload_images_endpoint():
    success, result = Funcs.upload_images(request.json)
    if success:
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@app.route("/add-banned-person", methods=["POST"])
def add_banned_person_endpoint():
    """
    Add a new banned person
    """
    data = request.json
    person = BannedPerson(
        full_name=request.json.get("full_name"),
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


@app.route("/latest_database", methods=["GET"])
def get_latest_database_pkl():
    filepath = Funcs.get_latest_database(request.args)
    if filepath:
        return send_file(filepath, as_attachment=True)

    return jsonify({"message": "Server Failed, check logs"}), 400


if __name__ == "__main__":
    app.run(debug=False, threaded=True, host="0.0.0.0", port=5000)
