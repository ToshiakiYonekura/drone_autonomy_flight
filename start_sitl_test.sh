#!/bin/bash
# Script to start ArduPilot SITL for testing

set -e

echo "=========================================="
echo "Starting ArduPilot SITL for Integration Test"
echo "=========================================="

# Check if ArduPilot exists
if [ ! -d "$HOME/ardupilot" ]; then
    echo "❌ ArduPilot not found at $HOME/ardupilot"
    exit 1
fi

# Navigate to ArduCopter directory
cd $HOME/ardupilot/ArduCopter

echo ""
echo "Starting SITL with the following configuration:"
echo "  Vehicle: ArduCopter"
echo "  Frame: quad"
echo "  Console: Yes"
echo "  Map: No (saves resources)"
echo "  Connection: udp:127.0.0.1:14550"
echo ""
echo "This will take ~30 seconds to initialize..."
echo ""

# Start SITL
# --no-rebuild: skip rebuild to start faster
# -w: wipe EEPROM (fresh start)
../Tools/autotest/sim_vehicle.py \
    --vehicle ArduCopter \
    --frame quad \
    --console \
    --no-rebuild \
    -L CMAC \
    --out udp:127.0.0.1:14550

echo ""
echo "SITL stopped."
