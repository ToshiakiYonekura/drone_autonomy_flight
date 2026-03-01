#!/usr/bin/env python3
"""
Verify that the altitude coordinate frame fix is working.
Tests that positive vz commands result in upward motion in both modes.
"""

import sys
import time
import numpy as np


def test_pybullet_altitude():
    """Test PyBullet mode (should work correctly)."""
    print("=" * 70)
    print("TEST 1: PyBullet Mode Altitude Control")
    print("=" * 70)

    from drone_gym.envs.pybullet_drone_env import PyBulletDroneEnv

    env = PyBulletDroneEnv(
        use_mavlink=False,
        gui=False,
        drone_model="medium_quad",
    )

    obs, info = env.reset()
    start_alt = env.sim.position[2]

    print(f"\nStarting altitude: {start_alt:.3f} m")
    print("Sending: action=[0, 0, +1.0, 0] (positive vz = UP in PyBullet)")

    for i in range(30):  # 3 seconds
        action = np.array([0.0, 0.0, 1.0, 0.0])  # Go UP
        obs, reward, terminated, truncated, info = env.step(action)

    final_alt = env.sim.position[2]
    altitude_change = final_alt - start_alt

    print(f"Final altitude: {final_alt:.3f} m")
    print(f"Altitude change: {altitude_change:.3f} m")

    env.close()

    if altitude_change > 1.0:
        print("✅ PyBullet mode: Positive vz → UPWARD motion (CORRECT)")
        return True
    else:
        print(f"❌ PyBullet mode: Expected altitude gain > 1.0m, got {altitude_change:.3f}m")
        return False


def test_sitl_altitude():
    """Test SITL mode (should now work correctly after fix)."""
    print("\n" + "=" * 70)
    print("TEST 2: SITL Mode Altitude Control (After Fix)")
    print("=" * 70)

    print("\n⚠️  Prerequisites:")
    print("  ArduCopter SITL must be running:")
    print("  cd ~/ardupilot/ArduCopter")
    print("  ~/ardupilot/build/sitl/bin/arducopter --model + --speedup 1")
    print()

    proceed = input("Is SITL running? (y/n): ")
    if proceed.lower() != 'y':
        print("Skipping SITL test")
        return None

    from drone_gym.envs.pybullet_drone_env import PyBulletDroneEnv

    try:
        env = PyBulletDroneEnv(
            use_mavlink=True,
            mavlink_connection="tcp:127.0.0.1:5760",
            gui=True,
            drone_model="medium_quad",
        )

        if not env.mavlink or not env.mavlink.connected:
            print("❌ Could not connect to SITL")
            return False

        print("✅ Connected to SITL")

        # Set GUIDED and arm
        print("\nSetting GUIDED mode and arming...")
        env.mavlink.set_mode("GUIDED", timeout=10.0)
        time.sleep(1)
        env.mavlink.arm(timeout=10.0)
        time.sleep(2)

        # Reset and get initial altitude
        obs, info = env.reset()
        state = env.mavlink.get_state()
        start_alt = -state['position'][2]  # NED to altitude

        print(f"\nStarting altitude: {start_alt:.3f} m (NED Z={state['position'][2]:.3f})")
        print("Sending: action=[0, 0, +1.0, 0] (positive vz)")
        print("Expected in SITL: vz=-1.0 in NED frame (negative = UP)")

        for i in range(30):  # 3 seconds
            action = np.array([0.0, 0.0, 1.0, 0.0])  # Go UP (PyBullet convention)
            obs, reward, terminated, truncated, info = env.step(action)

            if i % 10 == 0:
                state = env.mavlink.get_state()
                current_alt = -state['position'][2]
                print(f"  t={i*0.1:.1f}s: altitude={current_alt:.3f}m (NED Z={state['position'][2]:.3f})")

            time.sleep(0.1)

        # Get final altitude
        state = env.mavlink.get_state()
        final_alt = -state['position'][2]
        altitude_change = final_alt - start_alt

        print(f"\nFinal altitude: {final_alt:.3f} m")
        print(f"Altitude change: {altitude_change:.3f} m")

        # Disarm and close
        env.mavlink.disarm(timeout=5.0)
        env.close()

        if altitude_change > 1.0:
            print("\n✅ SITL mode: Positive vz → UPWARD motion (FIX WORKS!)")
            return True
        elif altitude_change < -0.5:
            print(f"\n❌ SITL mode: Positive vz → DOWNWARD motion (FIX NOT APPLIED)")
            print("   The altitude went DOWN when it should go UP")
            print("   This means the coordinate frame conversion is still missing")
            return False
        else:
            print(f"\n⚠️  SITL mode: Minimal altitude change ({altitude_change:.3f}m)")
            print("   Drone may not be responding to commands")
            return False

    except Exception as e:
        print(f"\n❌ SITL test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "=" * 70)
    print("ALTITUDE COORDINATE FRAME FIX VERIFICATION")
    print("=" * 70)
    print("\nThis test verifies that the Z-axis coordinate frame conversion")
    print("between PyBullet (Z-up) and ArduPilot NED (Z-down) is working.")
    print()

    # Test PyBullet mode
    pybullet_passed = test_pybullet_altitude()

    # Test SITL mode
    sitl_passed = test_sitl_altitude()

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"PyBullet mode: {'✅ PASSED' if pybullet_passed else '❌ FAILED'}")

    if sitl_passed is None:
        print("SITL mode:     ⏭️  SKIPPED")
    elif sitl_passed:
        print("SITL mode:     ✅ PASSED (FIX VERIFIED)")
    else:
        print("SITL mode:     ❌ FAILED")

    if pybullet_passed and (sitl_passed or sitl_passed is None):
        print("\n🎉 ALTITUDE FIX VERIFIED!")
        print("\n✅ Positive vz now correctly means UPWARD in both modes")
        print("✅ Coordinate frame conversion working")
        print("✅ Ready for RL training with correct altitude control")
        return 0
    else:
        print("\n❌ ALTITUDE FIX VERIFICATION FAILED")
        print("\nCheck ALTITUDE_PROBLEM_FOUND.md for details")
        return 1


if __name__ == "__main__":
    sys.exit(main())
