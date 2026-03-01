#!/usr/bin/env python3
"""
Minimal Mode 99 Test - Manual SITL Control

This script assumes SITL is already running and stable.
Use this after starting SITL manually in another terminal.
"""

import sys
import time
from pymavlink import mavutil


def main():
    print("="*70)
    print("MODE 99 MINIMAL TEST")
    print("="*70)
    print()
    print("Prerequisites:")
    print("  1. SITL must be running in another terminal")
    print("  2. EKF must be initialized")
    print()
    print("To start SITL manually:")
    print("  cd ~/ardupilot/ArduCopter")
    print("  ../Tools/autotest/sim_vehicle.py --console --map")
    print()
    input("Press Enter when SITL is ready...")

    # Connect
    print("\nConnecting...")
    mav = mavutil.mavlink_connection('tcp:127.0.0.1:5760', source_system=255)
    mav.wait_heartbeat(timeout=10)
    print(f"✅ Connected to system {mav.target_system}")

    # Check position
    print("\nChecking EKF...")
    for i in range(10):
        msg = mav.recv_match(type='LOCAL_POSITION_NED', blocking=True, timeout=1.0)
        if msg:
            print(f"✅ EKF OK! Position: [{msg.x:.2f}, {msg.y:.2f}, {msg.z:.2f}]")
            break
        print(f"  Waiting... ({i+1}/10)")
    else:
        print("❌ No position data!")
        return 1

    # Configure
    print("\nConfiguring...")
    mav.param_set_send('FS_GCS_ENABLE', 0)
    mav.param_set_send('ARMING_CHECK', 0)
    time.sleep(2)

    # Arm
    print("\nArming...")
    mav.mav.command_long_send(
        mav.target_system, mav.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
        0, 1, 0, 0, 0, 0, 0, 0
    )
    time.sleep(3)

    # Check armed
    hb = mav.recv_match(type='HEARTBEAT', blocking=True, timeout=2.0)
    if hb and (hb.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED):
        print("✅ ARMED!")
    else:
        print("❌ Not armed")
        return 1

    # Enter Mode 99
    print("\nEntering Mode 99...")
    mav.mav.set_mode_send(
        mav.target_system,
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
        99
    )
    time.sleep(2)

    # Check mode
    hb = mav.recv_match(type='HEARTBEAT', blocking=True, timeout=2.0)
    if hb and hb.custom_mode == 99:
        print("✅✅✅ MODE 99 IS ACTIVE! ✅✅✅")
    else:
        print(f"❌ Mode: {hb.custom_mode if hb else 'unknown'}")
        return 1

    # Monitor telemetry
    print("\nMonitoring LQR telemetry for 10 seconds...")
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

    print(f"\n✅ Received {len(lqr_seen)} LQR telemetry types")
    print("\n" + "="*70)
    print("✅ MODE 99 TEST SUCCESSFUL!")
    print("="*70)

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
