#!/usr/bin/env python3
"""
Test trained RL agent in PyBullet drone environment.

This script loads a trained model and evaluates it in the environment.
"""

import argparse
import os
import time

import numpy as np
from stable_baselines3 import PPO, SAC, TD3
from stable_baselines3.common.vec_env import VecNormalize, DummyVecEnv

from drone_gym.envs.pybullet_drone_env import PyBulletDroneEnv


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Test trained RL agent for PyBullet drone"
    )
    parser.add_argument(
        "model_path",
        type=str,
        help="Path to trained model checkpoint",
    )
    parser.add_argument(
        "--algorithm",
        type=str,
        default="PPO",
        choices=["PPO", "SAC", "TD3"],
        help="RL algorithm used",
    )
    parser.add_argument(
        "--n-episodes",
        type=int,
        default=10,
        help="Number of episodes to test",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Show PyBullet GUI",
    )
    parser.add_argument(
        "--vec-normalize-path",
        type=str,
        default=None,
        help="Path to VecNormalize stats (optional)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed",
    )
    parser.add_argument(
        "--deterministic",
        action="store_true",
        help="Use deterministic policy",
    )
    parser.add_argument(
        "--render-delay",
        type=float,
        default=0.01,
        help="Delay between steps for visualization (seconds)",
    )
    return parser.parse_args()


def main():
    """Main testing function."""
    args = parse_args()

    print(f"Loading model from: {args.model_path}")
    print(f"Algorithm: {args.algorithm}")
    print(f"Number of episodes: {args.n_episodes}")
    print(f"Deterministic: {args.deterministic}")
    print(f"GUI: {args.gui}")

    # Create environment
    env = PyBulletDroneEnv(
        use_mavlink=False,
        gui=args.gui,
        max_steps=1000,
        goal_threshold=0.5,
        collision_penalty=-100.0,
        goal_reward=100.0,
        step_penalty=-0.1,
    )

    # Wrap in DummyVecEnv for compatibility
    env = DummyVecEnv([lambda: env])

    # Load VecNormalize stats if provided
    if args.vec_normalize_path:
        print(f"Loading normalization stats from: {args.vec_normalize_path}")
        env = VecNormalize.load(args.vec_normalize_path, env)
        env.training = False  # Disable training mode
        env.norm_reward = False  # Don't normalize rewards during evaluation

    # Load model
    print("Loading model...")
    if args.algorithm == "PPO":
        model = PPO.load(args.model_path, env=env)
    elif args.algorithm == "SAC":
        model = SAC.load(args.model_path, env=env)
    elif args.algorithm == "TD3":
        model = TD3.load(args.model_path, env=env)
    else:
        raise ValueError(f"Unknown algorithm: {args.algorithm}")

    print("\nStarting evaluation...")

    # Statistics
    episode_rewards = []
    episode_lengths = []
    success_count = 0
    collision_count = 0

    for episode in range(args.n_episodes):
        obs = env.reset()
        episode_reward = 0
        episode_length = 0
        done = False

        print(f"\nEpisode {episode + 1}/{args.n_episodes}")

        while not done:
            # Get action from model
            action, _ = model.predict(
                obs, deterministic=args.deterministic
            )

            # Step environment
            obs, reward, done, info = env.step(action)

            episode_reward += reward[0]
            episode_length += 1

            # Render if GUI enabled
            if args.gui:
                time.sleep(args.render_delay)

            # Check if episode ended
            if done[0]:
                # Extract info from vectorized environment
                episode_info = info[0]

                # Check termination reason
                if episode_info.get("collision", False):
                    collision_count += 1
                    print(f"  Result: COLLISION at step {episode_length}")
                elif episode_info["distance_to_goal"] < 0.5:
                    success_count += 1
                    print(f"  Result: SUCCESS at step {episode_length}")
                else:
                    print(f"  Result: TIMEOUT at step {episode_length}")

                print(f"  Reward: {episode_reward:.2f}")
                print(
                    f"  Final distance to goal: {episode_info['distance_to_goal']:.2f}m"
                )

                break

        episode_rewards.append(episode_reward)
        episode_lengths.append(episode_length)

    # Print statistics
    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)
    print(f"Episodes: {args.n_episodes}")
    print(f"Success rate: {success_count / args.n_episodes * 100:.1f}%")
    print(f"Collision rate: {collision_count / args.n_episodes * 100:.1f}%")
    print(f"\nReward statistics:")
    print(f"  Mean: {np.mean(episode_rewards):.2f}")
    print(f"  Std: {np.std(episode_rewards):.2f}")
    print(f"  Min: {np.min(episode_rewards):.2f}")
    print(f"  Max: {np.max(episode_rewards):.2f}")
    print(f"\nEpisode length statistics:")
    print(f"  Mean: {np.mean(episode_lengths):.1f} steps")
    print(f"  Std: {np.std(episode_lengths):.1f} steps")
    print(f"  Min: {np.min(episode_lengths)} steps")
    print(f"  Max: {np.max(episode_lengths)} steps")
    print("=" * 60)

    # Close environment
    env.close()


if __name__ == "__main__":
    main()
