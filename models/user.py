# pylint: disable=R0913,W0622,R0903
"""
A model for a user that mimics the database schema
"""

class User:
    """
    A user is an employee of a store
    """
    def __init__(self, full_name, email, phone_number, is_admin, store_id, id=None):
        self.full_name = full_name
        self.email = email
        self.phone_number = phone_number
        self.is_admin = is_admin
        self.store_id = store_id
        self.id = id

    def __str__(self):
        return f"User: {self.full_name} {self.email} \
        {self.phone_number} {self.is_admin} {self.store_id} {self.id}"
