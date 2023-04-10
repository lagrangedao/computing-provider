import os
from logging.config import dictConfig
from celery import Celery
from kombu import Queue, Exchange

from computing_provider.computing_worker import celeryconfig
from computing_provider.computing_worker.celeryconfig import  BUILD_SPACE_QUEUE

# debug settings
debug = eval(os.environ.get("DEBUG", "False"))
dictConfig({
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
        },
        "access": {
            "format": "%(message)s",
        }
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
        "email": {
            "class": "logging.handlers.SMTPHandler",
            "formatter": "default",
            "level": "ERROR",
            "mailhost": ("smtp.example.com", 587),
            "fromaddr": "devops@example.com",
            "toaddrs": ["receiver@example.com", "receiver2@example.com"],
            "subject": "Error Logs",
            "credentials": ("username", "password"),
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "default",
            "filename": "logs/gunicorn.error.log",
            "maxBytes": 10000,
            "backupCount": 10,
            "delay": "True",
        },
        "access_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "access",
            "filename": "logs/gunicorn.access.log",
            "maxBytes": 10000,
            "backupCount": 10,
            "delay": "True",
        }
    },
    "loggers": {
        "gunicorn.error": {
            "handlers": ["console"] if debug else ["console", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        "gunicorn.access": {
            "handlers": ["console"] if debug else ["console", "access_file"],
            "level": "INFO",
            "propagate": False,
        }
    },
    "root": {
        "level": "DEBUG" if debug else "INFO",
        "handlers": ["console"] if debug else ["console", ],
    }
})

celery_app = Celery()
celery_app.config_from_object(celeryconfig)
celery_app.conf.task_queues = (
    Queue(
        name=BUILD_SPACE_QUEUE,
        exchange=Exchange(BUILD_SPACE_QUEUE),
        routing_key=BUILD_SPACE_QUEUE,
    ),
)

