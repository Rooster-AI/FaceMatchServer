import os
from supabaseDAO import add_user, get_user_by_id, delete_user_by_id

def db_test():
    response = add_user("Bridger", "b@example.com", "121", True, 1)
    response = get_user_by_id(response['id'])
    response = delete_user_by_id(response['id'])


if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    db_test()
