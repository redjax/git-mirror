from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import threading
import typing as t
import concurrent.futures

from git_mirror.core import APP_SETTINGS, GIT_MIRROR_SETTINGS, LOGGING_SETTINGS, setup

from loguru import logger as log

class GitNotInstalled(Exception):
    def __init__(self, message: str = None):
        ## Provide a default message if none is provided
        if message is None:
            message = f"git is not installed. Please install git (https://git-scm.com) before re-running this script."
        super().__init__(message)


def is_git_installed(raise_on_err: bool = False) -> bool:
    """Check if the 'git' command is available on the host system.

    Returns:
        bool: True if 'git' is installed, False otherwise.

    """
    try:
        # Run 'git --version' to check if Git is installed
        result = subprocess.run(
            ["git", "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        log.info(f"Git is installed: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        log.debug("Git is not installed or not found in PATH.")
        
        if raise_on_err:
            raise GitNotInstalled()
        else:
            return False
    except subprocess.CalledProcessError as e:
        log.debug(f"Git command failed: {e.stderr.strip()}")
        
        if raise_on_err:
            raise GitNotInstalled()
        else:    
            return False


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
    """Run a command and handle errors, with optional real-time output streaming.

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

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for mirror in mirrors:
            log.debug(f"Mirror source: {mirror['src']}, Mirror target: {mirror['mirror']}")
            try:
                src = mirror["src"]
                mirror_url = mirror["mirror"]
                print(f"Processing repository: {src}")

                repo_name = Path(src.split("/")[-1]).stem + ".git"  # Add .git suffix
                repo_dir = base_path / repo_name

                if not repo_dir.exists():
                    futures.append(executor.submit(clone_mirror, src, repo_dir))
                    futures.append(executor.submit(set_push_remote, repo_dir, mirror_url))
                    futures.append(executor.submit(push_mirror, repo_dir))
                else:
                    log.info(f"Repository {repo_dir} already exists. Updating mirror...")
                    futures.append(executor.submit(update_mirror, repo_dir))

            except Exception as e:
                log.error(f"Error processing repository {src}: {e}")
                continue

        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                log.error(f"Error running git operation: {e}")


def main(mirrors_file: str = GIT_MIRROR_SETTINGS.get("MIRRORS_FILE", default="<unset>"), repositories_dir: str = GIT_MIRROR_SETTINGS.get("REPOSITORIES_DIR", default="<unset>")):
    if not is_git_installed():
        raise GitNotInstalled

    try:
        mirrors = load_mirrors(mirrors_file)
        process_repositories(mirrors, repositories_dir)
    except Exception as e:
        print(f"Failed to process repositories: {e}")

if __name__ == "__main__":
    setup.setup_logging(log_level=LOGGING_SETTINGS.get("LOG_LEVEL", default="INFO"), add_file_logger=True, add_error_file_logger=True, colorize=True)
    
    mirrors_file_str: str = APP_SETTINGS.get("MIRRORS_FILE", default="mirrors.json")
    repositories_dir_str: str = APP_SETTINGS.get("REPOSITORIES_DIR", default="repositories")
    
    mirrors_file = Path(mirrors_file_str)
    repositories_dir = repositories_dir_str
    
    log.debug(f"App settings: {APP_SETTINGS.as_dict()}")
    
    log.debug(f"Mirrors file: {mirrors_file}")
    log.debug(f"Repositories directory: {repositories_dir}")
    log.debug(f"Logs directory: {LOGGING_SETTINGS.get('LOG_DIR', default='<unset>')}")
    
    try:
        main(mirrors_file=mirrors_file, repositories_dir=repositories_dir)
    except GitNotInstalled:
        log.warning(GitNotInstalled())
        
        exit(1)

    ## Wait for a time between executions when running in a container.
    if APP_SETTINGS.get("CONTAINER_ENV", default=False):
        import datetime
        import time

        sleep_seconds: int = APP_SETTINGS.get('EXEC_SLEEP', default=3600)
        log.info(f"Detected script is running in a container. Sleeping for {sleep_seconds} before restarting...")
        
        ## Get the current time and add the sleep_seconds to it
        next_execution = datetime.datetime.now() + datetime.timedelta(seconds=sleep_seconds)
        log.info(f"Next execution: {next_execution.strftime('%Y-%m-%d %H:%M:%S')}")
        
        time.sleep(sleep_seconds)
        
        log.info("Restarting container...")


        exit(0)
    else:
        exit(0)
