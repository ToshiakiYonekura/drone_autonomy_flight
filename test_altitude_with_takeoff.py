#!/usr/bin/env python3
"""
Improved altitude test with proper takeoff sequence.
"""

import sys
import time
import numpy as np
from drone_gym.envs.pybullet_drone_env import PyBulletDroneEnv

def main():
    print("=" * 70)
    print("ALTITUDE TEST WITH TAKEOFF - SITL")
    print("=" * 70)

    print("\n⚠️  Make sure SITL is running in another terminal!")

    proceed = input("\nIs SITL ready? (y/n): ")
    if proceed.lower() != 'y':
        return 1

    try:
        print("\n" + "=" * 70)
        print("PHASE 1: Connect")
        print("=" * 70)

        env = PyBulletDroneEnv(
            use_mavlink=True,
            mavlink_connection="tcp:127.0.0.1:5760",
            gui=False,
            drone_model="medium_quad",
        )

        if not env.mavlink or not env.mavlink.connected:
            print("❌ Cannot connect to SITL")
            return 1

        print("✅ Connected to SITL")

        # Wait for EKF to initialize
        print("\nWaiting 3 seconds for EKF to initialize...")
        time.sleep(3)

        print("\n" + "=" * 70)
        print("PHASE 2: Set Mode and Arm")
        print("=" * 70)

        # Set GUIDED mode
        print("Setting GUIDED mode...")
        env.mavlink.set_mode("GUIDED", timeout=10.0)
        time.sleep(1)

        # Force arm (bypass pre-arm checks)
        print("Arming with force=True...")
        if not env.mavlink.arm(timeout=10.0, force=True):
            print("❌ Arming failed even with force")
            return 1

        print("✅ Armed successfully")
        time.sleep(1)

        # Verify armed state
        state = env.mavlink.get_state()
        print(f"\nArmed state: {state['armed']}")
        if not state['armed']:
            print("❌ Drone reports not armed!")
            return 1

        print("\n" + "=" * 70)
        print("PHASE 3: Takeoff to 5m")
        print("=" * 70)

        print("Commanding upward velocity for 8 seconds...")
        for i in range(80):  # 8 seconds
            # Command UP at 1 m/s
            action = np.array([0.0, 0.0, 1.0, 0.0])
            obs, reward, terminated, truncated, info = env.step(action)

            state = env.mavlink.get_state()
            current_alt = -state['position'][2]
            motor_rpms = info.get('motor_rpms', np.zeros(4))

            if i % 20 == 0:  # Print every 2 seconds
                print(f"t={i*0.1:.1f}s: alt={current_alt:.2f}m, motors={motor_rpms.mean():.0f}rpm")

            time.sleep(0.1)

        # Final measurement
        state = env.mavlink.get_state()
        final_alt = -state['position'][2]
        motor_rpms = info.get('motor_rpms', np.zeros(4))

        print("\n" + "=" * 70)
        print("RESULTS")
        print("=" * 70)

        print(f"\nFinal altitude: {final_alt:.2f} m")
        print(f"Motor RPMs: {motor_rpms}")
        print(f"Average motor RPM: {motor_rpms.mean():.0f}")

        print("\n" + "=" * 70)
        print("VERDICT")
        print("=" * 70)

        if motor_rpms.mean() < 100:
            print("\n❌❌❌ MOTORS NOT SPINNING ❌❌❌")
            print("Motor outputs not being received from SITL")
            print("This is the real problem - need to debug motor output reception")
            result = False
        elif final_alt > 2.0:
            print("\n✅✅✅ SUCCESS! ✅✅✅")
            print(f"Drone climbed to {final_alt:.2f}m")
            print("✅ Altitude control is WORKING!")
            print("✅ Coordinate frame conversion is CORRECT!")
            result = True
        elif final_alt < -2.0:
            print("\n❌❌❌ INVERTED! ❌❌❌")
            print(f"Commanded UP but went DOWN to {final_alt:.2f}m")
            print("❌ Coordinate frame is INVERTED!")
            result = False
        else:
            print(f"\n⚠️  MINIMAL CHANGE ({final_alt:.2f}m)")
            print("Drone is responding but not as expected")
            result = None

        # Disarm
        print("\nDisarming...")
        env.mavlink.disarm(timeout=5.0)
        env.close()

        return 0 if result is True else (1 if result is False else 2)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
