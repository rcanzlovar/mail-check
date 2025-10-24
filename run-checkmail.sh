#!/usr/bin/env bash
# Bob Anzlovar 22-oct-2025
#
# Add date information to the log
echo "### $0 $(date '+%Y-%m-%d %H:%M') ### "

# ensure we are in the same directory as the script and comments directory
# directory
# Where is the script?
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

# go there
pushd "${SCRIPT_DIR}" >/dev/null

# do the thing
uv run \
    --with paramiko \
    --with scp \
    checkmail-config.py

# go back to where you once belonged
popd >/dev/null
