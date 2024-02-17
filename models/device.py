# pylint: disable=R0913,W0622,R0903
"""
A model for a device that mimics the database schema
device are our computers, like raspberry pi's, that are in the field
"""


class Device:
    """
    devices are associated with a store
    """

    def __init__(self, created_at, store_id, notes, id=None):
        self.store_id = store_id
        self.created_at = created_at
        self.notes = notes
        self.id = id

    def __str__(self):
        return f"Log: {self.store_id} {self.notes} \
        {self.id}"
