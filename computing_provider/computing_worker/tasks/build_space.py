import logging
import os
import time
import requests
import re
import tomli
import docker

from celery import states
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
def build_space_task(self, space_name, wallet_address):
    logger.info(
        f"Attempting to download spaces from Lagrange. spaces name and wallet: {space_name}, {wallet_address}"
    )
    space_api_response = requests.get(f"http://127.0.0.1:5002/spaces/{wallet_address}/{space_name}")
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
        try:
            download_space_path = '/'.join(os.path.dirname(files[0]['name']).split('/')[0:2])
            for file in files:
                dir_path = os.path.dirname(file['name'])
                os.makedirs(build_folder + dir_path, exist_ok=True)
                with open(build_folder + file['name'], "wb") as f:
                    f.write(requests.get(file['url']).content)
                logger.info("Download %s successfully." % space_name)

            image_path = os.path.join(build_folder, download_space_path, space_name)
            space_name = f"{space_name.lower()}-{wallet_address.lower()}"
            repository = 'nebulablock/' + space_name
            registry = 'docker.io'
            # use timestamp as image tag
            tag = str(int(time.time()))
            image = repository + ":" + tag
            logger.info('image path: %s' % image_path)
            docker_client = Docker(registry)
            docker_client.build(image_path, image)
            #docker_client.push(repository, tag)

            dockerfile_path = image_path + "/Dockerfile"
            expose_pattern = r'^EXPOSE (\d+)$'
            with open(dockerfile_path, 'r') as f:
                dockerfile_content = f.read()

            # Find the exposed port in the Dockerfile content
            expose_match = re.search(expose_pattern, dockerfile_content, flags=re.MULTILINE)
            if expose_match:
                # Extract the port number from the match object
                exposed_port = int(expose_match.group(1))
                logger.info(f"The exposed port is {exposed_port}")
                container_port = exposed_port
            else:
                container_port = 7860
                logger.warning("No exposed port found in the Dockerfile, using default port 7680.")

            client = docker.from_env()
            host_port = get_random_port()
            port_bindings = {container_port: host_port}

            # Stop running containers on current port if any
            containers = client.containers.list(filters={'name': f"{wallet_address}-{space_name}"})

            for container in containers:
                container.stop()
                container.remove()

            logger.info(f"Creating container for {image} on port {host_port}")
            client.containers.run(
                image,
                detach=True,
                ports=port_bindings,
                name=f"{wallet_address}-{space_name}"
            )
            logger.info(f"Container created")
            logger.info(f"Final port: {host_port}")            
            return host_port
            container_name = "computing-worker"
            host_name = space_name + ".crosschain.computer"
            """             container = Container(container_name, image, container_port, host_port)
            logger.info(f"Loading kube config")
            config.load_kube_config()
            apps_v1 = client.AppsV1Api()
            core_v1_api = client.CoreV1Api()
            networking_v1_api = client.NetworkingV1Api()
            logger.info(f"Creating deployment object")
            deployment = create_deployment_object(container, space_name)
            # New task for existed Space
            if get_deployment(space_name):
                logging.info("Task already existed. Space name: %s" % space_name)
                update_deployment(apps_v1,deployment, space_name)
                logger.info('Deployment updated. Container name: %s' % container_name)
            # New task for new Space
            else:
                create_deployment(apps_v1, deployment)
                create_service(core_v1_api, container_port, space_name)
                create_ingress(networking_v1_api, container_port, space_name, host_name)

                logger.info('New deployment created. Container name: %s' % container_name) """

        except Exception as e:
            logger.error(e.message)
            logger.error(traceback.format_exc())
    else:
        logger.info("Space %s is not found." % space_name)
    
    logger.info(f"Final port: {host_port}")
    return host_port

