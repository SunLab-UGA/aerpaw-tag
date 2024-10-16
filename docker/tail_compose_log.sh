#!/bin/sh

# This script tails the logs of the containers in the docker compose file

docker compose logs -f --tail=10