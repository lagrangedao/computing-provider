import json
import logging
import os
import time
import uuid
from typing import Dict

from computing_provider.constant import BIDDING_SUBMITTED
from computing_provider.obj_model.job import Job
from swan_mcs import APIClient, BucketAPI
from swan_mcs.object.bucket_storage import File


def upload_replace_file(file_path: str, bucket_name: str, dest_file_path: str) -> File:
    """
    Upload a file by file path, bucket name and the target path
    :rtype: object
    :param file_path: the source file path
    :param bucket_name: the bucket name user want to upload
    :param dest_file_path: the destination of the file you want to store exclude the bucket name
    :return: File Object
    """
    mcs_api = APIClient(os.getenv("MCS_API_KEY"), os.getenv("MCS_ACCESS_TOKEN"), "polygon.mainnet")
    bucket_client = BucketAPI(mcs_api)
    # check if file exist
    file_data = bucket_client.get_file(bucket_name, dest_file_path)
    if file_data:
        logging.info("File exist,replace file: %s", file_path)
        bucket_client.delete_file(bucket_name, dest_file_path)
    file_data: File = bucket_client.upload_file(bucket_name, dest_file_path, file_path)
    return file_data


def create_job_from_job_detail(job_detail: Dict) -> Job:
    logging.info("create_job_from_job_detail")
    uuid = job_detail.get('uuid')
    name = job_detail.get('name')
    status = job_detail.get('status')
    duration = job_detail.get('duration')
    hardware = job_detail.get('hardware')
    job_source_uri = job_detail.get('job_source_uri')
    job_result_uri = job_detail.get('job_result_uri')
    storage_source = job_detail.get('storage_source')
    task_uuid = job_detail.get('task_uuid')
    created_at = job_detail.get('created_at')
    updated_at = job_detail.get('updated_at')

    job = Job(uuid=uuid, name=name, status=status, duration=duration, hardware=hardware,
              job_source_uri=job_source_uri, job_result_uri=job_result_uri, storage_source=storage_source,
              created_at=created_at, task_uuid=task_uuid, updated_at=updated_at)

    return job


def submit_job(job: Job) -> File:
    logging.info("Submitting job...")
    folder_path = "jobs"
    job_detail_file_name = os.path.join(folder_path, str(uuid.uuid4()) + ".json")
    file_cache_path = os.getenv("FILE_CACHE_PATH")
    os.makedirs(os.path.join(file_cache_path, folder_path), exist_ok=True)
    task_detail_file_path = os.path.join(file_cache_path, job_detail_file_name)

    with open(task_detail_file_path, 'wb') as f:
        # Create the folder if it does not exist
        os.makedirs(folder_path, exist_ok=True)
        job.status = BIDDING_SUBMITTED
        job.updated_at = str(time.time())
        f.write(json.dumps(job.to_dict()).encode('utf-8'))

    mcs_file: File = upload_replace_file(task_detail_file_path, os.getenv("MCS_BUCKET"), job_detail_file_name)
    logging.info("Job submitted to IPFS %s" % mcs_file.to_json())

    job.job_result_uri = mcs_file.ipfs_url
    return mcs_file
