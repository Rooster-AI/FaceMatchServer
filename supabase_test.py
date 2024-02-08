import base64
import os
import unittest


import cv2
from supabaseDAO import *


class TestDAO(unittest.TestCase):

    def test_add_store(self):
        response = add_store("Rooster", "Startup Building", "121")
        store_id = response["id"]
        self.assertEqual(response['name'], "Rooster", "Rooster was not added")

        response = delete_store_by_id(store_id)
        self.assertEqual(response['id'], store_id, "Unable to remove store")
    
        response = get_store_by_id(store_id)
        self.assertEqual(response, [], "Store was deleted but was still in database")

    
    def test_add_user(self):
        response = add_store("Rooster", "Startup Building", "121")
        store_id = response["id"]
        self.assertEqual(response['name'], "Rooster", "Rooster was not added")

        response = add_user("Devin", "d@example.com", "45151", False, store_id)
        devin_id = response['id']
        response = get_user_by_id(devin_id)
        self.assertEqual(response['full_name'], "Devin", "Devin was not added")

        response = delete_user_by_id(devin_id)
        self.assertEqual(response['id'], devin_id, "Correct id was not returned")

        response = get_user_by_id(devin_id)

        self.assertEqual(response, [], "user was deleted but was still in database")

        response = delete_store_by_id(store_id)
    

    def test_add_admin(self):
        response = add_store("Rooster", "Startup Building", "121")
        store_id = response["id"]
        self.assertEqual(response['name'], "Rooster", "Rooster was not added")

        response = add_user("Bridger", "b@example.com", "121", True, store_id)
        bridger_id = response['id']
        self.assertEqual(response['full_name'], "Bridger", "Bridger was not added")
        
        response = get_user_by_id(bridger_id)
        self.assertEqual(response['full_name'], "Bridger", "Bridger was not added")
        print(response)
        self.assertEqual(response['is_admin'], True, "Bridger was found but is not admin")

        response = delete_user_by_id(bridger_id)
        self.assertEqual(response['id'], bridger_id, "Correct id was not returned")

        response = get_user_by_id(bridger_id)

        self.assertEqual(response, [], "user was deleted but was still in database")

        response = delete_store_by_id(store_id)



    


def db_teardown_test():
    response = delete_store_by_id(TestDAO.ids['store'])


    # def test_get_employees(self):
    #     response = get_store_employees(TestDAO.ids['store'])
    #     self.assertEqual(len(response), 2, "Incorrect number of employees returned should have been 2 but was " + str(len(response)) + "response " + str(response))

    # def test_get_admins(self):
    #     response = get_store_admins(TestDAO.ids['store'])
    #     self.assertEqual(len(response), 1, "Incorrect number of admins returned should have been 1 but was " + str(len(response)) + "response " + str(response))
        

    # def test_ban_person(self):
    #     image = cv2.imread("testBanned.jpg")
    #     _, buffer = cv2.imencode('.jpg', image)
    #     base64image = base64.b64encode(buffer).decode() 
    #     response = add_banned_person("Spencer", "598465", 874, TestDAO.ids['store'], 'now()', "TRUE", "An absolute literal clown", base64image)
    #     TestDAO.ids['spencer'] = response['id']
    #     self.assertEqual(response["full_name"], "Spencer", "Spencer was not added " + str(response))

    #     image = cv2.imread("testBanned2.jpg")
    #     _, buffer = cv2.imencode('.jpg', image)
    #     base64image = base64.b64encode(buffer).decode() 
    #     response = add_banned_person("Anton", "000001", 3, TestDAO.ids['store'], 'now()', "False", "Speed Racer", base64image)
    #     TestDAO.ids['anton'] = response['id']
    #     self.assertEqual(response["full_name"], "Anton", "Anton was not added " + str(response))

    #     image = cv2.imread("testBanned3.jpg")
    #     _, buffer = cv2.imencode('.jpg', image)
    #     base64image = base64.b64encode(buffer).decode() 
    #     response = add_banned_person("Charlie", "0154", 58, 1, 'now()', "False", "Hardened criminal", base64image)
    #     TestDAO.ids['charlie'] = response['id']
    #     self.assertEqual(response["full_name"], "Charlie", "Charlie was not added " + str(response))

    # def test_get_banned_person(self):
    #     response = get_banned_person(TestDAO.ids['anton'])
    #     self.assertEqual(response['id'], TestDAO.ids['anton'], "Anton was not found")

    # def test_get_banned_person_by_store(self):
    #     response = get_people_banned_by_store(TestDAO.ids['store'])
    #     self.assertEqual(len(response), 2, "Incorrect number of banned people returned for a store should have been 2 but was " + str(len(response)) + "response " + str(response))
        

    # def test_get_all_banned(self):
    #     response = get_all_banned_people()
    #     self.assertGreater(len(response), 2, "Incorrect number of banned people returned for a store should have been more than 2 but was " + str(len(response)) + "response " + str(response))



if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    unittest.main()
