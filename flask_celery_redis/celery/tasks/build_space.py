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
    space_api_response = requests.get(f"http://api.lagrangedao.org/spaces/{space_name}")
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
    build_folder = 'flask_celery_redis/static/build/'
    if files:
        download_space_path = '/'.join(os.path.dirname(files[0]['name']).split('/')[0:2])
        for file in files:
            dir_path = os.path.dirname(file['name'])
            os.makedirs(build_folder + dir_path, exist_ok=True)
            with open(build_folder + file['name'], "wb") as f:
                f.write(requests.get(file['url']).content)
            logger.info("Download %s successfully." % space_name)

        image_path = os.path.join(build_folder, download_space_path, space_name)
        repository = 'nbaicloud/' + space_name
        registry = 'docker.io'
        logger.info('image path: %s' % image_path)
        docker_client = Docker(registry)
        docker_client.build(path=image_path, repository=repository)
        docker_client.push(repository)
        container = docker_client.api_client.create_container(
            repository, detach=True)
        logger.info('Create container: %s' % container.get('Id'))
        docker_client.api_client.start(container=container.get('Id'))

    else:
        logger.info("Space %s is not found." % space_name)


