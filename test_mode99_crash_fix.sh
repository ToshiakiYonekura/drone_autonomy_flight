#!/bin/bash
# Test if Mode 99 crash is fixed

echo "========================================================================"
echo "Testing Mode 99 Crash Fix"
echo "========================================================================"

# Clean up
pkill -9 arducopter 2>/dev/null
sleep 2
cd ~/ardupilot/ArduCopter
rm -f eeprom.bin mav.parm mav.tlog*

# Start SITL
echo "Starting SITL..."
~/ardupilot/build/sitl/bin/arducopter --model + --speedup 1 \
  --defaults ~/ardupilot/Tools/autotest/default_params/copter.parm \
  > /tmp/sitl_crash_test.log 2>&1 &

SITL_PID=$!
echo "SITL PID: $SITL_PID"
sleep 10

# Test with Python
echo "Testing Mode 99 entry..."
python3 << 'PYEOF'
import time
from pymavlink import mavutil

master = mavutil.mavlink_connection('tcp:127.0.0.1:5760', source_system=255)
print("Connecting...")
if not master.wait_heartbeat(timeout=10.0):
    print("❌ No heartbeat")
    exit(1)

print("✅ Connected")

# Disable failsafe
print("Disabling failsafe...")
master.mav.param_set_send(
    master.target_system, master.target_component,
    b'FS_GCS_ENABLE', 0, mavutil.mavlink.MAV_PARAM_TYPE_INT8)
time.sleep(1)

# Try to enter Mode 99
print("Entering Mode 99...")
master.mav.set_mode_send(
    master.target_system,
    mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
    99)

# Wait and check
time.sleep(3)
msg = master.recv_match(type='HEARTBEAT', blocking=True, timeout=2.0)
if msg and msg.custom_mode == 99:
    print("✅✅✅ MODE 99 ACTIVE - NO CRASH! ✅✅✅")
    exit(0)
else:
    print(f"⚠️  Current mode: {msg.custom_mode if msg else 'unknown'}")
    exit(1)
PYEOF

TEST_RESULT=$?

# Cleanup
kill $SITL_PID 2>/dev/null
pkill -9 arducopter 2>/dev/null

# Check for crash
if grep -q "Floating point exception" /tmp/sitl_crash_test.log; then
    echo "❌❌❌ STILL CRASHES ❌❌❌"
    echo "Log:"
    tail -20 /tmp/sitl_crash_test.log
    exit 1
elif grep -q "SMARTPHOTO99" /tmp/sitl_crash_test.log; then
    echo "✅✅✅ CRASH FIXED! Mode 99 initialized successfully! ✅✅✅"
    echo "Mode 99 messages:"
    grep "SMARTPHOTO99\|MODE99" /tmp/sitl_crash_test.log
    exit 0
else
    echo "⚠️  Test inconclusive"
    exit 2
fi
