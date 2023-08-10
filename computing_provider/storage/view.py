import logging
import tomli
from os import path

from flask import Blueprint, jsonify, request

from computing_provider.computing_worker.tasks.build_space import (
    build_space_task,
    delete_space_task,
)
from computing_provider.obj_model.job import Job
from computing_provider.storage.service import create_job_from_job_detail, submit_job
from dotenv import load_dotenv

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, "./../../.env"))

logger = logging.getLogger(__name__)
storage_blueprint = Blueprint("storage", __name__)


@storage_blueprint.post('/api/v1/computing/lagrange/jobs')
def receive_job():
    job_data = request.json
    logging.info("Job received %s" % job_data)
    # TODO Async Processing the job
    result = process_job(job_data)
    return jsonify(result), 200


def process_job(job_data):

    job: Job = create_job_from_job_detail(job_data)
    space_name = job.job_source_uri.split('/')[-1]
    wallet_address = job.job_source_uri.split('/')[-2]
    task = build_space_task.delay(space_name, wallet_address)
    #job.job_result_uri = f"https://{app_name}.{domain}"
    port = task.get(timeout=120)
    logging.info(f"Final port: {port}")
    job.job_result_uri = f"http://localhost:{port}/"
    mcs_file = submit_job(job)
    return job.to_dict()


@storage_blueprint.get("/lagrange/space/<task_name>")
def build_space(task_name):
    """
    Goes out to the third-party Space API and downloads space
    """
    task = build_space_task.delay(task_name)
    logger.info(f"build spaces task task created! Task ID: {task!r}")
    task.wait(10)
    return jsonify({"taskId": task.id, "endPoint": f"http://localhost:{task.result}/"}), 202


@storage_blueprint.delete("/lagrange/space/<task_name>")
def delete_task(task_name):
    delete_space_task(task_name)

    return jsonify({"space_name": task_name}), 202

@storage_blueprint.post("/lagrange/jobs/renew")
def renew():
    import json
    print(request.get_json())

    return jsonify({"bid_status": "Reject"}), 200


@storage_blueprint.get("/hosts/info")
def ping():
    #TODO send back more info about the provider in the request. For now this is all we really need
    return jsonify({"status": "success"}), 200
        

@storage_blueprint.delete("/api/v1/computing/lagrange/jobs")
def delete():
    data = request.get_data()
    logging.info(f"Received delete request {data}")
    logging.info(f"Received delete request {request.data}")
    return jsonify({"status": "success"}), 200
        