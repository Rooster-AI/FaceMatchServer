FROM python:3.9

WORKDIR .

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install opencv-python-headless

# TO DO: fix this so that it only copies the necessary files
COPY . .

EXPOSE 5000:5000

CMD ["python", "facial-recognition-server/server.py"]