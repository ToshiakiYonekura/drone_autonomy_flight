#!/bin/bash
# Automated Mode 99 LQR Test

set -e

echo "========================================================================"
echo "MODE 99 LQR STATE FEEDBACK TEST"
echo "========================================================================"

# Kill any existing SITL
echo "1. Cleaning up old SITL processes..."
pkill -9 -f arducopter 2>/dev/null || true
sleep 2

# Verify sysid_params.txt exists
if [ ! -f ~/ardupilot/ArduCopter/sysid_params.txt ]; then
    echo "❌ ERROR: sysid_params.txt not found!"
    exit 1
fi

echo "2. System ID parameters found:"
cat ~/ardupilot/ArduCopter/sysid_params.txt | grep -E "^[A-Z]"
echo ""

# Start SITL
echo "3. Starting ArduCopter SITL..."
cd ~/ardupilot/ArduCopter
~/ardupilot/build/sitl/bin/arducopter --model + --speedup 1 \
  --defaults ~/ardupilot/Tools/autotest/default_params/copter.parm \
  > /tmp/sitl_mode99_test.log 2>&1 &

SITL_PID=$!
echo "   SITL PID: $SITL_PID"

# Wait for SITL to start
echo "4. Waiting 10 seconds for SITL to initialize..."
sleep 10

# Check if SITL is still running
if ! kill -0 $SITL_PID 2>/dev/null; then
    echo "   ❌ SITL crashed! Check /tmp/sitl_mode99_test.log"
    cat /tmp/sitl_mode99_test.log
    exit 1
fi

echo "   ✅ SITL is running"

# Run the test
echo "5. Running Mode 99 test..."
echo ""
cd /home/yonetoshi27/autonomous_drone_sim
python3 test_mode99_lqr.py

TEST_RESULT=$?

# Cleanup
echo ""
echo "6. Cleaning up..."
kill $SITL_PID 2>/dev/null || true
pkill -9 -f arducopter 2>/dev/null || true

echo ""
echo "========================================================================"
if [ $TEST_RESULT -eq 0 ]; then
    echo "✅✅✅ MODE 99 TEST COMPLETED! ✅✅✅"
else
    echo "❌❌❌ MODE 99 TEST FAILED! ❌❌❌"
fi
echo "========================================================================"
echo ""
echo "Check /tmp/sitl_mode99_test.log for SITL output"

exit $TEST_RESULT
