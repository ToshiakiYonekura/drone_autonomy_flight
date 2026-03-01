#!/bin/bash
#
# Simple Mode 99 Test using MAVProxy commands
#

echo "======================================================================"
echo "MODE 99 SIMPLE TEST - Using Direct MAVProxy Commands"
echo "======================================================================"

# Connect with MAVProxy and send commands
python3 << 'EOF'
from pymavlink import mavutil
import time

print("\n[1] Connecting to SITL...")
mav = mavutil.mavlink_connection('tcp:127.0.0.1:5760', source_system=255)
mav.wait_heartbeat()
print(f"✅ Connected to system {mav.target_system}")

print("\n[2] Waiting for EKF to initialize (20 seconds)...")
time.sleep(20)

print("\n[3] Disabling failsafes...")
mav.param_set_send('FS_GCS_ENABLE', 0)
mav.param_set_send('FS_EKF_ACTION', 0)
time.sleep(2)

print("\n[4] Arming with force...")
mav.mav.command_long_send(
    mav.target_system, mav.target_component,
    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
    0, 1, 21196, 0, 0, 0, 0, 0
)

# Wait for arm
armed = False
for i in range(100):
    hb = mav.recv_match(type='HEARTBEAT', blocking=True, timeout=0.1)
    if hb and (hb.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED):
        armed = True
        break
    time.sleep(0.1)

if not armed:
    print("❌ Failed to arm")
    exit(1)

print("✅ Armed!")

print("\n[5] Setting Mode 99...")
mav.mav.set_mode_send(
    mav.target_system,
    mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
    99
)
time.sleep(2)

# Check mode
hb = mav.recv_match(type='HEARTBEAT', blocking=True, timeout=2.0)
if hb:
    if hb.custom_mode == 99:
        print("✅✅✅ MODE 99 IS ACTIVE! ✅✅✅")
    else:
        print(f"❌ Mode: {hb.custom_mode} (expected 99)")
        exit(1)

print("\n[6] Sending position commands and monitoring telemetry for 15 seconds...")
start_time = time.time()
lqr_count = 0

while time.time() - start_time < 15:
    # Send hover command
    mav.mav.set_position_target_local_ned_send(
        int((time.time() - start_time) * 1000),
        mav.target_system, mav.target_component,
        mavutil.mavlink.MAV_FRAME_LOCAL_NED,
        0b0000111111000111,
        0, 0, 0,  # pos
        0, 0, 0,  # vel (hover)
        0, 0, 0,  # accel
        0, 0      # yaw
    )

    # Check for any LQR telemetry
    msg = mav.recv_match(type='NAMED_VALUE_FLOAT', blocking=False)
    if msg and msg.name.startswith('LQR'):
        print(f"  {msg.name}: {msg.value:.3f}")
        lqr_count += 1

    time.sleep(0.5)

if lqr_count > 0:
    print(f"\n✅ Received {lqr_count} LQR telemetry messages!")
else:
    print("\n⚠️  No LQR telemetry received")

print("\n[7] Disarming...")
mav.mav.command_long_send(
    mav.target_system, mav.target_component,
    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
    0, 0, 0, 0, 0, 0, 0, 0
)
time.sleep(2)

print("\n======================================================================")
print("✅ MODE 99 TEST COMPLETE")
print("======================================================================")

EOF
