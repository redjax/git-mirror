#!/bin/bash

CONTAINERS_SSH_DIR="./containers/ssh"
SSH_KEY_COMMENT="gituser@git-mirror_container"

if ! command -v ssh-keygen &> /dev/null; then
    echo "ssh-keygen is not installed. Please install ssh-keygen (https://manpages.debian.org/stretch/ssh-keygen.1.en.html) before re-running this script."
    echo "Note that ssh-keygen is installed with OpenSSH server."

    exit 1
fi

if [[ ! -d CONTAINERS_SSH_DIR ]]; then
  echo "[WARNING] Container SSH directory does not exist. Creating path: $CONTAINERS_SSH_DIR"
  mkdir -pv $CONTAINERS_SSH_DIR
fi

echo ""
echo "Generating SSH keys for git-mirror container at path '${CONTAINERS_SSH_DIR}'..."
echo ""
ssh-keygen -t rsa -b 4096 -C "${SSH_KEY_COMMENT}" -N "" -f "${CONTAINERS_SSH_DIR}/git_mirror_id_rsa"

if [[ $? -ne 0 ]]; then
    echo ""
    echo "[ERROR] Failed to generate SSH keys for git-mirror container."
    exit 1
else
    echo ""
    echo "SSH keys generated. Keys exist at path: ${CONTAINERS_SSH_DIR}"
    echo ""

    exit 0
fi
