# PyBullet Drone Simulation - Quick Start Guide

## Overview

This project now includes a lightweight PyBullet-based drone simulation environment for reinforcement learning. PyBullet was chosen as an alternative to AirSim because it's:

- **Lightweight**: Fast simulation for efficient RL training
- **Easy to install**: No complex dependencies
- **Well-integrated**: Works seamlessly with Stable Baselines3 and Gym
- **Compatible**: Works on Ubuntu 22.04 without dependency issues

## What's Included

### 1. Physics Simulation (`drone_gym/physics/`)

- `pybullet_drone.py` - PyBullet-based quadcopter physics simulation
  - 360-degree LiDAR simulation
  - Camera rendering (RGB images)
  - Collision detection
  - Dynamic obstacles
  - Realistic physics with force/torque control

### 2. Gym Environment (`drone_gym/envs/`)

- `pybullet_drone_env.py` - OpenAI Gym environment for RL training
  - **Observation space**: 884D (LiDAR 360 + Camera 512 + State 12)
  - **Action space**: 4D continuous [vx, vy, vz, yaw_rate]
  - **Reward shaping**: Goal reaching, collision avoidance, progress tracking
  - **Episode termination**: Goal reached, collision, boundary violation, timeout

### 3. Training Scripts (`examples/`)

- `train_pybullet_rl.py` - Train RL agent with PPO/SAC/TD3
- `test_pybullet_rl.py` - Evaluate trained agent
- `test_environment.py` - Verify environment setup
- `test_environment_gui.py` - Interactive visualization with GUI
- `README_PYBULLET.md` - Detailed documentation

## Getting Started

### Step 1: Build Docker Image

The Docker image already includes PyBullet in `requirements.txt`:

```bash
docker compose build
```

This will:
- Install PyBullet >=3.2.5
- Set up all ML/RL dependencies (Stable Baselines3, etc.)
- Configure ArduPilot SITL (optional, for advanced testing)

### Step 2: Start Container

```bash
docker compose up -d
docker exec -it autonomous_drone_sim bash
```

### Step 3: Verify Installation

Test that the environment works:

```bash
cd /workspace
python3 examples/test_environment.py
```

Expected output:
```
============================================================
PyBullet Drone Environment Test
============================================================

1. Creating environment...
   SUCCESS: Environment created

2. Checking observation and action spaces...
   Observation space: (884,)
   Action space: (4,)
   SUCCESS: Spaces are correct

...

ALL TESTS PASSED!
```

### Step 4: Train Your First Agent

Train a PPO agent with default settings:

```bash
python3 examples/train_pybullet_rl.py
```

With custom parameters:

```bash
python3 examples/train_pybullet_rl.py \
    --algorithm PPO \
    --total-timesteps 2000000 \
    --n-envs 8 \
    --learning-rate 3e-4
```

Monitor training with TensorBoard:

```bash
tensorboard --logdir data/logs
```

### Step 5: Test Trained Agent

```bash
python3 examples/test_pybullet_rl.py \
    data/checkpoints/PPO_*/best/best_model.zip \
    --algorithm PPO \
    --gui \
    --n-episodes 10
```

## Environment Details

### Observation Space (884 dimensions)

| Component | Dimensions | Description |
|-----------|------------|-------------|
| LiDAR | 360 | 360-degree 2D distance scan (normalized) |
| Camera | 512 | Compressed visual features from 64x64 RGB |
| Position | 3 | Current position [x, y, z] |
| Velocity | 3 | Linear velocity [vx, vy, vz] |
| Orientation | 3 | Euler angles [roll, pitch, yaw] |
| Goal Relative | 3 | Relative goal position [dx, dy, dz] |

### Action Space (4 dimensions)

| Action | Range | Unit | Description |
|--------|-------|------|-------------|
| vx | [-5, 5] | m/s | Forward/backward velocity |
| vy | [-5, 5] | m/s | Left/right velocity |
| vz | [-2, 2] | m/s | Up/down velocity |
| yaw_rate | [-1, 1] | rad/s | Rotation rate around z-axis |

### Rewards

- **Goal reached** (+100): Drone reaches within 0.5m of goal
- **Collision** (-100): Drone hits obstacle or boundary
- **Step penalty** (-0.1): Encourages faster completion
- **Progress reward** (variable): Proportional to distance reduction

### Episode Termination

Episodes end when:
1. Goal reached (distance < 0.5m)
2. Collision with obstacle
3. Altitude out of bounds (< 0.2m or > 10m)
4. Maximum steps reached (default: 1000)

## Architecture

```
PyBulletDroneEnv (Gym)
    |
    +-- PyBulletDrone (Physics)
    |       |
    |       +-- Quadcopter dynamics
    |       +-- LiDAR sensor
    |       +-- Camera sensor
    |       +-- Collision detection
    |       +-- Obstacle management
    |
    +-- MAVLinkInterface (optional)
            |
            +-- ArduPilot SITL control
```

## Comparison: AirSim vs PyBullet

| Feature | AirSim | PyBullet |
|---------|--------|----------|
| Installation | Complex | Simple |
| Dependencies | Many (outdated) | Few (up-to-date) |
| Performance | Heavy (GPU) | Fast (CPU/GPU) |
| RL Training Speed | Slow | Fast |
| Ubuntu 22.04 | Not compatible | Fully compatible |
| Realism | High | Medium |
| Best for | Visual realism | RL training |

## Tips for Best Results

### 1. Use Multiple Parallel Environments

More environments = faster training:

```bash
python3 examples/train_pybullet_rl.py --n-envs 16
```

### 2. Start with PPO

PPO is the most stable for continuous control:

```bash
python3 examples/train_pybullet_rl.py --algorithm PPO
```

### 3. Monitor with TensorBoard

Watch training progress in real-time:

```bash
tensorboard --logdir data/logs --host 0.0.0.0
```

Then open http://localhost:6006

### 4. Test Before Training

Always verify setup first:

```bash
python3 examples/test_environment.py
```

### 5. Use GUI for Debugging

Visualize agent behavior:

```bash
python3 examples/test_environment_gui.py --episodes 3
```

## Advanced: Integration with ArduPilot SITL

You can optionally test trained policies with real ArduPilot control:

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

3. Train/test as usual - actions will be sent to ArduPilot SITL

## Troubleshooting

### "ModuleNotFoundError: No module named 'pybullet'"

Make sure you're inside the Docker container:
```bash
docker exec -it autonomous_drone_sim bash
```

### "OpenGL error" in GUI mode

PyBullet GUI requires X11 forwarding or VNC. For headless training, simply don't use `--gui`.

### Training is slow

- Increase `--n-envs` (more parallel environments)
- Use CPU-optimized settings: `--batch-size 32`
- Don't use GUI during training

### Agent not learning

- Check TensorBoard for reward trends
- Increase training time: `--total-timesteps 5000000`
- Try different algorithm: `--algorithm SAC`
- Adjust learning rate: `--learning-rate 1e-4`

## Next Steps

1. **Train a baseline**: `python3 examples/train_pybullet_rl.py`
2. **Monitor progress**: `tensorboard --logdir data/logs`
3. **Test results**: `python3 examples/test_pybullet_rl.py data/checkpoints/...`
4. **Tune hyperparameters**: Adjust learning rate, batch size, etc.
5. **Deploy**: Integrate with your navigation stack

## References

- [PyBullet Quick Start](https://docs.google.com/document/d/10sXEhzFRSnvFcl3XxNGhnD4N2SedqwdAvK3dsihxVUA/)
- [Stable Baselines3 Docs](https://stable-baselines3.readthedocs.io/)
- [Gymnasium Docs](https://gymnasium.farama.org/)
- [ArduPilot SITL](https://ardupilot.org/dev/docs/sitl-simulator-software-in-the-loop.html)

## Support

For issues or questions:
1. Check `examples/README_PYBULLET.md` for detailed usage
2. Review error messages in TensorBoard logs
3. Test environment with `examples/test_environment.py`
4. Visualize with `examples/test_environment_gui.py`
