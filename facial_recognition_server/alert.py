# pylint: disable=C0413,E0401
"""
    Contains the code for sending alerts
"""

import sys
import os
import base64
import resend
from dotenv import load_dotenv

MAIN_DIR = os.path.dirname(__file__)
sys.path.append(MAIN_DIR)

# Parent imports
PAR_DIR = os.path.dirname(MAIN_DIR)
sys.path.append(PAR_DIR)
from models.alert import Alert
from supabase_dao import (
    get_store_employees,
    get_store_by_id,
    get_store_employees_from_device,
    log_alert,
)

load_dotenv()
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
resend.api_key = RESEND_API_KEY


def notify(match_image, first_frame, match_person, device_id, mode="EMAIL"):
    """Notifies the necessary parties that the person is in the store"""
    match_person.id = 8
    alert = Alert(None, match_person.id, match_image, None, None, 1)
    log_alert(alert)

    employees = get_store_employees_from_device(device_id)
    if mode == "EMAIL":
        send_email(match_image, first_frame, match_person, employees)
        return
    if mode == "TEXT":
        print("Notify mode not setup yet")
        return
    if mode == "IN_APP":
        print("Notify mode not setup yet")
        return

    print("Notify mode not valid")
    return


def send_email(match_image, first_frame, match_person, employees):
    """Sends an email alert with attached images for shoplifter identification."""

    # TO DO - Add the email address of the store owner to the "to" list
    # TO DO - Add the information of the match to the email content
    # print(match_image)

    emails = []
    for employee in employees:
        emails.append(employee.email)

    with open(os.path.join(MAIN_DIR, "roosterLogo.png"), "rb") as image_file:
        logo = base64.b64encode(image_file.read())

    info = ""
    if match_person.full_name:
        info += f"<p>Name: {match_person.full_name}</p>"

    if match_person.drivers_license:
        info += f"<p>Drivers License: {match_person.drivers_license}</p>"

    if match_person.est_value_stolen:
        info += f"<p>Estimated Value Stolen: {match_person.est_value_stolen}</p>"

    if match_person.description:
        info += f"<p>Description: {match_person.description}</p>"

    if match_person.report_date:
        info += f"<p>Report Date: {match_person.report_date}</p>"

    if match_person.reporting_store_id:
        reporting_store = get_store_by_id(match_person.reporting_store_id)
        info += f"<p>Reporting Store: {reporting_store.name}</p>"

    html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Rooster Identity Confirmation</title>
        <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #c22026; /* Adjusted to match logo color */
            color: #000000;
            padding: 20px;
        }}
        .email-container {{
            max-width: 600px;
            margin: 20px auto;
            padding: 20px;
            background-color: #ffffff;
            border: 1px solid #ddd;
            border-radius: 8px;
            text-align: center;
        }}
        .header {{
            background-color: #fff; /* Adjusted to match logo color */
            padding: 10px;
            text-align: center;
            border-radius: 8px 8px 0 0;
        }}
        .footer {{
            background-color: #c22026; /* Adjusted to match logo color */
            padding: 10px;
            text-align: center;
            border-radius: 0 0 8px 8px;
            color: #ffffff;
        }}
        .button {{
            display: inline-block;
            padding: 10px 20px;
            margin: 10px 0;
            background-color: #c22026;
            color: #ffffff !important;
            text-decoration: none;
            border-radius: 4px;
        }}
        a {{
            color: #ffffff !important;
            text-decoration: none;
        }}


        </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <img src="data:image/jpeg;base64,{logo.decode('utf-8')}" alt="Rooster Logo" class="image" width="100">
                </div>

                <h1>Confirm the Match</h1>
                <p>Please review the images below to confirm the identity of the individual:</p>
                <div>
                    <img src="data:image/jpeg;base64,{first_frame}" alt="Person in Store" class="image" style="margin-center: 10px;">
                    <img src="data:image/jpeg;base64,{match_image}" alt="Match" class="image" style="margin-center: 10px;">
                </div>
                <p>Is this a match?</p>
                <p>{info}</p>
                <div class="footer">
                    <p>Contact us for support at support@userooster.com</p>
                </div>
            </div>
        </body>
        </html>
    """
    # <a href="#" class="button">Yes, it's a match</a>
    # <a href="#" class="button">No, it's not a match</a>
    for email in emails:
        params = {
            "from": "Rooster <no-reply@alert.userooster.com>",
            "to": email,
            "subject": "Alert: Shoplifter Identified in Your Store",
            "html": html_content,
            # we may want to add the images as attachments,
            # but they were not working
            # "attachments": [
            #     {
            #         "name": "Person in Store.jpg",
            #         "content": first_frame.decode("utf-8"),
            #     },
            #     {
            #         "name": "Match.jpg",
            #         "content": match_image.decode("utf-8"),
            #     },
            # ],
        }
        resend.Emails.send(params)


def send_warning_email(message: str):
    """Sends a warning email to founders of rooster"""

    founders = get_store_employees(472)  # 472 is Rooster

    emails = []
    for employee in founders:
        emails.append(employee.email)

    html_content = f"<html><body>{message}</body></html>"

    for email in emails:
        params = {
            "from": "Rooster <no-reply@alert.userooster.com>",
            "to": email,
            "subject": "!!Rooster FOUNDERS: There is a problem!!",
            "html": html_content,
        }
        resend.Emails.send(params)
