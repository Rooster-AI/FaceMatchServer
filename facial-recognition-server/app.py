"""
    This module uses Flask and DeepFace to recognize faces in uploaded images.
    It checks images against a database to find matches and can send alerts for identified faces.
"""

import os
import time
import base64
from datetime import datetime
import json
import csv
import sys
from concurrent.futures import ThreadPoolExecutor, wait

sys.path.append('../')

from dotenv import load_dotenv
from flask import Flask, request, jsonify
import numpy as np
import cv2
import resend
from PIL import Image as im
from deepface import DeepFace
from deepface.rooster_deepface import match_face, verify, get_embedding
from supabase_dao import *

os.chdir(os.path.dirname(__file__))
load_dotenv()


MODEL = "ArcFace"
BACKEND = "mtcnn"
DIST = "cosine"
MIN_VERIFICATIONS = 3
MODEL_DIST = f"{MODEL}_{DIST}"
DB = "data/database"
BACKEND_MIN_CONFIDENCE = 0.999
ACTIVITY_LOG_FILE = "./archive/activity.csv"
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
TESTING_MODE = False

app = Flask(__name__)

# Set the environment variable
# os.environ["RESEND_API_KEY"] = RESEND_API_KEY

# resend.api_key = os.environ["RESEND_API_KEY"]
resend.api_key = RESEND_API_KEY

with open("data/startupList.json", encoding="utf-8") as f:
    contacts = json.load(f)


@app.route("/upload-images", methods=["POST"])
def upload_images():
    """
        Handles the POST request to upload and process images for facial recognition.
        This function decodes base64-encoded images, extracts faces, groups similar faces together,
        and verifies them against a database.
        It returns a response indicating the outcome of the processing.
    """
    print("Uploading Images", flush=True)
    if "images" not in request.json:
        return jsonify({"message": "No images found in the request"}), 400
    images = request.json["images"]
    first_frame = images[0]
    decoded_images = decode_images(images)

    with ThreadPoolExecutor(max_workers=20) as executor:
        all_faces = []
        s = time.time()
        to_finish_extract = [
            executor.submit(extract, frame, all_faces) for frame in decoded_images
        ]
        wait(to_finish_extract)
        if TESTING_MODE:
            print(f"Extracted {len(all_faces)} Faces in {time.time()-s}s")

        s = time.time()
        group_matches = {i: [] for i in range(len(all_faces))}
        finish_comps = []
        for i, face in enumerate(all_faces):
            finish_comps.append(
                executor.submit(comp_face, face, i, all_faces[i + 1 :], group_matches)
            )
        wait(finish_comps)
        if TESTING_MODE:
            print(f"Grouped Faces in {time.time() - s}s")
            print(
                f"Group Sizes: {[len(group_matches[a]) for a in group_matches.keys()]}"
            )

        s = time.time()
        face_groups = make_face_groups(group_matches, all_faces)

        verify_faces(face_groups, first_frame)
        print(f"Verified Faces in {time.time()-s}s")

    return jsonify({"message": f"{len(decoded_images)} files uploaded and processed"}), 200

def decode_images(images):
    """Decodes base64-encoded images and converts them to numpy arrays."""
    decoded_images = []
    for image in images:
        decoded_bytes = base64.b64decode(image)
        np_array = np.frombuffer(decoded_bytes, np.uint8)
        image_bgr = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
        # image_rgb = cv2.cvtColor(image_bgr , cv2.COLOR_BGR2RGB)
        # im.fromarray(image_rgb).save(f"./THISFACE_{index}.jpg")
        decoded_images.append(np.array(image_bgr))
    return decoded_images

def make_face_groups(group_matches, all_faces):
    """
        Groups faces based on similarity by updating group matches and grouping them.
        Returns a dictionary mapping each group key to the list of faces in that group.
    """
    face_groups = {}

    for k in group_matches.keys():
        group_matches[k] = set(group_matches[k])

    def group(i):
        change = False
        for v in group_matches[i]:
            if v in group_matches.keys():
                group_matches[i].update(group_matches.pop(v))
                change = True
                break

        return change

    done_grouping = False
    while not done_grouping:
        done_grouping = True
        for k in group_matches.keys():
            change = group(k)
            if change:
                done_grouping = False
                break

    for k in group_matches.keys():
        face_groups[k] = [all_faces[i] for i in list(group_matches[k]) + [k]]

    return face_groups


def comp_face(face, i, faces_to_match, group_matches):
    """
        Compares a given face to a list of other faces to find matches based on their embeddings.
        Updates group_matches with indices of matching faces for grouping similar faces together.
    """
    for tmi, to_match in enumerate(faces_to_match):
        try:
            result = verify(
                face["embedding"],
                to_match["embedding"],
                model_name="ArcFace",
                embedded_mode=True,
            )
            if result["verified"]:
                group_matches[i].append(i + tmi + 1)
        except ValueError:
            continue


def extract(frame, all_faces):
    """
        Extracts faces from a given frame using the DeepFace library,
        filters them based on a confidence threshold, and adds their embeddings to a shared list.
    """
    try:
        faces = DeepFace.extract_faces(
            frame, detector_backend=BACKEND, enforce_detection=True
        )
        for face in faces:
            if face["confidence"] > BACKEND_MIN_CONFIDENCE:
                # Add embedding so only has to be calculated once
                emb = get_embedding(face["face"])
                face["embedding"] = emb
                all_faces.append(face)
    except ValueError as e:
        print(e)
        return
    return


def verify_faces(face_groups, first_frame):
    """
        Verifies identified faces against groups, logs matches, and optionally sends an alert if
        a match is found. Saves face images and match data in testing mode.
    """
    if TESTING_MODE:
        faces_folder, epoch_folder = make_test_directory()
        confidence_levels = {}
    face_dict = {}
    # connect to database
    for k, key in enumerate(face_groups.keys()):
        for i, face in enumerate(face_groups[key]):
            if TESTING_MODE:
                title = f"face_{k}_{i}.png"
                save_face(face, os.path.join(faces_folder, title))
                confidence_levels[title] = face["confidence"]
            finder(face, face_dict)

    match = find_lowest_average(face_dict)
    match_image = None
    for person in contacts:
        if person["Name"] == match:
            match_image = person["Image"]

    if TESTING_MODE:
        write_to_test_directory(match, face_dict, confidence_levels, epoch_folder)
    else:
        send_email(match_image, first_frame)
    face_groups.clear()

def make_test_directory():
    """Makes directory for storing server test results"""
    base_directory = os.path.dirname(os.path.abspath(__file__))
    epoch_folder = f"archive/{datetime.now().strftime('%y-%m-%d-%H-%M-%S')}"
    faces_folder = os.path.join(epoch_folder, "faces")
    os.makedirs(os.path.join(base_directory, epoch_folder), exist_ok=True)
    os.mkdir(faces_folder)
    return faces_folder, epoch_folder

def write_to_test_directory(match, face_dict, confidence_levels, epoch_folder):
    """Writes server results to test directory"""
    print(match)
    epoch_info = {
        "match": {
            "name": match,
        },
        "everyone": face_dict,
        "faces_confidence": confidence_levels,
    }
    with open(os.path.join(epoch_folder, "epoch_results.json"), "w", encoding="utf-8") as file:
        json.dump(epoch_info, file, indent=4)

    if match is not None:
        with open(ACTIVITY_LOG_FILE, "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([match, datetime.now().strftime("%y-%m-%d %H:%M:%S")])

def send_email(match_image, first_frame):
    """Sends an email alert with attached images for shoplifter identification."""
    # connect to database
    file_path = os.path.join(os.path.dirname(__file__), f"data/database/{match_image[0]}")
    with open(file_path, "rb") as file:
        data = file.read()
    html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Suspected Shoplifter Alert</title>
            </head>
            <body>
                <p style="text-align: center; font-weight: bold;">
                    Please review the two attached images to verify if this is a correct match.
                </p>
            </body>
            </html>
        """
    params = {
        "from": "Rooster <no-reply@alert.userooster.com>",
        "to": ["spencerkunkel@userooster.com"],
        "subject": "Alert: Shoplifter Identified in Your Store",
        "html": html_content,
        "attachments": [
            {"filename": "person_in_store.jpg", "content": first_frame},
            {"filename": "match.jpg", "content": list(data)},
        ],
    }
    resend.Emails.send(params)


def finder(facial_data, face_dict):
    """
        Searches for matches of the given facial data in the database.
        Updates face_dict with the distances of close matches.
    """
    result = None
    try:
        result = match_face(
            facial_data,
            db_path=DB,
            model_name=MODEL,
            detector_backend=BACKEND,
            distance_metric=DIST,
            enforce_detection=True,
            silent=True,
        )
        try:
            find_face(result, face_dict)
        except KeyError as e:
            print("Failed in for loop", e)
    except ValueError as e:
        print("Error while finding: ", e)

def find_face(result, face_dict):
    """Updates a dictionary with faces identified from results, including distances."""
    if not result:
        print("Result returned empty")
    for res in result:
        # For each person identified:
        images_close = [
            get_name_from_file(image)
            for image in res["identity"].to_list()
        ]
        distances = res[MODEL_DIST].to_list()
        if len(images_close) > 0 and len(distances) > 0:
            for key in images_close:
                if key in face_dict.keys():
                    for value in distances:
                        face_dict[key].append(value)
                        distances.remove(value)
                else:
                    for value in distances:
                        face_dict[key] = [value]
                        distances.remove(value)
        else:
            print("no images close")


def save_face(face_data, path_name):
    """Saves a face image to the specified path."""
    new_face = face_data["face"] * 255
    new_face = new_face.astype(np.uint8)
    image = im.fromarray(new_face)
    image.save(path_name)


def get_name_from_file(image_path):
    """Retrieves the name associated with an image file."""
    try:
        for contact in contacts:
            if os.path.split(image_path)[-1] in contact["Image"]:
                return contact["Name"]
    except (TypeError, KeyError) as e:
        print(f"An error occurred: {e}")
    return None


def find_lowest_average(face_dict):
    """Finds the key with the lowest average value in a dictionary."""
    if not face_dict:
        return None  # Return None if the dictionary is empty

    lowest_key = None
    lowest_average = float("inf")  # Set initial lowest_average to positive infinity

    for key, values in face_dict.items():
        if len(values) >= MIN_VERIFICATIONS:  # Check if the list of values is not empty

            # Sort values and take only the 4 lowest values if there are more than 4
            sorted_values = sorted(values)[:4] if len(values) > 4 else values

            average = sum(sorted_values) / len(sorted_values)
            print(f"Average threshhold for {key} was {average}")
            if average < lowest_average:
                lowest_average = average
                lowest_key = key

    return lowest_key

def update_banned_list():
    """Updates the banned list with the latest data."""
    new_banned_list = get_all_banned_person_images()
    print(new_banned_list)
    for person_image in new_banned_list:
        path = f"data/database2/{person_image.banned_person_id}_{person_image.id}.jpg"
        decoded = base64.b64decode(person_image.image)
        with open(path, "wb") as file:
            file.write(decoded)



if __name__ == "__main__":
    # app.run(debug=True, threaded=True, host="192.168.0.16", port=5000)
    update_banned_list()
