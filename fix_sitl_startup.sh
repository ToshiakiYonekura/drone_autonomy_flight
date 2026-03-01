#!/bin/bash
# Fix SITL Startup - Proper Method
# This script starts SITL with physics simulator correctly

set -e  # Exit on error

echo "============================================"
echo "Starting ArduPilot SITL Properly"
echo "============================================"

# Clean up any old processes
echo "1. Cleaning up old processes..."
pkill -9 -f "arducopter" 2>/dev/null || true
pkill -9 -f "sim_vehicle" 2>/dev/null || true
pkill -9 -f "MAVProxy" 2>/dev/null || true
sleep 2

# Clean old files
echo "2. Cleaning old SITL files..."
cd ~/ardupilot/ArduCopter
rm -f eeprom.bin mav.tlog* logs/*.BIN 2>/dev/null || true

# Start SITL with proper options
echo "3. Starting SITL..."
echo ""
echo "NOTE: This will start MAVProxy in console mode."
echo "      To test Mode 99, use these commands in MAVProxy:"
echo ""
echo "      MAV> param set FS_GCS_ENABLE 0"
echo "      MAV> param set ARMING_CHECK 0"
echo "      MAV> arm throttle"
echo "      MAV> mode 99"
echo ""
echo "Starting in 3 seconds..."
sleep 3

# Method 1: Standard startup with MAVProxy
../Tools/autotest/sim_vehicle.py -v ArduCopter \
    --map \
    --console \
    -L CMAC \
    --out=127.0.0.1:14550 \
    --out=127.0.0.1:14551

# If you want no MAVProxy (for automated testing), use this instead:
# ../Tools/autotest/sim_vehicle.py -v ArduCopter --no-mavproxy --console

echo ""
echo "SITL stopped."
