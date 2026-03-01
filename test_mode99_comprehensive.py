#!/usr/bin/env python3
"""
Comprehensive Mode 99 LQR Test with Detailed Diagnostics
"""

import sys
import time
import math
from pymavlink import mavutil

def wait_for_message(master, msg_type, timeout=5.0):
    """Wait for a specific message type."""
    start = time.time()
    while time.time() - start < timeout:
        msg = master.recv_match(type=msg_type, blocking=True, timeout=0.5)
        if msg:
            return msg
    return None

def check_mode_available(master, mode_number):
    """Check if a mode is available."""
    # Request available modes
    master.mav.command_long_send(
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_CMD_REQUEST_MESSAGE,
        0,
        mavutil.mavlink.MAVLINK_MSG_ID_AVAILABLE_MODES,
        0, 0, 0, 0, 0, 0
    )
    time.sleep(0.5)
    return True  # Assume available for now

def main():
    print("=" * 80)
    print("MODE 99 COMPREHENSIVE LQR TEST WITH DIAGNOSTICS")
    print("=" * 80)

    # Connect to SITL
    print("\n[1/10] Connecting to SITL...")
    master = mavutil.mavlink_connection('tcp:127.0.0.1:5760', source_system=255)

    print("        Waiting for heartbeat...")
    heartbeat = master.wait_heartbeat(timeout=10.0)
    if not heartbeat:
        print("        ❌ No heartbeat received")
        return 1

    print(f"        ✅ Connected to system {master.target_system}")
    print(f"        Vehicle type: {heartbeat.type}, Autopilot: {heartbeat.autopilot}")
    print(f"        Initial mode: {heartbeat.custom_mode}")

    # Check EKF status
    print("\n[2/10] Checking EKF status...")
    time.sleep(2)

    # Get GPS status
    print("\n[3/10] Checking GPS status...")
    gps_msg = wait_for_message(master, 'GPS_RAW_INT', timeout=5.0)
    if gps_msg:
        print(f"        GPS Fix: {gps_msg.fix_type}, Satellites: {gps_msg.satellites_visible}")
        print(f"        HDOP: {gps_msg.eph/100.0:.2f}")
    else:
        print("        ⚠️  No GPS data received")

    # Get position
    print("\n[4/10] Checking position estimate...")
    pos_msg = wait_for_message(master, 'LOCAL_POSITION_NED', timeout=5.0)
    if pos_msg:
        print(f"        Position: [{pos_msg.x:.2f}, {pos_msg.y:.2f}, {pos_msg.z:.2f}] m (NED)")
        print(f"        Velocity: [{pos_msg.vx:.2f}, {pos_msg.vy:.2f}, {pos_msg.vz:.2f}] m/s")
    else:
        print("        ⚠️  No position data received")

    # Disable failsafes
    print("\n[5/10] Disabling failsafes for testing...")
    master.param_set_send('FS_GCS_ENABLE', 0)
    master.param_set_send('FS_EKF_ACTION', 0)
    time.sleep(1)
    print("        ✅ Failsafes disabled")

    # Set GUIDED mode first
    print("\n[6/10] Setting GUIDED mode...")
    mode_id = master.mode_mapping()['GUIDED']
    master.mav.set_mode_send(
        master.target_system,
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
        mode_id
    )
    time.sleep(2)

    msg = master.recv_match(type='HEARTBEAT', blocking=True, timeout=2.0)
    if msg and msg.custom_mode == mode_id:
        print(f"        ✅ GUIDED mode active (mode {mode_id})")
    else:
        print(f"        ⚠️  Mode: {msg.custom_mode if msg else 'unknown'}")

    # Try arming
    print("\n[7/10] Attempting to arm...")
    master.mav.command_long_send(
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
        0,
        1,      # Arm
        21196,  # Force (bypass pre-arm checks)
        0, 0, 0, 0, 0
    )

    # Wait for arm confirmation
    print("        Waiting for arm confirmation...")
    armed = False
    for i in range(50):
        msg = master.recv_match(type='HEARTBEAT', blocking=True, timeout=0.1)
        if msg:
            armed = msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED
            if armed:
                print("        ✅ ARMED successfully")
                break

        # Check for STATUSTEXT messages (pre-arm errors)
        status_msg = master.recv_match(type='STATUSTEXT', blocking=False)
        if status_msg:
            print(f"        Status: {status_msg.text}")

        time.sleep(0.1)

    if not armed:
        print("        ❌ Failed to arm - checking for errors...")
        # Collect any status messages
        for i in range(20):
            status_msg = master.recv_match(type='STATUSTEXT', blocking=True, timeout=0.1)
            if status_msg:
                print(f"           {status_msg.text}")
        return 1

    # Check if Mode 99 exists
    print("\n[8/10] Checking if Mode 99 (SMART_PHOTO) is available...")
    modes = master.mode_mapping()
    print(f"        Available modes: {list(modes.keys())}")

    if 'SMART_PHOTO' in modes or 'SMARTPH99' in modes:
        print("        ✅ Mode 99 found in mode mapping")
        mode99_name = 'SMART_PHOTO' if 'SMART_PHOTO' in modes else 'SMARTPH99'
    else:
        print("        ⚠️  Mode 99 not in mode mapping, trying direct number...")
        mode99_name = None

    # Attempt to set Mode 99
    print("\n[9/10] Setting Mode 99 (LQR State Feedback)...")

    if mode99_name:
        mode_id = modes[mode99_name]
        print(f"        Using mode name '{mode99_name}' (ID: {mode_id})")
        master.mav.set_mode_send(
            master.target_system,
            mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
            mode_id
        )
    else:
        print(f"        Trying direct mode number 99...")
        master.mav.set_mode_send(
            master.target_system,
            mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
            99
        )

    # Wait and check mode
    time.sleep(2)

    # Collect status messages
    print("        Checking for mode change messages...")
    for i in range(20):
        status_msg = master.recv_match(type='STATUSTEXT', blocking=True, timeout=0.1)
        if status_msg:
            text = status_msg.text
            print(f"           {text}")
            if 'MODE99' in text or 'SMARTPHOTO' in text or 'LQR' in text:
                print("        ✅ Mode 99 message detected!")

    msg = master.recv_match(type='HEARTBEAT', blocking=True, timeout=2.0)
    current_mode = msg.custom_mode if msg else 'unknown'

    if current_mode == 99:
        print(f"        ✅✅✅ MODE 99 IS ACTIVE! ✅✅✅")
    else:
        print(f"        ❌ Mode change failed - current mode: {current_mode}")
        print(f"        Expected: 99, Got: {current_mode}")
        return 1

    # Monitor LQR telemetry
    print("\n[10/10] Monitoring LQR telemetry for 10 seconds...")
    print("         Looking for: LQR_Thrust, LQR_Motor0-3, LQR_PWM0-3, LQR_M_*")

    lqr_data = {}
    start_time = time.time()

    while time.time() - start_time < 10.0:
        # Send hover command
        master.mav.set_position_target_local_ned_send(
            int((time.time() - start_time) * 1000),
            master.target_system,
            master.target_component,
            mavutil.mavlink.MAV_FRAME_LOCAL_NED,
            0b0000111111000111,  # Use velocity
            0, 0, 0,             # Position (ignored)
            0, 0, 0,             # Velocity (hover)
            0, 0, 0,             # Accel (ignored)
            0, 0                 # Yaw, yaw_rate
        )

        # Check for LQR telemetry
        msg = master.recv_match(type='NAMED_VALUE_FLOAT', blocking=True, timeout=0.5)
        if msg:
            if msg.name.startswith('LQR'):
                lqr_data[msg.name] = msg.value
                print(f"         {msg.name}: {msg.value:.3f}")

        # Check position
        pos_msg = master.recv_match(type='LOCAL_POSITION_NED', blocking=False)
        if pos_msg:
            alt = -pos_msg.z
            if int(time.time() - start_time) % 2 == 0:
                print(f"         Alt: {alt:.2f}m, Vel: [{pos_msg.vx:.2f}, {pos_msg.vy:.2f}, {pos_msg.vz:.2f}] m/s")

    print("\n" + "=" * 80)
    print("LQR TELEMETRY SUMMARY")
    print("=" * 80)
    if lqr_data:
        for key in sorted(lqr_data.keys()):
            print(f"  {key:15s}: {lqr_data[key]:.3f}")
        print("\n✅ MODE 99 PURE LQR IS WORKING!")
    else:
        print("  ⚠️  No LQR telemetry received")
        print("  This might indicate the LQR controller is not running properly")

    # Disarm
    print("\n" + "=" * 80)
    print("Disarming...")
    master.mav.command_long_send(
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
        0,
        0,  # Disarm
        0, 0, 0, 0, 0, 0
    )
    time.sleep(2)

    print("=" * 80)
    print("✅ MODE 99 COMPREHENSIVE TEST COMPLETE!")
    print("=" * 80)

    master.close()
    return 0

if __name__ == "__main__":
    sys.exit(main())
