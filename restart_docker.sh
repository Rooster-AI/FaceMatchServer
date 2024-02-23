#!/bin/bash

# Get the directory of the script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Change to the directory of the script
cd "$DIR"

# Stop all docker containers
docker stop $(docker ps -q)

git pull

# Rebuild
docker build -t rooster-server .

# Start the Docker container
docker run -d -p 5000:5000 --restart always rooster-server

