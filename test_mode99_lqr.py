#!/usr/bin/env python3
"""
Test Mode 99 LQR State Feedback Controller
"""

import sys
import time
import math
from pymavlink import mavutil

def main():
    print("=" * 70)
    print("MODE 99 LQR STATE FEEDBACK CONTROLLER TEST")
    print("=" * 70)

    # Connect to SITL
    print("\n1. Connecting to SITL...")
    master = mavutil.mavlink_connection('tcp:127.0.0.1:5760', source_system=255)

    print("   Waiting for heartbeat...")
    heartbeat = master.wait_heartbeat(timeout=10.0)
    if not heartbeat:
        print("   ❌ No heartbeat received")
        return 1

    print(f"   ✅ Connected to system {master.target_system}")

    # Wait for EKF to initialize
    print("\n2. Waiting for EKF to initialize (10 seconds)...")
    time.sleep(10)

    # Set GUIDED mode
    print("\n3. Setting GUIDED mode...")
    mode_id = master.mode_mapping()['GUIDED']
    master.mav.set_mode_send(
        master.target_system,
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
        mode_id
    )
    time.sleep(2)

    # Arm with force
    print("\n4. Arming (force)...")
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
    print("   Waiting for arm confirmation...")
    armed = False
    for i in range(50):  # 5 second timeout
        msg = master.recv_match(type='HEARTBEAT', blocking=True, timeout=0.1)
        if msg:
            armed = msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED
            if armed:
                print("   ✅ Armed successfully")
                break
        time.sleep(0.1)

    if not armed:
        print("   ⚠️  Arming may have failed, but continuing...")

    time.sleep(1)

    # Set Mode 99
    print("\n5. Setting Mode 99 (LQR State Feedback)...")
    master.mav.set_mode_send(
        master.target_system,
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
        99  # Mode 99
    )

    # Wait for mode change
    time.sleep(2)

    # Verify mode
    msg = master.recv_match(type='HEARTBEAT', blocking=True, timeout=2.0)
    if msg and msg.custom_mode == 99:
        print("   ✅ Mode 99 ACTIVE!")
    else:
        print(f"   ⚠️  Current mode: {msg.custom_mode if msg else 'unknown'}")

    # Get home position for reference
    print("\n6. Getting home position...")
    master.mav.command_long_send(
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_CMD_REQUEST_MESSAGE,
        0,
        mavutil.mavlink.MAVLINK_MSG_ID_HOME_POSITION,
        0, 0, 0, 0, 0, 0
    )

    home_msg = master.recv_match(type='HOME_POSITION', blocking=True, timeout=2.0)
    if home_msg:
        print(f"   Home: lat={home_msg.latitude/1e7:.6f}, lon={home_msg.longitude/1e7:.6f}, alt={home_msg.altitude/1000:.1f}m")

    print("\n" + "=" * 70)
    print("TEST SEQUENCE: Hover → Climb 5m → Hold")
    print("=" * 70)

    # Test sequence
    test_duration = 30  # 30 seconds
    start_time = time.time()

    print("\nPhase 1: Hover at origin for 5 seconds")
    phase_start = time.time()
    while time.time() - phase_start < 5.0:
        # Send position command: [0, 0, 0] NED, hover velocity
        master.mav.set_position_target_local_ned_send(
            int((time.time() - start_time) * 1000),  # time_boot_ms
            master.target_system,
            master.target_component,
            mavutil.mavlink.MAV_FRAME_LOCAL_NED,
            0b0000111111000111,  # type_mask (ignore position, use velocity)
            0, 0, 0,             # x, y, z position (ignored)
            0, 0, 0,             # vx, vy, vz (hover)
            0, 0, 0,             # afx, afy, afz (ignored)
            0, 0                 # yaw, yaw_rate (ignore)
        )

        # Read telemetry
        msg = master.recv_match(type='LOCAL_POSITION_NED', blocking=False)
        if msg:
            print(f"  t={time.time()-start_time:.1f}s: pos=[{msg.x:.2f}, {msg.y:.2f}, {msg.z:.2f}]m, "
                  f"vel=[{msg.vx:.2f}, {msg.vy:.2f}, {msg.vz:.2f}]m/s")

        time.sleep(0.5)

    print("\nPhase 2: Climb to 5m at 1 m/s for 10 seconds")
    phase_start = time.time()
    while time.time() - phase_start < 10.0:
        # Send velocity command: climb at 1 m/s (vz = -1 in NED)
        master.mav.set_position_target_local_ned_send(
            int((time.time() - start_time) * 1000),
            master.target_system,
            master.target_component,
            mavutil.mavlink.MAV_FRAME_LOCAL_NED,
            0b0000111111000111,  # type_mask (use velocity)
            0, 0, 0,             # position (ignored)
            0, 0, -1.0,          # vx, vy, vz (climb at 1 m/s)
            0, 0, 0,             # acceleration (ignored)
            0, 0                 # yaw, yaw_rate
        )

        # Read telemetry
        msg = master.recv_match(type='LOCAL_POSITION_NED', blocking=False)
        if msg:
            alt = -msg.z  # Convert NED Z to altitude
            print(f"  t={time.time()-start_time:.1f}s: alt={alt:.2f}m, "
                  f"vel=[{msg.vx:.2f}, {msg.vy:.2f}, {msg.vz:.2f}]m/s")

        # Check for LQR telemetry
        lqr_msg = master.recv_match(type='NAMED_VALUE_FLOAT', blocking=False)
        if lqr_msg and lqr_msg.name.startswith('LQR'):
            print(f"    {lqr_msg.name}: {lqr_msg.value:.3f}")

        time.sleep(0.5)

    print("\nPhase 3: Hold position for 5 seconds")
    phase_start = time.time()
    while time.time() - phase_start < 5.0:
        # Send hover command
        master.mav.set_position_target_local_ned_send(
            int((time.time() - start_time) * 1000),
            master.target_system,
            master.target_component,
            mavutil.mavlink.MAV_FRAME_LOCAL_NED,
            0b0000111111000111,
            0, 0, 0,
            0, 0, 0,  # Hover (zero velocity)
            0, 0, 0,
            0, 0
        )

        msg = master.recv_match(type='LOCAL_POSITION_NED', blocking=False)
        if msg:
            alt = -msg.z
            print(f"  t={time.time()-start_time:.1f}s: alt={alt:.2f}m, holding...")

        time.sleep(0.5)

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
    time.sleep(2)

    print("\n" + "=" * 70)
    print("✅ Mode 99 LQR Test Complete!")
    print("=" * 70)

    master.close()
    return 0

if __name__ == "__main__":
    sys.exit(main())
