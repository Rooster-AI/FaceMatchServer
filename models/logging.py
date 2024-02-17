# pylint: disable=R0913,W0622,R0903
"""
A model for a logging row that mimics the database schema
"""


class Logging:
    """
    Each row in logging comes from devices logging info
    """

    def __init__(self, device_id, severity, message, id=None):
        self.device_id = device_id
        self.severity = severity
        self.message = message
        self.id = id

    def __str__(self):
        return f"Log: {self.device_id} {self.severity} \
        {self.message} {self.id}"
