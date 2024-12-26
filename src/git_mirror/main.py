from __future__ import annotations

import json
from pathlib import Path
import subprocess

from git_mirror.core import setup

from loguru import logger as log

def return_script_dir():
    script_dir = Path(__file__).resolve().parent
    log.debug(f"Script path: {script_dir}")
    
    return script_dir


def run_git_command(command, cwd=None):
    """Run a git command and handle errors."""
    try:
        log.info(f"Running command: {' '.join(command)} in {cwd or Path.cwd()}")
        result = subprocess.run(command, cwd=cwd, check=True, text=True, capture_output=True)
        if result.stdout:
            log.info(result.stdout)

        return result
    except subprocess.CalledProcessError as e:
        log.error(f"Error running command: {' '.join(command)}. Details: {e.stderr}")
        
        raise
    except Exception as exc:
        msg = f"({type(exc)}) Unhandled exception runnint git command. Details: {exc}"
        log.error(msg)
        
        raise

def clone_mirror(src_url, dest_dir):
    """Clone a repository as a bare mirror."""
    log.info(f"Cloning repository {src_url} into {dest_dir}")
    
    try:
        run_git_command(["git", "clone", "--mirror", src_url, str(dest_dir)])
    except subprocess.CalledProcessError as e:
        log.error(f"Error cloning repository {src_url}: {e.stderr}")
        raise
    except Exception as exc:
        msg = f"({type(exc)}) Unhandled exception cloning repository. Details: {exc}"
        log.error(msg)
        
        raise


def set_push_remote(repo_dir, mirror_url):
    """Set the push URL for the repository."""
    log.info(f"Setting push remote URL to {mirror_url} in {repo_dir}")
    try:
        run_git_command(["git", "remote", "set-url", "--push", "origin", mirror_url], cwd=repo_dir)
    except subprocess.CalledProcessError as e:
        log.error(f"Error setting push remote URL: {e.stderr}")
        raise
    except Exception as exc:
        msg = f"({type(exc)}) Unhandled exception setting push remote URL. Details: {exc}"
        log.error(msg)
        
        raise


def push_mirror(repo_dir):
    """Push all branches and tags to the mirror repository."""
    log.info(f"Pushing all branches and tags from {repo_dir}")
    try:
        run_git_command(["git", "push", "--mirror"], cwd=repo_dir)
    except subprocess.CalledProcessError as e:
        log.error(f"Error pushing mirror: {e.stderr}")
        raise
    except Exception as exc:
        msg = f"({type(exc)}) Unhandled exception pushing mirror. Details: {exc}"
        log.error(msg)
        
        raise


def update_mirror(repo_dir):
    """Update the mirror by fetching and pushing changes."""
    log.info(f"Updating mirror for {repo_dir}")
    
    log.info("Fetching changes from remote")
    try:
        run_git_command(["git", "fetch", "-p", "origin"], cwd=repo_dir)
    except subprocess.CalledProcessError as e:
        log.error(f"Error fetching changes: {e.stderr}")
        raise
    except Exception as exc:
        msg = f"({type(exc)}) Unhandled exception fetching changes. Details: {exc}"
        log.error(msg)
        
        raise
    
    log.info("Pushing changes to remote")
    try:
        run_git_command(["git", "push", "--mirror"], cwd=repo_dir)
    except subprocess.CalledProcessError as e:
        log.error(f"Error pushing changes: {e.stderr}")
        raise
    except Exception as exc:
        msg = f"({type(exc)}) Unhandled exception pushing changes. Details: {exc}"
        log.error(msg)
        
        raise

def load_mirrors(mirrors_file):
    """Load the mirrors configuration from a JSON file."""
    if not Path(str(mirrors_file)).exists():    
        log.error(f"Mirrors file not found: {mirrors_file}")
        raise FileNotFoundError(f"Mirrors file not found: {mirrors_file}")

    log.info(f"Loading mirrors from file: {mirrors_file}")
    try:
        with open(mirrors_file, "r") as f:
            return json.load(f)
    except Exception as e:
        log.error(f"Error loading mirrors from {mirrors_file}: {e}")
        raise

def process_repositories(mirrors, base_dir):
    """Process each repository to set up or update the mirror."""
    log.info(f"Mirroring [{len(mirrors)}] {'repositories' if len(mirrors) > 1 else 'repository'}.")

    base_path = Path(base_dir)
    base_path.mkdir(exist_ok=True)

    for mirror in mirrors:
        log.debug(f"Mirror source: {mirror['src']}, Mirror target: {mirror['mirror']}")
        try:
            src = mirror["src"]
            mirror_url = mirror["mirror"]
            print(f"Processing repository: {src}")

            repo_name = Path(src.split("/")[-1]).stem + ".git"  # Add .git suffix
            repo_dir = base_path / repo_name

            if not repo_dir.exists():
                clone_mirror(src, repo_dir)
                set_push_remote(repo_dir, mirror_url)
                push_mirror(repo_dir)
            else:
                log.info(f"Repository {repo_dir} already exists. Updating mirror...")
                update_mirror(repo_dir)

        except Exception as e:
            log.error(f"Error processing repository {src}: {e}")
            continue


if __name__ == "__main__":
    setup.setup_logging(log_level="DEBUG", add_file_logger=True, add_error_file_logger=True, colorize=True)
    
    log.info("Start git_mirror script")

    mirrors_path = Path("mirrors.json")
    base_dir = "repositories"

    try:
        mirrors = load_mirrors(mirrors_path)
        process_repositories(mirrors, base_dir)
    except Exception as e:
        print(f"Failed to process repositories: {e}")
