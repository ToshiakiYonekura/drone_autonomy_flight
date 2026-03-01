#!/usr/bin/env python3
"""
Simplified Mode 99 test - focus on arming and mode change
"""

import time
from pymavlink import mavutil

print("=" * 70)
print("MODE 99 - SIMPLIFIED TEST")
print("=" * 70)

# Connect
print("\n1. Connecting...")
master = mavutil.mavlink_connection('tcp:127.0.0.1:5760', source_system=255)
heartbeat = master.wait_heartbeat(timeout=10.0)
if not heartbeat:
    print("❌ No heartbeat")
    exit(1)
print(f"✅ Connected to system {master.target_system}")

# Wait for EKF
print("\n2. Waiting 5 seconds for EKF...")
time.sleep(5)

# Disable pre-arm checks
print("\n3. Disabling pre-arm checks...")
master.mav.param_set_send(
    master.target_system,
    master.target_component,
    b'ARMING_CHECK',
    0,  # Disable all pre-arm checks
    mavutil.mavlink.MAV_PARAM_TYPE_INT8
)
time.sleep(1)

# Set GUIDED mode
print("\n4. Setting GUIDED mode...")
mode_id = master.mode_mapping()['GUIDED']
master.mav.set_mode_send(
    master.target_system,
    mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
    mode_id
)
time.sleep(2)

# Arm
print("\n5. Arming...")
master.mav.command_long_send(
    master.target_system,
    master.target_component,
    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
    0,
    1,      # Arm
    0,      # No force needed now
    0, 0, 0, 0, 0
)

# Wait for arm
armed = False
for i in range(50):
    msg = master.recv_match(type='HEARTBEAT', blocking=True, timeout=0.1)
    if msg:
        armed = msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED
        if armed:
            print("   ✅ ARMED!")
            break
time.sleep(1)

if not armed:
    print("   ❌ Still not armed")
    exit(1)

# Try to set Mode 99
print("\n6. Setting Mode 99...")
master.mav.set_mode_send(
    master.target_system,
    mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
    99
)
time.sleep(2)

# Check mode
msg = master.recv_match(type='HEARTBEAT', blocking=True, timeout=2.0)
if msg:
    if msg.custom_mode == 99:
        print("   ✅✅✅ MODE 99 ACTIVE! ✅✅✅")
    else:
        print(f"   ❌ Current mode: {msg.custom_mode} (not 99)")
        print("   Checking for error messages...")

        # Listen for status text
        for i in range(10):
            status_msg = master.recv_match(type='STATUSTEXT', blocking=False)
            if status_msg:
                print(f"     SITL: {status_msg.text}")
            time.sleep(0.1)

# Disarm
print("\n7. Disarming...")
master.mav.command_long_send(
    master.target_system,
    master.target_component,
    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
    0,
    0,  # Disarm
    0, 0, 0, 0, 0, 0
)
time.sleep(1)

master.close()
print("\n" + "=" * 70)
