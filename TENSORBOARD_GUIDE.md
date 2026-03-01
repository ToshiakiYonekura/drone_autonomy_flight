# TensorBoard Monitoring Guide

## 🎯 Quick Start

**TensorBoard URL**: http://localhost:6006

Open this in your browser right now to see live training graphs!

---

## 📊 What You'll See

### Main Interface

When you open TensorBoard, you'll see:

1. **Left Sidebar**: Lists all training runs
   - You should see: `PPO_20251228_161158`
   - This is your current training session

2. **Top Navigation Tabs**:
   - **SCALARS** ← Start here! (most important)
   - IMAGES (not used in this project)
   - GRAPHS (neural network architecture)
   - DISTRIBUTIONS (weight distributions)
   - HISTOGRAMS (detailed statistics)

3. **Main Display Area**: Shows the graphs

---

## 📈 Key Metrics Explained

### 1. rollout/ep_rew_mean (Episode Reward Mean)

**What it shows**: Average reward per episode

**What to look for**:
- Should start negative (around -50 to -100)
- Should gradually increase over time
- Target: >40 after 1M steps
- When it reaches 45+, you have >95% success rate

**Graph interpretation**:
```
 50 |                                    /--
    |                              /----/
  0 |                      /------/
    |              /------/
-50 |      /------/
    | ----/
-100|----
    +----------------------------------------
       0k    200k   400k   600k   800k   1M
```

### 2. rollout/ep_len_mean (Episode Length Mean)

**What it shows**: Average number of steps per episode

**What to look for**:
- May vary a lot initially (50-300 steps)
- Should stabilize around 200-400 steps
- Lower is sometimes better (reached goal faster)
- Very low (<50) might mean collisions

### 3. train/policy_loss (Policy Gradient Loss)

**What it shows**: How much the policy is changing

**What to look for**:
- Often negative values
- Should decrease in magnitude over time
- Large fluctuations are normal early on
- Should become more stable later

### 4. train/value_loss (Value Function Loss)

**What it shows**: Error in predicting future rewards

**What to look for**:
- Should start high (0.5-2.0)
- Should decrease over time
- Target: <0.5 after training
- Lower = better predictions

### 5. train/explained_variance

**What it shows**: How well the value function predicts returns (0-1 scale)

**What to look for**:
- Should start low (0-0.3)
- Should increase toward 1.0
- Target: >0.7 after training
- Higher = better understanding

### 6. train/learning_rate

**What it shows**: Current learning rate

**What to look for**:
- Should be constant at 0.0003
- If it changes, indicates learning rate scheduling

### 7. time/fps (Frames Per Second)

**What it shows**: Training speed

**What to look for**:
- Should be 200-300 FPS (with 8 envs)
- Higher is better (faster training)
- May vary based on CPU load

---

## 🎨 TensorBoard Tips

### Adjust Smoothing

The "Smoothing" slider at the top (default 0.6):
- **Lower (0.0-0.3)**: See all raw data (noisy)
- **Medium (0.4-0.6)**: Good balance (recommended)
- **Higher (0.7-0.9)**: Very smooth (may hide details)

### Zoom Into Graphs

- Click and drag on a graph to zoom
- Double-click to reset zoom
- Use mouse wheel to zoom in/out

### Compare Multiple Runs

If you train multiple models:
- All will appear in the left sidebar
- Toggle checkboxes to show/hide runs
- Different colors for each run

### Refresh Data

- TensorBoard auto-refreshes every 30 seconds
- Manual refresh: Click the reload button (top-right)
- Or refresh your browser page

---

## 🎯 Training Progress Milestones

### Phase 1: Exploration (0-200k steps, 0-20%)

**Expected metrics**:
- ep_rew_mean: -100 to -30
- ep_len_mean: 80-150
- Behavior: Random, chaotic

**TensorBoard shows**:
- Noisy, fluctuating graphs
- Slow improvement
- High variance

### Phase 2: Learning (200k-600k steps, 20-60%)

**Expected metrics**:
- ep_rew_mean: -30 to +20
- ep_len_mean: 150-300
- Behavior: Starting to navigate

**TensorBoard shows**:
- Upward trend in rewards
- Value loss decreasing
- Explained variance increasing

### Phase 3: Optimization (600k-1M steps, 60-100%)

**Expected metrics**:
- ep_rew_mean: +20 to +50
- ep_len_mean: 200-400 (stable)
- Behavior: Consistent navigation

**TensorBoard shows**:
- Stable, high rewards
- Low losses
- High explained variance (>0.7)

---

## ✅ Success Indicators

### Good Training (Everything Working)

Look for these signs:
- ✓ ep_rew_mean is increasing
- ✓ value_loss is decreasing
- ✓ explained_variance is increasing
- ✓ Graphs show clear upward/downward trends
- ✓ No sudden crashes or flat lines

### Potential Issues

Watch out for:
- ⚠ ep_rew_mean stuck at very negative values
- ⚠ value_loss not decreasing
- ⚠ explained_variance stays near 0
- ⚠ Graphs completely flat
- ⚠ Sudden drop to zero (training crashed)

If you see issues, check:
```bash
docker exec drone_sim ps aux | grep train_pybullet
```

---

## 🔄 Refresh Guide

### If Graphs Don't Appear

1. Wait 30 seconds (data needs time to write)
2. Refresh your browser page
3. Check left sidebar - is run listed?
4. Try clicking on the run name in sidebar

### If Data Stops Updating

1. Check training is still running:
   ```bash
   ./monitor_training.sh
   ```

2. Verify TensorBoard is running:
   ```bash
   docker ps | grep tensorboard
   ```

3. Restart TensorBoard if needed:
   ```bash
   docker compose restart tensorboard
   ```

---

## 📱 Alternative Views

### If Browser Not Available

Text-based monitoring:
```bash
# Quick status
./monitor_training.sh

# Watch checkpoints
watch -n 30 'docker exec drone_sim ls -lh /workspace/data/checkpoints/PPO_20251228_161158/'

# Live resource usage
docker stats drone_sim
```

---

## 🎓 Understanding the Numbers

### Current Status (50k steps, ~5%)

- **Reward**: Likely -50 to -80 (negative = learning)
- **Length**: ~100-150 steps
- **Success rate**: ~10-20% (early training)

### Expected at 500k steps (~50%)

- **Reward**: -10 to +10 (improving)
- **Length**: ~200-250 steps
- **Success rate**: ~60-70%

### Expected at 1M steps (100%)

- **Reward**: +40 to +50 (excellent)
- **Length**: ~250-350 steps (stable)
- **Success rate**: >95%

---

## 🚀 Quick Actions

```bash
# Open TensorBoard
# Already running at: http://localhost:6006

# Check if TensorBoard is running
docker ps | grep tensorboard

# Restart TensorBoard
docker compose restart tensorboard

# Stop TensorBoard
docker compose stop tensorboard

# View TensorBoard logs
docker logs tensorboard

# Check training status
./monitor_training.sh
```

---

## 💡 Pro Tips

1. **Keep TensorBoard open** - It updates automatically
2. **Check every 30 minutes** - To see progress
3. **Don't panic if noisy** - Early training is random
4. **Focus on trends** - Not individual points
5. **Use smoothing** - Makes patterns clearer
6. **Save screenshots** - Document your progress

---

## 📸 What Good Training Looks Like

### Reward Graph (Should Look Like This)

```
  50 |                               ___/---
     |                          ____/
  25 |                    _____/
     |              _____/
   0 |        _____/
     |   ____/
 -25 | _/
     |/
 -50 +----------------------------------------
      0k    200k   400k   600k   800k   1M
```

### Value Loss (Should Look Like This)

```
 2.0 |\
     | \___
 1.5 |     \___
     |         \___
 1.0 |             \___
     |                 \___
 0.5 |                     \___________
     |
 0.0 +----------------------------------------
      0k    200k   400k   600k   800k   1M
```

---

**Current Training Session**: PPO_20251228_161158
**TensorBoard**: http://localhost:6006
**Status**: ✅ Active and recording
**Last Updated**: 2025-12-29 16:21 JST
