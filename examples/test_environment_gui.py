#!/usr/bin/env python3
"""
Interactive test of PyBullet drone environment with GUI.

This script allows you to visualize the drone and test random or manual control.
"""

import argparse
import time

import numpy as np
from drone_gym.envs.pybullet_drone_env import PyBulletDroneEnv


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Test PyBullet drone environment with GUI"
    )
    parser.add_argument(
        "--episodes",
        type=int,
        default=3,
        help="Number of episodes to run",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=500,
        help="Maximum steps per episode",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.01,
        help="Delay between steps (seconds)",
    )
    parser.add_argument(
        "--random-actions",
        action="store_true",
        help="Use random actions instead of simple controller",
    )
    return parser.parse_args()


def simple_controller(env, goal_position):
    """
    Simple proportional controller to reach goal.

    Args:
        env: Environment instance
        goal_position: Target position [x, y, z]

    Returns:
        Action [vx, vy, vz, yaw_rate]
    """
    # Get current position
    state = env.sim.get_state()
    position = state["position"]

    # Calculate error
    error = goal_position - position

    # Proportional gain
    kp = 1.0

    # Velocity command
    vx = np.clip(kp * error[0], -5.0, 5.0)
    vy = np.clip(kp * error[1], -5.0, 5.0)
    vz = np.clip(kp * error[2], -2.0, 2.0)

    # No yaw control
    yaw_rate = 0.0

    return np.array([vx, vy, vz, yaw_rate])


def main():
    """Main test function."""
    args = parse_args()

    print("=" * 60)
    print("PyBullet Drone Environment - GUI Test")
    print("=" * 60)
    print(f"\nSettings:")
    print(f"  Episodes: {args.episodes}")
    print(f"  Max steps per episode: {args.max_steps}")
    print(f"  Control mode: {'Random' if args.random_actions else 'Simple P controller'}")
    print(f"  Delay: {args.delay}s per step")
    print("\nStarting in 2 seconds...")
    time.sleep(2)

    # Create environment with GUI
    env = PyBulletDroneEnv(
        use_mavlink=False,
        gui=True,
        max_steps=args.max_steps,
        goal_threshold=0.5,
        collision_penalty=-100.0,
        goal_reward=100.0,
        step_penalty=-0.1,
    )

    # Run episodes
    episode_rewards = []
    success_count = 0
    collision_count = 0

    for episode in range(args.episodes):
        print(f"\n{'=' * 60}")
        print(f"Episode {episode + 1}/{args.episodes}")
        print('=' * 60)

        obs, info = env.reset()
        goal = info["goal_position"]

        print(f"Goal position: [{goal[0]:.2f}, {goal[1]:.2f}, {goal[2]:.2f}]")
        print(f"Initial distance: {info['initial_distance']:.2f}m")

        episode_reward = 0
        step = 0

        for step in range(args.max_steps):
            # Choose action
            if args.random_actions:
                action = env.action_space.sample()
            else:
                action = simple_controller(env, goal)

            # Step environment
            obs, reward, terminated, truncated, info = env.step(action)
            episode_reward += reward

            # Print progress every 50 steps
            if (step + 1) % 50 == 0:
                pos = info["position"]
                dist = info["distance_to_goal"]
                print(
                    f"  Step {step + 1:3d}: "
                    f"Pos=[{pos[0]:5.2f}, {pos[1]:5.2f}, {pos[2]:5.2f}], "
                    f"Dist={dist:5.2f}m, "
                    f"Reward={reward:6.2f}"
                )

            # Delay for visualization
            time.sleep(args.delay)

            # Check termination
            if terminated or truncated:
                pos = info["position"]
                dist = info["distance_to_goal"]

                print(f"\nEpisode ended at step {step + 1}")
                print(f"  Final position: [{pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f}]")
                print(f"  Final distance: {dist:.2f}m")
                print(f"  Total reward: {episode_reward:.2f}")

                if info.get("collision", False):
                    collision_count += 1
                    print("  Result: COLLISION")
                elif dist < 0.5:
                    success_count += 1
                    print("  Result: SUCCESS - Goal reached!")
                else:
                    print("  Result: TIMEOUT")

                break

        episode_rewards.append(episode_reward)

        # Pause between episodes
        if episode < args.episodes - 1:
            print("\nNext episode in 2 seconds...")
            time.sleep(2)

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total episodes: {args.episodes}")
    print(f"Success rate: {success_count / args.episodes * 100:.1f}%")
    print(f"Collision rate: {collision_count / args.episodes * 100:.1f}%")
    print(f"\nReward statistics:")
    print(f"  Mean: {np.mean(episode_rewards):.2f}")
    print(f"  Std: {np.std(episode_rewards):.2f}")
    print(f"  Min: {np.min(episode_rewards):.2f}")
    print(f"  Max: {np.max(episode_rewards):.2f}")
    print("=" * 60)

    # Close environment
    env.close()

    print("\nEnvironment test complete!")


if __name__ == "__main__":
    main()
