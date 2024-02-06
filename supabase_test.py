import os
from supabaseDAO import *

def db_test():
    # response = add_user("Bridger", "b@example.com", "121", True, 1)
    # response = get_user_by_id(response['id'])
    # response = delete_user_by_id(response['id'])

    # response = add_store("Rooster", "Startup building", "121")
    # response = get_store_by_id(response['id'])
    # response = delete_store_by_id(response['id'])
    # response = get_store_employees(1)
    response = get_store_admins(1)
    print(response)



if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    db_test()
