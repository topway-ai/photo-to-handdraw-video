#!/usr/bin/env bash
set -e

echo "=== Installing photo-to-handdraw-video dependencies ==="

# Check ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "Warning: ffmpeg is not found. Please install ffmpeg via: brew install ffmpeg (macOS) or apt-get install ffmpeg (Linux)"
fi

# Install python dependencies
pip install -r requirements.txt

# Optionally link as global skill for Google Antigravity
SKILL_TARGET="$HOME/.gemini/config/skills/photo-to-handdraw-video"
if [ "$1" == "--link-skill" ]; then
    mkdir -p "$(dirname "$SKILL_TARGET")"
    ln -sfn "$(pwd)" "$SKILL_TARGET"
    echo "Successfully linked skill to $SKILL_TARGET"
fi

echo "=== Setup completed successfully! ==="
