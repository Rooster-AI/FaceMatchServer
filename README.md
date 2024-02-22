# Facial Recognition Server

## Introduction

This is the Rooster server-side code for facial recogntion and verification. This code will be deployed onto a cloud based server. This server is designed to provide efficient real-time matching capabilities. This server is designed to receive multiple image frames from a security camera and process those frames by looking for faces that match those in the Rooster database.

## Prerequisites

Before running this server, ensure you have the following dependencies installed:

- Python
- Required Python packages (listed in `requirements.txt`)

## Getting Started

1. Clone this repository to your local machine:

   ```shell
   git clone https://github.com/Rooster-AI/FaceMatchServer.git

2. Run setup.bash
3. Set Regular git pull and database download:
   a. crontab -e
   b. add this line to the file: 0 3 * * * /path/to/your/bash/update.sh
## Running Unit Tests

(python-env) -m unittest discover -s test

## Using Docker

1. Build the docker image
   - from the facial-recognition-server dir run
     '''shell
     docker build -t rooster-server .

2. Run th docker image
     '''shell
      run -p 5000:5000 -it rooster-server


## API

### POST: /upload-images
- headers: application/json
- body: {'images':['','']} // List of base64 encoded images

### POST: /add-banned-person
- headers: application/json
- body:
```json
{
   "full_name": "", 
   "drivers_license": "",
   "est_value_stolen": "", 
   "reporting_store_id": "",
   "is_private": "", 
   "description": "",
   "image_encoding":""
}
```

### GET: /latest_database?model=ArcFace&backend=mtcnn
- URL params are optional, those are the defaults
- If the server has not compiled with that model and backend, will return an errror
- Returns:
   - a .pkl file as as attachment containing the latest encoded database of faces


### API TODO
- /upload-images add store id to get the raspberry pi it was coming from
