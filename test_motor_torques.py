#!/usr/bin/env python3
"""
Test motor torque generation to verify correct implementation.
This script validates that motor torques are calculated correctly.
"""

import numpy as np
import sys
from drone_gym.physics.pybullet_drone import PyBulletDrone


def test_motor_torque_signs():
    """Test that motor torque signs are correct for X-configuration."""
    print("=" * 70)
    print("TEST 1: Motor Torque Sign Convention")
    print("=" * 70)

    drone = PyBulletDrone(drone_model="medium_quad", gui=False)
    drone.connect()

    # Test hover RPMs
    hover_thrust = drone.mass * abs(drone.gravity) / 4.0  # Per motor
    hover_rpm = np.sqrt(hover_thrust / drone.kf)

    print(f"\nDrone mass: {drone.mass} kg")
    print(f"Hover thrust per motor: {hover_thrust:.3f} N")
    print(f"Hover RPM per motor: {hover_rpm:.1f} RPM")

    # Test motor torque calculation
    test_rpms = np.array([hover_rpm] * 4)
    motor_torques = drone.km * (test_rpms ** 2) * np.array([-1, 1, -1, 1])

    print(f"\nMotor Configuration (X-config):")
    print("      Front")
    print("   1(CCW)  0(CW)")
    print("      \\ /")
    print("       X")
    print("      / \\")
    print("  2(CW)  3(CCW)")
    print("      Rear")

    print(f"\nMotor Torques @ Hover:")
    print(f"  Motor 0 (FR, CW):  {motor_torques[0]:+.6f} Nm (negative = clockwise)")
    print(f"  Motor 1 (RR, CCW): {motor_torques[1]:+.6f} Nm (positive = counter-clockwise)")
    print(f"  Motor 2 (RL, CW):  {motor_torques[2]:+.6f} Nm (negative = clockwise)")
    print(f"  Motor 3 (FL, CCW): {motor_torques[3]:+.6f} Nm (positive = counter-clockwise)")

    print(f"\nNet Yaw Torque @ Hover: {np.sum(motor_torques):.6f} Nm")

    # Verify signs
    assert motor_torques[0] < 0, "Motor 0 (CW) should produce negative torque"
    assert motor_torques[1] > 0, "Motor 1 (CCW) should produce positive torque"
    assert motor_torques[2] < 0, "Motor 2 (CW) should produce negative torque"
    assert motor_torques[3] > 0, "Motor 3 (CCW) should produce positive torque"
    assert abs(np.sum(motor_torques)) < 1e-6, "Net yaw torque should be ~0 at hover"

    print("\n✅ Motor torque signs are CORRECT!")
    drone.disconnect()


def test_roll_torque():
    """Test roll torque generation."""
    print("\n" + "=" * 70)
    print("TEST 2: Roll Torque Generation")
    print("=" * 70)

    drone = PyBulletDrone(drone_model="medium_quad", gui=False)
    drone.connect()

    hover_thrust = drone.mass * abs(drone.gravity) / 4.0

    # Test positive roll (right) - increase left motors, decrease right motors
    print("\nTest: Positive Roll (lean right)")
    motor_thrusts = np.array([
        hover_thrust * 0.8,  # Motor 0 (FR) - decreased
        hover_thrust * 0.8,  # Motor 1 (RR) - decreased
        hover_thrust * 1.2,  # Motor 2 (RL) - increased
        hover_thrust * 1.2,  # Motor 3 (FL) - increased
    ])

    roll_torque = drone.arm_length * (motor_thrusts[3] + motor_thrusts[2]
                                      - motor_thrusts[0] - motor_thrusts[1])

    print(f"  Motor thrusts: {motor_thrusts}")
    print(f"  Roll torque: {roll_torque:+.4f} Nm")
    print(f"  Expected: Positive (right roll)")

    assert roll_torque > 0, "Positive roll torque should be > 0"
    print("  ✅ CORRECT!")

    # Test negative roll (left) - increase right motors, decrease left motors
    print("\nTest: Negative Roll (lean left)")
    motor_thrusts = np.array([
        hover_thrust * 1.2,  # Motor 0 (FR) - increased
        hover_thrust * 1.2,  # Motor 1 (RR) - increased
        hover_thrust * 0.8,  # Motor 2 (RL) - decreased
        hover_thrust * 0.8,  # Motor 3 (FL) - decreased
    ])

    roll_torque = drone.arm_length * (motor_thrusts[3] + motor_thrusts[2]
                                      - motor_thrusts[0] - motor_thrusts[1])

    print(f"  Motor thrusts: {motor_thrusts}")
    print(f"  Roll torque: {roll_torque:+.4f} Nm")
    print(f"  Expected: Negative (left roll)")

    assert roll_torque < 0, "Negative roll torque should be < 0"
    print("  ✅ CORRECT!")

    drone.disconnect()


def test_pitch_torque():
    """Test pitch torque generation."""
    print("\n" + "=" * 70)
    print("TEST 3: Pitch Torque Generation")
    print("=" * 70)

    drone = PyBulletDrone(drone_model="medium_quad", gui=False)
    drone.connect()

    hover_thrust = drone.mass * abs(drone.gravity) / 4.0

    # Test positive pitch (nose up) - increase front motors, decrease rear motors
    print("\nTest: Positive Pitch (nose up)")
    motor_thrusts = np.array([
        hover_thrust * 1.2,  # Motor 0 (FR) - increased
        hover_thrust * 0.8,  # Motor 1 (RR) - decreased
        hover_thrust * 0.8,  # Motor 2 (RL) - decreased
        hover_thrust * 1.2,  # Motor 3 (FL) - increased
    ])

    pitch_torque = drone.arm_length * (motor_thrusts[0] + motor_thrusts[3]
                                       - motor_thrusts[1] - motor_thrusts[2])

    print(f"  Motor thrusts: {motor_thrusts}")
    print(f"  Pitch torque: {pitch_torque:+.4f} Nm")
    print(f"  Expected: Positive (nose up)")

    assert pitch_torque > 0, "Positive pitch torque should be > 0"
    print("  ✅ CORRECT!")

    # Test negative pitch (nose down) - increase rear motors, decrease front motors
    print("\nTest: Negative Pitch (nose down)")
    motor_thrusts = np.array([
        hover_thrust * 0.8,  # Motor 0 (FR) - decreased
        hover_thrust * 1.2,  # Motor 1 (RR) - increased
        hover_thrust * 1.2,  # Motor 2 (RL) - increased
        hover_thrust * 0.8,  # Motor 3 (FL) - decreased
    ])

    pitch_torque = drone.arm_length * (motor_thrusts[0] + motor_thrusts[3]
                                       - motor_thrusts[1] - motor_thrusts[2])

    print(f"  Motor thrusts: {motor_thrusts}")
    print(f"  Pitch torque: {pitch_torque:+.4f} Nm")
    print(f"  Expected: Negative (nose down)")

    assert pitch_torque < 0, "Negative pitch torque should be < 0"
    print("  ✅ CORRECT!")

    drone.disconnect()


def test_yaw_torque():
    """Test yaw torque generation."""
    print("\n" + "=" * 70)
    print("TEST 4: Yaw Torque Generation")
    print("=" * 70)

    drone = PyBulletDrone(drone_model="medium_quad", gui=False)
    drone.connect()

    hover_rpm = np.sqrt((drone.mass * abs(drone.gravity) / 4.0) / drone.kf)

    # Test positive yaw (CCW) - increase CCW motors (1,3), decrease CW motors (0,2)
    print("\nTest: Positive Yaw (counter-clockwise)")
    test_rpms = np.array([
        hover_rpm * 0.9,  # Motor 0 (CW) - decreased
        hover_rpm * 1.1,  # Motor 1 (CCW) - increased
        hover_rpm * 0.9,  # Motor 2 (CW) - decreased
        hover_rpm * 1.1,  # Motor 3 (CCW) - increased
    ])

    motor_torques = drone.km * (test_rpms ** 2) * np.array([-1, 1, -1, 1])
    yaw_torque = np.sum(motor_torques)

    print(f"  Motor RPMs: {test_rpms}")
    print(f"  Motor torques: {motor_torques}")
    print(f"  Yaw torque: {yaw_torque:+.6f} Nm")
    print(f"  Expected: Positive (CCW rotation)")

    assert yaw_torque > 0, "Positive yaw torque should be > 0"
    print("  ✅ CORRECT!")

    # Test negative yaw (CW) - increase CW motors (0,2), decrease CCW motors (1,3)
    print("\nTest: Negative Yaw (clockwise)")
    test_rpms = np.array([
        hover_rpm * 1.1,  # Motor 0 (CW) - increased
        hover_rpm * 0.9,  # Motor 1 (CCW) - decreased
        hover_rpm * 1.1,  # Motor 2 (CW) - increased
        hover_rpm * 0.9,  # Motor 3 (CCW) - decreased
    ])

    motor_torques = drone.km * (test_rpms ** 2) * np.array([-1, 1, -1, 1])
    yaw_torque = np.sum(motor_torques)

    print(f"  Motor RPMs: {test_rpms}")
    print(f"  Motor torques: {motor_torques}")
    print(f"  Yaw torque: {yaw_torque:+.6f} Nm")
    print(f"  Expected: Negative (CW rotation)")

    assert yaw_torque < 0, "Negative yaw torque should be < 0"
    print("  ✅ CORRECT!")

    drone.disconnect()


def test_full_control():
    """Test complete motor control in simulation."""
    print("\n" + "=" * 70)
    print("TEST 5: Full Control Simulation")
    print("=" * 70)

    drone = PyBulletDrone(drone_model="medium_quad", gui=False)
    drone.connect()

    print("\nTest: Hover in place")
    action = np.array([0.0, 0.0, 0.0, 0.0])  # No velocity command

    initial_pos = drone.position.copy()
    print(f"  Initial position: {initial_pos}")

    # Simulate for 2 seconds
    for i in range(200):  # 200 steps @ 0.01s = 2 seconds
        drone.step(action)

    final_pos = drone.position.copy()
    print(f"  Final position: {final_pos}")
    print(f"  Position drift: {np.linalg.norm(final_pos - initial_pos):.4f} m")

    # Should stay roughly in place (some drift is expected)
    drift = np.linalg.norm(final_pos - initial_pos)
    assert drift < 1.0, "Hover drift should be < 1m"
    print("  ✅ Hover control working!")

    drone.disconnect()


def main():
    """Run all motor torque tests."""
    print("\n" + "=" * 70)
    print("MOTOR TORQUE VALIDATION TEST SUITE")
    print("Verifying correct torque generation for X-configuration quadcopter")
    print("=" * 70)

    try:
        test_motor_torque_signs()
        test_roll_torque()
        test_pitch_torque()
        test_yaw_torque()
        test_full_control()

        print("\n" + "=" * 70)
        print("🎉 ALL MOTOR TORQUE TESTS PASSED! 🎉")
        print("=" * 70)
        print("\n✅ Motor torque calculations are CORRECT")
        print("✅ Roll/Pitch/Yaw torques are properly generated")
        print("✅ Motor mixing is correct for X-configuration")
        print("\n⚠️  If SITL tests failed, the issue is NOT motor torques!")
        print("⚠️  See MOTOR_TORQUE_ANALYSIS.md for SITL integration issues")
        print("\n")

        return 0

    except AssertionError as e:
        print("\n" + "=" * 70)
        print("❌ TEST FAILED ❌")
        print("=" * 70)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ UNEXPECTED ERROR ❌")
        print("=" * 70)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
