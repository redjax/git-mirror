from loguru import logger as log
from dynaconf import Dynaconf

LOGGING_SETTINGS = Dynaconf(
    environments=True,
    env="logging",
    envvar_prefix="LOG",
    settings_files=["settings.toml", ".secrets.toml"]
)

GIT_MIRROR_SETTINGS = Dynaconf(
    environments=True,
    env="git",
    envvar_prefix="GIT",
    settings_files=["settings.toml", ".secrets.toml"]
)
