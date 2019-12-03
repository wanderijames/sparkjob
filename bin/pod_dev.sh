#!/usr/bin/env bash
COMMAND="cd /usr/local/lib/jobs && $@"
image_name_="spark-xyz"

IMAGE_SEARCH=$(docker images | grep "${image_name_}")
if [ -z "$IMAGE_SEARCH" ]; then
    echo "Docker image ${image_name_} not found, building ...."
    docker build -t spark-xyz -f docker/spark/Dockerfile .
fi

docker run -t --rm --name dev -p 8888:8888 --volume=$(pwd):/usr/local/lib/jobs ${image_name_} bash -c "$COMMAND"
## Check if last command passed
#echo $?
