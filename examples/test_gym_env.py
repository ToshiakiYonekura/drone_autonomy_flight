#!/usr/bin/env python3
"""Test the Gym environment with Crazyflie model."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np


def test_gym_environment():
    """Test PyBulletDroneEnv with Crazyflie model."""
    print("=" * 60)
    print("Testing PyBulletDroneEnv with Crazyflie Model")
    print("=" * 60)

    # Import environment
    from drone_gym.envs.pybullet_drone_env import PyBulletDroneEnv

    print("\n1. Creating environment...")
    env = PyBulletDroneEnv(
        use_mavlink=False,
        gui=False,
        max_steps=100,
    )
    print("   ✓ Environment created")

    print("\n2. Resetting environment...")
    obs, info = env.reset()
    print(f"   ✓ Reset successful")
    print(f"   Observation shape: {obs.shape}")
    print(f"   Goal position: {info['goal_position']}")
    print(f"   Initial distance: {info['initial_distance']:.3f} m")

    print("\n3. Checking observation components...")
    lidar = obs[:360]
    camera = obs[360:872]
    state = obs[872:884]
    print(f"   LiDAR: {lidar.shape} (min: {lidar.min():.3f}, max: {lidar.max():.3f})")
    print(f"   Camera: {camera.shape} (min: {camera.min():.3f}, max: {camera.max():.3f})")
    print(f"   State: {state.shape}")

    print("\n4. Running episode with random actions...")
    total_reward = 0
    for step in range(50):
        # Random action
        action = env.action_space.sample()

        # Step environment
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward

        if step % 10 == 0:
            print(f"   Step {step:2d}: reward={reward:7.3f}, "
                  f"distance={info['distance_to_goal']:.3f}m, "
                  f"collision={info['collision']}")

        if terminated or truncated:
            print(f"   Episode ended at step {step}")
            break

    print(f"\n   Total reward: {total_reward:.3f}")

    print("\n5. Testing controlled flight...")
    obs, info = env.reset()

    # Fly towards goal
    for step in range(50):
        # Proportional controller towards goal
        # Get current position from sim state
        sim_state = env.sim.get_state()
        current_pos = sim_state['position']
        goal_pos = info['goal_position']
        direction = goal_pos - current_pos
        distance = np.linalg.norm(direction)

        if distance > 0.1:
            direction = direction / distance
            velocity = direction * 2.0  # 2 m/s
        else:
            velocity = np.zeros(3)

        action = np.array([velocity[0], velocity[1], velocity[2], 0.0])

        obs, reward, terminated, truncated, info = env.step(action)

        if step % 10 == 0:
            print(f"   Step {step:2d}: distance={info['distance_to_goal']:.3f}m, "
                  f"reward={reward:.3f}")

        if terminated:
            if info['distance_to_goal'] < env.goal_threshold:
                print(f"   ✓ Goal reached at step {step}!")
            else:
                print(f"   ✗ Collision at step {step}")
            break

    print("\n6. Checking drone physics parameters...")
    sim = env.sim
    print(f"   Mass: {sim.mass} kg")
    print(f"   Arm length: {sim.arm_length} m")
    print(f"   Thrust-to-weight: {sim.thrust_to_weight}")
    print(f"   Current motor RPMs: {sim.motor_rpms}")

    print("\n7. Closing environment...")
    env.close()
    print("   ✓ Environment closed")

    print("\n" + "=" * 60)
    print("Gym environment test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    test_gym_environment()
