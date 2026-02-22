#!/bin/bash

# Exit immediately on error, treat unset variables as an error, and fail if any command in a pipeline fails.
set -euo pipefail

# Function to run a command and show logs only on error
run_command() {
    local command_to_run="$*"
    local output
    local exit_code
    
    # Capture all output (stdout and stderr)
    output=$(eval "$command_to_run" 2>&1) || exit_code=$?
    exit_code=${exit_code:-0}
    
    if [ $exit_code -ne 0 ]; then
        echo -e "\033[0;31m[ERROR] Command failed (Exit Code $exit_code): $command_to_run\033[0m" >&2
        echo -e "\033[0;31m$output\033[0m" >&2
        
        exit $exit_code
    fi
}

# Installing UV (Python package manager)
echo -e "\n🐍 Installing UV - Python Package Manager..."
run_command "pipx install uv"
echo "✅ Done"

# Installing CLI-based AI Agents

echo -e "\n🤖 Installing Gemini CLI..."
run_command "npm install -g @google/gemini-cli@latest"
echo "✅ Done"

# Installing Aider
echo -e "\n🤖 Installing Aider - AI-Assisted Fixing..."
run_command "uv tool install --upgrade aider-chat --force --from git+https://github.com/wolffy-au/aider-speckit.git@uplift-linting"
echo "✅ Done"

echo -e "\n🤖 Installing Specify CLI..."
run_command "uv tool install --upgrade specify-cli --force --from git+https://github.com/github/spec-kit.git"
echo "✅ Done"

# Installing commitizen
echo -e "\n🛠️ Installing commitizen..."
run_command "pipx install commitizen"
echo "✅ Done"

echo -e "\n🧹 Cleaning cache..."
run_command "sudo apt-get autoclean"
run_command "sudo apt-get clean"

echo "✅ Setup completed. Happy coding! 🚀"
