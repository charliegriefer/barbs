#!/bin/bash

# Build script for Barbs Docker container
# This script should be run from the project root directory

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Building Barbs Docker container...${NC}"

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo -e "${RED}Error: This script must be run from the project root directory${NC}"
    exit 1
fi

# Default values
IMAGE_NAME="barbs"
TAG="latest"
DOCKERFILE_PATH="docker/Dockerfile"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--tag)
            TAG="$2"
            shift 2
            ;;
        -n|--name)
            IMAGE_NAME="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -t, --tag TAG       Set the image tag (default: latest)"
            echo "  -n, --name NAME     Set the image name (default: barbs)"
            echo "  -h, --help          Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Build the Docker image
echo -e "${YELLOW}Building image: ${IMAGE_NAME}:${TAG}${NC}"
docker build -f "${DOCKERFILE_PATH}" -t "${IMAGE_NAME}:${TAG}" .

echo -e "${GREEN}✅ Docker image built successfully: ${IMAGE_NAME}:${TAG}${NC}"
echo -e "${YELLOW}To run the container:${NC}"
echo "docker run --rm -p 8080:80 -p 8443:443 --name barbs-test ${IMAGE_NAME}:${TAG}"
