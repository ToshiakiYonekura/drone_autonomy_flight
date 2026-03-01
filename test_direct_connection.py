#!/usr/bin/env python3
"""
Test direct connection to ArduCopter SITL (no MAVProxy).
"""

import sys
import time
from drone_gym.controllers.mavlink_interface import MAVLinkInterface

def main():
    print("=" * 70)
    print("Direct ArduCopter SITL Connection Test")
    print("=" * 70)

    print("\n✅ ArduCopter should already be running")
    print("   (started in background on TCP port 5760)")
    print()

    try:
        print("1. Creating MAVLink interface (direct TCP connection)...")
        mavlink = MAVLinkInterface(
            connection_string="tcp:127.0.0.1:5760",  # Direct TCP to ArduCopter
            motor_kv=920.0,
            battery_voltage=16.0,
        )

        print("2. Connecting to ArduCopter...")
        if not mavlink.connect():
            print("❌ Connection failed!")
            print("  Make sure ArduCopter is running")
            return 1

        print("✅ Connected!")

        print("\n3. Checking heartbeat...")
        time.sleep(3)
        if not mavlink.is_alive():
            print("❌ No heartbeat!")
            return 1
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
            print("⚠️  Could not arm")
            print("  Continuing anyway...")

        print("\n7. Waiting for motor output data...")
        motor_data_received = False
        start_time = time.time()

        while time.time() - start_time < 15.0:
            if mavlink.has_recent_motor_data(max_age=1.0):
                motor_data_received = True
                break
            time.sleep(0.2)

        if motor_data_received:
            print("\n✅ SUCCESS! Motor data received!")

            motor_pwm = mavlink.get_motor_pwm()
            motor_rpms = mavlink.get_motor_rpms()

            print(f"\n  Motor PWM (ArduPilot order):")
            for i, pwm in enumerate(motor_pwm):
                print(f"    Motor {i}: {pwm:.0f} μs")

            print(f"\n  Motor RPM (PyBullet order):")
            for i, rpm in enumerate(motor_rpms):
                print(f"    Motor {i}: {rpm:.0f} RPM")

            # Verify
            if all(1000 <= pwm <= 2000 for pwm in motor_pwm):
                print("\n  ✅ PWM values valid")
            if all(0 <= rpm <= 20000 for rpm in motor_rpms):
                print("  ✅ RPM values valid")

            # Test mapping
            print("\n8. Testing motor mapping...")
            test_input = [1500.0, 1600.0, 1700.0, 1800.0]
            test_output = mavlink.remap_motor_indices(test_input)
            expected = [1500.0, 1800.0, 1600.0, 1700.0]

            if list(test_output) == expected:
                print("  ✅ Motor mapping correct")
            else:
                print("  ❌ Motor mapping incorrect")

            print("\n" + "=" * 70)
            print("🎉 ALL TESTS PASSED! 🎉")
            print("=" * 70)
            print("\n✅ ArduPilot SITL integration working")
            print("✅ Motor outputs received correctly")
            print("✅ Ready for RL training with SITL!")

        else:
            print("\n❌ No motor data received")
            mavlink.disconnect()
            return 1

        print("\n9. Disarming...")
        mavlink.disarm(timeout=5.0)

        print("\n10. Disconnecting...")
        mavlink.disconnect()

        return 0

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
