from dulwich import porcelain
from dulwich.repo import Repo
from pathlib import Path
import json

def load_mirrors(json_path):
    with open(json_path, "r") as f:
        return json.load(f)

def ensure_git_suffix(repo_url):
    return repo_url if repo_url.endswith(".git") else f"{repo_url}.git"

def clone_or_open_repo(src_url, repo_dir):
    repo_path = Path(repo_dir)
    if not repo_path.exists():
        print(f"Cloning repository: {src_url}")
        porcelain.clone(src_url, str(repo_path))
    else:
        print(f"Repository already exists at {repo_path}. Opening existing repository.")
    return Repo(str(repo_path))

def fetch_all_branches(repo):
    print(f"Fetching all remote branches for {repo.path}")
    remote_refs = porcelain.fetch(repo, b"origin")
    print(f"Fetched remote refs: {remote_refs}")
    return remote_refs.refs

def checkout_remote_branches(repo, refs):
    for ref, sha in refs.items():
        if b"refs/heads/" in ref:
            branch_name = ref.split(b"/")[-1].decode()
            print(f"Checking out branch: {branch_name}")
            repo[b"HEAD"] = sha  # Update HEAD to point to this branch
            repo.refs[b"refs/heads/" + branch_name.encode()] = sha

def push_to_mirror(repo, mirror_url, refs):
    """
    Push all branches and tags to the mirror repository.
    """
    mirror_url = ensure_git_suffix(mirror_url)
    print(f"Pushing repository to mirror: {mirror_url}")

    # Push branches
    for ref, sha in refs.items():
        if b"refs/heads/" in ref:
            branch_name = ref.decode()
            print(f"Pushing branch: {branch_name}")
            porcelain.push(repo, mirror_url, ref + b":" + ref)
    
    # Push tags
    for ref, sha in refs.items():
        if b"refs/tags/" in ref:
            tag_name = ref.decode()
            print(f"Pushing tag: {tag_name}")
            porcelain.push(repo, mirror_url, ref + b":" + ref)

    print("Push complete.")


def process_repositories(mirrors, base_dir):
    base_path = Path(base_dir)
    base_path.mkdir(exist_ok=True)

    for mirror in mirrors:
        try:
            src = mirror["src"]
            mirror_url = mirror["mirror"]
            print(f"Processing repository: {src}")
            
            repo_name = Path(src.split("/")[-1]).stem  # Extract repo name without '.git'
            repo_dir = base_path / repo_name
            
            # Clone or open the repository
            repo = clone_or_open_repo(src, repo_dir)
            
            # Fetch all remote branches
            refs = fetch_all_branches(repo)
            
            # Checkout all remote branches locally
            checkout_remote_branches(repo, refs)
            
            # Push all branches and tags to the mirror
            push_to_mirror(repo, mirror_url, refs)
            
        except Exception as e:
            print(f"Error processing repository {src}: {e}")

if __name__ == "__main__":
    mirrors_path = Path("mirrors.json")
    base_dir = "repositories"
    try:
        mirrors = load_mirrors(mirrors_path)
        process_repositories(mirrors, base_dir)
    except Exception as e:
        print(f"Failed to process repositories: {e}")
