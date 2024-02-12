"""
Tests for using the DAO
"""
import base64
import os
import unittest
import cv2
from supabase_dao import *

class TestDAO(unittest.TestCase):
    """
    Tests for using the supabaseDAO
    """
    # def test_add_store(self):
    #     """
    #     Test adding and removing a store
    #     """
    #     store = Store("Rooster", "Startup Building", "121")
    #     response = add_store(store)
    #     store_id = response.id
    #     self.assertEqual(response.name, "Rooster", "Rooster was not added")

    #     response = delete_store_by_id(store_id)
    #     self.assertEqual(response.id, store_id, "Unable to remove store")

    #     response = get_store_by_id(store_id)
    #     self.assertEqual(response, None, "Store was deleted but was still in database")


    # def test_add_user(self):
    #     """
    #     Test adding, finding and removing a user
    #     """
    #     store = Store("Rooster", "Startup Building", "121")
    #     response = add_store(store)
    #     store_id = response.id

    #     devin = User("Devin", "d@example.com", "45151", False, store_id)
    #     response = add_user(devin)
    #     devin_id = response.id

    #     response = get_user_by_id(devin_id)
    #     self.assertEqual(response.full_name, "Devin", "Devin was not added")

    #     response = delete_user_by_id(devin_id)
    #     self.assertEqual(response.id, devin_id, "Correct id was not returned")

    #     response = get_user_by_id(devin_id)

    #     self.assertEqual(response, None, "user was deleted but was still in database")

    #     response = delete_store_by_id(store_id)


    # def test_add_admin(self):
    #     """
    #     Test adding and getting an admin
    #     """
    #     store = Store("Rooster", "Startup Building", "121")
    #     response = add_store(store)
    #     store_id = response.id

    #     bridger = User("Bridger", "b@example.com", "121", True, store_id)
    #     response = add_user(bridger)
    #     bridger_id = response.id
    #     self.assertEqual(response.full_name, "Bridger", "Bridger was not added")

    #     response = get_user_by_id(bridger_id)
    #     self.assertEqual(response.full_name, "Bridger", "Bridger was not added to db")

    #     self.assertEqual(response.is_admin, True, "Bridger was found but is not admin")

    #     response = delete_store_by_id(store_id)

    # def test_get_employees_and_admins(self):
    #     """
    #     Test getting employees and admins
    #     """
    #     store = Store("Rooster", "Startup Building", "121")
    #     response = add_store(store)
    #     store_id = response.id

    #     bridger = User("Bridger", "b@example.com", "121", True, store_id)
    #     response = add_user(bridger)
    #     bridger_id = response.id

    #     devin = User("Devin", "d@example.com", "45151", False, store_id)
    #     response = add_user(devin)

    #     response = get_store_employees(store_id)
    #     self.assertEqual(len(response), 2,
    #                      "Incorrect number of employees returned should have been 2 but was "
    #                      + str(len(response)) + "response " + str(response))
    #     # print(response) could assert that devin and bridger are on the list

    #     response = get_store_admins(store_id)
    #     self.assertEqual(len(response), 1,
    #                      "Incorrect number of admins returned should have been 1 but was "
    #                      + str(len(response)) + "response " + str(response))
    #     self.assertEqual(response[0].id, bridger_id)

    #     response = delete_store_by_id(store_id)

    def test_ban_person(self):
        """
        Test adding, finding by id, finding by store, finding all
        and deleting banned persons
        """
        store = Store("Rooster", "Startup Building", "121")
        response = add_store(store)
        store_id = response.id

        image = cv2.imread("testBanned.jpg")
        _, buffer = cv2.imencode('.jpg', image)
        base64image = base64.b64encode(buffer).decode()
        spencer = BannedPerson("Spencer", "598465", 874, store_id,
                               'now()', "TRUE", "An absolute literal clown")
        response = add_banned_person(spencer, base64image)
        # spencer_id = response['id']

        self.assertEqual(response.full_name,
                         "Spencer", "Spencer was not added " + str(response))

        image = cv2.imread("testBanned2.jpg")
        _, buffer = cv2.imencode('.jpg', image)
        base64image = base64.b64encode(buffer).decode()
        anton = BannedPerson("Anton", "000001", 3, store_id, 'now()', "False",
                             "Speed Racer")
        response = add_banned_person(anton, base64image)
        anton_id = response.id
        self.assertEqual(response.full_name, "Anton",
                         "Anton was not added " + str(response))

        image = cv2.imread("testBanned3.jpg")
        _, buffer = cv2.imencode('.jpg', image)
        base64image = base64.b64encode(buffer).decode()
        
        charlie = BannedPerson("Charlie", "0154", 58, 1, 'now()', "False",
                               "Hardened criminal")
        response = add_banned_person(charlie, base64image)
        # charlie_id = response['id']
        self.assertEqual(response.full_name, "Charlie",
                         "Charlie was not added " + str(response))

        response = get_banned_person(anton_id)
        self.assertEqual(response.id, anton_id,
                         "Anton was not found. response: " + str(response))

        response = get_people_banned_by_store(store_id)

        self.assertEqual(len(response), 2,
                         "Incorrect number of banned people returned from a store should have been " 
                          + "2 but was "+ str(len(response)) + " response " + str(response))

        response = get_all_banned_people()
        self.assertGreater(len(response), 2,
                           "Incorrect number of banned people returned for a store should "
                           + "have been more than 2 but was "
                           + str(len(response)) + " response " + str(response))
        # this could be a lot smarter

        response = delete_store_by_id(store_id)

    # def test_banned_person_images(self):
    #     """
    #     Test adding an additonal image, finding all images of a person and removing an image
    #     """
    #     response = add_store("Rooster", "Startup Building", "121")
    #     store_id = response["id"]

    #     image = cv2.imread("testBanned.jpg")
    #     _, buffer = cv2.imencode('.jpg', image)
    #     base64image = base64.b64encode(buffer).decode()
    #     response = add_banned_person("Spencer", "598465", 874, store_id,
    #                                  'now()', "TRUE", "An absolute literal clown",
    #                                  base64image)
    #     spencer_id = response['id']

    #     image = cv2.imread("testBanned2.jpg")
    #     _, buffer = cv2.imencode('.jpg', image)
    #     base64image = base64.b64encode(buffer).decode()
    #     response = add_banned_person_image(spencer_id, base64image)

    #     response = get_banned_person_images(spencer_id)
    #     self.assertEqual(len(response), 2,
    #                      "Incorrect number of images returned for a banned person should have been"
    #                      + " 2 but was " + str(len(response)))

    #     image_id = response[0]['id']

    #     # remove an image of a banned person
    #     response = remove_banned_person_image_by_id(image_id)
    #     self.assertEqual(response['id'], image_id,
    #                      "Incorrect id returned for deleted image")

    #     response = get_banned_person_images(spencer_id)
    #     self.assertEqual(len(response), 1,
    #                      "Incorrect number of images returned for a banned person should have been"
    #                      + " 1 but was " + str(len(response)))

    #     response = delete_store_by_id(store_id)

    # def test_update_banned_person(self):
    #     """
    #     Test updating a banned person
    #     """
    #     response = add_store("Rooster", "Startup Building", "121")
    #     store_id = response["id"]

    #     image = cv2.imread("testBanned.jpg")
    #     _, buffer = cv2.imencode('.jpg', image)
    #     base64image = base64.b64encode(buffer).decode()
    #     response = add_banned_person("Spencer", "598465", 874, store_id,
    #                                     'now()', "TRUE", "An absolute literal clown",
    #                                     base64image)
    #     spencer_id = response['id']

    #     response = update_banned_person(spencer_id, "Spencer", "598465", 85874, store_id,
    #                                     'now()', "TRUE",
    #                                     "An absolute literal clown who has taken a lot of money")

    #     self.assertEqual(response['est_value_stolen'], 85874,
    #                         "Incorrect value of stolen goods returned for updated banned person")
    #     self.assertEqual(response['description'],
    #                         "An absolute literal clown who has taken a lot of money",
    #                         "Incorrect description returned for updated banned person")

    #     response = delete_store_by_id(store_id)


if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    unittest.main()
