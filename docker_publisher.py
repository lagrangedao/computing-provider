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
import json
import logging
import os

import click
import docker
from dotenv import load_dotenv

DOCKER_API_CLIENT = docker.APIClient(base_url="unix://var/run/docker.sock")

REGISTRY = "docker.io"

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

import json
import logging
import re

import docker

log = logging.getLogger(__name__)


class StreamLineBuildGenerator(object):
    def __init__(self, json_data):
        self.__dict__ = json.loads(json_data)


class Docker(object):
    REGISTRY = "some_docker_registry"

    def __init__(self):
        self.client = docker.from_env()
        self.api_client = docker.APIClient()

    def build(self, path, repository):
        tag = "{}/{}".format(Docker.REGISTRY, repository)
        output = self.api_client.build(path=path, tag=tag)
        self._process_output(output)
        log.info("done building {}".format(repository))

    def push(self, repository):
        tag = "{}/{}".format(Docker.REGISTRY, repository)
        output = self.client.images.push(tag)
        self._process_output(output)
        log.info("done pushing {}".format(tag))

    def _process_output(self, output):
        if type(output) == str:
            output = output.split("\n")

        for line in output:
            if line:
                errors = set()
                try:
                    stream_line = StreamLineBuildGenerator(line)

                    if hasattr(stream_line, "status"):
                        log.info(stream_line.status)

                    elif hasattr(stream_line, "stream"):
                        stream = re.sub("^\n", "", stream_line.stream)
                        stream = re.sub("\n$", "", stream)
                        # found after newline to close (red) "error" blocks: 27 91 48 109
                        stream = re.sub("\n(\x1B\[0m)$", "\\1", stream)
                        if stream:
                            log.info(stream)

                    elif hasattr(stream_line, "aux"):
                        if hasattr(stream_line.aux, "Digest"):
                            log.info("digest: {}".format(stream_line.aux["Digest"]))

                        if hasattr(stream_line.aux, "ID"):
                            log.info("ID: {}".format(stream_line.aux["ID"]))

                    else:
                        log.info("not recognized (1): {}".format(line))

                    if hasattr(stream_line, "error"):
                        errors.add(stream_line.error)

                    if hasattr(stream_line, "errorDetail"):
                        errors.add(stream_line.errorDetail["message"])

                        if hasattr(stream_line.errorDetail, "code"):
                            error_code = stream_line.errorDetail["code"]
                            errors.add("Error code: {}".format(error_code))

                except ValueError as e:
                    log.error("not recognized (2): {}".format(line))

                if errors:
                    message = "problem executing Docker: {}".format(". ".join(errors))
                    raise SystemError(message)

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
    # WARNING: We assume that you tagged your images correctly!!!
    # It should be formatted like `user/repository` as per Docker Hub!!
    IMAGE_TAG_NAME = "nbaicloud/hello_world"
    IMAGE_PATH = './hello_world'
    image, build_logs = client.images.build(path=IMAGE_PATH,tag=IMAGE_TAG_NAME, quiet=False)
    print(image.id)
    #
    # # Print the build logs to the console
    # for line in build_logs:
    #     print(line)

    # Print the ID of the built image
    # print("Image ID:", image.id)
    generator = DOCKER_API_CLIENT.build(IMAGE_PATH, tag=IMAGE_TAG_NAME, rm=True)
    while True:
        try:
            output = generator.__next__
            output = output.strip('\r\n')
            json_output = json.loads(output)
            if 'stream' in json_output:
                click.echo(json_output['stream'].strip('\n'))
        except StopIteration:
            click.echo("Docker image build complete.")
            break
        except ValueError:
            click.echo("Error parsing output from docker image build: %s" % output)
    push_images(DOCKER_API_CLIENT.images(name=IMAGE_TAG_NAME), credentials)
