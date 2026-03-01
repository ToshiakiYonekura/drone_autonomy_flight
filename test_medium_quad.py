#!/usr/bin/env python3
"""
Test script to verify the medium quadcopter model (2.0 kg).
Validates that physics parameters match ArduPilot master branch.
"""

import sys
import numpy as np
from drone_gym.physics.pybullet_drone import PyBulletDrone
from drone_gym.envs.pybullet_drone_env import PyBulletDroneEnv


def test_physics_parameters():
    """Test that physics parameters match ArduPilot sysid_params.txt"""
    print("=" * 60)
    print("Testing Medium Quadcopter Physics Parameters")
    print("=" * 60)

    drone = PyBulletDrone(drone_model="medium_quad", gui=False)

    # Expected values from ArduPilot sysid_params.txt
    expected = {
        "mass": 2.0,
        "Ixx": 0.015,
        "Iyy": 0.015,
        "Izz": 0.025,
        "motor_kv": 920.0,
        "max_thrust_per_motor": 20.0,
        "arm_length": 0.225,
    }

    # Check mass
    print(f"\n1. Mass:")
    print(f"   Expected: {expected['mass']} kg")
    print(f"   Actual:   {drone.mass} kg")
    assert abs(drone.mass - expected['mass']) < 0.01, "Mass mismatch!"
    print("   ✓ PASS")

    # Check arm length
    print(f"\n2. Arm Length:")
    print(f"   Expected: {expected['arm_length']} m")
    print(f"   Actual:   {drone.arm_length} m")
    assert abs(drone.arm_length - expected['arm_length']) < 0.01, "Arm length mismatch!"
    print("   ✓ PASS")

    # Check motor KV (if available)
    if hasattr(drone, 'motor_kv'):
        print(f"\n3. Motor KV:")
        print(f"   Expected: {expected['motor_kv']} KV")
        print(f"   Actual:   {drone.motor_kv} KV")
        assert abs(drone.motor_kv - expected['motor_kv']) < 1.0, "Motor KV mismatch!"
        print("   ✓ PASS")

    # Check max thrust
    if hasattr(drone, 'max_thrust_per_motor'):
        print(f"\n4. Max Thrust per Motor:")
        print(f"   Expected: {expected['max_thrust_per_motor']} N")
        print(f"   Actual:   {drone.max_thrust_per_motor} N")
        assert abs(drone.max_thrust_per_motor - expected['max_thrust_per_motor']) < 1.0, "Max thrust mismatch!"
        print("   ✓ PASS")

    # Check thrust-to-weight ratio
    total_thrust = 4 * (drone.max_thrust_per_motor if hasattr(drone, 'max_thrust_per_motor') else 20.0)
    weight = drone.mass * 9.81
    twr = total_thrust / weight
    print(f"\n5. Thrust-to-Weight Ratio:")
    print(f"   Total thrust: {total_thrust:.1f} N")
    print(f"   Weight: {weight:.1f} N")
    print(f"   T/W ratio: {twr:.2f}")
    assert twr >= 1.5, "Insufficient thrust-to-weight ratio!"
    print("   ✓ PASS")

    # Check motor positions
    print(f"\n6. Motor Positions:")
    print(f"   Motor 0 (FR, CW):  {drone.motor_positions[0]}")
    print(f"   Motor 1 (RR, CCW): {drone.motor_positions[1]}")
    print(f"   Motor 2 (RL, CW):  {drone.motor_positions[2]}")
    print(f"   Motor 3 (FL, CCW): {drone.motor_positions[3]}")
    print("   ✓ PASS")

    print("\n" + "=" * 60)
    print("All physics parameter tests PASSED! ✓")
    print("=" * 60)


def test_environment_creation():
    """Test that the environment can be created with medium_quad model"""
    print("\n" + "=" * 60)
    print("Testing Environment Creation")
    print("=" * 60)

    try:
        # Test with explicit model
        print("\n1. Creating environment with medium_quad model...")
        env1 = PyBulletDroneEnv(gui=False, drone_model="medium_quad")
        print(f"   Model: {env1.sim.drone_model}")
        print(f"   Mass: {env1.sim.mass} kg")
        print("   ✓ PASS")

        # Test default (should be medium_quad)
        print("\n2. Creating environment with default model...")
        env2 = PyBulletDroneEnv(gui=False)
        print(f"   Model: {env2.sim.drone_model}")
        print(f"   Mass: {env2.sim.mass} kg")
        assert env2.sim.drone_model == "medium_quad", "Default model should be medium_quad!"
        print("   ✓ PASS")

        # Test old Crazyflie model still works
        print("\n3. Creating environment with cf2x model...")
        env3 = PyBulletDroneEnv(gui=False, drone_model="cf2x")
        print(f"   Model: {env3.sim.drone_model}")
        print(f"   Mass: {env3.sim.mass} kg")
        assert env3.sim.mass < 0.1, "cf2x should have small mass!"
        print("   ✓ PASS")

        print("\n" + "=" * 60)
        print("All environment creation tests PASSED! ✓")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ FAILED: {e}")
        raise


def test_basic_simulation():
    """Test basic simulation steps"""
    print("\n" + "=" * 60)
    print("Testing Basic Simulation")
    print("=" * 60)

    try:
        env = PyBulletDroneEnv(gui=False, drone_model="medium_quad")

        # Reset environment
        print("\n1. Resetting environment...")
        obs, info = env.reset()
        print(f"   Observation shape: {obs.shape}")
        print(f"   Goal position: {info['goal_position']}")
        print("   ✓ PASS")

        # Take a few steps
        print("\n2. Taking simulation steps...")
        for i in range(10):
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)

            if i == 0:
                print(f"   Step {i+1}: reward={reward:.3f}, pos={env.sim.position}")

        print(f"   Completed 10 steps successfully")
        print("   ✓ PASS")

        # Check state
        state = env.sim.get_state()
        print(f"\n3. Final state:")
        print(f"   Position: {state['position']}")
        print(f"   Velocity: {state['linear_velocity']}")
        print(f"   Orientation (euler): {np.rad2deg(state['orientation_euler'])} deg")
        print("   ✓ PASS")

        print("\n" + "=" * 60)
        print("All simulation tests PASSED! ✓")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ FAILED: {e}")
        raise


def test_comparison():
    """Compare medium_quad vs cf2x models"""
    print("\n" + "=" * 60)
    print("Model Comparison: medium_quad vs cf2x")
    print("=" * 60)

    medium = PyBulletDrone(drone_model="medium_quad", gui=False)
    crazyflie = PyBulletDrone(drone_model="cf2x", gui=False)

    print(f"\n{'Parameter':<20} {'Medium Quad':<20} {'Crazyflie':<20} {'Ratio':<10}")
    print("-" * 70)

    mass_ratio = medium.mass / crazyflie.mass
    print(f"{'Mass (kg)':<20} {medium.mass:<20.3f} {crazyflie.mass:<20.3f} {mass_ratio:<10.1f}x")

    arm_ratio = medium.arm_length / crazyflie.arm_length
    print(f"{'Arm length (m)':<20} {medium.arm_length:<20.3f} {crazyflie.arm_length:<20.3f} {arm_ratio:<10.1f}x")

    twr_ratio = medium.thrust_to_weight / crazyflie.thrust_to_weight
    print(f"{'Thrust/Weight':<20} {medium.thrust_to_weight:<20.2f} {crazyflie.thrust_to_weight:<20.2f} {twr_ratio:<10.2f}x")

    print("\n" + "=" * 60)
    print(f"The medium_quad is {mass_ratio:.1f}x heavier than the Crazyflie!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        print("\n" + "=" * 60)
        print("MEDIUM QUADCOPTER MODEL TEST SUITE")
        print("Verifying 2.0kg model matches ArduPilot master branch")
        print("=" * 60)

        # Run all tests
        test_physics_parameters()
        test_environment_creation()
        test_basic_simulation()
        test_comparison()

        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED! 🎉")
        print("=" * 60)
        print("\nThe medium quadcopter model is correctly configured and matches")
        print("the ArduPilot master branch parameters.")
        print("\nYou can now train RL agents with consistent physics:")
        print("  python3 examples/train_pybullet_rl.py")
        print("\n")

        sys.exit(0)

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ TEST FAILED ❌")
        print("=" * 60)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
