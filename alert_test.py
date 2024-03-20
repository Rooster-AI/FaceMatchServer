"""
simple code to test the add alert
"""
from models.alert import Alert
from facial_recognition_server.alert import notify
from supabase_dao import log_alert


def test_alert():
    alert = Alert(None, 779, "image", None, None, 1)
    print(alert)
    log_alert(alert)


if __name__ == "__main__":
    test_alert()
    # notify("image", "first_frame", "match_person", "device_id", "EMAIL")