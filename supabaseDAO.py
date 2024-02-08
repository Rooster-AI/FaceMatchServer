import os
from supabase import create_client, Client

url: str = "https://njmckcmrwmpmwdnfxxsj.supabase.co"
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5qbWNrY21yd21wbXdkbmZ4eHNqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MDcxNjQyOTEsImV4cCI6MjAyMjc0MDI5MX0.eVKm1TuiJ8E5qTt3FLlEnNjsLtbcBv0mx3g1bTA94Fw"

def getClient():
    return create_client(url, key)

# add user
def add_user(full_name, email, phone_number, is_admin, store_id):
    supabase = getClient()
    data, count = supabase.table('users').insert({
        'full_name': full_name,
        'email': email,
        'phone_number': phone_number,
        'is_admin': is_admin,
        'store_id': store_id,
        }).execute()
    return data[1][0]

def get_user_by_id(id):
    supabase = getClient()
    data, count = supabase.table('users').select('*').eq('id', id).execute()
    print(data[1])
    if len(data[1]) > 0:
        return data[1][0]
    else:
        return data[1]

def delete_user_by_id(id):
    supabase = getClient()
    data, count = supabase.table('users').delete().eq('id', id).execute()
    return data[1][0]

# add store
def add_store(name, address, billing_info):
    supabase = getClient()
    data, count = supabase.table('stores').insert({
        'name': name,
        'address': address,
        'billing_info': billing_info,
        }).execute()
    return data[1][0]

def get_store_by_id(id):
    supabase = getClient()
    data, count = supabase.table('stores').select('*').eq('id', id).execute()
    if len(data[1]) > 0:
        return data[1][0]
    else:
        return data[1]

def delete_store_by_id(id):
    supabase = getClient()
    data, count = supabase.table('stores').delete().eq('id', id).execute()
    return data[1][0]

def get_store_employees(store_id):
    supabase = getClient()
    data, count = supabase.table('users').select('*').eq('store_id', store_id).execute()
    return data[1]

def get_store_admins(store_id):
    supabase = getClient()
    data, count = supabase.table('users').select('*').eq('store_id', store_id).eq('is_admin', 'TRUE').execute()
    return data[1]

def add_banned_person(full_name, license, est_value_stolen, reporting_store_id, report_date, is_private, description, image):
    supabase = getClient()
    data, count = supabase.table('banned_person').insert({
        'full_name': full_name,
        'license': license,
        'est_value_stolen': est_value_stolen,
        'reporting_store_id': reporting_store_id,
        'report_date': report_date,
        'is_private': is_private,
        'description': description,
        }).execute()
    id = data[1][0]['id']

    response = supabase.table('banned_person_images').insert({
        'banned_person_id': id,
        'image': image
    }).execute()

    return data[1][0]

# remove banned person
def remove_banned_person_by_id(id):  
    supabase = getClient()
    data, count = supabase.table('banned_person').delete().eq('id', id).execute()
    return data[1][0]

# get a banned person by id
def get_banned_person(id):
    supabase = getClient()
    data, count = supabase.table('banned_person').select('*').eq('id', id).execute()
    return data
   

# get all banned people
def get_all_banned_people():
    supabase = getClient()
    data, count = supabase.table('banned_person').select('*').execute()

# get all people banned by a store
def get_people_banned_by_store(store_id):
    supabase = getClient()
    data, count = supabase.table('banned_person').select('*').eq('reporting_store_id', store_id).execute()
    return data

# get all images of banned people

# get all images of a banned person

# remove image

# add image

# update a person banned by a store

# add conviction

# change banned_person_image

# add event to person

