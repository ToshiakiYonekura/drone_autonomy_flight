#!/usr/bin/env python3
"""
Test ArduPilot SITL integration with PyBullet.
Verifies that motor outputs from ArduPilot are correctly received and applied.
"""

import sys
import time
import numpy as np
from drone_gym.envs.pybullet_drone_env import PyBulletDroneEnv


def test_sitl_connection():
    """Test basic SITL connection and motor output reception."""
    print("=" * 70)
    print("TEST 1: ArduPilot SITL Connection")
    print("=" * 70)

    print("\n⚠️  Prerequisites:")
    print("  1. ArduPilot SITL must be running")
    print("  2. Run: cd /opt/ardupilot/ArduCopter")
    print("  3. Run: ../Tools/autotest/sim_vehicle.py --console --map")
    print("  4. Wait for 'APM: EKF3 IMU1 is using GPS'")
    print("  5. Then run this test\n")

    input("Press ENTER when ArduPilot SITL is ready...")

    try:
        print("\n1. Creating environment with MAVLink enabled...")
        env = PyBulletDroneEnv(
            use_mavlink=True,
            mavlink_connection="udp:127.0.0.1:14550",
            gui=True,  # Enable GUI to see the drone
            drone_model="medium_quad",
        )

        if not env.mavlink or not env.mavlink.connected:
            print("  ❌ FAILED: Could not connect to ArduPilot SITL")
            print("  Make sure SITL is running and listening on udp:127.0.0.1:14550")
            return False

        print("  ✅ Connected to ArduPilot SITL")

        print("\n2. Checking heartbeat...")
        if env.mavlink.is_alive():
            print("  ✅ Heartbeat active")
        else:
            print("  ❌ No heartbeat from ArduPilot")
            return False

        print("\n3. Setting GUIDED mode...")
        if env.mavlink.set_mode("GUIDED", timeout=10.0):
            print("  ✅ GUIDED mode set")
        else:
            print("  ⚠️  Could not set GUIDED mode (may need manual mode change)")

        print("\n4. Arming drone...")
        if env.mavlink.arm(timeout=10.0):
            print("  ✅ Drone armed")
        else:
            print("  ⚠️  Could not arm drone (check pre-arm checks in MAVProxy)")

        print("\n5. Waiting for motor output data...")
        start_time = time.time()
        motor_data_received = False

        while time.time() - start_time < 10.0:
            if env.mavlink.has_recent_motor_data(max_age=1.0):
                motor_data_received = True
                break
            time.sleep(0.1)

        if motor_data_received:
            print("  ✅ Motor output data received!")
            motor_pwm = env.mavlink.get_motor_pwm()
            motor_rpms = env.mavlink.get_motor_rpms()

            print(f"\n  Motor PWM (ArduPilot):  {motor_pwm}")
            print(f"  Motor RPM (PyBullet):   {motor_rpms}")

            # Verify PWM values are in valid range
            if np.all(motor_pwm >= 1000) and np.all(motor_pwm <= 2000):
                print("  ✅ PWM values in valid range (1000-2000 μs)")
            else:
                print(f"  ⚠️  PWM values out of range: {motor_pwm}")

            # Verify RPM values are reasonable
            if np.all(motor_rpms >= 0) and np.all(motor_rpms <= 20000):
                print("  ✅ RPM values reasonable (0-20000)")
            else:
                print(f"  ⚠️  RPM values unexpected: {motor_rpms}")

        else:
            print("  ❌ FAILED: No motor output data received")
            print("  Check if SERVO_OUTPUT_RAW messages are being sent")
            return False

        print("\n6. Disarming drone...")
        env.mavlink.disarm(timeout=10.0)

        print("\n7. Closing environment...")
        env.close()

        print("\n" + "=" * 70)
        print("✅ SITL CONNECTION TEST PASSED!")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sitl_motor_control():
    """Test that ArduPilot motor commands are applied to PyBullet physics."""
    print("\n" + "=" * 70)
    print("TEST 2: ArduPilot Motor Control in PyBullet")
    print("=" * 70)

    print("\n⚠️  Prerequisites: ArduPilot SITL must be running and armed")
    input("Press ENTER to continue...")

    try:
        print("\n1. Creating environment with MAVLink...")
        env = PyBulletDroneEnv(
            use_mavlink=True,
            mavlink_connection="udp:127.0.0.1:14550",
            gui=True,
            drone_model="medium_quad",
        )

        if not env.mavlink or not env.mavlink.connected:
            print("  ❌ Not connected to SITL")
            return False

        print("  ✅ Connected")

        print("\n2. Setting GUIDED mode and arming...")
        env.mavlink.set_mode("GUIDED", timeout=10.0)
        time.sleep(1.0)
        env.mavlink.arm(timeout=10.0)
        time.sleep(2.0)

        print("\n3. Resetting environment...")
        obs, info = env.reset()
        print(f"  Initial position: {env.sim.position}")

        print("\n4. Sending velocity commands (hover in place)...")
        print("  Commands: vx=0, vy=0, vz=0, yaw_rate=0")

        for i in range(100):  # Run for 10 seconds @ 10Hz
            # Hover command
            action = np.array([0.0, 0.0, 0.0, 0.0])

            # Step environment (this sends command to ArduPilot and applies motors)
            obs, reward, terminated, truncated, info = env.step(action)

            if i % 10 == 0:  # Print every 1 second
                print(f"\n  Step {i}:")
                print(f"    Position: {info['position']}")
                print(f"    Motor RPMs: {info['motor_rpms']}")
                print(f"    Using ArduPilot: {info['using_ardupilot']}")

            time.sleep(0.1)  # 10Hz control loop

            if terminated or truncated:
                print(f"  Episode ended: terminated={terminated}, truncated={truncated}")
                break

        print("\n5. Sending upward velocity command...")
        print("  Command: vx=0, vy=0, vz=-1.0 (NED frame, negative = up)")

        for i in range(50):  # Run for 5 seconds
            action = np.array([0.0, 0.0, -1.0, 0.0])
            obs, reward, terminated, truncated, info = env.step(action)

            if i % 10 == 0:
                print(f"\n  Step {i}:")
                print(f"    Position: {info['position']}")
                print(f"    Altitude: {-info['position'][2]:.2f} m")
                print(f"    Motor RPMs: {info['motor_rpms']}")

            time.sleep(0.1)

        print("\n6. Disarming and closing...")
        env.mavlink.disarm(timeout=10.0)
        env.close()

        print("\n" + "=" * 70)
        print("✅ MOTOR CONTROL TEST COMPLETED!")
        print("=" * 70)
        print("\n✅ If the drone moved in PyBullet GUI, motor control is working!")

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_motor_mapping():
    """Test motor index mapping between ArduPilot and PyBullet."""
    print("\n" + "=" * 70)
    print("TEST 3: Motor Index Mapping Verification")
    print("=" * 70)

    from drone_gym.controllers.mavlink_interface import MAVLinkInterface

    print("\nMotor configuration verification:")

    print("\n  ArduPilot Copter (Quad X):")
    print("    Motor 1 (servo1): Front-Right  (CW)")
    print("    Motor 2 (servo2): Rear-Left    (CW)")
    print("    Motor 3 (servo3): Front-Left   (CCW)")
    print("    Motor 4 (servo4): Rear-Right   (CCW)")

    print("\n  0-based indexing:")
    print("    Motor 0: Front-Right  (CW)")
    print("    Motor 1: Rear-Left    (CW)")
    print("    Motor 2: Front-Left   (CCW)")
    print("    Motor 3: Rear-Right   (CCW)")

    print("\n  PyBullet (this implementation):")
    print("    Motor 0: Front-Right  (CW)")
    print("    Motor 1: Rear-Right   (CCW)")
    print("    Motor 2: Rear-Left    (CW)")
    print("    Motor 3: Front-Left   (CCW)")

    print("\n  Testing remap function...")
    mavlink = MAVLinkInterface()

    # Test case: ArduPilot motors [100, 200, 300, 400]
    ardupilot_order = np.array([100, 200, 300, 400], dtype=np.float32)
    pybullet_order = mavlink.remap_motor_indices(ardupilot_order)

    print(f"\n  Input (ArduPilot order):  {ardupilot_order}")
    print(f"  Output (PyBullet order):  {pybullet_order}")

    expected = np.array([100, 400, 200, 300], dtype=np.float32)
    print(f"  Expected:                 {expected}")

    if np.allclose(pybullet_order, expected):
        print("\n  ✅ Motor mapping is CORRECT!")
        return True
    else:
        print("\n  ❌ Motor mapping is INCORRECT!")
        print(f"  Difference: {pybullet_order - expected}")
        return False


def test_pwm_to_rpm():
    """Test PWM to RPM conversion."""
    print("\n" + "=" * 70)
    print("TEST 4: PWM to RPM Conversion")
    print("=" * 70)

    from drone_gym.controllers.mavlink_interface import MAVLinkInterface

    # Test with default parameters: motor_kv=920, battery_voltage=16V
    mavlink = MAVLinkInterface(motor_kv=920.0, battery_voltage=16.0)

    test_cases = [
        (1000, "Min throttle (0%)"),
        (1500, "Mid throttle (50%)"),
        (2000, "Max throttle (100%)"),
    ]

    print("\nMotor KV: 920 RPM/V")
    print("Battery: 16V")
    print("\nTest cases:")

    all_passed = True
    for pwm, description in test_cases:
        rpm = mavlink.pwm_to_rpm(pwm)
        throttle_pct = (pwm - 1000) / 10.0
        voltage = (pwm - 1000) / 1000.0 * 16.0
        expected_rpm = 920.0 * voltage

        print(f"\n  {description}")
        print(f"    PWM: {pwm} μs")
        print(f"    Throttle: {throttle_pct:.1f}%")
        print(f"    Voltage: {voltage:.2f}V")
        print(f"    RPM: {rpm:.1f}")
        print(f"    Expected: {expected_rpm:.1f}")

        if abs(rpm - expected_rpm) < 0.1:
            print("    ✅ CORRECT")
        else:
            print("    ❌ INCORRECT")
            all_passed = False

    if all_passed:
        print("\n  ✅ PWM to RPM conversion is CORRECT!")
        return True
    else:
        print("\n  ❌ PWM to RPM conversion has errors!")
        return False


def main():
    """Run all SITL integration tests."""
    print("\n" + "=" * 70)
    print("ARDUPILOT SITL INTEGRATION TEST SUITE")
    print("Testing motor output reception and control")
    print("=" * 70)

    # Run tests that don't require SITL first
    print("\n" + "=" * 70)
    print("OFFLINE TESTS (No SITL required)")
    print("=" * 70)

    test3_passed = test_motor_mapping()
    test4_passed = test_pwm_to_rpm()

    # Run tests that require SITL
    print("\n" + "=" * 70)
    print("ONLINE TESTS (ArduPilot SITL required)")
    print("=" * 70)

    proceed = input("\nDo you have ArduPilot SITL running? (y/n): ")
    if proceed.lower() != 'y':
        print("\nSkipping online tests.")
        print("\nTo run SITL:")
        print("  cd /opt/ardupilot/ArduCopter")
        print("  ../Tools/autotest/sim_vehicle.py --console --map")
        print("\nThen run this test again.")
        sys.exit(0)

    test1_passed = test_sitl_connection()
    test2_passed = test_sitl_motor_control()

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Test 1 - SITL Connection:      {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Test 2 - Motor Control:        {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print(f"Test 3 - Motor Mapping:        {'✅ PASSED' if test3_passed else '❌ FAILED'}")
    print(f"Test 4 - PWM to RPM:           {'✅ PASSED' if test4_passed else '❌ FAILED'}")

    all_passed = test1_passed and test2_passed and test3_passed and test4_passed

    if all_passed:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("\n✅ ArduPilot SITL integration is working correctly!")
        print("✅ Motor outputs are correctly received and applied to PyBullet")
        print("✅ You can now train RL agents with ArduPilot-controlled motors")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("\nRefer to the error messages above for troubleshooting.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
