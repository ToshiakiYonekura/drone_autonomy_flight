#!/usr/bin/env python3
"""
Test MAVLink connection only (assumes SITL is already running).
Run this AFTER starting SITL manually.
"""

import sys
import time
from drone_gym.controllers.mavlink_interface import MAVLinkInterface

def main():
    print("=" * 70)
    print("MAVLink Connection Test")
    print("=" * 70)
    print("\n⚠️  Make sure ArduPilot SITL is running before proceeding!")
    print("\nTo start SITL:")
    print("  cd ~/ardupilot/ArduCopter")
    print("  ../Tools/autotest/sim_vehicle.py --vehicle ArduCopter --frame quad --no-rebuild\\")
    print("    --console --out udp:127.0.0.1:14550")
    print()

    input("Press ENTER when SITL is ready (showing 'APM: ArduPilot Ready')...")

    try:
        print("\n1. Creating MAVLink interface...")
        mavlink = MAVLinkInterface(
            connection_string="udp:127.0.0.1:14550",
            motor_kv=920.0,
            battery_voltage=16.0,
        )

        print("2. Connecting to ArduPilot...")
        if not mavlink.connect():
            print("❌ Connection failed!")
            print("  Check that SITL is running and accessible at udp:127.0.0.1:14550")
            return 1

        print("✅ Connected!")

        print("\n3. Checking heartbeat...")
        time.sleep(2)
        if not mavlink.is_alive():
            print("❌ No heartbeat!")
            return 1
        print("✅ Heartbeat received")

        print("\n4. Getting vehicle state...")
        state = mavlink.get_state()
        print(f"  Position (NED): {state['position']}")
        print(f"  Attitude: roll={state['attitude'][0]:.3f}, pitch={state['attitude'][1]:.3f}, yaw={state['attitude'][2]:.3f}")
        print(f"  Armed: {state['armed']}")
        print(f"  Mode: {state['mode']}")

        print("\n5. Setting GUIDED mode...")
        if mavlink.set_mode("GUIDED", timeout=10.0):
            print("✅ GUIDED mode set")
        else:
            print("⚠️  Could not set GUIDED mode")
            print("  Try manually: mode GUIDED")

        print("\n6. Arming drone...")
        if mavlink.arm(timeout=10.0):
            print("✅ Armed successfully")
        else:
            print("⚠️  Could not arm")
            print("  Try manually: arm throttle")
            print("  This is OK - continuing test...")

        print("\n7. Waiting for motor output data (SERVO_OUTPUT_RAW messages)...")
        print("  This is the critical test - receiving motor PWM from ArduPilot...")

        motor_data_received = False
        start_time = time.time()
        attempts = 0

        while time.time() - start_time < 15.0:
            if mavlink.has_recent_motor_data(max_age=1.0):
                motor_data_received = True
                break

            # Print progress
            attempts += 1
            if attempts % 10 == 0:
                elapsed = time.time() - start_time
                print(f"  Waiting... ({elapsed:.1f}s elapsed)")

            time.sleep(0.2)

        if motor_data_received:
            print("\n✅ SUCCESS! Motor output data received from ArduPilot!")

            motor_pwm = mavlink.get_motor_pwm()
            motor_rpms = mavlink.get_motor_rpms()

            print(f"\n  Raw PWM values (ArduPilot order):")
            for i, pwm in enumerate(motor_pwm):
                print(f"    Motor {i}: {pwm:.0f} μs")

            print(f"\n  Converted RPM values (PyBullet order):")
            for i, rpm in enumerate(motor_rpms):
                print(f"    Motor {i}: {rpm:.0f} RPM")

            # Verify values
            errors = []

            if not all(1000 <= pwm <= 2000 for pwm in motor_pwm):
                errors.append("PWM values out of range (should be 1000-2000 μs)")
            else:
                print("\n  ✅ PWM values valid (1000-2000 μs)")

            if not all(0 <= rpm <= 20000 for rpm in motor_rpms):
                errors.append("RPM values out of range (should be 0-20000)")
            else:
                print("  ✅ RPM values valid (0-20000 RPM)")

            # Test motor mapping
            print("\n8. Verifying motor index mapping...")
            test_input = [1500.0, 1600.0, 1700.0, 1800.0]
            test_output = mavlink.remap_motor_indices(test_input)
            expected = [1500.0, 1800.0, 1600.0, 1700.0]

            print(f"  Test input (ArduPilot order): {test_input}")
            print(f"  Test output (PyBullet order): {list(test_output)}")
            print(f"  Expected:                     {expected}")

            if list(test_output) == expected:
                print("  ✅ Motor mapping correct")
            else:
                errors.append("Motor mapping incorrect")

            # Test PWM to RPM conversion
            print("\n9. Verifying PWM to RPM conversion...")
            test_conversions = [
                (1000, 0),      # 0% throttle
                (1500, 7360),   # 50% throttle
                (2000, 14720),  # 100% throttle
            ]

            for pwm, expected_rpm in test_conversions:
                actual_rpm = mavlink.pwm_to_rpm(pwm)
                print(f"  PWM {pwm} μs → {actual_rpm:.0f} RPM (expected {expected_rpm})")
                if abs(actual_rpm - expected_rpm) > 0.1:
                    errors.append(f"PWM-to-RPM conversion error at {pwm}")

            if len([e for e in errors if "PWM-to-RPM" in e]) == 0:
                print("  ✅ PWM to RPM conversion correct")

            # Summary
            print("\n" + "=" * 70)
            if len(errors) == 0:
                print("🎉 ALL TESTS PASSED! 🎉")
                print("=" * 70)
                print("\n✅ ArduPilot SITL motor outputs correctly received")
                print("✅ Motor index mapping working")
                print("✅ PWM to RPM conversion working")
                print("\n🚀 Ready for RL training with SITL control!")
            else:
                print("⚠️  SOME ISSUES DETECTED")
                print("=" * 70)
                for error in errors:
                    print(f"  ❌ {error}")
                mavlink.disconnect()
                return 1

        else:
            print("\n❌ FAILED: No motor output data received from ArduPilot!")
            print("\nTroubleshooting:")
            print("  1. Check if drone is armed in MAVProxy: 'arm throttle'")
            print("  2. Check stream rates: 'set streamrate 50'")
            print("  3. Verify SERVO_OUTPUT_RAW messages in MAVProxy:")
            print("     - Type: link 1")
            print("     - Type: output servo")
            print("  4. Make sure SITL hasn't crashed")
            mavlink.disconnect()
            return 1

        print("\n10. Disarming...")
        mavlink.disarm(timeout=5.0)

        print("\n11. Disconnecting...")
        mavlink.disconnect()

        print("\n" + "=" * 70)
        print("Test completed successfully!")
        print("You can now stop SITL (Ctrl+C in SITL terminal)")
        print("=" * 70)

        return 0

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
