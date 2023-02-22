#### Lagrange Asynchronous Tasks  Pipeline

As a pipeline, the states are changing according to the build needs.

Standard build process:

* Webhook trigger
* Task creation
    * Task details from CID
    * Download the Space
    * Make build
    * Push to the remote docker hub
    * Clean up
        * build file
        * local cache
        * images

Manual started

```shell
gunicorn -c "python:config.gunicorn" --reload "flask_celery_redis.app:create_app()"
```

Start a worker

```shell
celery --app flask_celery_redis.celery.celery_app worker --loglevel "${CELERY_LOG_LEVEL:-INFO}"
```

Build all services:

```bash
docker-compose build
```

Start all serivces:

```bash
docker-compose up
```

Stop all serivces:

```bash
docker-compose stop
```

Once everything is up and running navigate to `http://127.0.0.1:8000 to test out the application in a browser!
