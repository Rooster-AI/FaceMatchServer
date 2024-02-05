import os
from supabaseDAO import add_user

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    print("hello there")
    add_user("Bridger", "b@example.com", "121", True, 1)