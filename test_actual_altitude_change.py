#!/usr/bin/env python3
"""
CRITICAL TEST: Actually measure altitude change in SITL.
This is what should have been tested before!
"""

import sys
import time
import numpy as np
from drone_gym.envs.pybullet_drone_env import PyBulletDroneEnv

def main():
    print("=" * 70)
    print("ACTUAL ALTITUDE CHANGE TEST - SITL")
    print("This test will MEASURE actual altitude movement")
    print("=" * 70)

    print("\n⚠️  CRITICAL: SITL must be running first!")
    print("\nIn another terminal, run:")
    print("  cd ~/ardupilot/ArduCopter")
    print("  ~/ardupilot/build/sitl/bin/arducopter --model + --speedup 1")
    print("\nWait for: 'APM: EKF3 IMU0 is using GPS'")
    print()

    proceed = input("Is SITL ready and initialized? (y/n): ")
    if proceed.lower() != 'y':
        return 1

    try:
        print("\n" + "=" * 70)
        print("PHASE 1: Connect and Arm")
        print("=" * 70)

        env = PyBulletDroneEnv(
            use_mavlink=True,
            mavlink_connection="tcp:127.0.0.1:5760",
            gui=False,
            drone_model="medium_quad",
        )

        if not env.mavlink or not env.mavlink.connected:
            print("❌ Cannot connect to SITL")
            print("Make sure SITL is running on tcp:127.0.0.1:5760")
            return 1

        print("✅ Connected to SITL")

        # Set GUIDED mode
        print("Setting GUIDED mode...")
        env.mavlink.set_mode("GUIDED", timeout=10.0)
        time.sleep(2)

        # Arm
        print("Arming...")
        if not env.mavlink.arm(timeout=10.0):
            print("⚠️  Arming failed - trying to continue anyway")
        else:
            print("✅ Armed")

        time.sleep(2)

        # Get initial state
        state = env.mavlink.get_state()
        print(f"\nInitial state:")
        print(f"  Position (NED): {state['position']}")
        print(f"  Altitude (AGL): {-state['position'][2]:.3f} m")
        print(f"  Armed: {state['armed']}")

        # Reset environment
        env.reset()
        time.sleep(1)

        print("\n" + "=" * 70)
        print("PHASE 2: Baseline - Record Starting Altitude")
        print("=" * 70)

        # Hover for a bit to stabilize
        print("Hovering for 3 seconds to get stable baseline...")
        for i in range(30):
            action = np.array([0.0, 0.0, 0.0, 0.0])
            env.step(action)
            time.sleep(0.1)

        state = env.mavlink.get_state()
        baseline_altitude = -state['position'][2]
        baseline_ned_z = state['position'][2]

        print(f"\n✅ Baseline established:")
        print(f"  Altitude (AGL): {baseline_altitude:.3f} m")
        print(f"  NED Z: {baseline_ned_z:.3f} m")

        print("\n" + "=" * 70)
        print("PHASE 3: CRITICAL TEST - Command UPWARD Motion")
        print("=" * 70)

        print("\nSending: action = [0, 0, +1.0, 0]")
        print("  In PyBullet convention: vz=+1.0 means UP")
        print("  After conversion: vz=-1.0 in NED means UP")
        print("\nExpected result: Altitude INCREASES (NED Z DECREASES)")
        print("\nMeasuring for 10 seconds...")

        altitude_history = []
        ned_z_history = []
        motor_rpm_history = []

        for i in range(100):  # 10 seconds
            # Command upward velocity
            action = np.array([0.0, 0.0, 1.0, 0.0])  # UP in PyBullet frame
            obs, reward, terminated, truncated, info = env.step(action)

            state = env.mavlink.get_state()
            current_alt = -state['position'][2]
            current_ned_z = state['position'][2]
            motor_rpms = info.get('motor_rpms', np.zeros(4))

            altitude_history.append(current_alt)
            ned_z_history.append(current_ned_z)
            motor_rpm_history.append(motor_rpms.mean())

            if i % 20 == 0:  # Print every 2 seconds
                print(f"t={i*0.1:.1f}s: "
                      f"alt={current_alt:.3f}m (Δ{current_alt-baseline_altitude:+.3f}), "
                      f"NED_Z={current_ned_z:.3f} (Δ{current_ned_z-baseline_ned_z:+.3f}), "
                      f"motors={motor_rpms.mean():.0f}rpm")

            time.sleep(0.1)

        final_altitude = altitude_history[-1]
        final_ned_z = ned_z_history[-1]

        altitude_change = final_altitude - baseline_altitude
        ned_z_change = final_ned_z - baseline_ned_z

        print("\n" + "=" * 70)
        print("RESULTS - THIS IS THE TRUTH")
        print("=" * 70)

        print(f"\nBaseline altitude: {baseline_altitude:.3f} m")
        print(f"Final altitude:    {final_altitude:.3f} m")
        print(f"Altitude change:   {altitude_change:+.3f} m")

        print(f"\nBaseline NED Z: {baseline_ned_z:.3f} m")
        print(f"Final NED Z:    {final_ned_z:.3f} m")
        print(f"NED Z change:   {ned_z_change:+.3f} m")

        print(f"\nAverage motor RPM: {np.mean(motor_rpm_history):.0f} RPM")
        print(f"Motor RPM range: {np.min(motor_rpm_history):.0f} - {np.max(motor_rpm_history):.0f} RPM")

        print("\n" + "=" * 70)
        print("VERDICT")
        print("=" * 70)

        if altitude_change > 1.0:
            print("\n✅✅✅ SUCCESS! ✅✅✅")
            print(f"Commanded +1.0 m/s UP → Altitude INCREASED by {altitude_change:.2f}m")
            print("✅ Coordinate frame conversion is WORKING!")
            print("✅ SITL altitude control is CORRECT!")
            result = True

        elif altitude_change < -1.0:
            print("\n❌❌❌ FAILURE! ❌❌❌")
            print(f"Commanded +1.0 m/s UP → Altitude DECREASED by {abs(altitude_change):.2f}m")
            print("❌ Coordinate frame conversion is BROKEN or NOT APPLIED!")
            print("❌ The vz negation is not working!")
            result = False

        elif abs(altitude_change) < 0.3:
            print("\n⚠️⚠️⚠️  INCONCLUSIVE ⚠️⚠️⚠️")
            print(f"Altitude barely changed ({altitude_change:+.3f}m)")
            print("Possible reasons:")
            print("  - Drone not responding to commands")
            print("  - Not properly armed")
            print("  - Controller gains too low")
            print(f"  - Motor RPMs: {np.mean(motor_rpm_history):.0f} (should be > 1000)")
            result = None

        else:
            print(f"\n⚠️  PARTIAL CHANGE ({altitude_change:+.3f}m)")
            print("Some response but less than expected")
            result = None

        # Disarm
        print("\nDisarming...")
        env.mavlink.disarm(timeout=5.0)
        env.close()

        if result is True:
            print("\n🎉 ALL SITL PROBLEMS CONFIRMED FIXED! 🎉")
            return 0
        elif result is False:
            print("\n❌ SITL altitude problem NOT FIXED")
            return 1
        else:
            print("\n⚠️  Test inconclusive - check SITL configuration")
            return 2

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
