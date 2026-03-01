#!/bin/bash
# Complete SITL integration test

set -e

echo "=========================================="
echo "ArduPilot SITL Integration Test"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo "This script will:"
echo "  1. Start ArduPilot SITL in background"
echo "  2. Wait for initialization"
echo "  3. Run integration tests"
echo "  4. Stop SITL"
echo ""

# Check if SITL is already running
if pgrep -f "arducopter" > /dev/null; then
    echo -e "${YELLOW}⚠️  ArduPilot SITL is already running${NC}"
    echo "Please stop it first with: pkill -f arducopter"
    exit 1
fi

# Navigate to ArduCopter directory
cd $HOME/ardupilot/ArduCopter

echo "Step 1: Starting ArduPilot SITL in background..."
echo "-----------------------------------------------"

# Start SITL in background
../Tools/autotest/sim_vehicle.py \
    --vehicle ArduCopter \
    --frame quad \
    --no-rebuild \
    -L CMAC \
    --out udp:127.0.0.1:14550 \
    > /tmp/sitl_output.log 2>&1 &

SITL_PID=$!
echo "SITL PID: $SITL_PID"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Cleaning up..."
    if [ ! -z "$SITL_PID" ]; then
        echo "Stopping SITL (PID: $SITL_PID)..."
        kill $SITL_PID 2>/dev/null || true
        pkill -f "arducopter" 2>/dev/null || true
    fi
}

trap cleanup EXIT INT TERM

echo ""
echo "Step 2: Waiting for SITL initialization..."
echo "-------------------------------------------"
echo "This takes ~30-40 seconds..."

# Wait for SITL to initialize
sleep 5

# Check if SITL is still running
if ! ps -p $SITL_PID > /dev/null; then
    echo -e "${RED}❌ SITL failed to start${NC}"
    echo "Check log: tail /tmp/sitl_output.log"
    exit 1
fi

# Wait for EKF ready message
echo "Waiting for EKF initialization..."
TIMEOUT=60
ELAPSED=0

while [ $ELAPSED -lt $TIMEOUT ]; do
    if grep -q "EKF3 IMU" /tmp/sitl_output.log 2>/dev/null; then
        echo -e "${GREEN}✅ SITL initialized successfully${NC}"
        break
    fi

    if [ $ELAPSED -eq 30 ]; then
        echo "Still waiting... (30s elapsed)"
    fi

    sleep 2
    ELAPSED=$((ELAPSED + 2))

    # Check if SITL crashed
    if ! ps -p $SITL_PID > /dev/null; then
        echo -e "${RED}❌ SITL crashed during initialization${NC}"
        echo "Last 20 lines of log:"
        tail -20 /tmp/sitl_output.log
        exit 1
    fi
done

if [ $ELAPSED -ge $TIMEOUT ]; then
    echo -e "${RED}❌ SITL initialization timeout${NC}"
    echo "Last 20 lines of log:"
    tail -20 /tmp/sitl_output.log
    exit 1
fi

sleep 5  # Extra time for full initialization

echo ""
echo "Step 3: Running integration tests..."
echo "-------------------------------------"

cd /home/yonetoshi27/autonomous_drone_sim

# Run Python integration test
python3 test_sitl_integration.py << EOF
y
EOF

TEST_RESULT=$?

echo ""
echo "=========================================="
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ SITL INTEGRATION TEST PASSED!${NC}"
else
    echo -e "${RED}❌ SITL INTEGRATION TEST FAILED${NC}"
fi
echo "=========================================="

echo ""
echo "SITL log available at: /tmp/sitl_output.log"
echo "View with: tail -f /tmp/sitl_output.log"

exit $TEST_RESULT
