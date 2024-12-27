from __future__ import annotations

from dynaconf import Dynaconf
from loguru import logger as log

APP_SETTINGS = Dynaconf(
    environments=True,
    env="app",
    envvar_prefix="APP",
    settings_files=["settings.toml", ".secrets.toml"]
)

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
