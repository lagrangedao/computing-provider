import logging

from flask import Blueprint, jsonify, request

from computing_provider.computing_worker.tasks.build_space import (
    build_space_task,
    delete_space_task,
)

logger = logging.getLogger(__name__)
pokemon_blueprint = Blueprint("pokemon", __name__)


@pokemon_blueprint.post('/lagrange/jobs')
def receive_job():
    job_data = request.json
    logging.info("Job received %s" % job_data)
    # Process the job
    result = process_job(job_data)

    return jsonify(result), 200


def process_job(job_data):
    # Here, you can implement your custom logic to process the job_data
    # For demonstration purposes, we'll simply return the job_data as the result
    return job_data


@pokemon_blueprint.get("/lagrange/space/<task_name>")
def build_space(task_name):
    """
    Goes out to the third-party PokeAPI and downloads a sprite

    :param str pokemon_name: Name of the pokemon to download the sprite for
    :return: Task Id working on sprite retrieval, 202 status code
    """
    task = build_space_task.delay(task_name)
    logger.info(f"build spaces task task created! Task ID: {task!r}")

    return jsonify({"taskId": task.id, "endPoint": "https://" + task_name + ".crosschain.computer"}), 202


@pokemon_blueprint.delete("/lagrange/space/<task_name>")
def delete_task(task_name):
    delete_space_task(task_name)

    return jsonify({"space_name": task_name}), 202
