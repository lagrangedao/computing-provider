import logging
import os
import subprocess

import docker
from celery import states
from celery.exceptions import Ignore
import requests

from flask_celery_redis.celery.celery_app import celery_app
from flask_celery_redis.celery.tasks.docker_service import Docker

logger = logging.getLogger(__name__)
DOCKER_BUILD_SPACE_TASK = "build_space_task"


@celery_app.task(name=DOCKER_BUILD_SPACE_TASK, bind=True)
def build_space_task(self, space_name):
    logger.info(
        f"Attempting to download spaces from Lagrange. spaces name:{space_name}"
    )
    space_api_response = requests.get(f"http://18.221.71.211:5000/spaces/{space_name}")
    logger.info(f"Space API response received. Response: {space_api_response.status_code}")

    if not space_api_response.ok:
        logger.warning(f"Updating Celery task to FAILED state!")

        self.update_state(
            state=states.FAILURE,
            meta=f"Space API response not OK. Status Code: {space_api_response.status_code}",
        )
        raise Exception("Space not found!")

    space_json = space_api_response.json()
    files = space_json['data']['files']
    build_folder = 'flask_celery_redis/static/build/0x96216849c49358B10257cb55b28eA603c874b05E/spaces/hello_world/'
    for file in files:
        dir_path = os.path.dirname(file['name'])

        os.makedirs(build_folder + dir_path, exist_ok=True)
        with open(build_folder + file['name'], "wb") as f:
            f.write(requests.get(file['url']).content)
    logger.info("Download %s successfully."%space_name)

    # start build
    # client = docker.from_env()
    # for image in client.images.list():
    #     print(image.id)
    # WARNING: We assume that you tagged your images correctly!!!
    # It should be formatted like `user/repository` as per Docker Hub!!
    image_path = build_folder
    repository = 'nbaicloud/'+space_name
    registry = 'docker.io'
    docker_client = Docker(registry)
    docker_client.build(path=image_path, repository=repository)
    docker_client.push(repository)
    # build_cmd=['docker' ,'build', '-t' ,repository,image_path]
    # result = subprocess.Popen(" ".join(build_cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    # print(result.stdout.readline())
    # print(result.stderr.readline())
