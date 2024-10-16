#!/bin/bash

# Remove all containers associated with the application
# We clean up with the .env variable COMPOSE_PROJECT_NAME=aerpaw_tag

PROJECT_NAME="aerpaw_tag"

echo "Stopping and removing all project containers"
docker compose -p $PROJECT_NAME down

# optinally remove all images (untested)
# echo "Removing all project images"
# docker image prune -f --filter label=com.docker.compose.project=$PROJECT_NAME

# optinally remove all volumes (untested) they are persistent so we just need to rm -rf the volume directory
# echo "Removing all project volumes"
# rm -rf ./docker_volumes

# nuke it from orbit (remove all containers, images, volumes, caches, and networks)
# docker system prune -a -f --volumes