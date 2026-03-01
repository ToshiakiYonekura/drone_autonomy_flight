#!/usr/bin/env python3
"""
Mode 99 Test with Docker-based SITL

This script launches SITL in a Docker container (more reliable in WSL2)
and tests Mode 99 LQR control.
"""

import sys
import time
import subprocess
from pymavlink import mavutil


def start_sitl_docker():
    """Start SITL in Docker container."""
    print("="*70)
    print("STARTING ARDUPILOT SITL IN DOCKER")
    print("="*70)

    # Stop any existing container
    subprocess.run(["docker", "stop", "ardupilot_sitl"],
                   capture_output=True, check=False)
    subprocess.run(["docker", "rm", "ardupilot_sitl"],
                   capture_output=True, check=False)

    # Build custom ArduPilot image with Mode 99
    print("\nChecking if ArduPilot with Mode 99 is built...")
    result = subprocess.run(
        ["docker", "images", "-q", "ardupilot-mode99:latest"],
        capture_output=True,
        text=True
    )

    if not result.stdout.strip():
        print("Building ArduPilot with Mode 99...")
        # TODO: Create Dockerfile for ArduPilot with Mode 99
        print("❌ Image not found. Please build ardupilot-mode99:latest first.")
        print("\nTo build:")
        print("  1. Create Dockerfile with Mode 99 code")
        print("  2. Run: docker build -t ardupilot-mode99:latest .")
        return False

    print("✅ Image found: ardupilot-mode99:latest")

    # Start SITL container
    print("\nStarting SITL container...")
    cmd = [
        "docker", "run",
        "-d",
        "--name", "ardupilot_sitl",
        "--network", "host",
        "--privileged",
        "ardupilot-mode99:latest",
        "bash", "-c",
        "cd /ardupilot/ArduCopter && ../Tools/autotest/sim_vehicle.py --console --map -I0"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Failed to start container: {result.stderr}")
        return False

    print("✅ SITL container started")
    return True


def wait_for_sitl(timeout=30):
    """Wait for SITL to be ready."""
    print(f"\nWaiting for SITL (timeout: {timeout}s)...")

    start = time.time()
    while time.time() - start < timeout:
        try:
            # Try to connect
            mav = mavutil.mavlink_connection('tcp:127.0.0.1:5760',
                                             source_system=255,
                                             timeout=2)
            mav.wait_heartbeat(timeout=2)

            # Check for position data
            msg = mav.recv_match(type='LOCAL_POSITION_NED', blocking=True, timeout=2.0)
            if msg:
                print(f"✅ SITL ready! Position: [{msg.x:.2f}, {msg.y:.2f}, {msg.z:.2f}]")
                mav.close()
                return True

        except Exception as e:
            pass

        time.sleep(2)
        print("  Still waiting...")

    print("❌ SITL not ready after timeout")
    return False


def test_mode99():
    """Test Mode 99 functionality."""
    print("\n" + "="*70)
    print("TESTING MODE 99")
    print("="*70)

    # Connect
    print("\nConnecting to SITL...")
    mav = mavutil.mavlink_connection('tcp:127.0.0.1:5760', source_system=255)
    mav.wait_heartbeat(timeout=10)
    print(f"✅ Connected to system {mav.target_system}")

    # Disable failsafes
    print("\nConfiguring parameters...")
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
    if not (hb and (hb.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)):
        print("❌ Failed to arm")
        return False
    print("✅ Armed")

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
    if not (hb and hb.custom_mode == 99):
        print(f"❌ Mode change failed. Current mode: {hb.custom_mode if hb else 'unknown'}")
        return False

    print("✅✅✅ MODE 99 IS ACTIVE! ✅✅✅")

    # Monitor telemetry
    print("\nMonitoring LQR telemetry for 10 seconds...")
    lqr_fields = set()
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
            if msg.name not in lqr_fields:
                lqr_fields.add(msg.name)
                print(f"  ✅ {msg.name}: {msg.value:.3f}")

        time.sleep(0.1)

    print(f"\n✅ Received {len(lqr_fields)} LQR telemetry types")
    print("\nLQR fields detected:")
    for field in sorted(lqr_fields):
        print(f"  - {field}")

    mav.close()
    return True


def stop_sitl_docker():
    """Stop SITL Docker container."""
    print("\n" + "="*70)
    print("STOPPING SITL")
    print("="*70)

    subprocess.run(["docker", "stop", "ardupilot_sitl"],
                   capture_output=True, check=False)
    subprocess.run(["docker", "rm", "ardupilot_sitl"],
                   capture_output=True, check=False)

    print("✅ SITL stopped")


def main():
    try:
        # Start SITL
        if not start_sitl_docker():
            return 1

        # Wait for ready
        if not wait_for_sitl():
            stop_sitl_docker()
            return 1

        # Test Mode 99
        success = test_mode99()

        # Cleanup
        stop_sitl_docker()

        if success:
            print("\n" + "="*70)
            print("✅ MODE 99 TEST SUCCESSFUL!")
            print("="*70)
            return 0
        else:
            print("\n❌ Mode 99 test failed")
            return 1

    except KeyboardInterrupt:
        print("\n\nTest interrupted")
        stop_sitl_docker()
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        stop_sitl_docker()
        return 1


if __name__ == '__main__':
    sys.exit(main())
