from pathlib import Path
import json
from dulwich import porcelain
from dulwich.porcelain import push
from dulwich.repo import Repo

from loguru import logger as log
from git_mirror.core import setup


def return_script_dir():
    script_dir = Path(__file__).resolve().parent
    log.debug(f"Script path: {script_dir}")
    
    return script_dir


def ensure_git_suffix(repo_url: str) -> str:
    """Ensure the repository URL ends with .git."""
    if not repo_url.endswith(".git"):
        return f"{repo_url}.git"

    log.debug(f"Git repository URL (with .git suffix ensured): {repo_url}")
    return repo_url


def clone_repo(src_repo: str, mirror_dir: Path) -> str:
    """Clone the source repository if it doesn't exist locally.
    
    Params:
        src_repo (str): URL of the source repository.
        mirror_dir (Path): Path where source repository will be cloned.
        
    Returns:
        str: Path to the cloned repository.
    
    """
    ## Get repository name from URL
    repo_name: str = Path(src_repo).stem
    ## Path where repository will be cloned
    repo_path: Path = mirror_dir / repo_name

    ## Clone repository if local path doesn't exist.
    if not repo_path.exists():
        log.info(f"Cloning repository {src_repo} into {repo_path}")
        porcelain.clone(src_repo, target=str(repo_path), bare=True)
        
        log.debug(f"Repository cloned to path: {repo_path}")
        
        return repo_path
    else:
        log.info(f"Repository {repo_name} already exists at path: {repo_path}. Skipping clone.")

        return repo_path


def fetch_all_remote_branches(repo_path: Path):
    """Fetch all remote branches after cloning the repository."""
    log.info(f"Fetching all remote branches for repository {repo_path}")

    # Ensure repo_path is a string
    repo_path: str = str(repo_path)

    # Open the local repository
    try:
        repo: Repo = Repo(repo_path)
    except Exception as exc:
        log.error(f"Failed to open repository at {repo_path}: {exc}")
        return

    # Get all remote references
    try:
        remote_refs = [ref for ref in repo.refs if ref.name.startswith("refs/remotes/")]
        log.info(f"Found remote refs: {remote_refs}")
    except Exception as exc:
        log.error(f"Failed to list remote refs: {exc}")
        return

    # Loop over each remote branch and fetch it
    for remote_ref in remote_refs:
        branch_name = remote_ref.name.replace("refs/remotes/", "")
        try:
            log.info(f"Fetching branch: {branch_name}")
            repo.git.fetch(remote_ref.remote.name, branch_name)  # Fetch each remote branch
        except Exception as exc:
            log.error(f"Failed to fetch branch {branch_name}: {exc}")
            continue

    log.success(f"Successfully fetched all remote branches.")



def push_new_remote(repo_path: Path, target_repo: str):
    """Push the repository to the target mirror."""
    log.info(f"Pushing local repository {repo_path} to mirror repository: {target_repo}")

    ## Ensure repo_path is a string
    repo_path: str = str(repo_path)

    ## Open the local repository
    repo: Repo = Repo(repo_path)

    ## Add or update the remote target URL
    target_repo: str = ensure_git_suffix(target_repo)
    repo.get_config().set(("remote", "origin"), b"url", target_repo.encode())

    ## List available refs in the local repository
    try:
        available_refs = {k.decode(): v for k, v in repo.get_refs().items()}
        log.info(f"Available refs: {available_refs}")
    except Exception as exc:
        log.error(f"Failed to list refs: {exc}")
        return

    log.info(f"Gathering refs...")

    ## Gather refs to push (local branches and remote tracking branches)
    refspecs: list[bytes] = []
    for ref_name in available_refs.keys():
        if ref_name.startswith("refs/heads/") or ref_name.startswith("refs/remotes/") or ref_name.startswith("refs/tags/"):
            # Ensure refs are bytes
            refspecs.append(ref_name.encode())

    log.debug(f"Refspecs: {refspecs}")

    ## Attempt to push all specified refs
    try:
        push(repo, target_repo, refspecs=refspecs, force=True)
        log.success(f"Successfully mirrored to {target_repo}")
    except Exception as exc:
        log.error(f"Failed to push to {target_repo}. Error: {exc}")

        
def main(mirror_staging_dir: str = "repositories", mirrors_json_file: str = "mirrors.json"):
    ## Path where this script is located.
    #  Note: This is inside the Python package itself.
    script_dir: Path = return_script_dir()
    
    ## Path where repositories/ directory will be created.
    #  This path is where repositories will be cloned for mirroring.
    mirror_dir: Path = Path(str(mirror_staging_dir))
    ## Path to JSON file defining mirror sources/targets.
    mirrors_file: Path = Path(str(mirrors_json_file))

    if not mirror_dir.exists():
        log.debug(f"Creating mirror staging path: {mirror_dir}")

        ## Create the mirror directory
        mirror_dir.mkdir(parents=True, exist_ok=True)

    ## Load the mirrors from the JSON file
    if not mirrors_file.exists():
        log.error(f"Mirrors file not found at path: {mirrors_file}")
        raise FileNotFoundError(f"Mirrors file not found: {mirrors_file}")

    try:
        ## Read the mirrors JSON file
        with mirrors_file.open("r") as f:
            mirrors = json.load(f)
    except Exception as exc:
        msg = f"({type(exc)}) Error loading mirrors from file '{mirrors_file}'. Details: {exc}"
        log.error(msg)
        
        raise exc
        
    for mirror in mirrors:
        log.debug(f"Mirror: {mirror}")

    ## Process each mirror source/target
    for entry in mirrors:
        ## URL of the source repository
        src_repo = ensure_git_suffix(entry["src"])
        ## URL where source repository will be mirrored
        target_repo = ensure_git_suffix(entry["mirror"])

        ## Clone the repository if not already done
        repo_path = clone_repo(src_repo, mirror_dir)
        
        ## Fetch all remote branches
        fetch_all_remote_branches(repo_path=repo_path)

        ## Push the repository to the target mirror
        push_new_remote(repo_path, target_repo)


if __name__ == "__main__":
    setup.setup_logging(log_level="DEBUG", add_file_logger=True, add_error_file_logger=True, colorize=True)
    
    log.info("Start git_mirror script")
    main()
