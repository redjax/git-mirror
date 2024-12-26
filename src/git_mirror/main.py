from __future__ import annotations

import typing as t
import json
import sys
from pathlib import Path
import subprocess
import threading

from git_mirror.core import setup

from loguru import logger as log

def return_script_dir():
    script_dir = Path(__file__).resolve().parent
    log.debug(f"Script path: {script_dir}")
    
    return script_dir


def _stream_output(pipe, output_function):
    """Stream subprocess output line by line."""
    try:
        for line in iter(pipe.readline, ''):
            output_function(line)
    finally:
        pipe.close()

def run_command(command, cwd=None, stream=False):
    """
    Run a command and handle errors, with optional real-time output streaming.

    Args:
        command (list): The command to run as a list of arguments.
        cwd (str or Path, optional): The working directory to run the command in.
        stream (bool): If True, stream output in real time. If False, capture output.

    Returns:
        subprocess.CompletedProcess: The result of the subprocess call if stream=False.
        None: If stream=True (real-time streaming mode).
    """
    log.info(f"Running command: {' '.join(command)} in {cwd or Path.cwd()}")

    try:
        if stream:
            with subprocess.Popen(
                command,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
            ) as process:
                # Create threads to handle stdout and stderr concurrently
                stdout_thread = threading.Thread(target=_stream_output, args=(process.stdout, sys.stdout.write))
                stderr_thread = threading.Thread(target=_stream_output, args=(process.stderr, sys.stderr.write))
                
                stdout_thread.start()
                stderr_thread.start()

                # Wait for the process to complete
                process.wait()

                # Ensure threads finish
                stdout_thread.join()
                stderr_thread.join()

                # Check if the command was successful
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode, command)

            return None
        else:
            # Run the command and capture output
            result = subprocess.run(
                command, cwd=cwd, check=True, text=True, capture_output=True
            )
            if result.stdout:
                log.info(result.stdout)
            if result.stderr:
                log.info(result.stderr)
            return result
    except subprocess.CalledProcessError as e:
        log.error(f"Error running command: {' '.join(command)}. Details: {e.stderr}")
        raise
    except Exception as exc:
        msg = f"({type(exc).__name__}) Unhandled exception running command. Details: {exc}"
        log.error(msg)
        raise
    

def clone_mirror(src_url: str, dest_dir: t.Union[str, Path], stream: bool = True):
    """Clone a repository as a bare mirror."""
    log.info(f"Cloning repository {src_url} into {dest_dir}")
    
    try:
        run_command(["git", "clone", "--mirror", src_url, str(dest_dir)], stream=stream)
    except subprocess.CalledProcessError as e:
        log.error(f"Error cloning repository {src_url}: {e.stderr}")
        raise
    except Exception as exc:
        msg = f"({type(exc)}) Unhandled exception cloning repository. Details: {exc}"
        log.error(msg)
        
        raise


def set_push_remote(repo_dir: t.Union[str, Path], mirror_url: str, stream: bool = True):
    """Set the push URL for the repository."""
    log.info(f"Setting push remote URL to {mirror_url} in {repo_dir}")
    try:
        run_command(["git", "remote", "set-url", "--push", "origin", mirror_url], cwd=repo_dir, stream=stream)
    except subprocess.CalledProcessError as e:
        log.error(f"Error setting push remote URL: {e.stderr}")
        raise
    except Exception as exc:
        msg = f"({type(exc)}) Unhandled exception setting push remote URL. Details: {exc}"
        log.error(msg)
        
        raise


def push_mirror(repo_dir: t.Union[str, Path], stream: bool = True):
    """Push all branches and tags to the mirror repository."""
    log.info(f"Pushing all branches and tags from {repo_dir}")
    try:
        run_command(["git", "push", "--mirror"], cwd=repo_dir, stream=stream)
    except subprocess.CalledProcessError as e:
        log.error(f"Error pushing mirror: {e.stderr}")
        raise
    except Exception as exc:
        msg = f"({type(exc)}) Unhandled exception pushing mirror. Details: {exc}"
        log.error(msg)
        
        raise


def update_mirror(repo_dir: t.Union[str, Path], stream: bool = True):
    """Update the mirror by fetching and pushing changes."""
    log.info(f"Updating mirror for {repo_dir}")
    
    log.info("Fetching changes from remote")
    try:
        run_command(["git", "fetch", "-p", "origin"], cwd=repo_dir, stream=stream)
    except subprocess.CalledProcessError as e:
        log.error(f"Error fetching changes: {e.stderr}")
        raise
    except Exception as exc:
        msg = f"({type(exc)}) Unhandled exception fetching changes. Details: {exc}"
        log.error(msg)
        
        raise
    
    log.info("Pushing changes to remote")
    try:
        run_command(["git", "push", "--mirror"], cwd=repo_dir, stream=stream)
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
