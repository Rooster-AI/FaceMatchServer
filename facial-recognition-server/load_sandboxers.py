from ast import Store
import base64
import sys
import cv2
sys.path.append("../")
from models.banned_person import BannedPerson
from models.store import Store
from supabase_dao import add_banned_person_image, add_store, add_banned_person
from models.banned_person_image import BannedPersonImage


def add_sandboxers():
    store = Store("Sandbox", "Startup Building", "121")
    store = add_store(store)
    store_id = store.id

    banned_persons = []
    images = []

    path = "./data/database/adamchandler.jpg"
    person, image = create_person(path, store_id, "Adam Chandler")
    banned_persons.append(person)
    images.append(image)

    path = "./data/database/adamrounsville.jpg"
    person, image = create_person(path, store_id, "Adam Rounsville")
    banned_persons.append(person)
    images.append(image)

    path = "./data/database/alexanderdensley.jpg"
    person, image = create_person(path, store_id, "Alexander Densley")
    banned_persons.append(person)
    images.append(image)

    path = "./data/database/antonalley.jpg"
    person, image = create_person(path, store_id, "Anton Alley")
    banned_persons.append(person)
    images.append(image)

    # aspenfisher
    path = "./data/database/aspenfisher.jpg"
    person, image = create_person(path, store_id, "Aspen Fisher")
    banned_persons.append(person)
    images.append(image)

    # benjaminfisher
    path = "./data/database/benjaminfisher.jpg"
    person, image = create_person(path, store_id, "Benjamin Fisher")
    banned_persons.append(person)
    images.append(image)

    # cairomurphy
    path = "./data/database/cairomurphy.jpg"
    person, image = create_person(path, store_id, "Cairo Murphy")
    banned_persons.append(person)
    images.append(image)

    # cannonfarr
    path = "./data/database/cannonfarr.jpg"
    person, image = create_person(path, store_id, "Cannon Farr")
    banned_persons.append(person)
    images.append(image)

    # chadsauder
    path = "./data/database/chadsauder.jpg"
    person, image = create_person(path, store_id, "Chad Sauder")
    banned_persons.append(person)
    images.append(image)

    # dallinbartholomew
    path = "./data/database/dallinbartholomew.jpg"
    person, image = create_person(path, store_id, "Dallin Bartholomew")
    banned_persons.append(person)
    images.append(image)

    # dallinburningham
    path = "./data/database/dallinburningham.jpg"
    person, image = create_person(path, store_id, "Dallin Burningham")
    banned_persons.append(person)
    images.append(image)

    # devinjernigan
    path = "./data/database/devinjernigan.png"
    person, image = create_person(path, store_id, "Devin Jernigan")
    banned_persons.append(person)
    images.append(image)

    # gavinshelley
    path = "./data/database/gavinshelley.jpg"
    person, image = create_person(path, store_id, "Gavin Shelley")
    banned_persons.append(person)
    images.append(image)

    # jasonlowe
    path = "./data/database/jasonlowe.jpg"
    person, image = create_person(path, store_id, "Jason Lowe")
    banned_persons.append(person)
    images.append(image)

    # josemontoya
    path = "./data/database/josemontoya.jpg"
    person, image = create_person(path, store_id, "Jose Montoya")
    banned_persons.append(person)
    images.append(image)

    # LoganOrr
    path = "./data/database/loganorr.jpg"
    img = cv2.imread(path)
    _, buffer = cv2.imencode('.jpg', img)
    image1 = base64.b64encode(buffer).decode()

    person = BannedPerson(full_name="Logan Orr", reporting_store_id=store_id,
                            report_date='now()', is_private="TRUE",
                            drivers_license=None, est_value_stolen=None, description="goofy")
    
    path = "./data/database/LoganOrr.jpg"
    img = cv2.imread(path)
    _, buffer = cv2.imencode('.jpg', img)
    image2 = base64.b64encode(buffer).decode()
    images.append((image1, image2))

    # oakleymiller
    path = "./data/database/oakleymiller.jpg"
    person, image = create_person(path, store_id, "Oakley Miller")
    banned_persons.append(person)
    images.append(image)

    # sambenion
    path = "./data/database/sambenion.jpg"
    person, image = create_person(path, store_id, "Sam Benion")
    banned_persons.append(person)
    images.append(image)

    # spencerkunkel
    path = "./data/database/spencerkunkel.jpg"

    person, image = create_person(path, store_id, "Spencer Kunkel")
    path = "./data/database/spencerkunkel3.png"
    image2 = cv2.imread(path)
    _, buffer = cv2.imencode('.jpg', image2)
    image2 = base64.b64encode(buffer).decode()
    images.append((image, image2))

    # tannerking
    path = "./data/database/tannerking.jpg"
    person, image = create_person(path, store_id, "Tanner King")
    banned_persons.append(person)
    images.append(image)

    # timothybrown
    path = "./data/database/timothybrown.jpg"
    person, image = create_person(path, store_id, "Timothy Brown")
    banned_persons.append(person)
    images.append(image)

    # xanderhunt
    path = "./data/database/xanderhunt.jpg"
    person, image = create_person(path, store_id, "Xander Hunt")
    banned_persons.append(person)
    images.append(image)

    for person, image in zip(banned_persons, images):

        if isinstance(image, tuple):
            id = 0
            response = add_banned_person(person, image[0])
            id = response.id
            banned_person_image = BannedPersonImage(banned_person_id=id, image_encoding=image[1])
            add_banned_person_image(banned_person_image)

        else:
            add_banned_person(person, image)

    




    # response = add_banned_person(spencer, base64image)

def create_person(path, store_id, name):
    image = cv2.imread(path)
    _, buffer = cv2.imencode('.jpg', image)
    base64image = base64.b64encode(buffer).decode()
    person = BannedPerson(full_name=name, reporting_store_id=store_id,
                            report_date='now()', is_private="TRUE",
                            drivers_license=None, est_value_stolen=None, description="goofy")
    return person, base64image
    

if __name__ == "__main__":
    add_sandboxers()
    print("Sandboxers added")