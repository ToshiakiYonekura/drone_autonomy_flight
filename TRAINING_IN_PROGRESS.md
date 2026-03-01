# 🚀 Training In Progress

**Started**: 2025-12-29 16:11 JST
**Status**: ✅ RUNNING
**Expected Duration**: 1-2 hours
**Expected Completion**: ~17:11-18:11 JST

---

## 📊 Current Training Configuration

```
Algorithm: PPO (Proximal Policy Optimization)
Total Timesteps: 1,000,000
Parallel Environments: 8
Learning Rate: 0.0003
Batch Size: 64
Gamma: 0.99
Seed: 42

Training Session: PPO_20251228_161158
```

---

## 🎯 What's Happening Now

Your Crazyflie drone is learning autonomous navigation through:

1. **Exploration** (first ~200k steps)
   - Randomly trying different actions
   - Learning from successes and failures
   - Success rate: ~10-30%

2. **Learning** (200k-600k steps)
   - Discovering effective strategies
   - Improving navigation skills
   - Success rate: ~50-80%

3. **Refinement** (600k-1M steps)
   - Optimizing policy
   - Fine-tuning behavior
   - Success rate: ~90-95%+

---

## 📈 How to Monitor Training

### Option 1: TensorBoard (Best Visualization)

**Start TensorBoard:**
```bash
docker exec -it drone_sim tensorboard --logdir=/workspace/data/logs --host=0.0.0.0 --port=6006
```

**Then open in browser:** http://localhost:6006

**Key Metrics to Watch:**
- `rollout/ep_rew_mean` → Should increase over time
- `rollout/ep_len_mean` → Should stabilize around 200-400
- `train/policy_loss` → Should decrease
- `train/value_loss` → Should decrease
- `train/explained_variance` → Should increase toward 1.0

### Option 2: Quick Status Check

**Run the monitor script:**
```bash
./monitor_training.sh
```

**Or check process status:**
```bash
docker exec drone_sim ps aux | grep train_pybullet
```

### Option 3: View Checkpoints

**List saved models:**
```bash
docker exec drone_sim ls -lh /workspace/data/checkpoints/PPO_20251228_161158/
```

**Checkpoints are saved:**
- Every 50,000 steps
- When best performance is achieved
- At training completion

---

## ⏱️ Expected Timeline

| Time | Progress | What's Happening |
|------|----------|------------------|
| **0:00** | Started | Initializing 8 parallel environments |
| **0:05** | ~50k steps | Random exploration, learning basics |
| **0:15** | ~150k steps | Starting to navigate toward goals |
| **0:30** | ~300k steps | Success rate improving to ~50% |
| **0:45** | ~450k steps | Consistent navigation, avoiding obstacles |
| **1:00** | ~600k steps | Success rate >80% |
| **1:15** | ~750k steps | Refining policy, >90% success |
| **1:30** | ~900k steps | Near-optimal performance |
| **1:45** | 1M steps | **Training complete!** |

*Times are approximate and depend on CPU performance*

---

## 📊 Current Status (Live)

**Check real-time status:**
```bash
# Quick check
./monitor_training.sh

# Detailed view
docker logs drone_sim | tail -100
```

**System Resources:**
- CPU Usage: ~200% (expected with 8 workers)
- Memory: ~6-7 GB
- Disk: Logs growing to ~100-500 MB

---

## ✅ Signs Training is Working

You should see:
- ✓ Process using high CPU (~150-250%)
- ✓ Log files growing in `data/logs/PPO_*/`
- ✓ Checkpoints appearing in `data/checkpoints/PPO_*/`
- ✓ Episode rewards increasing in TensorBoard
- ✓ No crash or error messages

---

## ⚠️ What to Do If Training Stops

### Check if it crashed:
```bash
docker exec drone_sim ps aux | grep train_pybullet
```

If no process found:
```bash
# Check logs for errors
docker logs drone_sim | tail -200

# Restart if needed
docker exec drone_sim python3 /workspace/examples/train_pybullet_rl.py \
    --algorithm PPO \
    --total-timesteps 1000000 \
    --n-envs 8 \
    --learning-rate 3e-4 \
    --batch-size 64
```

---

## 🎯 After Training Completes

### 1. Find Your Trained Model

```bash
docker exec drone_sim ls -lh /workspace/data/checkpoints/PPO_20251228_161158/best/
```

The best model will be: `best_model.zip`

### 2. Evaluate Performance

```bash
docker exec drone_sim python3 /workspace/examples/test_pybullet_rl.py \
    /workspace/data/checkpoints/PPO_20251228_161158/best/best_model.zip \
    --algorithm PPO \
    --n-episodes 100 \
    --gui
```

### 3. Expected Results

After full training, you should achieve:
- **Success rate**: >95% (95+ out of 100 episodes)
- **Average reward**: 40-50+
- **Goal accuracy**: <0.5m average distance
- **Collision rate**: <5%

---

## 📁 Files Being Generated

```
data/
├── logs/
│   └── PPO_20251228_161158/
│       └── PPO_1/
│           ├── events.out.tfevents.*  # TensorBoard logs
│           └── progress.csv           # Training metrics
└── checkpoints/
    └── PPO_20251228_161158/
        ├── best/
        │   └── best_model.zip         # Best performing model
        ├── ppo_model_50000_steps.zip  # Checkpoint at 50k
        ├── ppo_model_100000_steps.zip # Checkpoint at 100k
        └── ... (more checkpoints)
```

---

## 💡 Tips While Training

### Do:
- ✅ Monitor TensorBoard occasionally
- ✅ Check disk space if training multiple models
- ✅ Let it run uninterrupted for best results
- ✅ Keep the docker container running

### Don't:
- ❌ Stop training prematurely (wait for 1M steps)
- ❌ Restart docker container during training
- ❌ Delete checkpoint files while training
- ❌ Run multiple trainings simultaneously (memory)

---

## 🔧 Useful Commands

```bash
# Monitor training
./monitor_training.sh

# View TensorBoard
docker exec -it drone_sim tensorboard --logdir=/workspace/data/logs --host=0.0.0.0 --port=6006

# Check progress CSV
docker exec drone_sim tail -20 /workspace/data/logs/PPO_20251228_161158/PPO_1/progress.csv

# Watch checkpoints being created
watch -n 60 'docker exec drone_sim ls -lh /workspace/data/checkpoints/PPO_20251228_161158/'

# Check training is still running
docker exec drone_sim ps aux | grep train_pybullet

# View recent logs
docker logs drone_sim --tail 100 --follow
```

---

## 📊 Understanding the Metrics

### Episode Reward Mean (`ep_rew_mean`)
- **Meaning**: Average reward per episode
- **Target**: Increase from negative to positive
- **Good**: >40 after 1M steps

### Episode Length Mean (`ep_len_mean`)
- **Meaning**: Average steps to complete episode
- **Target**: Stabilize around 200-400
- **Good**: Consistent, not growing

### Policy Loss
- **Meaning**: How much policy is changing
- **Target**: Decrease over time
- **Good**: Small, stable values

### Value Loss
- **Meaning**: Prediction error of value function
- **Target**: Decrease over time
- **Good**: <0.5 after training

### Explained Variance
- **Meaning**: How well value function predicts returns
- **Target**: Increase toward 1.0
- **Good**: >0.7 after training

---

## 🎊 Training Complete Checklist

When training finishes, verify:

- [ ] Training reached 1,000,000 timesteps
- [ ] Best model saved in `checkpoints/*/best/`
- [ ] Final reward >40 in TensorBoard
- [ ] Multiple checkpoints created
- [ ] No error messages in logs
- [ ] Ready to evaluate!

---

**Current Status**: ✅ Training is running smoothly!
**Next Step**: Wait for completion, then evaluate the trained model.
**Estimated Time Remaining**: Check with `./monitor_training.sh`

---

**Last Updated**: 2025-12-29 16:14 JST
**Session**: PPO_20251228_161158
