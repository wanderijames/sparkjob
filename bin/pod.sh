#!/usr/bin/env bash
COMMAND="cd /usr/local/lib/jobs && $@"
image_name_="wanderijames/spark:alpine"

docker run -t --rm --name job-tests --volume=$(pwd):/usr/local/lib/jobs ${image_name_} bash -c "$COMMAND"
## Check if last command passed
#echo $?
