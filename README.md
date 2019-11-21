# Design

![Alt ecs fargate spark job](docs/images/sparkjob.jpg?raw=true "Architecture")


# Unit Testing

Ensure you have docker before executing the following commands.

Unit testing, PEP8 checks and other lint checks:

    ./bin/pod.sh tox

To run only unit test:

    ./bin/pod.sh tox -e py36

