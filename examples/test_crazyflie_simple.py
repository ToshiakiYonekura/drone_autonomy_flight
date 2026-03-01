#!/usr/bin/env python3
"""Simple test script for Crazyflie 2.x URDF model in PyBullet."""

import sys
import os
import numpy as np
import pybullet as p
import pybullet_data

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_urdf_loading():
    """Test loading the Crazyflie URDF file directly."""
    print("=" * 60)
    print("Testing Crazyflie 2.x URDF Model Loading")
    print("=" * 60)

    # Get URDF path
    urdf_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'drone_gym',
        'assets',
        'cf2x.urdf'
    )
    urdf_path = os.path.abspath(urdf_path)

    print(f"\n1. URDF file path: {urdf_path}")
    print(f"   File exists: {os.path.exists(urdf_path)}")

    if not os.path.exists(urdf_path):
        print("   ✗ URDF file not found!")
        return

    # Connect to PyBullet with GUI
    print("\n2. Connecting to PyBullet...")
    client_id = p.connect(p.GUI)
    print(f"   ✓ Connected (client ID: {client_id})")

    # Setup physics
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, -9.81)
    p.setTimeStep(0.01)

    # Load ground plane
    plane_id = p.loadURDF("plane.urdf")
    print(f"   ✓ Ground plane loaded (ID: {plane_id})")

    # Load Crazyflie URDF
    print("\n3. Loading Crazyflie URDF...")
    try:
        drone_id = p.loadURDF(
            urdf_path,
            basePosition=[0, 0, 1.0],
            baseOrientation=[0, 0, 0, 1],
            flags=p.URDF_USE_INERTIA_FROM_FILE,
        )
        print(f"   ✓ Drone loaded successfully (ID: {drone_id})")
    except Exception as e:
        print(f"   ✗ Failed to load URDF: {e}")
        p.disconnect()
        return

    # Get drone info
    print("\n4. Drone information:")
    base_pos, base_orn = p.getBasePositionAndOrientation(drone_id)
    print(f"   Position: {base_pos}")
    print(f"   Orientation: {base_orn}")

    # Get number of joints
    num_joints = p.getNumJoints(drone_id)
    print(f"   Number of joints: {num_joints}")

    # List all joints
    if num_joints > 0:
        print("\n   Joints:")
        for i in range(num_joints):
            joint_info = p.getJointInfo(drone_id, i)
            joint_name = joint_info[1].decode('utf-8')
            joint_type = joint_info[2]
            print(f"     [{i}] {joint_name} (type: {joint_type})")

    # Get dynamics info
    dynamics = p.getDynamicsInfo(drone_id, -1)  # -1 for base link
    print(f"\n   Mass: {dynamics[0]} kg")
    print(f"   Inertia diagonal: {dynamics[2]}")

    # Run simulation for a few seconds
    print("\n5. Running simulation (hover test)...")
    print("   Applying upward thrust to counteract gravity...")

    mass = dynamics[0]
    hover_force = mass * 9.81 * 1.1  # 110% of weight to lift slightly

    for step in range(500):  # 5 seconds at 100 Hz
        # Apply upward force
        p.applyExternalForce(
            drone_id,
            -1,  # base link
            [0, 0, hover_force],
            [0, 0, 0],
            p.WORLD_FRAME,
        )

        p.stepSimulation()

        # Print position every second
        if step % 100 == 0:
            pos, _ = p.getBasePositionAndOrientation(drone_id)
            lin_vel, ang_vel = p.getBaseVelocity(drone_id)
            print(f"   Step {step:3d}: z = {pos[2]:.3f} m, vz = {lin_vel[2]:.3f} m/s")

    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)
    print("\nThe PyBullet GUI window will remain open.")
    print("Press Ctrl+C to close and exit.")

    # Keep GUI open
    try:
        import time
        while True:
            p.stepSimulation()
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    finally:
        p.disconnect()
        print("Disconnected from PyBullet")


if __name__ == "__main__":
    test_urdf_loading()
