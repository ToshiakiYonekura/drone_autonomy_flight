#!/usr/bin/env python3
"""
Final comprehensive SITL test - verify ALL fixes.
"""

import sys
import time
import numpy as np
from drone_gym.envs.pybullet_drone_env import PyBulletDroneEnv

def main():
    print("=" * 70)
    print("FINAL SITL INTEGRATION TEST")
    print("Verifying: Motor outputs + Altitude control")
    print("=" * 70)

    print("\n⚠️  Make sure SITL is running:")
    print("  cd ~/ardupilot/ArduCopter")
    print("  ~/ardupilot/build/sitl/bin/arducopter --model + --speedup 1")
    print()

    proceed = input("Is SITL running? (y/n): ")
    if proceed.lower() != 'y':
        print("Please start SITL first")
        return 1

    try:
        print("\n1. Connecting to SITL...")
        env = PyBulletDroneEnv(
            use_mavlink=True,
            mavlink_connection="tcp:127.0.0.1:5760",
            gui=False,
            drone_model="medium_quad",
        )

        if not env.mavlink or not env.mavlink.connected:
            print("❌ Connection failed")
            return 1

        print("✅ Connected")

        print("\n2. Setting GUIDED mode and arming...")
        env.mavlink.set_mode("GUIDED", timeout=10.0)
        time.sleep(1)

        if not env.mavlink.arm(timeout=10.0):
            print("⚠️  Could not arm (pre-arm checks may be failing)")
            print("   Continuing anyway to test motor outputs...")
        else:
            print("✅ Armed")

        time.sleep(2)

        print("\n3. Testing motor output reception...")
        if env.mavlink.has_recent_motor_data(max_age=2.0):
            motor_pwm = env.mavlink.get_motor_pwm()
            motor_rpms = env.mavlink.get_motor_rpms()
            print(f"✅ Motor PWM: {motor_pwm}")
            print(f"✅ Motor RPM: {motor_rpms}")
        else:
            print("❌ No motor data received")
            env.close()
            return 1

        print("\n4. Resetting environment...")
        obs, info = env.reset()

        print("\n5. Testing altitude - HOVER (vz=0)...")
        state = env.mavlink.get_state()
        start_alt = -state['position'][2]
        print(f"   Start altitude: {start_alt:.3f} m (NED Z={state['position'][2]:.3f})")

        for i in range(30):  # 3 seconds
            action = np.array([0.0, 0.0, 0.0, 0.0])
            obs, reward, terminated, truncated, info = env.step(action)
            time.sleep(0.1)

        state = env.mavlink.get_state()
        hover_alt = -state['position'][2]
        print(f"   After hover: {hover_alt:.3f} m (drift: {hover_alt-start_alt:+.3f} m)")

        if abs(hover_alt - start_alt) < 0.5:
            print("   ✅ Hover stable")
        else:
            print(f"   ⚠️  Altitude drifted by {hover_alt-start_alt:.3f} m")

        print("\n6. Testing altitude - CLIMB (vz=+1.0 in PyBullet frame)...")
        print("   This should convert to vz=-1.0 in NED (upward)")

        start_state = env.mavlink.get_state()
        start_alt = -start_state['position'][2]
        start_ned_z = start_state['position'][2]

        print(f"   Before climb: altitude={start_alt:.3f}m, NED_Z={start_ned_z:.3f}")

        for i in range(50):  # 5 seconds
            # Positive vz in PyBullet convention (UP)
            # Should be converted to negative vz in NED (also UP)
            action = np.array([0.0, 0.0, 1.0, 0.0])
            obs, reward, terminated, truncated, info = env.step(action)

            if i % 10 == 0:
                state = env.mavlink.get_state()
                current_alt = -state['position'][2]
                current_ned_z = state['position'][2]
                motor_rpms = info.get('motor_rpms', [0,0,0,0])
                print(f"   t={i*0.1:.1f}s: alt={current_alt:.3f}m, NED_Z={current_ned_z:.3f}, motors={motor_rpms.mean():.0f}rpm")

            time.sleep(0.1)

        final_state = env.mavlink.get_state()
        final_alt = -final_state['position'][2]
        final_ned_z = final_state['position'][2]
        altitude_change = final_alt - start_alt
        ned_z_change = final_ned_z - start_ned_z

        print(f"\n   Final: altitude={final_alt:.3f}m, NED_Z={final_ned_z:.3f}")
        print(f"   Altitude change: {altitude_change:+.3f} m")
        print(f"   NED Z change: {ned_z_change:+.3f} m")

        # Verify direction
        print("\n7. CRITICAL VERIFICATION:")
        if altitude_change > 0.5:
            print("   ✅ Positive vz command → UPWARD motion (altitude increased)")
            print("   ✅ Coordinate frame conversion WORKING!")
            altitude_ok = True
        elif altitude_change < -0.5:
            print("   ❌ Positive vz command → DOWNWARD motion (altitude decreased)")
            print("   ❌ Coordinate frame conversion BROKEN!")
            altitude_ok = False
        else:
            print(f"   ⚠️  Minimal altitude change ({altitude_change:.3f}m)")
            print("   ⚠️  Cannot verify - drone may not be responding")
            altitude_ok = None

        print("\n8. Disarming...")
        env.mavlink.disarm(timeout=5.0)
        env.close()

        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print("✅ Motor output reception: WORKING")

        if altitude_ok is True:
            print("✅ Altitude coordinate frame: WORKING")
            print("\n🎉 ALL SITL PROBLEMS FIXED AND VERIFIED!")
            return 0
        elif altitude_ok is False:
            print("❌ Altitude coordinate frame: BROKEN")
            print("\n⚠️  Motor outputs work, but altitude frame needs fix")
            return 1
        else:
            print("⚠️  Altitude coordinate frame: COULD NOT VERIFY")
            print("\n⚠️  Motor outputs work, altitude needs manual verification")
            return 1

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
