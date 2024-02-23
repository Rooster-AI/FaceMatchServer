#!/bin/bash

# Stop all docker containers
docker stop $(docker ps -q)

# Start the Docker container
docker run -d -p 5000:5000 --restart always rooster-server

