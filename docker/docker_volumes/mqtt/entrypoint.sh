#!/bin/sh

# Move data from the source directory to the mounted volume if the volume is empty

DATA_DIR="/app"
SOURCE_DIR="/usr/src/app/data"

# Check if the directory is empty
if [ ! "$(ls -A $DATA_DIR)" ]; then
  echo "Initializing, copying data from $SOURCE_DIR to $DATA_DIR"
  cp -r $SOURCE_DIR/* $DATA_DIR
fi
echo "Initialization Completed"

# After performing the copy, run the main process
exec "$@"