import logging
import os

import requests
from kubernetes import client, config

from computing_provider.computing_worker.celery_app import celery_app
from computing_provider.computing_worker.tasks.docker_service import Docker
from computing_provider.computing_worker.tasks.k8s_service import *


logger = logging.getLogger(__name__)
BUILD_SPACE_TASK = "build_space_task"
DELETE_SPACE_TASK = "delete_space_task"

@celery_app.task(name=DELETE_SPACE_TASK, bind=True)
def delete_space_task(self, space_name):
    config.load_kube_config()
    apps_v1 = client.AppsV1Api()
    core_v1_api = client.CoreV1Api()
    networking_v1_api = client.NetworkingV1Api()
    delete_ingress(networking_v1_api, space_name)
    delete_service(core_v1_api, space_name)
    delete_deployment(apps_v1, space_name)


@celery_app.task(name=BUILD_SPACE_TASK, bind=True)
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
    build_folder = 'computing_provider/static/build/'
    if files:
        download_space_path = '/'.join(os.path.dirname(files[0]['name']).split('/')[0:2])
        for file in files:
            dir_path = os.path.dirname(file['name'])
            os.makedirs(build_folder + dir_path, exist_ok=True)
            with open(build_folder + file['name'], "wb") as f:
                f.write(requests.get(file['url']).content)
            logger.info("Download %s successfully." % space_name)

        image_path = os.path.join(build_folder, download_space_path, space_name)
        repository = 'nebulablock/' + space_name
        registry = 'docker.io'
        logger.info('image path: %s' % image_path)
        docker_client = Docker(registry)
        docker_client.build(path=image_path, repository=repository)
        docker_client.push(repository)

        container_name = "computing-worker"
        container_port = 7860
        host_port = get_random_port()
        host_name = space_name + ".crosschain.computer"
        container = Container(container_name, repository, container_port, host_port)
        config.load_kube_config()
        apps_v1 = client.AppsV1Api()
        core_v1_api = client.CoreV1Api()
        networking_v1_api = client.NetworkingV1Api()
        deployment = create_deployment_object(container, space_name)
        create_deployment(apps_v1, deployment)
        create_service(core_v1_api, container_port, space_name)
        create_ingress(networking_v1_api, container_port, space_name, host_name)

        logger.info('Container created: %s' % container_name)

        #container = docker_client.api_client.create_container(
        #    repository, detach=True)
        #logger.info('Create container: %s' % container.get('Id'))
        #docker_client.api_client.start(container=container.get('Id'))
    else:
        logger.info("Space %s is not found." % space_name)

