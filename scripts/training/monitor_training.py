#!/usr/bin/env python3
"""
Real-time Training Monitor

Displays training progress and metrics in a clean dashboard format.

Usage:
    python scripts/training/monitor_training.py --log-dir data/logs/20260110_180049
"""

import argparse
import csv
import time
import os
from pathlib import Path
from datetime import datetime, timedelta


def clear_screen():
    """Clear terminal screen."""
    os.system('clear' if os.name != 'nt' else 'cls')


def format_time(seconds):
    """Format seconds into human-readable time."""
    return str(timedelta(seconds=int(seconds)))


def format_number(num):
    """Format number with commas."""
    if isinstance(num, (int, float)):
        if num >= 1000:
            return f"{num:,.0f}"
        elif num >= 1:
            return f"{num:.2f}"
        else:
            return f"{num:.4f}"
    return str(num)


def parse_progress_csv(csv_path):
    """Parse the progress.csv file and return latest metrics."""
    if not csv_path.exists():
        return None

    try:
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if not rows:
                return None
            return rows[-1]  # Return latest row
    except Exception as e:
        return None


def display_dashboard(log_dir, start_time, checkpoint_dir):
    """Display training dashboard."""
    log_dir = Path(log_dir)
    checkpoint_dir = Path(checkpoint_dir) if checkpoint_dir else None
    progress_csv = log_dir / "progress.csv"

    # Get latest metrics
    latest = parse_progress_csv(progress_csv)

    # Calculate elapsed time
    elapsed = time.time() - start_time

    clear_screen()

    # Header
    print("=" * 80)
    print(" " * 20 + "🚁 DRONE RL TRAINING MONITOR 🚁")
    print("=" * 80)
    print()

    # Training Info
    print("📊 TRAINING STATUS")
    print("-" * 80)
    print(f"  Log Directory:      {log_dir}")
    print(f"  Elapsed Time:       {format_time(elapsed)}")
    print(f"  Current Time:       {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    if latest:
        # Progress
        total_timesteps = int(float(latest.get('time/total_timesteps', 0)))
        target_timesteps = 1_770_000  # 770k + 1M
        progress_pct = (total_timesteps / target_timesteps) * 100

        print("📈 PROGRESS")
        print("-" * 80)
        print(f"  Timesteps:          {format_number(total_timesteps)} / {format_number(target_timesteps)}")
        print(f"  Progress:           {progress_pct:.1f}%")

        # Progress bar
        bar_length = 50
        filled = int(bar_length * progress_pct / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"  [{bar}] {progress_pct:.1f}%")
        print()

        # Performance Metrics
        print("🎯 PERFORMANCE METRICS")
        print("-" * 80)

        ep_reward = latest.get('rollout/ep_rew_mean', 'N/A')
        ep_len = latest.get('rollout/ep_len_mean', 'N/A')

        if ep_reward != 'N/A' and ep_reward and ep_reward.strip():
            ep_reward = format_number(float(ep_reward))
        else:
            ep_reward = 'N/A'
        if ep_len != 'N/A' and ep_len and ep_len.strip():
            ep_len = format_number(float(ep_len))
        else:
            ep_len = 'N/A'

        print(f"  Episode Reward:     {ep_reward}")
        print(f"  Episode Length:     {ep_len}")

        # Success rate (if available)
        success_rate = latest.get('eval/success_rate', None)
        if success_rate:
            print(f"  Success Rate:       {float(success_rate)*100:.1f}%")

        print()

        # Learning Metrics
        print("🧠 LEARNING METRICS")
        print("-" * 80)

        learning_rate = latest.get('train/learning_rate', 'N/A')
        value_loss = latest.get('train/value_loss', 'N/A')
        policy_loss = latest.get('train/policy_gradient_loss', 'N/A')
        entropy = latest.get('train/entropy_loss', 'N/A')

        if learning_rate != 'N/A' and learning_rate and learning_rate.strip():
            learning_rate = format_number(float(learning_rate))
        else:
            learning_rate = 'N/A'
        if value_loss != 'N/A' and value_loss and value_loss.strip():
            value_loss = format_number(float(value_loss))
        else:
            value_loss = 'N/A'
        if policy_loss != 'N/A' and policy_loss and policy_loss.strip():
            policy_loss = format_number(float(policy_loss))
        else:
            policy_loss = 'N/A'
        if entropy != 'N/A' and entropy and entropy.strip():
            entropy = format_number(float(entropy))
        else:
            entropy = 'N/A'

        print(f"  Learning Rate:      {learning_rate}")
        print(f"  Value Loss:         {value_loss}")
        print(f"  Policy Loss:        {policy_loss}")
        print(f"  Entropy:            {entropy}")
        print()

        # FPS
        fps = latest.get('time/fps', 'N/A')
        if fps != 'N/A' and fps and fps.strip():
            fps = format_number(float(fps))
        else:
            fps = 'N/A'

        print("⚡ PERFORMANCE")
        print("-" * 80)
        print(f"  Training FPS:       {fps}")
        print()
    else:
        print("⏳ Waiting for training data...")
        print("   (This may take a few minutes for the first rollout)")
        print()

    # Checkpoints
    if checkpoint_dir and checkpoint_dir.exists():
        checkpoints = sorted(checkpoint_dir.glob("rl_model_*.zip"))
        if checkpoints:
            print("💾 CHECKPOINTS")
            print("-" * 80)
            print(f"  Total Checkpoints:  {len(checkpoints)}")
            latest_checkpoint = checkpoints[-1]
            checkpoint_time = datetime.fromtimestamp(latest_checkpoint.stat().st_mtime)
            print(f"  Latest:             {latest_checkpoint.name}")
            print(f"  Saved at:           {checkpoint_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print()

    # TensorBoard Info
    print("📺 TENSORBOARD")
    print("-" * 80)
    print("  Primary:            http://localhost:6006  (Docker - all logs)")
    print("  Dedicated:          http://localhost:6007  (This training run)")
    print()

    print("=" * 80)
    print("  Press Ctrl+C to exit monitor (training continues in background)")
    print("=" * 80)


def main():
    """Main monitoring loop."""
    parser = argparse.ArgumentParser(description="Monitor RL training progress")
    parser.add_argument(
        '--log-dir',
        type=str,
        default='data/logs/20260110_180049',
        help='Path to training log directory'
    )
    parser.add_argument(
        '--checkpoint-dir',
        type=str,
        default='data/checkpoints/PPO_continued_20260110_180049',
        help='Path to checkpoint directory'
    )
    parser.add_argument(
        '--refresh',
        type=int,
        default=5,
        help='Refresh interval in seconds (default: 5)'
    )

    args = parser.parse_args()

    start_time = time.time()

    print("Starting training monitor...")
    time.sleep(1)

    try:
        while True:
            display_dashboard(args.log_dir, start_time, args.checkpoint_dir)
            time.sleep(args.refresh)
    except KeyboardInterrupt:
        print("\n\nMonitor stopped. Training continues in background.")
        print(f"To view TensorBoard: http://localhost:6007")
        print(f"To stop training: kill {os.getpid()}")


if __name__ == "__main__":
    main()
