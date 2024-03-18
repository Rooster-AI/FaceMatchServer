"""
Interface for Alert
"""
class Alert:
    def __init__(self, alert_id, banned_person_id, image, timestamp, description, alerted_store):
        self.alert_id = alert_id
        self.banned_person_id = banned_person_id
        self.image = image
        self.timestamp = timestamp
        self.description = description
        self.alerted_store = 1

