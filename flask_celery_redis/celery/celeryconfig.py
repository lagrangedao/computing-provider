DOWNLOAD_POKEMON_SPRITE_QUEUE = "download_pokemon_sprite_queue"
BUILD_SPACE_QUEUE = "build_space_queue"


broker_url = "redis://127.0.0.1:6379/0"
imports = ["flask_celery_redis.celery.tasks.download_pokemon_sprite","flask_celery_redis.celery.tasks.build_space"]
result_backend = "db+sqlite:///results.db"
task_default_queue = DOWNLOAD_POKEMON_SPRITE_QUEUE
