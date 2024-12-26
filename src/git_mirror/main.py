from loguru import logger as log
from git_mirror.core import setup



def return_script_dir():
    script_dir = Path(__file__).resolve().parent
    log.debug(f"Script path: {script_dir}")
    
    return script_dir

import subprocess
from pathlib import Path
import json

def run_git_command(command, cwd=None):
    """Run a git command and handle errors."""
    try:
        print(f"Running command: {' '.join(command)} in {cwd or Path.cwd()}")
        result = subprocess.run(command, cwd=cwd, check=True, text=True, capture_output=True)
        print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {' '.join(command)}")
        print(e.stderr)
        raise

def clone_mirror(src_url, dest_dir):
    """Clone a repository as a bare mirror."""
    print(f"Cloning repository {src_url} into {dest_dir}")
    run_git_command(["git", "clone", "--mirror", src_url, str(dest_dir)])

def set_push_remote(repo_dir, mirror_url):
    """Set the push URL for the repository."""
    print(f"Setting push remote URL to {mirror_url} in {repo_dir}")
    run_git_command(["git", "remote", "set-url", "--push", "origin", mirror_url], cwd=repo_dir)

def push_mirror(repo_dir):
    """Push all branches and tags to the mirror repository."""
    print(f"Pushing all branches and tags from {repo_dir}")
    run_git_command(["git", "push", "--mirror"], cwd=repo_dir)

def update_mirror(repo_dir):
    """Update the mirror by fetching and pushing changes."""
    print(f"Updating mirror for {repo_dir}")
    run_git_command(["git", "fetch", "-p", "origin"], cwd=repo_dir)
    run_git_command(["git", "push", "--mirror"], cwd=repo_dir)

def load_mirrors(json_path):
    """Load the mirrors configuration from a JSON file."""
    try:
        with open(json_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading mirrors from {json_path}: {e}")
        raise

def process_repositories(mirrors, base_dir):
    """Process each repository to set up or update the mirror."""
    base_path = Path(base_dir)
    base_path.mkdir(exist_ok=True)

    for mirror in mirrors:
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
                print(f"Repository {repo_dir} already exists. Updating mirror...")
                update_mirror(repo_dir)

        except Exception as e:
            print(f"Error processing repository {src}: {e}")

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
