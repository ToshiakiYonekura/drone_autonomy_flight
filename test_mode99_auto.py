#!/usr/bin/env python3
"""Automated Mode 99 Test - No user interaction needed"""

import sys
import time
from pymavlink import mavutil

print("="*70)
print("MODE 99 AUTOMATED TEST")
print("="*70)

# Connect
print("\n[1/6] Connecting to SITL...")
try:
    mav = mavutil.mavlink_connection('tcp:127.0.0.1:5760', source_system=255, timeout=5)
    mav.wait_heartbeat(timeout=10)
    print(f"✅ Connected to system {mav.target_system}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    sys.exit(1)

# Wait for EKF
print("\n[2/6] Waiting for EKF to initialize...")
for i in range(20):
    msg = mav.recv_match(type='LOCAL_POSITION_NED', blocking=True, timeout=1.0)
    if msg:
        print(f"✅ EKF ready! Position: [{msg.x:.2f}, {msg.y:.2f}, {msg.z:.2f}]")
        break
    time.sleep(0.5)
else:
    print("❌ EKF not ready after 10 seconds")
    sys.exit(1)

# Configure
print("\n[3/6] Configuring parameters...")
mav.param_set_send('FS_GCS_ENABLE', 0)
mav.param_set_send('ARMING_CHECK', 0)
time.sleep(2)
print("✅ Parameters set")

# Arm
print("\n[4/6] Arming...")
mav.mav.command_long_send(
    mav.target_system, mav.target_component,
    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
    0, 1, 0, 0, 0, 0, 0, 0
)
time.sleep(3)

hb = mav.recv_match(type='HEARTBEAT', blocking=True, timeout=2.0)
if hb and (hb.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED):
    print("✅ ARMED!")
else:
    print("❌ Failed to arm")
    sys.exit(1)

# Enter Mode 99
print("\n[5/6] Entering Mode 99...")
mav.mav.set_mode_send(
    mav.target_system,
    mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
    99
)
time.sleep(2)

hb = mav.recv_match(type='HEARTBEAT', blocking=True, timeout=2.0)
if hb and hb.custom_mode == 99:
    print("✅✅✅ MODE 99 IS ACTIVE! ✅✅✅")
else:
    print(f"❌ Mode 99 failed. Current mode: {hb.custom_mode if hb else 'unknown'}")
    sys.exit(1)

# Monitor telemetry
print("\n[6/6] Monitoring LQR telemetry...")
lqr_seen = set()
start = time.time()

while time.time() - start < 10:
    # Send hover command
    mav.mav.set_position_target_local_ned_send(
        int((time.time() - start) * 1000),
        mav.target_system, mav.target_component,
        mavutil.mavlink.MAV_FRAME_LOCAL_NED,
        0b0000111111000111,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    )

    # Check telemetry
    msg = mav.recv_match(type='NAMED_VALUE_FLOAT', blocking=False)
    if msg and msg.name.startswith('LQR'):
        if msg.name not in lqr_seen:
            lqr_seen.add(msg.name)
            print(f"  ✅ {msg.name}: {msg.value:.3f}")

    time.sleep(0.1)

print(f"\n✅ Received {len(lqr_seen)} LQR telemetry types:")
for field in sorted(lqr_seen):
    print(f"  - {field}")

print("\n" + "="*70)
print("✅ MODE 99 TEST SUCCESSFUL!")
print("="*70)

mav.close()
