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
