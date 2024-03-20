# pylint: disable=R0913, R0903
"""
Interface for Alert
"""
class Alert:
    """
    The model of an alert
    """

    def __init__(self, alert_id, banned_person_id, banned_person_image, matched_frame, timestamp, description, alerted_store):
        self.alert_id = alert_id
        self.banned_person_id = banned_person_id
        self.banned_person_image = banned_person_image
        self.matched_frame = matched_frame
        self.timestamp = timestamp
        self.description = description
        self.alerted_store = alerted_store

    def __str__(self):
        return f'Alert: {self.alert_id}, \
            bannedPersonId: {self.banned_person_id}, \
            Image: {self.banned_person_image}, \
            matchedFrame: {self.matched_frame}, \
            timestamp: {self.timestamp}, \
            description: {self.description}, \
            alertedStore: {self.alerted_store}'

