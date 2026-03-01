#!/bin/bash
# Build ArduPilot with Mode 99 in Docker
# This creates a reliable SITL environment for WSL2

set -e

echo "======================================================================"
echo "BUILDING ARDUPILOT WITH MODE 99 (DOCKER IMAGE)"
echo "======================================================================"
echo ""

# Check if ArduPilot source exists
if [ ! -d "$HOME/ardupilot" ]; then
    echo "❌ ArduPilot source not found at ~/ardupilot"
    echo "   Please clone ArduPilot first:"
    echo "   git clone --recurse-submodules https://github.com/ArduPilot/ardupilot.git ~/ardupilot"
    exit 1
fi

# Check if Mode 99 files exist
if [ ! -f "$HOME/ardupilot/ArduCopter/mode_smartphoto99.cpp" ]; then
    echo "❌ Mode 99 files not found in ~/ardupilot/ArduCopter/"
    echo "   Required files:"
    echo "   - mode_smartphoto99.h"
    echo "   - mode_smartphoto99.cpp"
    echo "   - sysid_params.txt"
    exit 1
fi

echo "✅ ArduPilot source found"
echo "✅ Mode 99 files found"
echo ""

# Create build context directory
BUILD_DIR="/tmp/ardupilot_mode99_build"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

echo "Copying Mode 99 files to build context..."
cp "$HOME/ardupilot/ArduCopter/mode_smartphoto99.h" "$BUILD_DIR/"
cp "$HOME/ardupilot/ArduCopter/mode_smartphoto99.cpp" "$BUILD_DIR/"
cp "$HOME/ardupilot/ArduCopter/sysid_params.txt" "$BUILD_DIR/"
cp "$(dirname "$0")/docker/Dockerfile.ardupilot-mode99" "$BUILD_DIR/Dockerfile"

echo "✅ Files copied"
echo ""

# Build Docker image
echo "Building Docker image (this may take 10-15 minutes)..."
cd "$BUILD_DIR"

docker build \
    --tag ardupilot-mode99:latest \
    --build-arg BUILDKIT_PROGRESS=plain \
    .

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================================================"
    echo "✅ BUILD SUCCESSFUL!"
    echo "======================================================================"
    echo ""
    echo "Docker image: ardupilot-mode99:latest"
    echo ""
    echo "To test Mode 99:"
    echo "  python3 test_mode99_docker.py"
    echo ""
    echo "To run SITL manually:"
    echo "  docker run -it --rm --network host ardupilot-mode99:latest --console --map"
    echo ""
else
    echo "❌ Build failed"
    exit 1
fi

# Cleanup
rm -rf "$BUILD_DIR"
