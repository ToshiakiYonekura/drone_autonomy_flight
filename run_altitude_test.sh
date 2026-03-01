#!/bin/bash
# Complete automated altitude test with SITL

set -e

echo "========================================================================"
echo "AUTOMATED ALTITUDE TEST"
echo "========================================================================"

# Kill any existing SITL
echo "1. Cleaning up old SITL processes..."
pkill -9 -f arducopter 2>/dev/null || true
sleep 2

# Start SITL
echo "2. Starting ArduCopter SITL..."
cd ~/ardupilot/ArduCopter
~/ardupilot/build/sitl/bin/arducopter --model + --speedup 1 \
  --defaults ~/ardupilot/Tools/autotest/default_params/copter.parm \
  > /tmp/sitl_altitude_test.log 2>&1 &

SITL_PID=$!
echo "   SITL PID: $SITL_PID"

# Wait for SITL to start
echo "3. Waiting 10 seconds for SITL to fully initialize..."
sleep 10

# Check if SITL is still running
if ! kill -0 $SITL_PID 2>/dev/null; then
    echo "   ❌ SITL crashed! Check /tmp/sitl_altitude_test.log"
    cat /tmp/sitl_altitude_test.log
    exit 1
fi

echo "   ✅ SITL is running"

# Run the Python test
echo "4. Running altitude test..."
echo ""
cd /home/yonetoshi27/autonomous_drone_sim

python3 test_altitude_with_takeoff.py << EOF
y
EOF

TEST_RESULT=$?

# Cleanup
echo ""
echo "5. Cleaning up..."
kill $SITL_PID 2>/dev/null || true
pkill -9 -f arducopter 2>/dev/null || true

echo ""
echo "========================================================================"
if [ $TEST_RESULT -eq 0 ]; then
    echo "✅✅✅ TEST PASSED! ✅✅✅"
elif [ $TEST_RESULT -eq 1 ]; then
    echo "❌❌❌ TEST FAILED! ❌❌❌"
else
    echo "⚠️⚠️⚠️  TEST INCONCLUSIVE ⚠️⚠️⚠️"
fi
echo "========================================================================"

exit $TEST_RESULT
