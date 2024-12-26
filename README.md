# Git-Mirror <!-- omit in toc -->

A Python script & Docker container for mirroring repositories between git remotes.

## Table of Contents <!-- omit in toc -->

- [Requirements](#requirements)
- [Setup](#setup)
  - [SSH](#ssh)
  - [Python script](#python-script)
  - [Docker Compose stack](#docker-compose-stack)
- [Usage](#usage)
  - [Python script](#python-script-1)
  - [Docker Compose stack](#docker-compose-stack-1)
- [Links](#links)

## Requirements

- (Optional, can be installed with `uv`) [Python](https://python.org)
- Astral.sh [`uv` package manager](https://docs.astral.sh/uv)
- (Optional, only if running Docker container) [Docker and Docker Compose](https://docs.docker.com/engine/install/)

## Setup

By default, the Docker container mounts the host's `~/.ssh` directory. This is so the container can use the host's `~/.ssh/config` and the SSH key you use to interact with git remotes on the host.

If you have not already installed OpenSSH, do so before running this script. You can generally search your package manager for `openssh-server`, which installs the server and client packages and creates the directory `~/.ssh`.

You must also create a `mirrors.json` file by copying [`./mirrors.example.json`](./mirrors.example.json) -> `mirrors.json`. A `mirrors.json` file should look something like this:

```json
[
    {"src": "git@github.com:user/repo1.git", "mirror": "git@codeberg.org:user/repo1.git"},
    {"src": "git@github.com:user/repo2.git", "mirror": "git@gitlab.com:user/repo2.git"}
]
```

### SSH

If you have not already configured SSH keys, the simplest way to run this Python package is to run the [`./scripts/generate_ssh_keys.sh`](./scripts/generate_ssh_keys.sh) script. This will generate SSH keys and an SSH config file at [./containers/ssh](./containers). If you're using Docker, this can be mounted in the container by setting the value in your [`.env`](./.env.example) (`CONTAINER_SSH_DIR=./containers/ssh`).

If you have not already configured your SSH config for git remotes, create a file `~/.ssh/config` with the contents below; if your key is named something other than `git_id_rsa`, replace that line in any of the configs below with the name and path to your SSH key:

```text
## ~/.ssh/config

## Github
Host github.com
  User git
  IdentityFile ~/.ssh/git_id_rsa
  ## Optional, but must be 'no' when running in a container
  StrictHostKeyChecking no

## Gitlab
Host gitlab.com
  User git
  IdentityFile ~/.ssh/git_id_rsa
  ## Optional, but must be 'no' when running in a container
  StrictHostKeyChecking no

## Codeberg
Host codeberg.org
  User git
  IdentityFile ~/.ssh/git_id_rsa
  ## Optional, but must be 'no' when running in a container
  StrictHostKeyChecking no
```

On Linux, the SSH directory and files must have the following `chmod` permissions (you can change them with `chmod ### /path/to/file`):

*[Reference: Superuser.com answer](https://superuser.com/a/1559867)*

| Dir/File                                                                | Man Page                                                                                                                                                                                 | Recommended Permission | Mandatory Permission |
| ----------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------- | -------------------- |
| `~/.ssh/`                                                               | There is no general requirement to keep the entire contents of this directory secret, but the recommended permissions are read/write/execute for the user, and not accessible by others. | 700                    |                      |
| `~/.ssh/authorized_keys`                                                | This file is not highly sensitive, but the recommended permissions are read/write for the user, and not accessible by others                                                           | 600                    |                      |
| `~/.ssh/config`                                                         | Because of the potential for abuse, this file must have strict permissions: read/write for the user, and not writable by others                                                          |                        | 600                  |
| `~/.ssh/identity`  <br>`~/.ssh/id_dsa`  <br>`~/.ssh/id_rsa`             | These files contain sensitive data and should be readable by the user but not accessible by others (read/write/execute)                                                                  |                        | 600                  |
| `~/.ssh/identity.pub`  <br>`~/.ssh/id_dsa.pub`  <br>`~/.ssh/id_rsa.pub` | Contains the public key for authentication. These files are not sensitive and can (but need not) be readable by anyone.                                                                  | 644                    |                      |

### Python script

If you are just running the [`git_mirror` Python package](./src/git_mirror/), you do not need to copy the Docker files (i.e. [`.env.example`](./.env.example) -> `.env`).

- Copy the following files:
  - [`mirrors.example.json`](./mirrors.example.json) -> `mirrors.json`
  - [`config/settings.toml`](./config/settings.toml) -> `config/settings.local.toml`

### Docker Compose stack

To run the package inside a Docker container, there is some additional setup. Following the instructions in the [Python setup section](#python-script), you can skip steps related to copying/creating files in the [`./config`](./config) directory. You will need to copy some Docker files and create a `containers/logs` directory so the script doesn't throw permission errors.

- Copy the following files:
  - [`.env.example`](./.env.example) -> `.env`
- Create a directory at `containers/logs`
  - `$ mkdir ./containers/logs`
  - If the container creates this path, it is owned by `root:root` and the script fails in the container
- If you are not mounting the host's `~/.ssh` directory in the container, run the [`./scripts/generate_ssh_keys.sh`](./scripts/generate_ssh_keys.sh) script to create the container's SSH keys. Then, edit [`.env`](./.env.example), changing `CONTAINER_SSH_DIR=` to `CONTAINER_SSH_DIR=./containers/ssh`.

## Usage

### Python script

After completing the [Python script setup steps](#python-script), run the command `uv run git_mirror`.

### Docker Compose stack

After completing the [Docker setup steps](#docker-compose-stack), run `docker compose up -d`. You can check the container's logs with `docker compose logs -f git-mirror`.

## Links

- [sourcelevel.io: How to properly mirror a git repository](https://sourcelevel.io/blog/how-to-properly-mirror-a-git-repository)
- [SSH directory/file permissions reference](https://superuser.com/a/1559867)
- [Medium.com: Use your local SSH keys inside a Docker container](https://medium.com/trabe/use-your-local-ssh-keys-inside-a-docker-container-ea1d117515dc)
