from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor, wait
from deepface import DeepFace
from deepface.rooster_deepface import match_face, verify, get_embedding
from datetime import datetime
import os
import time
import numpy as np
from PIL import Image as im
import json
import csv
import base64
import cv2
import resend

os.chdir(os.path.dirname(__file__))

MODEL = "ArcFace" 
BACKEND = "mtcnn"
DIST = "cosine"
MIN_VERIFICATIONS = 3
MODEL_DIST = f"{MODEL}_{DIST}"
DB = "data/database"
BACKEND_MIN_CONFIDENCE = 0.999
ACTIVITY_LOG_FILE = "./archive/activity.csv"
TESTING_MODE = False

app = Flask(__name__)

api_key = 're_4R1GUEGA_MU5BxRc2YKFFYsnvB55eojoM'

# Set the environment variable
os.environ['RESEND_API_KEY'] = api_key

resend.api_key = os.environ["RESEND_API_KEY"]

firstFrame = None

with open("data/startupList.json") as f:
    contacts = json.load(f)

@app.route('/upload-images', methods=['POST'])
def upload_images():
    global firstFrame
    print("Uploading Images", flush=True)
    if 'images' not in request.json:
        return jsonify({'message': 'No images found in the request'}), 400
    images = request.json["images"]
    firstFrame = images[0]
    for index, image in enumerate(images):
        decoded_bytes = base64.b64decode(image)
        np_array = np.frombuffer(decoded_bytes, np.uint8)
        image_bgr = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
        # image_rgb = cv2.cvtColor(image_bgr , cv2.COLOR_BGR2RGB)
        # im.fromarray(image_rgb).save(f"./THISFACE_{index}.jpg")
        numpy_array = np.array(image_bgr)
        images[index] = numpy_array

    with ThreadPoolExecutor(max_workers=20) as executor:
        all_faces = []
        s = time.time()
        to_finish_extract = [executor.submit(extract, frame, all_faces) for frame in images]
        wait(to_finish_extract)
        if TESTING_MODE:
            print(f"Extracted {len(all_faces)} Faces in {time.time()-s}s")

        s = time.time()
        group_matches = {i:[] for i in range(len(all_faces))}
        finish_comps = []
        for i, face in enumerate(all_faces):
            finish_comps.append(executor.submit(comp_face, face, i, all_faces[i+1:], group_matches))
        wait(finish_comps)
        if TESTING_MODE:
            print(f"Grouped Faces in {time.time() - s}s")
            print(f"Group Sizes: {[len(group_matches[a]) for a in group_matches.keys()]}")

        s = time.time()
        faceGroups = make_face_groups(group_matches, all_faces)

        verify_faces(faceGroups)
        print(f"Verified Faces in {time.time()-s}s")

    return jsonify({'message': f'{len(images)} files uploaded and processed'}), 200


def make_face_groups(group_matches, all_faces):
    faceGroups = {}

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
    
    Done = False
    while not Done:
        Done = True
        for k in group_matches.keys():
            change = group(k)
            if change: 
                Done = False
                break

    for k in group_matches.keys():
        faceGroups[k] = [all_faces[i] for i in list(group_matches[k]) + [k]]

    return faceGroups
    

def comp_face(face, i, faces_to_match, group_matches):
    for tmi, to_match in enumerate(faces_to_match):
        try:
            result = verify(face['embedding'], to_match['embedding'], model_name="ArcFace", detector_backend="mtcnn", embedded_mode=True)
            if result['verified']:
                group_matches[i].append(i+tmi+1)
        except:
            continue
    return

def extract(frame, all_faces):
    try:
        faces = DeepFace.extract_faces(frame, detector_backend=BACKEND, enforce_detection=True)
        for f in faces:
            if f["confidence"] > BACKEND_MIN_CONFIDENCE:
                # Add embedding so only has to be calculated once
                emb = get_embedding(f['face'])
                f['embedding'] = emb
                all_faces.append(f)
    except Exception as e:
        print(e)
        return
    return


def verify_faces(faceGroups):
    global firstFrame
    if TESTING_MODE:    
        base_directory = os.path.dirname(os.path.abspath(__file__))
        epoch_folder = f"archive/{datetime.now().strftime('%y-%m-%d-%H-%M-%S')}"
        faces_folder = os.path.join(epoch_folder, "faces")
        os.makedirs(os.path.join(base_directory, epoch_folder), exist_ok=True)
        os.mkdir(faces_folder)
        confidence_levels = {}
    face_dict = {}
    for k, key in enumerate(faceGroups.keys()):
        for i, face in enumerate(faceGroups[key]):
            if TESTING_MODE: 
                title = f"face_{k}_{i}.png"
                save_face(face, os.path.join(faces_folder, title))
                confidence_levels[title] = face["confidence"]
            finder(face, face_dict)

    match = find_lowest_average(face_dict)
    match_image = None
    for person in contacts:
        if person['Name'] == match:
            match_image = person['Image']

    if TESTING_MODE: 
        print(match)

        epoch_info = {
            "match": {
                "name": match,
            },
            "everyone": face_dict,
            "faces_confidence": confidence_levels,
        }
        with open(os.path.join(epoch_folder, "epoch_results.json"), 'w') as f:
            json.dump(epoch_info,f, indent=4)

        if match is not None:
            with open(ACTIVITY_LOG_FILE, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([match, datetime.now().strftime('%y-%m-%d %H:%M:%S')])
    else:
        file = open(
            os.path.join(os.path.dirname(__file__), f"data/database/{match_image[0]}"), "rb"
        ).read()
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
            "attachments": [{"filename": "person_in_store.jpg", "content": firstFrame}, {"filename": "match.jpg", "content": list(file)}]
        }
        resend.Emails.send(params)
    faceGroups.clear()

def finder(facial_data, faceDict):
    result = None
    try:
        result = match_face(
            facial_data,
            db_path=DB,
            model_name=MODEL,
            detector_backend=BACKEND,
            distance_metric=DIST,
            enforce_detection=True,
            silent=True
        )
        try:
            if not len(result): print("Result returned empty")
            for i in range(len(result)):
                # For each person identified:
                images_close = [get_name_from_file(image) for image in result[i]['identity'].to_list()]
                distances = result[i][MODEL_DIST].to_list()
                if len(images_close) > 0 and len(distances) > 0:
                    for key in images_close:
                        if key in faceDict.keys():
                            for value in distances:
                                faceDict[key].append(value)
                                distances.remove(value)
                        else:   
                            for value in distances:
                                faceDict[key] = [value]
                                distances.remove(value)
                else:
                    print("no images close")
        except Exception as e:
            print("Failed in for loop", e)
    except Exception as e:
        print("Error while finding: ", e)
        
def save_face(face_data, path_name):
    new_face = face_data['face'] * 255
    new_face = new_face.astype(np.uint8)
    image = im.fromarray(new_face)
    image.save(path_name)

def get_name_from_file(image_path):
    try:
        for contact in contacts:
            if os.path.split(image_path)[-1] in contact["Image"]:
                return contact["Name"]
    except:
        pass
    
def find_lowest_average(faceDict):
    if not faceDict:
        return None  # Return None if the dictionary is empty

    lowest_key = None
    lowest_average = float('inf')  # Set initial lowest_average to positive infinity

    for key, values in faceDict.items():
        if len(values) >= MIN_VERIFICATIONS:  # Check if the list of values is not empty

            # Sort values and take only the 4 lowest values if there are more than 4
            sorted_values = sorted(values)[:4] if len(values) > 4 else values

            average = sum(sorted_values) / len(sorted_values)
            print(f"Average threshhold for {key} was {average}")
            if average < lowest_average:
                lowest_average = average
                lowest_key = key

    return lowest_key

if __name__ == '__main__':
    app.run(debug=True, threaded=True, host='192.168.0.16', port=5000)