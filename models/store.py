# pylint: disable=W0622,R0903
"""
A model for a store that mimics the database schema
"""

class Store:
    """
    A store that has cameras installed
    """
    def __init__(self, name, address, billing_info, id=None):
        self.id = id
        self.name = name
        self.address = address
        self.billing_info = billing_info

    def __str__(self):
        return f"Store: {self.name} {self.address} {self.billing_info} {self.id}"
