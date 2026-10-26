#!/bin/bash
# Build the image and push it to the Snowflake image registry.
# Usage (from the repository root or this folder): ./containers/build_and_push.sh [CONNECTION] [REPO_URL]
# Needs Docker running and a Snowflake CLI connection. REPO_URL is <registry host>/<database>/<schema>/<repository>
# in lower case. Without it, the host is the one `snow spcs image-registry url` gives for the connection and
# the path is the one containers/service_spec.yaml names (edit both to your own image repository).
set -euo pipefail

CONNECTION="${1:-snowflake}"
HERE="$(cd "$(dirname "$0")" && pwd)"
if [ -n "${2:-}" ]; then
  REPO_URL="$2"
else
  HOST="$(snow spcs image-registry url --connection "$CONNECTION" | tail -n 1)"
  REPO_PATH="$(sed -n 's/^ *image: *\/\(.*\)\/[^\/]*$/\1/p' "$HERE/service_spec.yaml" | head -n 1)"
  REPO_URL="$HOST/$REPO_PATH"
fi
IMAGE="coco-skills-shop"
TAG="dev"
PROJECT="$(cd "$HERE/.." && pwd)"
REPO_ROOT="$(cd "$PROJECT/../.." && pwd)"
CTX="$(mktemp -d)"
trap 'rm -rf "$CTX"' EXIT

echo "==> Build context in $CTX"
mkdir -p "$CTX/streamlit_coco_pkg" "$CTX/app"
cp -r "$REPO_ROOT/streamlit_coco" "$CTX/streamlit_coco_pkg/streamlit_coco"
cp "$REPO_ROOT/pyproject.toml" "$CTX/streamlit_coco_pkg/"
cp "$REPO_ROOT/README.md" "$CTX/streamlit_coco_pkg/" 2>/dev/null || true
cp -r "$REPO_ROOT/examples/skills_hub/app.py" "$REPO_ROOT/examples/skills_hub/shop" \
      "$REPO_ROOT/examples/skills_hub/samples" "$CTX/app/"
find "$CTX" -name "__pycache__" -type d -prune -exec rm -rf {} +
cp "$HERE/requirements.txt" "$CTX/requirements.txt"
cp "$HERE/Dockerfile" "$CTX/Dockerfile"

echo "==> Logging in to the Snowflake image registry"
snow spcs image-registry login --connection "$CONNECTION"

echo "==> Building linux/amd64 and pushing $REPO_URL/$IMAGE:$TAG"
docker buildx build --platform linux/amd64 --push -t "$REPO_URL/$IMAGE:$TAG" "$CTX"
echo "==> Pushed. Next: snow app run --connection $CONNECTION (from $PROJECT)"
