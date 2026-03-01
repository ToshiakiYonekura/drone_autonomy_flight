# RL Training Status - February 15, 2026

## Current Status: ⚠️ BLOCKED by numpy/stable-baselines3 compatibility issue

### Progress Made

✅ **Docker environment verified**
- Container: `drone_sim` running
- All packages installed: PyBullet, Stable-Baselines3 2.7.1, Gymnasium 1.2.3, PyTorch 2.9.1+cu128
- TensorBoard, Jupyter, Grafana all running

✅ **Environment selection**
- Identified `PyBulletDrone-v0` as the correct environment (pure PyBullet, no AirSim dependency)
- Environment tested successfully in isolation

✅ **Code fixes applied**
1. Updated `train_ppo.py`: Changed `import gym` → `import gymnasium as gym`
2. Updated `train_ppo.py`: Changed `env.seed()` → `env.reset(seed=...)`
3. Updated `train_ppo.py`: Added `PyBulletDrone-v0` to allowed environments
4. Updated `pybullet_drone_env.py`: Added explicit `dtype=np.float32` to action space arrays

### Current Blocker

**Error**: `TypeError: no implementation found for 'numpy.clip' on types that implement __array_function__`

**Location**: `stable_baselines3/common/on_policy_algorithm.py:216`
```python
clipped_actions = np.clip(actions, self.action_space.low, self.action_space.high)
```

**Root Cause**: Incompatibility between:
- NumPy 1.26.4
- Stable-Baselines3 2.7.1
- Gymnasium 1.2.3

The action_space.low and action_space.high arrays are getting wrapped in a way that numpy.clip cannot handle.

### Attempted Fixes

1. ✅ Added explicit dtype=np.float32 to action space (no effect)
2. ✅ Tried DummyVecEnv instead of SubprocVecEnv (no effect)
3. ⏳ Tried downgrading SB3 to 2.2.1 (installation hung)

### Next Steps to Resolve

**Option 1: Patch stable-baselines3 locally**
```python
# In stable_baselines3/common/on_policy_algorithm.py:216
# Replace:
clipped_actions = np.clip(actions, self.action_space.low, self.action_space.high)
# With:
clipped_actions = np.clip(actions,
                         np.asarray(self.action_space.low),
                         np.asarray(self.action_space.high))
```

**Option 2: Use older package versions**
- Stable-Baselines3==2.0.0
- Gymnasium==0.29.1

**Option 3: Use different RL library**
- CleanRL (minimal implementation)
- RLlib (Ray)

### Training Configuration Ready

Once the blocker is resolved, training is configured for:
- Environment: `PyBulletDrone-v0`
- Total timesteps: 1,000,000
- Parallel environments: 4
- Algorithm: PPO
- Expected training time: 20-24 hours
- Checkpoints save to: `/workspace/data/checkpoints/`
- TensorBoard logs to: `/workspace/data/logs/`

### Files Modified

- `scripts/training/train_ppo.py` - Updated for gymnasium, added PyBulletDrone-v0
- `drone_gym/envs/pybullet_drone_env.py` - Added explicit float32 dtypes

### Quick Test Command

```bash
# Inside drone_sim container
cd /workspace
python3 scripts/training/train_ppo.py --timesteps 10000 --n-envs 1
```

---

**Date**: 2026-02-15
**Next Action**: Fix numpy/SB3 compatibility OR proceed with SITL fixing in parallel
