# pylint: disable=W0511, C0413, C0411
"""
    Updates the Server's database nightly
"""

import base64
import os
import sys
from deepface import rooster_deepface


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from supabase_dao import database_log, get_all_banned_person_images

os.chdir(os.path.dirname(__file__))
from rooster_logger import logger
from models.logging import Logging

DEVICE_ID = 2  # For logging to the db


def update_banned_list():
    """Updates the banned list with the latest data."""
    new_banned_list = get_all_banned_person_images()
    print(new_banned_list)
    for person_image in new_banned_list:
        path = f"data/master_database/{person_image.banned_person_id}_{person_image.id}.jpg"
        decoded = base64.b64decode(person_image.image)
        with open(path, "wb") as file:
            file.write(decoded)


def update_encodings(model="ArcFace", backend="mtcnn"):
    """Updates the pkl file encodings from the database"""
    try:
        rooster_deepface.create_encodings_database(
            db_path="data/master_database",
            model_name=model,
            detector_backend=backend,
            force_recreate=True,
        )
    except ValueError as e:
        # TODO: when this happens, send an email or something becuase this has to be fixed
        # TODO: Most likely means it can't find a face in a face that was uploaded
        # TODO: Could change rooster-deepface to compile rest wihtout the face that threw the error
        logger.critical("SERVER ERROR: NO ABLE TO COMPILE DATABASE", exc_info=e)


if __name__ == "__main__":
    logger.info("Running rooster_update.py")
    update_banned_list()
    logger.info("Successfully updated images in master_database")
    update_encodings("ArcFace", "mtcnn")
    logger.info("Successfully updated encodings for arcface and mtcnn")
    update_encodings("ArcFace", "yolov8")  # For the client to grab updated pkl
    logger.info("Successfully updated encodings for arcface and yolov8")

    # Notify the database that it completed
    database_log(
        Logging(DEVICE_ID, "INFO", "Completed .pkl update to face database on server")
    )
