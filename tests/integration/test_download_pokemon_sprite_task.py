import pytest


from computing_provider.computing_worker.tasks.download_pokemon_sprite import (
    download_pokemon_sprite_task,
)


def test_download_pokemon_sprite_task_success():
    try:
        download_pokemon_sprite_task.run("squirtle")
    except Exception:
        assert False, "Unexpected error."


def test_download_pokemon_sprite_task_error():
    with pytest.raises(Exception):
        download_pokemon_sprite_task.run("squirtlee")
