#### Lagrange Asynchronous Tasks  Pipeline

As a pipeline, the states are changing according to the build needs.
![img.png](img.png)
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

Manual started Redis


```shell
 docker run -d --name computing_provider -p 6379:6379 redis/redis-stack-server:latest 
```

computing provider

```shell
sudo apt install -y gunicorn
```

```shell
gunicorn -c "python:config.gunicorn" --reload "computing_provider.app:create_app()" --log-level=info
```

Start a worker

```shell
sudo apt install -y python-celery-common 
```

```shell
celery --app computing_provider.computing_worker.celery_app worker --loglevel "${CELERY_LOG_LEVEL:-INFO}"
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

### Create a testing task

```shell
http://{{publisher_host}}/lagrange/space/hello_world
```
