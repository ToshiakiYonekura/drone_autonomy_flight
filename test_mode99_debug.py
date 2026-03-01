#!/usr/bin/env python3
"""Debug Mode 99 - Check why mode change fails"""

from pymavlink import mavutil
import time

print("=" * 80)
print("MODE 99 DEBUG TEST")
print("=" * 80)

mav = mavutil.mavlink_connection('tcp:127.0.0.1:5760', source_system=255)
mav.wait_heartbeat()
print(f"✅ Connected to system {mav.target_system}")

print("\nWaiting 25 seconds for full EKF initialization...")
time.sleep(25)

print("\nChecking system status...")

# Check GPS
gps_msg = mav.recv_match(type='GPS_RAW_INT', blocking=True, timeout=2.0)
if gps_msg:
    print(f"GPS: Fix={gps_msg.fix_type}, Sats={gps_msg.satellites_visible}, HDOP={gps_msg.eph/100.0:.2f}")

# Check position
pos_msg = mav.recv_match(type='LOCAL_POSITION_NED', blocking=True, timeout=2.0)
if pos_msg:
    print(f"Position: [{pos_msg.x:.2f}, {pos_msg.y:.2f}, {pos_msg.z:.2f}] m")
    print("✅ Position data available")
else:
    print("❌ NO POSITION DATA - Mode 99 will fail!")

# Check EKF
ekf_msg = mav.recv_match(type='EKF_STATUS_REPORT', blocking=True, timeout=2.0)
if ekf_msg:
    print(f"EKF: flags=0x{ekf_msg.flags:04x}, velocity_variance={ekf_msg.velocity_variance:.6f}")

print("\nDisabling failsafes...")
mav.param_set_send('FS_GCS_ENABLE', 0)
mav.param_set_send('FS_EKF_ACTION', 0)
mav.param_set_send('ARMING_CHECK', 0)  # Disable all arming checks
time.sleep(2)

print("\nArming...")
mav.mav.command_long_send(
    mav.target_system, mav.target_component,
    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
    0, 1, 0, 0, 0, 0, 0, 0  # Try without force first
)

# Wait for arm with STATUSTEXT monitoring
armed = False
for i in range(50):
    hb = mav.recv_match(type='HEARTBEAT', blocking=False)
    if hb and (hb.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED):
        armed = True
        print("✅ Armed!")
        break

    # Check for status messages
    status = mav.recv_match(type='STATUSTEXT', blocking=False)
    if status:
        print(f"  Status: {status.text}")

    time.sleep(0.1)

if not armed:
    print("❌ Failed to arm - trying with force...")
    mav.mav.command_long_send(
        mav.target_system, mav.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
        0, 1, 21196, 0, 0, 0, 0, 0
    )
    time.sleep(2)

    hb = mav.recv_match(type='HEARTBEAT', blocking=True, timeout=2.0)
    if hb and (hb.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED):
        print("✅ Armed with force!")
        armed = True

if not armed:
    print("❌ Cannot arm - aborting")
    exit(1)

print("\nAttempting Mode 99 change...")
print("Current mode before change:")
hb = mav.recv_match(type='HEARTBEAT', blocking=True, timeout=1.0)
if hb:
    print(f"  Mode: {hb.custom_mode}")

mav.mav.set_mode_send(
    mav.target_system,
    mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
    99
)

print("\nWaiting for mode change (monitoring STATUSTEXT)...")
mode_changed = False
for i in range(50):
    hb = mav.recv_match(type='HEARTBEAT', blocking=False)
    if hb and hb.custom_mode == 99:
        mode_changed = True
        print(f"✅✅✅ MODE 99 ACTIVE! ✅✅✅")
        break

    status = mav.recv_match(type='STATUSTEXT', blocking=False)
    if status:
        text = status.text
        print(f"  STATUSTEXT: {text}")

    time.sleep(0.1)

if not mode_changed:
    hb = mav.recv_match(type='HEARTBEAT', blocking=True, timeout=1.0)
    current_mode = hb.custom_mode if hb else 'unknown'
    print(f"❌ Mode change FAILED - current mode: {current_mode}")
else:
    print("\nSending test command...")
    mav.mav.set_position_target_local_ned_send(
        1000, mav.target_system, mav.target_component,
        mavutil.mavlink.MAV_FRAME_LOCAL_NED,
        0b0000111111000111,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    )

    print("Monitoring telemetry for 5 seconds...")
    for i in range(10):
        msg = mav.recv_match(type='NAMED_VALUE_FLOAT', blocking=True, timeout=0.5)
        if msg and msg.name.startswith('LQR'):
            print(f"  {msg.name}: {msg.value:.3f}")

print("\n" + "=" * 80)
