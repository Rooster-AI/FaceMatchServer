"""
A seris of functions that interact with the Supabase database.
"""
from supabase import create_client
from models.banned_person import BannedPerson
from models.banned_person_image import BannedPersonImage
from models.user import User
from models.store import Store

url: str = "https://njmckcmrwmpmwdnfxxsj.supabase.co"
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5qbWNrY21yd21wbXdkbmZ4eHNqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MDcxNjQyOTEsImV4cCI6MjAyMjc0MDI5MX0.eVKm1TuiJ8E5qTt3FLlEnNjsLtbcBv0mx3g1bTA94Fw"

def get_client():
    """
    Get the Supabase client.

    Returns:
        Supabase client: The Supabase client object.
    """
    return create_client(url, key)

def add_user(user: User):
    """
    Add a user to the database. A user is an employee of a store.
    """
    supabase = get_client()
    data, _ = supabase.table('users').insert({
        'full_name': user.full_name,
        'email': user.email,
        'phone_number': user.phone_number,
        'is_admin': user.is_admin,
        'store_id': user.store_id,
        }).execute()
    user = User(data[1][0]['full_name'], data[1][0]['email'], data[1][0]['phone_number'],
                data[1][0]['is_admin'], data[1][0]['store_id'], data[1][0]['id'])

    return user

def get_user_by_id(user_id):
    """
    Get a user by their id
    """
    supabase = get_client()
    data, _ = supabase.table('users').select('*').eq('id', user_id).execute()

    user = None
    if len(data[1]) > 0:
        user = User(data[1][0]['full_name'], data[1][0]['email'], data[1][0]['phone_number'],
                    data[1][0]['is_admin'], data[1][0]['store_id'], data[1][0]['id'])

    return user

def delete_user_by_id(user_id):
    """
    Delete a user by their id
    """
    supabase = get_client()
    data, _ = supabase.table('users').delete().eq('id', user_id).execute()
    user = None
    if len(data[1]) > 0:
        user = User(data[1][0]['full_name'], data[1][0]['email'], data[1][0]['phone_number'],
                    data[1][0]['is_admin'], data[1][0]['store_id'], data[1][0]['id'])
    return user

def add_store(store: Store):
    """
    Add a store to the database
    """
    supabase = get_client()
    data, _ = supabase.table('stores').insert({
        'name': store.name,
        'address': store.address,
        'billing_info': store.billing_info,
        }).execute()

    store = Store(data[1][0]['name'], data[1][0]['address'], data[1][0]['billing_info'], data[1][0]['id'])
    return store

def get_store_by_id(store_id):
    """
    Get a store by its id
    """
    supabase = get_client()
    data, _ = supabase.table('stores').select('*').eq('id', store_id).execute()
    store = None
    if len(data[1]) > 0:
        store = Store(data[1][0]['name'], data[1][0]['address'], data[1][0]['billing_info'], data[1][0]['id'])

    return store

def delete_store_by_id(store_id):
    """
    Delete a store by its id.
    Doing this will also delete all employees of the store
    as well as all people banned by that store and their images
    """
    supabase = get_client()
    data, _ = supabase.table('stores').delete().eq('id', store_id).execute()

    store = Store(data[1][0]['name'], data[1][0]['address'], data[1][0]['billing_info'], data[1][0]['id'])
    return store

def get_store_employees(store_id):
    """
    Get all employees of a store
    """
    supabase = get_client()
    data, _ = supabase.table('users').select('*').eq('store_id', store_id).execute()
    employees = []
    for employee in data[1]:
        employee = User(employee['full_name'], employee['email'], employee['phone_number'],
                    employee['is_admin'], employee['store_id'], employee['id'])
        employees.append(employee)

    return employees

def get_store_admins(store_id):
    """
    Get those employees of a store that have admin permissions
    """
    supabase = get_client()
    data, _ = supabase.table('users').select('*') \
        .eq('store_id', store_id).eq('is_admin', 'TRUE').execute()

    admins = []
    for admin in data[1]:
        admin = User(admin['full_name'], admin['email'], admin['phone_number'],
                    admin['is_admin'], admin['store_id'], admin['id'])
        admins.append(admin)

    return admins

def add_banned_person(banned_person: BannedPerson, image):
    """
    Ban a person from a store. If is private is true, they are only banned from the 
    original reporting store. Verification is required to ban them from other stores.
    """
    supabase = get_client()
    data, _ = supabase.table('banned_person').insert({
        'full_name': banned_person.full_name,
        'license': banned_person.drivers_license,
        'est_value_stolen': banned_person.est_value_stolen,
        'reporting_store_id': banned_person.reporting_store_id,
        'report_date': banned_person.report_date,
        'is_private': banned_person.is_private,
        'description': banned_person.description,
        }).execute()
    banned_person_id = data[1][0]['id']

    banned_person_image = BannedPersonImage(banned_person_id, image)

    add_banned_person_image(banned_person_image)

    banned_person = BannedPerson(data[1][0]['full_name'], data[1][0]['license'],
                                data[1][0]['est_value_stolen'], data[1][0]['reporting_store_id'],
                                data[1][0]['report_date'], data[1][0]['is_private'],
                                data[1][0]['description'], data[1][0]['id'])

    return banned_person

def add_banned_person_image(banned_person_image: BannedPersonImage):
    """
    Add an image to an existing banned person. A banned person can have multiple images.
    """
    supabase = get_client()
    data, _ = supabase.table('banned_person_images').insert({
        'banned_person_id': banned_person_image.banned_person_id,
        'image': banned_person_image.image
    }).execute()

    banned_person_image = BannedPersonImage(data[1][0]['banned_person_id'], data[1][0]['image'], data[1][0]['id'])

    return banned_person_image

# remove banned person
def remove_banned_person_by_id(banned_person_id):
    """
    Remove a banned person from the database.
    This is set to cascade meaning that the images are removed as well
    """
    supabase = get_client()
    data, _ = supabase.table('banned_person').delete().eq('id', banned_person_id).execute()

    banned_person_image = BannedPersonImage(data[1][0]['banned_person_id'], data[1][0]['image'], data[1][0]['id'])

    return banned_person_image

# get a banned person by id
def get_banned_person(banned_person_id):
    """
    Get a banned person by their id
    """
    supabase = get_client()
    data, _ = supabase.table('banned_person').select('*').eq('id', banned_person_id).execute()

    banned_person = BannedPerson(data[1][0]['full_name'], data[1][0]['license'],
                                data[1][0]['est_value_stolen'], data[1][0]['reporting_store_id'],
                                data[1][0]['report_date'], data[1][0]['is_private'],
                                data[1][0]['description'], data[1][0]['id'])
    return banned_person

# get all banned people
def get_all_banned_people():
    """
    Get all banned people
    """
    supabase = get_client()
    data, _ = supabase.table('banned_person').select('*').execute()

    banned_people = []
    for banned_person in data[1]:
        banned_person = BannedPerson(banned_person['full_name'],
                                     banned_person['license'],
                                    banned_person['est_value_stolen'],
                                    banned_person['reporting_store_id'],
                                    banned_person['report_date'],
                                    banned_person['is_private'],
                                    banned_person['description'],
                                    banned_person['id'])
        banned_people.append(banned_person)

    return banned_people

# get all people banned by a store
def get_people_banned_by_store(store_id):
    """
    Get all people banned by a store
    """
    supabase = get_client()
    data, _ = supabase.table('banned_person').select('*') \
        .eq('reporting_store_id', store_id).execute()
    print(store_id)
    banned_people = []
    for banned_person in data[1]:
        banned_person = BannedPerson(banned_person['full_name'],
                                     banned_person['license'],
                                    banned_person['est_value_stolen'],
                                    banned_person['reporting_store_id'],
                                    banned_person['report_date'],
                                    banned_person['is_private'],
                                    banned_person['description'],
                                    banned_person['id'])
        banned_people.append(banned_person)

    return banned_people

# get all images of a banned person
def get_banned_person_images(banned_person_id):
    """
    Get all images of a banned person
    """
    supabase = get_client()
    data, _ = supabase.table('banned_person_images').select('*') \
        .eq('banned_person_id', banned_person_id).execute()

    banned_person_images = []
    for banned_person_image in data[1]:
        banned_person_image = BannedPersonImage(banned_person_image['banned_person_id'],
                                                banned_person_image['image'],
                                                banned_person_image['id'])
        banned_person_images.append(banned_person_image)

    return banned_person_images

# get all images of banned people
def get_all_banned_person_images():
    """
    Get all images of banned people. Used for the model training
    """
    supabase = get_client()
    data, _ = supabase.table('banned_person_images') \
        .select('*').execute()

    banned_person_images = []
    for banned_person_image in data[1]:
        banned_person_image = BannedPersonImage(banned_person_image['banned_person_id'],
                                                banned_person_image['image'],
                                                banned_person_image['id'])
        banned_person_images.append(banned_person_image)

    return banned_person_images

# remove image
def remove_banned_person_image_by_id(banned_person_id):
    """
    Remove an image of a banned person by the image id
    """
    supabase = get_client()
    data, _ = supabase.table('banned_person_images') \
        .delete().eq('id', banned_person_id).execute()

    banned_person_image = BannedPersonImage(data[1][0]['banned_person_id'], data[1][0]['image'], data[1][0]['id'])

    return banned_person_image

# update a banned person
def update_banned_person(banned_person: BannedPerson):
    """
    Update a banned person
    """
    supabase = get_client()
    data, _ = supabase.table('banned_person').update({
        'full_name': banned_person.full_name,
        'license': banned_person.drivers_license,
        'est_value_stolen': banned_person.est_value_stolen,
        'reporting_store_id': banned_person.reporting_store_id,
        'report_date': banned_person.report_date,
        'is_private': banned_person.is_private,
        'description': banned_person.description,
        }).eq('id', banned_person.banned_person_id).execute()
    
    banned_person = BannedPerson(data[1][0]['full_name'], data[1][0]['license'],
                                data[1][0]['est_value_stolen'], data[1][0]['reporting_store_id'],
                                data[1][0]['report_date'], data[1][0]['is_private'],
                                data[1][0]['description'], data[1][0]['id'])
    return banned_person

# add conviction

# add event to person
