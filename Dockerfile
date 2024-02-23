FROM python:3.9

WORKDIR .

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install opencv-python-headless
RUN pip install gunicorn

# TO DO: fix this so that it only copies the necessary files
COPY . .

EXPOSE 5000:5000

CMD ["sh", "-c", "python facial_recognition_server/rooster_update.py && gunicorn --workers 2 --bind 0.0.0.0:5000 server:app --timeout 90"]