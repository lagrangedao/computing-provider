DOWNLOAD_POKEMON_SPRITE_QUEUE = "download_pokemon_sprite_queue"
BUILD_SPACE_QUEUE = "build_space_queue"


broker_url = "redis://127.0.0.1:6379/0"
imports = ["computing_provider.computing_worker.tasks.download_pokemon_sprite","computing_provider.computing_worker.tasks.build_space"]
result_backend = "db+sqlite:///results.db"
task_default_queue = DOWNLOAD_POKEMON_SPRITE_QUEUE
