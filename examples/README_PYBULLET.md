# PyBullet Drone RL Training Examples

This directory contains example scripts for training and testing reinforcement learning agents in the PyBullet drone environment.

## Overview

The PyBullet drone environment provides a lightweight, fast physics simulation for training RL agents to navigate drones. It replaces AirSim with PyBullet for better performance and ease of use.

## Files

- `train_pybullet_rl.py` - Train RL agent using Stable Baselines3
- `test_pybullet_rl.py` - Test trained agent and evaluate performance
- `README_PYBULLET.md` - This file

## Quick Start

### 1. Basic Training

Train a PPO agent with default settings:

```bash
python examples/train_pybullet_rl.py
```

### 2. Training with Custom Parameters

```bash
python examples/train_pybullet_rl.py \
    --algorithm PPO \
    --total-timesteps 2000000 \
    --n-envs 8 \
    --learning-rate 3e-4 \
    --batch-size 128
```

### 3. Training with Different Algorithms

SAC (Soft Actor-Critic):
```bash
python examples/train_pybullet_rl.py --algorithm SAC
```

TD3 (Twin Delayed DDPG):
```bash
python examples/train_pybullet_rl.py --algorithm TD3
```

### 4. Training with GUI (Single Environment Only)

```bash
python examples/train_pybullet_rl.py --n-envs 1 --gui
```

## Testing Trained Models

### Basic Testing

```bash
python examples/test_pybullet_rl.py \
    data/checkpoints/PPO_20231228_120000/final_model.zip \
    --algorithm PPO
```

### Testing with GUI

```bash
python examples/test_pybullet_rl.py \
    data/checkpoints/PPO_20231228_120000/final_model.zip \
    --algorithm PPO \
    --gui \
    --n-episodes 5 \
    --deterministic
```

### Testing with Normalization Stats

If you saved VecNormalize statistics during training:

```bash
python examples/test_pybullet_rl.py \
    data/checkpoints/PPO_20231228_120000/final_model.zip \
    --algorithm PPO \
    --vec-normalize-path data/checkpoints/PPO_20231228_120000/vec_normalize.pkl \
    --gui
```

## Training Parameters

### Common Parameters

- `--algorithm` - RL algorithm (PPO, SAC, TD3)
- `--total-timesteps` - Total training steps (default: 1,000,000)
- `--n-envs` - Number of parallel environments (default: 4)
- `--learning-rate` - Learning rate (default: 3e-4)
- `--batch-size` - Batch size (default: 64)
- `--gamma` - Discount factor (default: 0.99)
- `--gui` - Show PyBullet GUI (only with n-envs=1)
- `--output-dir` - Checkpoint directory (default: ./data/checkpoints)
- `--log-dir` - TensorBoard log directory (default: ./data/logs)
- `--eval-freq` - Evaluation frequency in timesteps (default: 10,000)
- `--checkpoint-freq` - Checkpoint save frequency (default: 50,000)
- `--seed` - Random seed (default: 42)
- `--load-checkpoint` - Continue training from checkpoint

## Monitoring Training

### TensorBoard

Monitor training progress with TensorBoard:

```bash
tensorboard --logdir data/logs
```

Then open http://localhost:6006 in your browser.

### Key Metrics to Watch

- `rollout/ep_rew_mean` - Average episode reward
- `rollout/ep_len_mean` - Average episode length
- `train/loss` - Training loss
- `eval/mean_reward` - Evaluation reward

## Environment Details

### Observation Space (884 dimensions)

1. **LiDAR scan (360)** - 360-degree 2D distance measurements
2. **Camera features (512)** - Compressed visual features
3. **State vector (12)**:
   - Position (3): x, y, z
   - Velocity (3): vx, vy, vz
   - Orientation (3): roll, pitch, yaw
   - Goal relative position (3): dx, dy, dz

### Action Space (4 dimensions)

- `vx` - Forward velocity [-5, 5] m/s
- `vy` - Lateral velocity [-5, 5] m/s
- `vz` - Vertical velocity [-2, 2] m/s
- `yaw_rate` - Yaw rate [-1, 1] rad/s

### Rewards

- **Goal reached**: +100.0
- **Collision**: -100.0
- **Step penalty**: -0.1 per step
- **Progress reward**: Proportional to distance reduction

### Episode Termination

Episodes terminate when:
- Drone reaches goal (distance < 0.5m)
- Collision with obstacle
- Altitude too low (< 0.2m) or too high (> 10m)
- Maximum steps reached (1000)

## Tips for Better Training

### 1. Start with PPO

PPO is generally the most stable algorithm for continuous control:

```bash
python examples/train_pybullet_rl.py --algorithm PPO --n-envs 8
```

### 2. Use Multiple Parallel Environments

More environments = faster training:

```bash
python examples/train_pybullet_rl.py --n-envs 16
```

### 3. Tune Hyperparameters

If training is unstable:
- Decrease learning rate: `--learning-rate 1e-4`
- Increase batch size: `--batch-size 256`
- Adjust gamma: `--gamma 0.95`

### 4. Resume Training from Checkpoint

```bash
python examples/train_pybullet_rl.py \
    --load-checkpoint data/checkpoints/PPO_20231228_120000/rl_model_500000_steps.zip
```

### 5. Save GPU Memory

PyBullet runs on CPU, so you can use smaller batches if training on CPU:

```bash
python examples/train_pybullet_rl.py --batch-size 32 --n-envs 4
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'pybullet'"

Install PyBullet:
```bash
pip install pybullet
```

### "OpenGL error" or GUI issues

Run without GUI:
```bash
python examples/train_pybullet_rl.py  # GUI is off by default
```

Or install OpenGL libraries:
```bash
sudo apt-get install mesa-utils libgl1-mesa-glx
```

### Training is slow

- Increase parallel environments: `--n-envs 16`
- Reduce render delay in testing: `--render-delay 0.001`
- Run in DIRECT mode (no GUI)

### Agent not learning

- Check TensorBoard for reward trends
- Increase training time: `--total-timesteps 5000000`
- Try different algorithm: `--algorithm SAC`
- Adjust learning rate: `--learning-rate 1e-4`

## Advanced Usage

### Custom Environment Parameters

You can modify the environment directly in the scripts:

```python
env = PyBulletDroneEnv(
    use_mavlink=False,
    gui=True,
    max_steps=2000,  # Longer episodes
    goal_threshold=0.3,  # Tighter goal tolerance
    collision_penalty=-200.0,  # Stronger collision penalty
    goal_reward=200.0,  # Higher goal reward
    step_penalty=-0.05,  # Smaller step penalty
)
```

### Integration with ArduPilot SITL

To test trained policies with ArduPilot SITL:

1. Start ArduPilot SITL:
```bash
cd /opt/ardupilot
./Tools/autotest/sim_vehicle.py -v ArduCopter --console --map
```

2. Enable MAVLink in environment:
```python
env = PyBulletDroneEnv(
    use_mavlink=True,
    mavlink_connection="udp:127.0.0.1:14550",
)
```

## Next Steps

1. Train a baseline model:
   ```bash
   python examples/train_pybullet_rl.py --total-timesteps 500000
   ```

2. Monitor with TensorBoard:
   ```bash
   tensorboard --logdir data/logs
   ```

3. Test the best model:
   ```bash
   python examples/test_pybullet_rl.py \
       data/checkpoints/PPO_*/best/best_model.zip \
       --algorithm PPO --gui --n-episodes 10
   ```

4. Fine-tune hyperparameters based on results

5. Integrate with your custom navigation stack

## References

- [Stable Baselines3 Documentation](https://stable-baselines3.readthedocs.io/)
- [PyBullet Quick Start Guide](https://docs.google.com/document/d/10sXEhzFRSnvFcl3XxNGhnD4N2SedqwdAvK3dsihxVUA/)
- [OpenAI Gym Documentation](https://www.gymlibrary.dev/)
