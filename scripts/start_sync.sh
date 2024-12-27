#!/bin/bash

SLEEP_SECONDS=3600

if ! command -v uv &> /dev/null; then
    echo "[ERROR] uv is not installed. Please install uv (https://github.com/astral-sh/uv) before re-running this script."
    exit 1
fi

echo ""
echo "Starting git mirror synch loop. Sleep for [${SLEEP_SECONDS}] second(s) between loops."
echo ""

APP_LOOP_SCRIPT=true uv run git_mirror

if [[ $? -ne 0 ]]; then
    echo ""
    echo "[ERROR] Failure during script execution."

    exit 1
else
    echo ""
    echo "Script completed successfully."
    exit 0
fi
