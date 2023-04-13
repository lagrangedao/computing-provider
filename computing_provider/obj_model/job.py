class Job:
    def __init__(self, uuid, name, status, duration, hardware, job_source_uri, job_result_uri, storage_source,task_uuid,
                 created_at, updated_at):
        self.uuid = uuid
        self.name = name
        self.status = status
        self.duration = duration
        self.hardware = hardware
        self.job_source_uri = job_source_uri
        self.job_result_uri = job_result_uri
        self.storage_source = storage_source
        self.task_uuid=task_uuid
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "status": self.status,
            "duration": self.duration,
            "hardware": self.hardware,
            "job_source_uri": self.job_source_uri,
            "job_result_uri": self.job_result_uri,
            "storage_source": self.storage_source,
            "self.task_uuid":self.task_uuid,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
