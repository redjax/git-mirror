#!/bin/bash

##
# You can schedule this script using crontab -e:
#
# # Assumes this repository was cloned to ~/git-mirror
# @reboot . $HOME/.profile; /bin/bash $HOME/git-mirror/scripts/start_sync.sh > /dev/null 2>&1
##

CWD=$(pwd)
THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SLEEP_SECONDS=3600

if ! command -v uv &> /dev/null; then
    echo "[ERROR] uv is not installed. Please install uv (https://github.com/astral-sh/uv) before re-running this script."
    exit 1
fi

echo ""
echo "Starting git mirror synch loop. Sleep for [${SLEEP_SECONDS}] second(s) between loops."
echo ""

## cd to git root
cd $THIS_DIR && cd ..
echo "[DEBUG] Working directory: " $(pwd)
APP_LOOP_SCRIPT=true uv run git_mirror

## cd back to path where script was called from
cd $CWD

if [[ $? -ne 0 ]]; then
    echo ""
    echo "[ERROR] Failure during script execution."

    exit 1
else
    echo ""
    echo "Script completed successfully."
    exit 0
fi
