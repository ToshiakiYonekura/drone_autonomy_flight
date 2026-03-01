#!/usr/bin/env python3
"""
Test altitude control in both PyBullet and SITL modes.
Check if the 0 altitude problem from yesterday is fixed.
"""

import sys
import time
import numpy as np
from drone_gym.envs.pybullet_drone_env import PyBulletDroneEnv

def test_pybullet_altitude():
    """Test altitude control with PyBullet internal controller."""
    print("=" * 70)
    print("TEST 1: PyBullet Altitude Control")
    print("=" * 70)

    env = PyBulletDroneEnv(
        use_mavlink=False,
        gui=True,
        drone_model="medium_quad",
    )

    print("\n1. Resetting environment...")
    obs, info = env.reset()

    initial_pos = env.sim.position.copy()
    print(f"   Initial position: {initial_pos}")
    print(f"   Initial altitude: {initial_pos[2]:.3f} m (up is positive in PyBullet)")

    print("\n2. Testing hover in place (0 velocity command)...")
    print("   Sending: [vx=0, vy=0, vz=0, yaw_rate=0] for 5 seconds")

    positions = []
    for i in range(50):  # 5 seconds at 10Hz
        action = np.array([0.0, 0.0, 0.0, 0.0])
        obs, reward, terminated, truncated, info = env.step(action)
        positions.append(info['position'].copy())

        if i % 10 == 0:
            print(f"   t={i*0.1:.1f}s: pos={info['position']}, alt={info['position'][2]:.3f}m")

        time.sleep(0.1)

    final_pos = positions[-1]
    altitude_change = final_pos[2] - initial_pos[2]

    print(f"\n   Final altitude: {final_pos[2]:.3f} m")
    print(f"   Altitude change: {altitude_change:.3f} m")

    if abs(altitude_change) < 0.5:
        print("   ✅ Hover control working (altitude stable)")
    else:
        print(f"   ⚠️  Altitude drifted by {altitude_change:.3f} m")

    print("\n3. Testing upward velocity command...")
    print("   Sending: [vx=0, vy=0, vz=1.0, yaw_rate=0] for 3 seconds")

    start_alt = env.sim.position[2]
    for i in range(30):  # 3 seconds
        action = np.array([0.0, 0.0, 1.0, 0.0])  # Upward velocity
        obs, reward, terminated, truncated, info = env.step(action)

        if i % 10 == 0:
            current_alt = info['position'][2]
            print(f"   t={i*0.1:.1f}s: altitude={current_alt:.3f}m, Δ={current_alt-start_alt:.3f}m")

        time.sleep(0.1)

    final_alt = env.sim.position[2]
    altitude_gain = final_alt - start_alt

    print(f"\n   Starting altitude: {start_alt:.3f} m")
    print(f"   Final altitude: {final_alt:.3f} m")
    print(f"   Altitude gained: {altitude_gain:.3f} m")

    if altitude_gain > 1.0:
        print("   ✅ Upward velocity control working")
    else:
        print(f"   ⚠️  Expected altitude gain > 1.0m, got {altitude_gain:.3f}m")

    print("\n4. Testing downward velocity command...")
    print("   Sending: [vx=0, vy=0, vz=-0.5, yaw_rate=0] for 2 seconds")

    start_alt = env.sim.position[2]
    for i in range(20):  # 2 seconds
        action = np.array([0.0, 0.0, -0.5, 0.0])  # Downward velocity
        obs, reward, terminated, truncated, info = env.step(action)

        if i % 10 == 0:
            current_alt = info['position'][2]
            print(f"   t={i*0.1:.1f}s: altitude={current_alt:.3f}m")

        time.sleep(0.1)

    final_alt = env.sim.position[2]
    altitude_loss = start_alt - final_alt

    print(f"\n   Altitude lost: {altitude_loss:.3f} m")

    if altitude_loss > 0.5:
        print("   ✅ Downward velocity control working")
    else:
        print(f"   ⚠️  Expected altitude loss > 0.5m, got {altitude_loss:.3f}m")

    env.close()

    print("\n" + "=" * 70)
    print("PyBullet altitude control test completed")
    print("=" * 70)


def test_sitl_altitude():
    """Test altitude control with ArduPilot SITL."""
    print("\n" + "=" * 70)
    print("TEST 2: ArduPilot SITL Altitude Control")
    print("=" * 70)

    print("\n⚠️  Prerequisites:")
    print("  1. ArduCopter SITL must be running")
    print("  2. Run in separate terminal:")
    print("     cd ~/ardupilot/ArduCopter")
    print("     ~/ardupilot/build/sitl/bin/arducopter --model + --speedup 1")
    print()

    proceed = input("Is SITL running? (y/n): ")
    if proceed.lower() != 'y':
        print("Skipping SITL altitude test")
        return

    try:
        env = PyBulletDroneEnv(
            use_mavlink=True,
            mavlink_connection="tcp:127.0.0.1:5760",
            gui=True,
            drone_model="medium_quad",
        )

        if not env.mavlink or not env.mavlink.connected:
            print("❌ Could not connect to SITL")
            return

        print("✅ Connected to SITL")

        # Set GUIDED mode and arm
        print("\nSetting GUIDED mode and arming...")
        env.mavlink.set_mode("GUIDED", timeout=10.0)
        time.sleep(1)
        env.mavlink.arm(timeout=10.0)
        time.sleep(2)

        print("\nResetting environment...")
        obs, info = env.reset()

        # Get initial state
        state = env.mavlink.get_state()
        initial_alt = -state['position'][2]  # NED to altitude
        print(f"Initial altitude (NED): {state['position'][2]:.3f} m")
        print(f"Initial altitude (AGL): {initial_alt:.3f} m")

        print("\n1. Testing hover with ArduPilot...")
        print("   Sending: [vx=0, vy=0, vz=0, yaw_rate=0] for 5 seconds")

        for i in range(50):  # 5 seconds at 10Hz
            action = np.array([0.0, 0.0, 0.0, 0.0])
            obs, reward, terminated, truncated, info = env.step(action)

            if i % 10 == 0:
                state = env.mavlink.get_state()
                alt = -state['position'][2]
                print(f"   t={i*0.1:.1f}s: altitude={alt:.3f}m, motor_rpms={info['motor_rpms']}")

            time.sleep(0.1)

        print("\n2. Testing upward velocity with ArduPilot...")
        print("   Sending: [vx=0, vy=0, vz=-1.0, yaw_rate=0] (NED: negative is up)")

        start_state = env.mavlink.get_state()
        start_alt = -start_state['position'][2]

        for i in range(30):  # 3 seconds
            action = np.array([0.0, 0.0, -1.0, 0.0])  # NED frame: negative = up
            obs, reward, terminated, truncated, info = env.step(action)

            if i % 10 == 0:
                state = env.mavlink.get_state()
                current_alt = -state['position'][2]
                print(f"   t={i*0.1:.1f}s: altitude={current_alt:.3f}m, Δ={current_alt-start_alt:.3f}m")

            time.sleep(0.1)

        final_state = env.mavlink.get_state()
        final_alt = -final_state['position'][2]
        altitude_gain = final_alt - start_alt

        print(f"\n   Altitude gained: {altitude_gain:.3f} m")

        if altitude_gain > 1.0:
            print("   ✅ ArduPilot altitude control working")
        else:
            print(f"   ⚠️  Expected altitude gain > 1.0m, got {altitude_gain:.3f}m")

        print("\nDisarming...")
        env.mavlink.disarm(timeout=5.0)
        env.close()

        print("\n" + "=" * 70)
        print("SITL altitude control test completed")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ SITL test failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    print("\n" + "=" * 70)
    print("ALTITUDE CONTROL TEST SUITE")
    print("Checking if 0 altitude problem is fixed")
    print("=" * 70)

    # Test PyBullet altitude control
    test_pybullet_altitude()

    # Ask if user wants to test SITL
    print("\n" + "=" * 70)
    test_sitl = input("\nTest SITL altitude control? (y/n): ")
    if test_sitl.lower() == 'y':
        test_sitl_altitude()
    else:
        print("Skipping SITL altitude test")

    print("\n" + "=" * 70)
    print("ALTITUDE TESTS COMPLETED")
    print("=" * 70)

if __name__ == "__main__":
    main()
