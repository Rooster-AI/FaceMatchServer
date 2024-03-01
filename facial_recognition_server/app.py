# pylint: disable=C0413, C0301, E1101, C0103. E0401
"""
    This module uses Flask and DeepFace to recognize faces in uploaded images.
    It checks images against a database to find matches and can send alerts for identified faces.
"""
import os
import re
import time
import base64
from datetime import datetime
import json
import csv
import sys
from concurrent.futures import ThreadPoolExecutor, wait
import numpy as np
import cv2
from PIL import Image as im
from deepface import DeepFace
from deepface.rooster_deepface import match_face, verify, get_embedding


MAIN_DIR = os.path.dirname(__file__)
sys.path.append(MAIN_DIR)
from alert import notify

# Parent imports
PAR_DIR = os.path.dirname(MAIN_DIR)
sys.path.append(PAR_DIR)
from models.logging import Logging
from supabase_dao import (
    get_banned_person,
    get_banned_person_images,
    database_log,
)


DEVICE_ID = 2  # For logging to the db
MODEL = "ArcFace"
BACKEND = "mtcnn"
DIST = "cosine"
MIN_VERIFICATIONS = 3
MODEL_DIST = f"{MODEL}_{DIST}"
DB = os.path.join(MAIN_DIR, "data/master_database")
BACKEND_MIN_CONFIDENCE = 0.999
ACTIVITY_LOG_FILE = os.path.join(MAIN_DIR, "archive/activity.csv")
TESTING_MODE = False
MAX_WORKERS = 4


def upload_images(data):
    """
    Handles the POST request to upload and process images for facial recognition.
    This function decodes base64-encoded images, extracts faces, groups similar faces together,
    and verifies them against a database.
    It returns a response indicating the outcome of the processing.
    """
    if "images" not in data:
        return False, {"message": "No images found in the request"}
    if "device_id" not in data:
        return False, {"message": "No device id found in the request"}

    images = data["images"]
    device_id = data["device_id"]
    first_frame = images[0]
    decoded_images = decode_images(images)

    executor = ThreadPoolExecutor(max_workers=1)
    executor.submit(analyze_images, decoded_images, first_frame, device_id)

    return True, {"message": f"{len(decoded_images)} files uploaded and processed"}


def analyze_images(decoded_images, first_frame, device_id):
    """
    Analyzes the decoded images and ids faces.
    """
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
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
        verify_faces(face_groups, first_frame, device_id)
        print(f"Verified Faces in {time.time()-s}s")


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


def verify_faces(face_groups, first_frame, device_id):
    """
    Verifies identified faces against groups, logs matches, and optionally sends an alert if
    a match is found. Saves face images and match data in testing mode.
    """
    confidence_levels = {}
    faces_folder = None
    epoch_folder = None

    if TESTING_MODE:
        faces_folder, epoch_folder = make_test_directory()
    face_dict = {}
    for k, key in enumerate(face_groups.keys()):
        for i, face in enumerate(face_groups[key]):
            if TESTING_MODE:
                title = f"face_{k}_{i}.png"
                save_face(face, os.path.join(faces_folder, title))
                confidence_levels[title] = face["confidence"]
            finder(face, face_dict)

    match = find_lowest_average(face_dict)
    print(f"Match: {match}")
    match_person = None
    if match is not None:
        match_person = get_banned_person(match)
        match_image = get_banned_person_images(match)[0].image

        if TESTING_MODE:
            write_to_test_directory(match, face_dict, confidence_levels, epoch_folder)
        else:
            notify(match_image, first_frame, match_person, device_id)
            database_log(
                Logging(
                    DEVICE_ID,
                    "INFO",
                    f"Found Shoplifter! Name:{match_person.full_name}, ID:{match_person.id} IN STORE: #TODO",
                )
            )

    face_groups.clear()


def make_test_directory():
    """Makes directory for storing server test results"""
    epoch_folder_name = f"archive/{datetime.now().strftime('%y-%m-%d-%H-%M-%S')}"
    epoch_folder = os.path.join(MAIN_DIR, epoch_folder_name)
    os.makedirs(epoch_folder, exist_ok=True)
    faces_folder = os.path.join(epoch_folder, "faces")
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
    with open(
        os.path.join(epoch_folder, "epoch_results.json"), "w", encoding="utf-8"
    ) as file:
        json.dump(epoch_info, file, indent=4)

    if match is not None:
        with open(ACTIVITY_LOG_FILE, "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([match, datetime.now().strftime("%y-%m-%d %H:%M:%S")])


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
        images_close = [get_id_from_file(image) for image in res["identity"].to_list()]
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


def get_id_from_file(image_path):
    """Retrieves the name associated with an image file."""
    pattern = r"(\d+_\d+).jpg$"
    match = re.search(pattern, image_path)
    if match:
        # Extract person id from file name
        file_name = match.group(1)
        uid = int(file_name.split("_")[0])
        return uid
    return None


def get_id_from_name(name):
    """Retrieves the name associated with an image file."""
    people_by_name = {
        "adamchandler": 320,
        "adamrounsville": 321,
        "alexanderdensley": 322,
        "antonalley": 323,
        "aspenfisher": 324,
        "benjaminfisher": 325,
        "cairomurphy": 326,
        "cannonfarr": 327,
        "chadsauder": 328,
        "dallinbartholomew": 329,
        "dallinburningham": 330,
        "devinjernigan": 331,
        "gavinshelley": 332,
        "jasonlowe": 333,
        "josemontoya": 334,
        "oakleymiller": 335,
        "sambenion": 336,
        "tannerking": 337,
        "timothybrown": 338,
        "xanderhunt": 339,
        "loganorr": 350,
        "spencerkunkel": 351,
    }
    return people_by_name[name]


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


def extract_id_from_filepath(filepath):
    """
    Extracts the ID from the given filepath with the structure "data/database2/(id)_(number).jpg".

    Parameters:
    - filepath: A string representing the file path.

    Returns:
    - The extracted ID as a string.
    """
    # Extract the basename of the file (e.g., "(id)_(number).jpg")
    basename = os.path.basename(filepath)

    # Split the basename by underscore ('_') and take the first part, which contains the ID
    id_part = basename.split("_")[0]

    return id_part


def get_latest_database(args):
    """Send the file of the latest representations database

    NOTE: Make sure rooster_update.py has ran recently, which will pull all the
    images from the database down and recreate the .pkl files

    """
    model = args.get("model")
    backend = args.get("backend")
    print("hio")
    if not model or not backend:
        model = "ArcFace"
        backend = "mtcnn"  # By default return the yolov8 version
    filename = f"representations_{model.lower().replace('-','_')}_{backend.lower().replace('-','_')}.pkl"

    filepath = os.path.join(os.getcwd(), "data", "master_database", filename)
    if os.path.exists(filepath):
        return filepath
    return False
