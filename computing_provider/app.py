import logging
import os
from os import path

from flask import Flask

from computing_provider.api.celery_status import celery_task_status_blueprint
from computing_provider.boot import cp_register



def create_app():
    """
    Create a Flask application using the app factory pattern.

    :return: Flask app
    """
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
        datefmt="%m-%d %H:%M",
        handlers=[
            logging.FileHandler("flask_celery_redis_api.log"),
            logging.StreamHandler(),
        ],
    )

    app = Flask(
        __name__,
        instance_relative_config=True,
    )

    app.config.from_pyfile("settings.py", silent=True)
    app.jinja_env.auto_reload = True
    from computing_provider.storage.view import storage_blueprint
    app.register_blueprint(celery_task_status_blueprint)
    app.register_blueprint(storage_blueprint)
    cp_register()
    return app
