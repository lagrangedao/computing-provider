"""
An example which shows how to push images to a docker registry
using the docker module.

Before starting, you will need a `.env` file with the following:

::

    OUR_DOCKER_USERNAME=Unknown
    OUR_DOCKER_PASSWORD=Unknown
    OUR_DOCKER_EMAIL=Unknown

Author:
    - @funilrys
"""

import logging
import os

import docker
from dotenv import load_dotenv

DOCKER_API_CLIENT = docker.APIClient(base_url="unix://var/run/docker.sock")

REGISTRY = "docker.io"

# WARNING: We assume that you tagged your images correctly!!!
# It should be formatted like `user/repository` as per Docker Hub!!
IMAGE_TAG_NAME = "nbaicloud/hello_world"

# Let's load the `.env` file.
load_dotenv(".env")


def log_response(response: dict) -> None:
    """
    Given a response from the Docker client.
    We log it.

    :raise Exception:
        When an error is caught.
    """

    if "stream" in response:
        for line in response["stream"].splitlines():
            if line:
                logging.info(line)

    if "progressDetail" in response and "status" in response:
        if "id" in response and response["progressDetail"]:
            percentage = round(
                (response["progressDetail"]["current"] * 100)
                / response["progressDetail"]["total"],
                2,
            )

            logging.info(
                "%s (%s): %s/%s (%s%%)",
                response["status"],
                response["id"],
                response["progressDetail"]["current"],
                response["progressDetail"]["total"],
                percentage,
            )
        elif "id" in response:
            logging.info("%s (%s)", response["status"], response["id"])
        else:
            logging.info("%s", response["status"])
    elif "errorDetail" in response and response["errorDetail"]:
        raise Exception(response["errorDetail"]["message"])
    elif "status" in response:
        logging.info("%s", response["status"])


def get_credentials_from_env() -> dict:
    """
    Try to get the credentials from the environment variables.

    :return:
        {
            "username": str,
            "password": str,
            "email": str
        }
    """

    var2env: dict = {
        "username": "OUR_DOCKER_USERNAME",
        "password": "OUR_DOCKER_PASSWORD",
        "email": "OUR_DOCKER_EMAIL",
    }

    return {k: os.getenv(v, None) for k, v in var2env.items()}


def push_images(images: list, creds: dict) -> None:
    """
    Given credentials and a list of images to push, push the
    image to the declared registry.

    :param creds:
        The credentials to use.

    :param images:
        A list of images to push.
    """

    for image in images:
        for tag in image["RepoTags"]:
            publisher = DOCKER_API_CLIENT.push(
                repository=f"{REGISTRY}/{tag}",
                stream=True,
                decode=True,
                auth_config=creds,
            )

            for response in publisher:
                log_response(response)


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    credentials = get_credentials_from_env()

    login = DOCKER_API_CLIENT.login(
        credentials["username"],
        password=credentials["password"],
        email=credentials["password"],
        registry=REGISTRY,
        reauth=True,
    )

    client = docker.from_env()
    # for image in client.images.list():
    #     print(image.id)

    # image, build_logs = client.images.build(path='./hello_world',tag="test/hello_world", quiet=False)
    #
    # # Print the build logs to the console
    # for line in build_logs:
    #     print(line)

    # Print the ID of the built image
    # print("Image ID:", image.id)
    build_logs = DOCKER_API_CLIENT.build('./hello_world',tag="test/hello_world" ,quiet=False)
    for line in build_logs:
        print(line)
    # push_images(DOCKER_API_CLIENT.images(name=IMAGE_TAG_NAME), credentials)
