#!/bin/bash

# Build and push script for GitHub Container Registry
# Usage: ./build-and-push.sh [version-tag]

set -e

# Configuration
GITHUB_USERNAME="mymeles"
REPO_NAME="litellm-wrapper"
IMAGE_NAME="ghcr.io/${GITHUB_USERNAME}/${REPO_NAME}"
VERSION="${1:-latest}"

echo "🔨 Building Docker image for linux/amd64 (Railway compatible)..."
docker buildx build --platform linux/amd64 -t "${IMAGE_NAME}:${VERSION}" --load .

# Also tag as latest if a specific version was provided
if [ "$VERSION" != "latest" ]; then
    echo "🏷️  Tagging as latest..."
    docker tag "${IMAGE_NAME}:${VERSION}" "${IMAGE_NAME}:latest"
fi

echo "✅ Build complete!"
echo ""
echo "📦 Image tagged as:"
echo "   - ${IMAGE_NAME}:${VERSION}"
if [ "$VERSION" != "latest" ]; then
    echo "   - ${IMAGE_NAME}:latest"
fi
echo ""
echo "To push to GitHub Container Registry:"
echo "1. First, authenticate with GHCR (if not already done):"
echo "   echo \$GITHUB_TOKEN | docker login ghcr.io -u ${GITHUB_USERNAME} --password-stdin"
echo ""
echo "2. Then push the image:"
echo "   docker push ${IMAGE_NAME}:${VERSION}"
if [ "$VERSION" != "latest" ]; then
    echo "   docker push ${IMAGE_NAME}:latest"
fi
echo ""
echo "Or run this script with --push flag to push automatically:"
echo "   ./build-and-push.sh ${VERSION} --push"

# Check if --push flag is provided
if [[ "$*" == *"--push"* ]]; then
    echo ""
    echo "🚀 Pushing to GitHub Container Registry..."
    docker push "${IMAGE_NAME}:${VERSION}"
    if [ "$VERSION" != "latest" ]; then
        docker push "${IMAGE_NAME}:latest"
    fi
    echo "✅ Push complete!"
    echo ""
    echo "Your image is now available at:"
    echo "   ${IMAGE_NAME}:${VERSION}"
fi

