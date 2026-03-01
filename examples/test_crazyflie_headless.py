#!/usr/bin/env python3
"""Headless test script for Crazyflie 2.x URDF model in PyBullet."""

import os
import numpy as np
import pybullet as p
import pybullet_data


def test_urdf_loading():
    """Test loading the Crazyflie URDF file in headless mode."""
    print("=" * 60)
    print("Testing Crazyflie 2.x URDF Model Loading (Headless)")
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
        return False

    # Check mesh file
    mesh_path = os.path.join(os.path.dirname(urdf_path), 'cf2.dae')
    print(f"   Mesh file: {mesh_path}")
    print(f"   Mesh exists: {os.path.exists(mesh_path)}")

    # Connect to PyBullet in DIRECT mode (headless)
    print("\n2. Connecting to PyBullet (DIRECT mode)...")
    client_id = p.connect(p.DIRECT)
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
        import traceback
        traceback.print_exc()
        p.disconnect()
        return False

    # Get drone info
    print("\n4. Drone information:")
    base_pos, base_orn = p.getBasePositionAndOrientation(drone_id)
    print(f"   Position: [{base_pos[0]:.3f}, {base_pos[1]:.3f}, {base_pos[2]:.3f}]")
    print(f"   Orientation: [{base_orn[0]:.3f}, {base_orn[1]:.3f}, {base_orn[2]:.3f}, {base_orn[3]:.3f}]")

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
            link_name = joint_info[12].decode('utf-8')
            print(f"     [{i}] Joint: {joint_name} -> Link: {link_name} (type: {joint_type})")

    # Get dynamics info
    dynamics = p.getDynamicsInfo(drone_id, -1)  # -1 for base link
    mass = dynamics[0]
    inertia = dynamics[2]
    print(f"\n   Base link dynamics:")
    print(f"     Mass: {mass} kg")
    print(f"     Inertia diagonal: [{inertia[0]:.6f}, {inertia[1]:.6f}, {inertia[2]:.6f}]")

    # Verify against expected Crazyflie parameters
    expected_mass = 0.027
    print(f"\n   Verification:")
    print(f"     Expected mass: {expected_mass} kg")
    print(f"     Loaded mass: {mass} kg")
    print(f"     Match: {'✓' if abs(mass - expected_mass) < 0.001 else '✗'}")

    # Run simulation for a few seconds
    print("\n5. Running physics simulation (5 seconds)...")
    print("   Testing hover with thrust force...")

    hover_force = mass * 9.81 * 1.05  # 105% of weight

    positions = []
    velocities = []

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

        # Record state
        pos, _ = p.getBasePositionAndOrientation(drone_id)
        lin_vel, _ = p.getBaseVelocity(drone_id)
        positions.append(pos[2])
        velocities.append(lin_vel[2])

        # Print position every second
        if step % 100 == 0:
            print(f"   Step {step:3d}: z = {pos[2]:.3f} m, vz = {lin_vel[2]:.3f} m/s")

    # Analyze results
    print("\n6. Results analysis:")
    final_altitude = positions[-1]
    initial_altitude = positions[0]
    altitude_change = final_altitude - initial_altitude
    print(f"   Initial altitude: {initial_altitude:.3f} m")
    print(f"   Final altitude: {final_altitude:.3f} m")
    print(f"   Altitude change: {altitude_change:.3f} m")
    print(f"   Hover stability: {'✓ Ascending as expected' if altitude_change > 0 else '✗ Problem detected'}")

    # Test motor dynamics
    print("\n7. Testing motor dynamics equations...")
    kf = 3.16e-10  # thrust coefficient from URDF
    km = 7.94e-12  # torque coefficient from URDF
    test_rpm = 15000  # RPM

    thrust = kf * (test_rpm ** 2)
    torque = km * (test_rpm ** 2)

    print(f"   Thrust coefficient (kf): {kf}")
    print(f"   Torque coefficient (km): {km}")
    print(f"   Test RPM: {test_rpm}")
    print(f"   Calculated thrust: {thrust:.6f} N")
    print(f"   Calculated torque: {torque:.8f} Nm")

    # Calculate hover RPM
    hover_thrust_per_motor = mass * 9.81 / 4.0
    hover_rpm = np.sqrt(hover_thrust_per_motor / kf)
    print(f"\n   Hover thrust per motor: {hover_thrust_per_motor:.6f} N")
    print(f"   Hover RPM: {hover_rpm:.0f}")

    # Cleanup
    p.disconnect()
    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)

    return True


if __name__ == "__main__":
    success = test_urdf_loading()
    exit(0 if success else 1)
