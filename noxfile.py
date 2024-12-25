from __future__ import annotations

import logging
from pathlib import Path
import socket

import nox

log = logging.getLogger("nox")
logging.basicConfig(level="DEBUG", format="%(asctime)s %(levelname)s %(name)s:%(lineno)d %(message)s", datefmt="%Y-%m-%d %H:%M:%S")


# this VENV_DIR constant specifies the name of the dir that the `dev`
# session will create, containing the virtualenv;
# the `resolve()` makes it portable
VENV_DIR = Path("./.venv").resolve()


def install_uv_project(session: nox.Session, external: bool = False) -> None:
    """Method to install uv and the current project in a nox session."""
    log.info("Installing uv in session")
    session.install("uv")
    log.info("Syncing uv project")
    session.run("uv", "sync", external=external)
    log.info("Installing project")
    session.run("uv", "pip", "install", ".", external=external)


def find_free_port(start_port=8000) -> int:
    """Find a free port starting from a specific port number."""
    port = start_port
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("0.0.0.0", port))
                return port
            except socket.error:
                log.info(f"Port {port} is in use, trying the next port.")
                port += 1
                

@nox.session(name="ruff-lint")
def ruff_lint(session: nox.Session):
    log.info("Installing ruff")
    session.install("ruff")
    
    log.info("Checking code with ruff")
    session.run("ruff", "check", ".", "--fix")
    session.run("ruff", "check", "./noxfile.py", "--fix")
