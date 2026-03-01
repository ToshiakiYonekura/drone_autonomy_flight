#!/usr/bin/env python3
"""
Continue Training PPO Agent from Checkpoint

Loads a previously trained PPO model and continues training.

Usage:
    python scripts/training/continue_training.py --checkpoint data/checkpoints/PPO_20251228_162953/best/best_model.zip --timesteps 1000000
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

import numpy as np
import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv
from stable_baselines3.common.callbacks import (
    CheckpointCallback,
    EvalCallback,
    CallbackList,
)
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.logger import configure

import drone_gym


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


def make_env(env_id: str, rank: int, seed: int = 0):
    """
    Create environment for training.

    Args:
        env_id: Gym environment ID
        rank: Process rank (for parallel environments)
        seed: Random seed

    Returns:
        Callable that creates environment
    """
    def _init():
        env = gym.make(env_id)
        env = Monitor(env)
        env.reset(seed=seed + rank)  # Gymnasium uses reset(seed=...) instead of seed()
        return env

    return _init


def continue_training(
    checkpoint_path: str,
    env_id: str = "PyBulletDrone-v0",
    total_timesteps: int = 1_000_000,
    n_envs: int = 8,
    learning_rate: float = None,  # Use model's learning rate if None
    save_dir: str = "./data/checkpoints",
    log_dir: str = "./data/logs",
    eval_freq: int = 10000,
    save_freq: int = 50000,
    seed: int = 0,
):
    """
    Continue training PPO agent from checkpoint.

    Args:
        checkpoint_path: Path to checkpoint model (.zip file)
        env_id: Gym environment ID
        total_timesteps: Additional training timesteps
        n_envs: Number of parallel environments
        learning_rate: Learning rate (None to keep existing)
        save_dir: Directory to save models
        log_dir: Directory to save logs
        eval_freq: Evaluation frequency
        save_freq: Checkpoint save frequency
        seed: Random seed
    """
    logger.info("=" * 80)
    logger.info("CONTINUING PPO TRAINING FROM CHECKPOINT")
    logger.info("=" * 80)
    logger.info(f"Checkpoint: {checkpoint_path}")
    logger.info(f"Environment: {env_id}")
    logger.info(f"Additional timesteps: {total_timesteps:,}")
    logger.info(f"Parallel environments: {n_envs}")
    logger.info("=" * 80)

    # Verify checkpoint exists
    checkpoint_path = Path(checkpoint_path)
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

    # Create directories
    save_dir = Path(save_dir)
    log_dir = Path(log_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create timestamp for this run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = save_dir / f"PPO_continued_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # Create vectorized environments
    logger.info(f"Creating {n_envs} parallel environments...")

    if n_envs > 1:
        env = SubprocVecEnv([make_env(env_id, i, seed) for i in range(n_envs)])
    else:
        env = DummyVecEnv([make_env(env_id, 0, seed)])

    # Create evaluation environment
    eval_env = DummyVecEnv([make_env(env_id, 0, seed + 1000)])

    # Load model from checkpoint
    logger.info(f"Loading model from {checkpoint_path}...")
    model = PPO.load(
        str(checkpoint_path),
        env=env,
        tensorboard_log=str(log_dir / timestamp),
    )

    # Update learning rate if specified
    if learning_rate is not None:
        logger.info(f"Updating learning rate to {learning_rate}")
        model.learning_rate = learning_rate

    logger.info(f"Model loaded successfully")
    logger.info(f"Current learning rate: {model.learning_rate}")
    logger.info(f"Current num_timesteps: {model.num_timesteps:,}")

    # Configure logger
    new_logger = configure(str(log_dir / timestamp), ["stdout", "csv", "tensorboard"])
    model.set_logger(new_logger)

    # Create callbacks
    checkpoint_callback = CheckpointCallback(
        save_freq=save_freq // n_envs,  # Adjust for parallel envs
        save_path=str(run_dir),
        name_prefix="rl_model",
    )

    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=str(run_dir / "best"),
        log_path=str(run_dir / "eval"),
        eval_freq=eval_freq // n_envs,  # Adjust for parallel envs
        deterministic=True,
        render=False,
        n_eval_episodes=100,  # More episodes for better evaluation
    )

    callback = CallbackList([checkpoint_callback, eval_callback])

    # Save configuration
    config = {
        'checkpoint_path': str(checkpoint_path),
        'env_id': env_id,
        'continued_timesteps': total_timesteps,
        'n_envs': n_envs,
        'learning_rate': float(model.learning_rate) if hasattr(model.learning_rate, '__float__') else model.learning_rate,
        'starting_timesteps': model.num_timesteps,
        'seed': seed,
        'timestamp': timestamp,
    }

    with open(run_dir / "config.yaml", 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

    logger.info(f"Configuration saved to {run_dir / 'config.yaml'}")

    # Train
    logger.info("-" * 80)
    logger.info("Continuing training...")
    logger.info("-" * 80)

    try:
        model.learn(
            total_timesteps=total_timesteps,
            callback=callback,
            log_interval=10,
            reset_num_timesteps=False,  # Keep counting from checkpoint
        )

        # Save final model
        final_model_path = run_dir / "final_model"
        model.save(str(final_model_path))
        logger.info(f"Final model saved to {final_model_path}")

        logger.info("=" * 80)
        logger.info("✓ CONTINUED TRAINING COMPLETED SUCCESSFULLY")
        logger.info(f"Total timesteps: {model.num_timesteps:,}")
        logger.info("=" * 80)

        return True

    except KeyboardInterrupt:
        logger.info("\nTraining interrupted by user")
        model.save(str(run_dir / "interrupted_model"))
        logger.info(f"Model saved to {run_dir / 'interrupted_model'}")
        return False

    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        return False

    finally:
        env.close()
        eval_env.close()


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Continue training PPO agent from checkpoint"
    )

    # Required
    parser.add_argument(
        '--checkpoint',
        type=str,
        required=True,
        help='Path to checkpoint model (.zip file)',
    )

    # Environment
    parser.add_argument(
        '--env',
        type=str,
        default='PyBulletDrone-v0',
        help='Environment ID (default: PyBulletDrone-v0)',
    )

    # Training
    parser.add_argument(
        '--timesteps',
        type=int,
        default=1_000_000,
        help='Additional training timesteps (default: 1,000,000)',
    )
    parser.add_argument(
        '--n-envs',
        type=int,
        default=8,
        help='Number of parallel environments (default: 8)',
    )

    # Hyperparameters
    parser.add_argument(
        '--lr',
        type=float,
        default=None,
        help='Learning rate (default: keep existing)',
    )

    # Directories
    parser.add_argument(
        '--save-dir',
        type=str,
        default='./data/checkpoints',
        help='Directory to save models',
    )
    parser.add_argument(
        '--log-dir',
        type=str,
        default='./data/logs',
        help='Directory to save logs',
    )

    # Other
    parser.add_argument(
        '--seed',
        type=int,
        default=0,
        help='Random seed (default: 0)',
    )

    args = parser.parse_args()

    try:
        success = continue_training(
            checkpoint_path=args.checkpoint,
            env_id=args.env,
            total_timesteps=args.timesteps,
            n_envs=args.n_envs,
            learning_rate=args.lr,
            save_dir=args.save_dir,
            log_dir=args.log_dir,
            seed=args.seed,
        )

        if success:
            sys.exit(0)
        else:
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
