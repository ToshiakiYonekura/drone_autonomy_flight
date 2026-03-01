#!/usr/bin/env python3
"""Test script for Crazyflie 2.x URDF model in PyBullet."""

import sys
import os
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from drone_gym.physics.pybullet_drone import PyBulletDrone


def test_crazyflie_model():
    """Test the Crazyflie URDF model loading and basic physics."""
    print("=" * 60)
    print("Testing Crazyflie 2.x URDF Model")
    print("=" * 60)

    # Create drone with GUI
    print("\n1. Initializing PyBullet with Crazyflie model...")
    drone = PyBulletDrone(gui=True, drone_model="cf2x")

    try:
        # Connect to physics server
        print("2. Connecting to PyBullet physics server...")
        drone.connect()
        print("   ✓ Connected successfully")
        print(f"   ✓ Drone ID: {drone.drone_id}")
        print(f"   ✓ Mass: {drone.mass} kg")
        print(f"   ✓ Arm length: {drone.arm_length} m")
        print(f"   ✓ Thrust-to-weight ratio: {drone.thrust_to_weight}")

        # Test initial state
        print("\n3. Checking initial state...")
        state = drone.get_state()
        print(f"   Position: {state['position']}")
        print(f"   Orientation (euler): {state['orientation_euler']}")
        print(f"   Linear velocity: {state['linear_velocity']}")

        # Test hover command
        print("\n4. Testing hover command (maintaining altitude)...")
        print("   Sending zero velocity command for 5 seconds...")

        hover_action = np.array([0.0, 0.0, 0.0, 0.0])  # [vx, vy, vz, yaw_rate]

        for i in range(500):  # 5 seconds at 100 Hz
            collision = drone.step(hover_action)

            if collision:
                print(f"   ✗ Collision detected at step {i}")
                break

            # Print state every second
            if i % 100 == 0:
                state = drone.get_state()
                pos_z = state['position'][2]
                print(f"   Step {i:3d}: altitude = {pos_z:.3f} m, "
                      f"motor RPMs = [{drone.motor_rpms[0]:.0f}, {drone.motor_rpms[1]:.0f}, "
                      f"{drone.motor_rpms[2]:.0f}, {drone.motor_rpms[3]:.0f}]")

        # Test forward movement
        print("\n5. Testing forward movement...")
        print("   Sending forward velocity command (vx=1.0 m/s) for 3 seconds...")

        forward_action = np.array([1.0, 0.0, 0.0, 0.0])

        for i in range(300):  # 3 seconds
            collision = drone.step(forward_action)

            if collision:
                print(f"   ✗ Collision detected at step {i}")
                break

            if i % 100 == 0:
                state = drone.get_state()
                pos = state['position']
                vel = state['linear_velocity']
                print(f"   Step {i:3d}: pos = [{pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f}], "
                      f"vel = [{vel[0]:.2f}, {vel[1]:.2f}, {vel[2]:.2f}]")

        # Test yaw rotation
        print("\n6. Testing yaw rotation...")
        print("   Sending yaw rate command (0.5 rad/s) for 3 seconds...")

        yaw_action = np.array([0.0, 0.0, 0.0, 0.5])

        for i in range(300):  # 3 seconds
            collision = drone.step(yaw_action)

            if collision:
                print(f"   ✗ Collision detected at step {i}")
                break

            if i % 100 == 0:
                state = drone.get_state()
                euler = state['orientation_euler']
                print(f"   Step {i:3d}: yaw = {euler[2]:.2f} rad")

        # Test sensors
        print("\n7. Testing sensors...")

        # LiDAR
        lidar = drone.get_lidar_scan()
        print(f"   ✓ LiDAR scan: {len(lidar)} rays")
        print(f"     Min distance: {np.min(lidar):.2f} m")
        print(f"     Max distance: {np.max(lidar):.2f} m")

        # Camera
        camera_img = drone.get_camera_image()
        print(f"   ✓ Camera image: {camera_img.shape}")

        print("\n" + "=" * 60)
        print("All tests completed successfully!")
        print("=" * 60)
        print("\nNote: The GUI window will remain open.")
        print("Press Ctrl+C to close and exit.")

        # Keep GUI open
        import time
        while True:
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\nShutting down...")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        drone.disconnect()
        print("Disconnected from PyBullet")


if __name__ == "__main__":
    test_crazyflie_model()
