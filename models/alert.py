# pylint: disable=R0913, R0903
"""
Interface for Alert
"""
class Alert:
    """
    The model of an alert
    """
    def __init__(self, alert_id, banned_person_id, image, timestamp, description, alerted_store):
        self.alert_id = alert_id
        self.banned_person_id = banned_person_id
        self.image = image
        self.timestamp = timestamp
        self.description = description
        self.alerted_store = alerted_store
