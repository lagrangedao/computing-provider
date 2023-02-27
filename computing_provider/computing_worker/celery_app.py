import logging

from celery import Celery
from kombu import Queue, Exchange

from computing_provider.computing_worker import celeryconfig
from computing_provider.computing_worker.celeryconfig import DOWNLOAD_POKEMON_SPRITE_QUEUE, BUILD_SPACE_QUEUE

logging.basicConfig(
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
    datefmt="%m-%d %H:%M",
    handlers=[
        logging.FileHandler("flask_celery_redis_celery_worker.log"),
        logging.StreamHandler(),
    ],
)

celery_app = Celery()
celery_app.config_from_object(celeryconfig)
celery_app.conf.task_queues = (
    Queue(
        name=DOWNLOAD_POKEMON_SPRITE_QUEUE,
        exchange=Exchange(DOWNLOAD_POKEMON_SPRITE_QUEUE),
        routing_key=DOWNLOAD_POKEMON_SPRITE_QUEUE,
    ),
    Queue(
        name=BUILD_SPACE_QUEUE,
        exchange=Exchange(BUILD_SPACE_QUEUE),
        routing_key=BUILD_SPACE_QUEUE,
    ),
)
