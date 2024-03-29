"""
An example which shows how to push images to a docker registry
using the docker module.

Before starting, you will need a `.env` storage with the following:

OUR_DOCKER_USERNAME=Unknown
OUR_DOCKER_PASSWORD=Unknown
OUR_DOCKER_EMAIL=Unknown

Author:
    - @claydrone
"""
import os
import json
import logging
import re
import docker
from dotenv import load_dotenv

# Let's load the `.env` storage.


log = logging.getLogger(__name__)


class StreamLineBuildGenerator(object):
    def __init__(self, json_data):
        self.__dict__ = json.loads(json_data)


class Docker(object):

    def __init__(self, registry_url):
        load_dotenv(".env")
        # self.client = docker.from_env()
        self.api_client = docker.APIClient(base_url="unix://var/run/docker.sock")
        self.registry = registry_url

    def get_credentials_from_env(self) -> dict:
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

    def log_response(self, response: dict) -> None:
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

    def build(self, path, tag):
        output = self.api_client.build(path=path, tag=tag)
        self._process_output(output)
        log.info("done building {}".format(tag))

    def push(self, repository, tag):
        publisher = self.api_client.push(repository=repository,
                                         tag=tag,
                                         stream=True,
                                         decode=True, auth_config=self.get_credentials_from_env()
                                         )
        for response in publisher:
            self.log_response(response)
        log.info("done pushing {}".format(repository + ":" + tag))

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

    # client = docker.from_env()
    # for image in client.images.list():
    #     print(image.id)
    # WARNING: We assume that you tagged your images correctly!!!
    # It should be formatted like `user/repository` as per Docker Hub!!
    IMAGE_TAG_NAME = "nbaicloud/hello_world"
    IMAGE_PATH = 'computing_provider/static/build/0x96216849c49358B10257cb55b28eA603c874b05E/spaces/hello_world/hello_world'
    repository = 'nbaicloud/hello_world'
    registry = 'docker.io'
    docker_client = Docker(registry)
    docker_client.build(path=IMAGE_PATH, repository=repository, tag="latest")
    docker_client.push(repository, "latest")
    container_id = docker_client.api_client.create_container(
        'busybox', 'ls', ports=[1111, 2222],
        host_config=docker_client.api_client.create_host_config(port_bindings={
            1111: 4567,
            2222: None
        })
    )
