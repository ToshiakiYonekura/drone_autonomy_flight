#!/usr/bin/env python3
"""
Example training script for PyBullet drone environment using Stable Baselines3.

This script demonstrates how to train a reinforcement learning agent
to navigate a drone using the PyBullet physics simulation.
"""

import argparse
import os
from datetime import datetime

import gymnasium as gym
import numpy as np
from stable_baselines3 import PPO, SAC, TD3
from stable_baselines3.common.callbacks import (
    CheckpointCallback,
    EvalCallback,
)
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import SubprocVecEnv, VecNormalize

from drone_gym.envs.pybullet_drone_env import PyBulletDroneEnv


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Train RL agent for PyBullet drone navigation"
    )
    parser.add_argument(
        "--algorithm",
        type=str,
        default="PPO",
        choices=["PPO", "SAC", "TD3"],
        help="RL algorithm to use",
    )
    parser.add_argument(
        "--total-timesteps",
        type=int,
        default=1_000_000,
        help="Total training timesteps",
    )
    parser.add_argument(
        "--n-envs",
        type=int,
        default=4,
        help="Number of parallel environments",
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=3e-4,
        help="Learning rate",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="Batch size",
    )
    parser.add_argument(
        "--gamma",
        type=float,
        default=0.99,
        help="Discount factor",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Show PyBullet GUI (only for n-envs=1)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./data/checkpoints",
        help="Output directory for checkpoints",
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default="./data/logs",
        help="Directory for TensorBoard logs",
    )
    parser.add_argument(
        "--eval-freq",
        type=int,
        default=10_000,
        help="Evaluation frequency (timesteps)",
    )
    parser.add_argument(
        "--checkpoint-freq",
        type=int,
        default=50_000,
        help="Checkpoint save frequency (timesteps)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed",
    )
    parser.add_argument(
        "--load-checkpoint",
        type=str,
        default=None,
        help="Path to checkpoint to load",
    )
    return parser.parse_args()


def make_env(rank: int, seed: int = 0, gui: bool = False):
    """
    Create environment with unique seed.

    Args:
        rank: Unique ID for the environment
        seed: Base random seed
        gui: Show PyBullet GUI

    Returns:
        Environment creation function
    """

    def _init():
        env = PyBulletDroneEnv(
            use_mavlink=False,
            gui=gui and rank == 0,  # Only show GUI for first env
            max_steps=1000,
            goal_threshold=0.5,
            collision_penalty=-100.0,
            goal_reward=100.0,
            step_penalty=-0.1,
        )
        env.reset(seed=seed + rank)
        return env

    return _init


def main():
    """Main training function."""
    args = parse_args()

    # Create output directories
    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(args.log_dir, exist_ok=True)

    # Create timestamp for this run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_name = f"{args.algorithm}_{timestamp}"

    print(f"Starting training: {run_name}")
    print(f"Algorithm: {args.algorithm}")
    print(f"Total timesteps: {args.total_timesteps:,}")
    print(f"Parallel environments: {args.n_envs}")
    print(f"Learning rate: {args.learning_rate}")
    print(f"Batch size: {args.batch_size}")
    print(f"Gamma: {args.gamma}")
    print(f"Seed: {args.seed}")

    # Disable GUI if using multiple environments
    gui = args.gui and args.n_envs == 1
    if args.gui and args.n_envs > 1:
        print("Warning: GUI disabled when using multiple environments")

    # Create vectorized environments
    print(f"\nCreating {args.n_envs} parallel environments...")
    env = make_vec_env(
        lambda: make_env(0, args.seed, gui)(),
        n_envs=args.n_envs,
        seed=args.seed,
        vec_env_cls=SubprocVecEnv if args.n_envs > 1 else None,
    )

    # Wrap with normalization (improves training stability)
    env = VecNormalize(
        env,
        norm_obs=True,
        norm_reward=True,
        clip_obs=10.0,
        clip_reward=10.0,
    )

    # Create evaluation environment
    eval_env = make_vec_env(
        lambda: make_env(1000, args.seed, False)(),
        n_envs=1,
        seed=args.seed,
    )
    eval_env = VecNormalize(
        eval_env,
        norm_obs=True,
        norm_reward=False,  # Don't normalize reward for evaluation
        clip_obs=10.0,
    )

    # Set up callbacks
    checkpoint_callback = CheckpointCallback(
        save_freq=args.checkpoint_freq // args.n_envs,
        save_path=os.path.join(args.output_dir, run_name),
        name_prefix="rl_model",
        save_replay_buffer=True,
        save_vecnormalize=True,
    )

    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=os.path.join(args.output_dir, run_name, "best"),
        log_path=os.path.join(args.log_dir, run_name),
        eval_freq=args.eval_freq // args.n_envs,
        n_eval_episodes=10,
        deterministic=True,
        render=False,
    )

    # Create RL model
    print(f"\nInitializing {args.algorithm} model...")

    model_kwargs = {
        "env": env,
        "learning_rate": args.learning_rate,
        "gamma": args.gamma,
        "verbose": 1,
        "tensorboard_log": os.path.join(args.log_dir, run_name),
        "seed": args.seed,
    }

    if args.algorithm == "PPO":
        model = PPO(
            policy="MlpPolicy",
            batch_size=args.batch_size,
            n_steps=2048 // args.n_envs,
            n_epochs=10,
            gae_lambda=0.95,
            clip_range=0.2,
            ent_coef=0.01,
            **model_kwargs,
        )
    elif args.algorithm == "SAC":
        model = SAC(
            policy="MlpPolicy",
            batch_size=args.batch_size,
            buffer_size=1_000_000,
            learning_starts=10_000,
            tau=0.005,
            **model_kwargs,
        )
    elif args.algorithm == "TD3":
        model = TD3(
            policy="MlpPolicy",
            batch_size=args.batch_size,
            buffer_size=1_000_000,
            learning_starts=10_000,
            tau=0.005,
            **model_kwargs,
        )
    else:
        raise ValueError(f"Unknown algorithm: {args.algorithm}")

    # Load checkpoint if specified
    if args.load_checkpoint:
        print(f"\nLoading checkpoint from: {args.load_checkpoint}")
        model = model.load(args.load_checkpoint, env=env)

    # Train the model
    print("\nStarting training...")
    print(f"Checkpoints will be saved to: {os.path.join(args.output_dir, run_name)}")
    print(f"TensorBoard logs: {os.path.join(args.log_dir, run_name)}")
    print("\nTo monitor training, run:")
    print(f"  tensorboard --logdir {args.log_dir}")

    try:
        model.learn(
            total_timesteps=args.total_timesteps,
            callback=[checkpoint_callback, eval_callback],
            progress_bar=True,
        )
    except KeyboardInterrupt:
        print("\n\nTraining interrupted by user")

    # Save final model
    final_path = os.path.join(args.output_dir, run_name, "final_model")
    print(f"\nSaving final model to: {final_path}")
    model.save(final_path)

    # Save normalization statistics
    env.save(os.path.join(args.output_dir, run_name, "vec_normalize.pkl"))

    print("\nTraining complete!")
    print(f"Model saved to: {final_path}")

    # Close environments
    env.close()
    eval_env.close()


if __name__ == "__main__":
    main()
