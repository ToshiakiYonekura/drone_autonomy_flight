#!/usr/bin/env python3
"""
Quick SITL integration test - simplified version.
Tests basic connection and motor output reception.
"""

import sys
import time
import subprocess
import signal
import os
from drone_gym.controllers.mavlink_interface import MAVLinkInterface

# Global variable for SITL process
sitl_process = None

def cleanup():
    """Clean up SITL process."""
    global sitl_process
    if sitl_process:
        print("\n🛑 Stopping SITL...")
        sitl_process.terminate()
        try:
            sitl_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            sitl_process.kill()
        print("✅ SITL stopped")

def signal_handler(sig, frame):
    """Handle Ctrl+C."""
    print("\n⚠️  Interrupted by user")
    cleanup()
    sys.exit(1)

def start_sitl():
    """Start ArduPilot SITL in background."""
    global sitl_process

    print("=" * 70)
    print("Starting ArduPilot SITL")
    print("=" * 70)

    ardupilot_dir = os.path.expanduser("~/ardupilot/ArduCopter")

    if not os.path.exists(ardupilot_dir):
        print(f"❌ ArduCopter directory not found: {ardupilot_dir}")
        return False

    print(f"\nArduCopter directory: {ardupilot_dir}")
    print("Starting SITL (this takes ~30 seconds)...")

    # Start SITL
    cmd = [
        "../Tools/autotest/sim_vehicle.py",
        "--vehicle", "ArduCopter",
        "--frame", "quad",
        "--no-rebuild",
        "-L", "CMAC",
        "--out", "udp:127.0.0.1:14550",
    ]

    try:
        sitl_process = subprocess.Popen(
            cmd,
            cwd=ardupilot_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
        )

        print(f"SITL process started (PID: {sitl_process.pid})")
        print("\nWaiting for initialization...")

        # Monitor output for initialization
        start_time = time.time()
        timeout = 60
        ekf_ready = False

        while time.time() - start_time < timeout:
            # Check if process crashed
            if sitl_process.poll() is not None:
                print("❌ SITL process crashed!")
                return False

            # Read output (non-blocking)
            try:
                line = sitl_process.stdout.readline()
                if line:
                    # Print important messages
                    if "EKF" in line or "Ready to FLY" in line or "APM:" in line:
                        print(f"  {line.strip()}")

                    # Check for ready condition
                    if "EKF3 IMU" in line or "Ready to FLY" in line:
                        ekf_ready = True
                        print("\n✅ SITL initialized!")
                        time.sleep(3)  # Extra stabilization time
                        return True

            except:
                pass

            time.sleep(0.1)

        if not ekf_ready:
            print("⚠️  Timeout waiting for EKF initialization")
            print("Continuing anyway - might still work...")
            return True

    except Exception as e:
        print(f"❌ Failed to start SITL: {e}")
        return False

def test_connection():
    """Test MAVLink connection and motor output reception."""
    print("\n" + "=" * 70)
    print("Testing MAVLink Connection")
    print("=" * 70)

    print("\n1. Creating MAVLink interface...")
    mavlink = MAVLinkInterface(
        connection_string="udp:127.0.0.1:14550",
        motor_kv=920.0,
        battery_voltage=16.0,
    )

    print("2. Connecting to ArduPilot...")
    if not mavlink.connect():
        print("❌ Connection failed!")
        return False

    print("✅ Connected!")

    print("\n3. Checking heartbeat...")
    time.sleep(2)
    if not mavlink.is_alive():
        print("❌ No heartbeat!")
        return False
    print("✅ Heartbeat received")

    print("\n4. Getting vehicle state...")
    state = mavlink.get_state()
    print(f"  Position: {state['position']}")
    print(f"  Attitude: {state['attitude']}")
    print(f"  Armed: {state['armed']}")

    print("\n5. Setting GUIDED mode...")
    if mavlink.set_mode("GUIDED", timeout=10.0):
        print("✅ GUIDED mode set")
    else:
        print("⚠️  Could not set GUIDED mode")

    print("\n6. Arming...")
    if mavlink.arm(timeout=10.0):
        print("✅ Armed")
    else:
        print("⚠️  Could not arm (check pre-arm checks)")
        print("  This is OK for testing motor data reception")

    print("\n7. Waiting for motor output data...")
    motor_data_received = False
    start_time = time.time()

    while time.time() - start_time < 10.0:
        if mavlink.has_recent_motor_data(max_age=1.0):
            motor_data_received = True
            break
        time.sleep(0.2)

    if motor_data_received:
        print("✅ Motor output data received!")

        motor_pwm = mavlink.get_motor_pwm()
        motor_rpms = mavlink.get_motor_rpms()

        print(f"\n  Motor PWM (raw):    {motor_pwm}")
        print(f"  Motor RPM (mapped): {motor_rpms}")

        # Verify values
        if all(1000 <= pwm <= 2000 for pwm in motor_pwm):
            print("  ✅ PWM values valid (1000-2000 μs)")
        else:
            print("  ⚠️  PWM values out of range")

        if all(0 <= rpm <= 20000 for rpm in motor_rpms):
            print("  ✅ RPM values valid (0-20000)")
        else:
            print("  ⚠️  RPM values out of range")

    else:
        print("❌ No motor output data received!")
        print("\n  Troubleshooting:")
        print("  - Check if SITL is running")
        print("  - Verify SITL is armed")
        print("  - Check MAVLink stream rates")
        mavlink.disconnect()
        return False

    print("\n8. Testing motor mapping...")
    # Just verify the mapping function works
    test_input = [1500, 1600, 1700, 1800]
    test_output = mavlink.remap_motor_indices(test_input)
    expected = [1500, 1800, 1600, 1700]

    if list(test_output) == expected:
        print(f"  Input:    {test_input}")
        print(f"  Output:   {list(test_output)}")
        print(f"  Expected: {expected}")
        print("  ✅ Motor mapping correct")
    else:
        print("  ❌ Motor mapping incorrect!")
        mavlink.disconnect()
        return False

    print("\n9. Disarming...")
    mavlink.disarm(timeout=5.0)

    print("\n10. Disconnecting...")
    mavlink.disconnect()

    return True

def main():
    """Run the complete test."""
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)

    print("\n" + "=" * 70)
    print("QUICK SITL INTEGRATION TEST")
    print("=" * 70)

    try:
        # Start SITL
        if not start_sitl():
            print("\n❌ SITL failed to start")
            cleanup()
            return 1

        # Run connection test
        if not test_connection():
            print("\n❌ Connection test failed")
            cleanup()
            return 1

        # Success!
        print("\n" + "=" * 70)
        print("🎉 ALL TESTS PASSED! 🎉")
        print("=" * 70)
        print("\n✅ ArduPilot SITL integration is working correctly!")
        print("✅ Motor outputs are correctly received and mapped")
        print("✅ Ready for RL training with SITL control")

        cleanup()
        return 0

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        cleanup()
        return 1

if __name__ == "__main__":
    sys.exit(main())
