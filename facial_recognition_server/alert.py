# pylint: disable=C0413,E0401,C0301,R0913,C0103,W0718,W0612,W0613
"""
    Contains the code for sending alerts
"""
import time
import sys
import os
import base64
import uuid
import resend
import boto3

from twilio.rest import Client
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
AWS_ACCESS_S3_KEY = os.getenv('AWS_ACCESS_S3_KEY')
AWS_SECRET_ACCESS_S3_KEY = os.getenv('AWS_SECRET_ACCESS_S3_KEY')


def notify(match_image, first_frame, match_person, device_id, mode="EMAIL", test_mode=False):
    """Notifies the necessary parties that the person is in the store"""

    if not test_mode:
        alert = Alert(
            alert_id=None,
            banned_person_id=match_person.id,
            banned_person_image=match_image,
            matched_frame=first_frame,
            timestamp=None,
            description=None,
            alerted_store=461) # to do get the store id from the device id

        log_alert(alert)

    employees = get_store_employees_from_device(device_id)

    if test_mode:
        employees = [employees[0]]

    if mode == "EMAIL":
        send_email(match_image, first_frame, match_person, employees)
        return
    if mode == "TEXT":
        send_notification(match_image, first_frame, match_person, employees)
        return
    if mode == "IN_APP":
        print("Notify mode not setup yet")
        return

    print("Notify mode not valid")
    return

def upload_to_s3(bucket_name, image_base64, object_name):
    """
    Upload a base64 image to S3 bucket.

    :param bucket_name: str - Name of the S3 bucket
    :param image_base64: str - Base64 encoded image data
    :param object_name: str - Object name under which the image will be saved in the bucket
    """
    # Initialize a session using your credentials
    session = boto3.Session(
        aws_access_key_id = AWS_ACCESS_S3_KEY,
        aws_secret_access_key= AWS_SECRET_ACCESS_S3_KEY,
        region_name='us-west-1',
    )

    # Create an S3 client
    s3 = session.client('s3')
    try:
        # Decode the base64 string
        image_data = base64.b64decode(image_base64)

        # Upload the image data to S3
        s3.put_object(
                Bucket=bucket_name,
                Key=object_name,
                Body=image_data,
                ContentType='image/jpeg'
            )

        print(f"Image uploaded successfully to {bucket_name}/{object_name}")
    except Exception as e:
        print(f"An error occurred: {e}")

    return f"https://s3.us-west-1.amazonaws.com/{bucket_name}/{object_name}"

def send_text_message(phone_number, first_frame_url, match_image_url):
    """Sends a text message alert with attached images for shoplifter identification."""
    account_sid = 'AC6f6e11855f474741f2184e6fea00b501'
    auth_token = '3b535f114ccbd896ab9b19b3a629a9b7'
    client = Client(account_sid, auth_token)

    message = client.messages.create(
    from_='+18889917482',
    body="Rooster Security Alert: A potential Match has been identified in your store.\n\nPlease review the images and confirm the match.\n\nWatchlisted person:",
    to=phone_number,
    )
    message = client.messages.create(
    from_='+18889917482',
    body="Image from security camera:",
    to=phone_number,
    media_url=match_image_url
    )
    message = client.messages.create(
    from_='+18889917482',
    body="Are these a match? Remeber that false matches are possible.\n\nText STOP to unsubscribe from alerts.",
    to=phone_number,
    media_url=first_frame_url
    )

def delete_s3_object(bucket_name, key):
    """delete an object from an S3 bucket"""
    # Initialize a session (optional step, depends on your setup)
    session = boto3.Session(
        aws_access_key_id = AWS_ACCESS_S3_KEY,
        aws_secret_access_key= AWS_SECRET_ACCESS_S3_KEY,
        region_name='us-west-1',
    )
    s3 = session.client('s3')

    # Delete the object
    response = s3.delete_object(Bucket=bucket_name, Key=key)
    return response



def send_notification(match_image, first_frame, match_person, employees):
    """Sends a text message alert with attached images for shoplifter identification."""

    # add images to s3 bucket
    bucket_name = 'rooster.test.image'
    match_object_name = f"m{str(uuid.uuid4())}.jpg"
    first_frame_object_name = f"f{str(uuid.uuid4())}.jpg"


    first_frame_url = upload_to_s3(bucket_name, first_frame, first_frame_object_name)
    match_image_url = upload_to_s3(bucket_name, match_image, match_object_name)

    # get correct phone numbers
    phone_numbers = []
    for employee in employees:
        if employee.phone_number:
            phone_numbers.append(f"+{employee.phone_number}")


    # send text message
    for number in phone_numbers:
        send_text_message([number], first_frame_url, match_image_url)

    # wait some amount of time
    time.sleep(30)

    # remove images from s3 bucket
    delete_s3_object(bucket_name, match_object_name)
    delete_s3_object(bucket_name, first_frame_object_name)


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

if __name__ == "__main__":
    # get path
    cur_dir = os.path.dirname(__file__)
    # encode image to base64
    with open(f"{cur_dir}/Headshot.JPG", "rb") as db_image_file:
        db_image = base64.b64encode(db_image_file.read())
    with open(f"{cur_dir}/20220624_162839.jpg", "rb") as first_frame_file:
        first_frame_ = base64.b64encode(first_frame_file.read())
    banned_person = {
        "id": 1,
        "full_name": "John Doe",
        "drivers_license": "123456789",
        "est_value_stolen": "$100",
        "reporting_store_id": 461,
    }

    notify(db_image, first_frame_, None, 4, mode="TEXT", test_mode=True)
    # send_warning_email("This is a test warning email")
    # notify("test", "test", "test", "
