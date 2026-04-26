#!/bin/bash
# render_gsap_remotion.sh — Set up and render a GSAP+Remotion composition to video
#
# Usage:
#   bash render_gsap_remotion.sh <project_dir> <composition_id> [output_path] [width] [height] [fps] [codec]
#
# Defaults: 1080x1080, 30fps, h264, output to out/<composition_id>.mp4

set -euo pipefail

PROJECT_DIR="${1:?Usage: render_gsap_remotion.sh <project_dir> <composition_id> [output_path]}"
COMPOSITION_ID="${2:?Composition ID required}"
OUTPUT_PATH="${3:-}"
WIDTH="${4:-1080}"
HEIGHT="${5:-1080}"
FPS="${6:-30}"
CODEC="${7:-h264}"

cd "$PROJECT_DIR"

# Default output path
if [ -z "$OUTPUT_PATH" ]; then
  mkdir -p out
  OUTPUT_PATH="out/${COMPOSITION_ID}.mp4"
fi

# Check dependencies
if ! command -v node &> /dev/null; then
  echo "Error: node is required but not found"
  exit 1
fi

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
  echo "Installing dependencies..."
  npm install
fi

# Ensure GSAP is installed
if [ ! -d "node_modules/gsap" ]; then
  echo "Installing gsap..."
  npm install gsap
fi

# Ensure Remotion CLI is available
if [ ! -d "node_modules/@remotion/cli" ]; then
  echo "Installing @remotion/cli..."
  npm install @remotion/cli
fi

# Detect browser
BROWSER=""
for cmd in google-chrome-stable chromium-browser chromium google-chrome; do
  if command -v "$cmd" &> /dev/null; then
    BROWSER="$cmd"
    break
  fi
done

# Build render command
RENDER_CMD="npx remotion render ${COMPOSITION_ID} ${OUTPUT_PATH}"
RENDER_CMD="${RENDER_CMD} --codec=${CODEC}"
RENDER_CMD="${RENDER_CMD} --fps=${FPS}"

if [ -n "$BROWSER" ]; then
  RENDER_CMD="${RENDER_CMD} --browser-executable=$(which $BROWSER)"
fi

echo "Rendering: ${COMPOSITION_ID}"
echo "Output: ${OUTPUT_PATH}"
echo "Settings: ${WIDTH}x${HEIGHT} @ ${FPS}fps, codec=${CODEC}"
echo ""

eval $RENDER_CMD

# Resolve to absolute path
ABS_OUTPUT="$(cd "$(dirname "$OUTPUT_PATH")" && pwd)/$(basename "$OUTPUT_PATH")"
echo ""
echo "Render complete: ${ABS_OUTPUT}"
