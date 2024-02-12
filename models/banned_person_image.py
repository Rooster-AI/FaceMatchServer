"""
A model of a banned person image that mimics the database schema
"""

class BannedPersonImage:
    """
    A banned person image is an image of a banned person
    """
    def __init__(self, banned_person_id, image_encoding, id=None):
        self.banned_person_id = banned_person_id
        self.image = image_encoding
        self.id = id

    def __str__(self):
        return f"BannedPersonImage: {self.banned_person_id} {self.image} {self.id}"
