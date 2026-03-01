#!/usr/bin/env python3
"""
Simple test to verify PyBullet drone environment works correctly.

This script runs a few episodes with random actions to check:
- Environment initialization
- Step function
- Observation/action spaces
- Termination conditions
"""

import numpy as np
from drone_gym.envs.pybullet_drone_env import PyBulletDroneEnv


def test_environment():
    """Test basic environment functionality."""
    print("=" * 60)
    print("PyBullet Drone Environment Test")
    print("=" * 60)

    # Create environment
    print("\n1. Creating environment...")
    try:
        env = PyBulletDroneEnv(
            use_mavlink=False,
            gui=False,  # No GUI for testing
            max_steps=100,
        )
        print("   SUCCESS: Environment created")
    except Exception as e:
        print(f"   FAILED: {e}")
        return False

    # Check spaces
    print("\n2. Checking observation and action spaces...")
    try:
        print(f"   Observation space: {env.observation_space.shape}")
        print(f"   Action space: {env.action_space.shape}")
        assert env.observation_space.shape == (884,), "Wrong observation shape"
        assert env.action_space.shape == (4,), "Wrong action shape"
        print("   SUCCESS: Spaces are correct")
    except Exception as e:
        print(f"   FAILED: {e}")
        env.close()
        return False

    # Test reset
    print("\n3. Testing reset...")
    try:
        obs, info = env.reset()
        print(f"   Observation shape: {obs.shape}")
        print(f"   Goal position: {info['goal_position']}")
        assert obs.shape == (884,), "Wrong observation shape"
        assert "goal_position" in info, "Missing goal_position in info"
        print("   SUCCESS: Reset works")
    except Exception as e:
        print(f"   FAILED: {e}")
        env.close()
        return False

    # Test step
    print("\n4. Testing step with random actions...")
    try:
        for i in range(10):
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)

            if i == 0:
                print(f"   First step:")
                print(f"     Action: {action}")
                print(f"     Reward: {reward:.2f}")
                print(f"     Position: {info['position']}")
                print(f"     Distance to goal: {info['distance_to_goal']:.2f}m")

            if terminated or truncated:
                print(f"   Episode ended at step {i + 1}")
                if info.get("collision", False):
                    print("     Reason: Collision")
                elif info["distance_to_goal"] < 0.5:
                    print("     Reason: Goal reached")
                else:
                    print("     Reason: Other termination")
                break

        print("   SUCCESS: Step function works")
    except Exception as e:
        print(f"   FAILED: {e}")
        env.close()
        return False

    # Test multiple episodes
    print("\n5. Running multiple episodes...")
    try:
        episode_rewards = []
        episode_lengths = []

        for episode in range(5):
            obs, info = env.reset()
            episode_reward = 0
            steps = 0

            for step in range(100):
                action = env.action_space.sample()
                obs, reward, terminated, truncated, info = env.step(action)
                episode_reward += reward
                steps += 1

                if terminated or truncated:
                    break

            episode_rewards.append(episode_reward)
            episode_lengths.append(steps)

            print(
                f"   Episode {episode + 1}: "
                f"Reward={episode_reward:.2f}, "
                f"Length={steps}, "
                f"Final distance={info['distance_to_goal']:.2f}m"
            )

        print(f"\n   Statistics:")
        print(f"     Mean reward: {np.mean(episode_rewards):.2f}")
        print(f"     Mean length: {np.mean(episode_lengths):.1f} steps")
        print("   SUCCESS: Multiple episodes work")
    except Exception as e:
        print(f"   FAILED: {e}")
        env.close()
        return False

    # Test observation components
    print("\n6. Testing observation components...")
    try:
        obs, info = env.reset()

        # Extract components
        lidar = obs[:360]
        camera = obs[360:872]
        state = obs[872:884]

        print(f"   LiDAR: shape={lidar.shape}, range=[{lidar.min():.2f}, {lidar.max():.2f}]")
        print(f"   Camera: shape={camera.shape}, range=[{camera.min():.2f}, {camera.max():.2f}]")
        print(f"   State: shape={state.shape}")
        print(f"     Position: {state[0:3]}")
        print(f"     Velocity: {state[3:6]}")
        print(f"     Orientation: {state[6:9]}")
        print(f"     Goal relative: {state[9:12]}")

        print("   SUCCESS: Observation components are correct")
    except Exception as e:
        print(f"   FAILED: {e}")
        env.close()
        return False

    # Close environment
    print("\n7. Closing environment...")
    try:
        env.close()
        print("   SUCCESS: Environment closed cleanly")
    except Exception as e:
        print(f"   FAILED: {e}")
        return False

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)
    print("\nYou can now:")
    print("1. Train an agent: python examples/train_pybullet_rl.py")
    print("2. Test with GUI: python examples/test_environment_gui.py")
    print("\n")

    return True


if __name__ == "__main__":
    success = test_environment()
    exit(0 if success else 1)
