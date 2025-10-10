#!/bin/bash
# csds.sh - Compatibility wrapper for all.sh
# This file exists for backward compatibility
# Use scripts/all.sh directly for the full-featured version

echo "🔄 Redirecting to scripts/all.sh..."
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if we're in the repo or need to download
if [ -f "${SCRIPT_DIR}/scripts/all.sh" ]; then
    # We're in the cloned repo
    bash "${SCRIPT_DIR}/scripts/all.sh" "$@"
else
    # We need to run the standalone version
    bash <(curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/scripts/all.sh)
fi

