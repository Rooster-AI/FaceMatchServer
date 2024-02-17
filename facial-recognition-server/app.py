# pylint: disable=C0413, C0301
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
from dotenv import load_dotenv
import numpy as np
import cv2
import resend
from PIL import Image as im
from deepface import DeepFace
from deepface.rooster_deepface import match_face, verify, get_embedding

os.chdir(os.path.dirname(__file__))


sys.path.append("../")
from supabase_dao import (
    get_banned_person,
    get_banned_person_images,
    get_store_employees,
    get_store_by_id,
)


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


resend.api_key = RESEND_API_KEY

with open("data/startupList.json", encoding="utf-8") as f:
    contacts = json.load(f)


def upload_images(data):
    """
    Handles the POST request to upload and process images for facial recognition.
    This function decodes base64-encoded images, extracts faces, groups similar faces together,
    and verifies them against a database.
    It returns a response indicating the outcome of the processing.
    """
    if "images" not in data:
        return False, {"message": "No images found in the request"}
    images = data["images"]
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

    return True, {"message": f"{len(decoded_images)} files uploaded and processed"}


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
        send_email(match_image, first_frame, match_person)
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
    with open(
        os.path.join(epoch_folder, "epoch_results.json"), "w", encoding="utf-8"
    ) as file:
        json.dump(epoch_info, file, indent=4)

    if match is not None:
        with open(ACTIVITY_LOG_FILE, "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([match, datetime.now().strftime("%y-%m-%d %H:%M:%S")])


def send_email(match_image, first_frame, match_person):
    """Sends an email alert with attached images for shoplifter identification."""

    # TO DO - Add the email address of the store owner to the "to" list
    # TO DO - Add the information of the match to the email content
    # print(match_image)
    store_id = match_person.reporting_store_id
    employees = get_store_employees(store_id)

    emails = []
    for employee in employees:
        emails.append(employee.email)

    with open("roosterLogo.png", "rb") as image_file:
        logo = base64.b64encode(image_file.read())

    info = ""
    if match_person.full_name:
        info += f"<p>Name: {match_person.full_name}</p>"

    if match_person.drivers_license:
        info += f"<p>Drivers License: {match_person.drivers_license}</p>"

    if match_person.est_value_stolen:
        info += f"<p>Estimated Value Stolen: {match_person.est_value_stolen}</p>"

    if match_person.description:
        info += f"<p>Description: {match_person.description}</p>"

    if match_person.report_date:
        info += f"<p>Report Date: {match_person.report_date}</p>"

    if match_person.reporting_store_id:
        reporting_store = get_store_by_id(match_person.reporting_store_id)
        info += f"<p>Reporting Store: {reporting_store.name}</p>"

    html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Rooster Identity Confirmation</title>
        <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #c22026; /* Adjusted to match logo color */
            color: #000000;
            padding: 20px;
        }}
        .email-container {{
            max-width: 600px;
            margin: 20px auto;
            padding: 20px;
            background-color: #ffffff;
            border: 1px solid #ddd;
            border-radius: 8px;
            text-align: center;
        }}
        .header {{
            background-color: #fff; /* Adjusted to match logo color */
            padding: 10px;
            text-align: center;
            border-radius: 8px 8px 0 0;
        }}
        .footer {{
            background-color: #c22026; /* Adjusted to match logo color */
            padding: 10px;
            text-align: center;
            border-radius: 0 0 8px 8px;
            color: #ffffff;
        }}
        .button {{
            display: inline-block;
            padding: 10px 20px;
            margin: 10px 0;
            background-color: #c22026;
            color: #ffffff !important;
            text-decoration: none;
            border-radius: 4px;
        }}
        a {{
            color: #ffffff !important;
            text-decoration: none;
        }}


        </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <img src="data:image/jpeg;base64,{logo.decode('utf-8')}" alt="Rooster Logo" class="image" width="100">
                </div>

                <h1>Confirm the Match</h1>
                <p>Please review the images below to confirm the identity of the individual:</p>
                <div>
                    <img src="data:image/jpeg;base64,{first_frame}" alt="Person in Store" class="image" style="margin-center: 10px;">
                    <img src="data:image/jpeg;base64,{match_image}" alt="Match" class="image" style="margin-center: 10px;">
                </div>
                <p>Is this a match?</p>
                <p>{info}</p>
                <div class="footer">
                    <p>Contact us for support at support@userooster.com</p>
                </div>
            </div>
        </body>
        </html>
    """
    # <a href="#" class="button">Yes, it's a match</a>
    # <a href="#" class="button">No, it's not a match</a>
    params = {
        "from": "Rooster <no-reply@alert.userooster.com>",
        "to": emails[0],
        "subject": "Alert: Shoplifter Identified in Your Store",
        "html": html_content,
        # we may want to add the images as attachments,
        # but they were not working
        # "attachments": [
        #     {
        #         "name": "Person in Store.jpg",
        #         "content": first_frame.decode("utf-8"),
        #     },
        #     {
        #         "name": "Match.jpg",
        #         "content": match_image.decode("utf-8"),
        #     },
        # ],
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
    # use this when deepface is updated to use new id file names
    # print(image_path)
    # pattern = r"(\d+_\d+).jpg$"
    # match = re.search(pattern, image_path)
    # print(match)
    # if match:
    #     return match.group(1)
    # return None

    # in the meantime, use this
    pattern = r"/([^/]+)\.jpg$"
    match = re.search(pattern, image_path)
    if match:
        return get_id_from_name(match.group(1))
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
