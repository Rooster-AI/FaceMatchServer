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
    return data[1][0]

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
    return data[1][0]

def delete_store_by_id(id):
    supabase = getClient()
    data, count = supabase.table('stores').delete().eq('id', id).execute()
    return data[1][0]

def get_store_employees(store_id):
    supabase = getClient()
    data, count = supabase.table('users').select('*, stores(id)').eq('stores.id', store_id).execute()
    return data[1]

def get_store_admins(store_id):
    supabase = getClient()
    data, count = supabase.table('users').select('*, stores(id)').eq('stores.id', store_id).eq('is_admin', 'TRUE').execute()
    return data[1]



# add banned_person

# add conviction



# add banned_person

# add conviction

# remove user

# remove store

# remove banned person

# find people banned by a store

# find admins in a store

# find employees in a store

# change banned_person_image

# add event to person

# get info about a banned person given id

