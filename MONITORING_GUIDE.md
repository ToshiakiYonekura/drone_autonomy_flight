# 🚁 Training Monitoring Dashboard - Setup Complete

## ✅ Current Training Status

**Training is ACTIVE and running successfully!**

- **Started:** 2026-01-10 18:00:59
- **Checkpoint:** data/checkpoints/PPO_20251228_162953/best/best_model.zip (770k steps)
- **Target:** 1,770,000 timesteps (770k + 1M additional)
- **Parallel Environments:** 8
- **Learning Rate:** 0.0003
- **Progress:** Currently at 780,000 timesteps (10k steps completed)

**Latest Metrics:**
- Mean Episode Reward: -403
- Mean Episode Length: 263 steps
- Training is actively learning with policy gradient updates

---

## 📺 TensorBoard Access

### Option 1: Docker TensorBoard (Recommended - All Logs)
```
URL: http://localhost:6006
```
- Shows all training runs in data/logs/
- Already running in Docker container
- Includes current and previous training sessions

### Option 2: Dedicated TensorBoard (This Training Run Only)
```
URL: http://localhost:6007
```
- Shows only current training run (data/logs/20260110_180049)
- Started specifically for this session
- Cleaner view of current progress

**How to Access:**
1. Open your web browser
2. Navigate to one of the URLs above
3. View real-time training metrics, losses, and rewards

---

## 🖥️ Monitoring Scripts

### Quick Status Check
```bash
./scripts/training/quick_monitor.sh
```

**Output includes:**
- Training status (running/stopped)
- Process ID
- Latest metrics (timesteps, rewards, episode length)
- Checkpoint count
- TensorBoard URLs

### Detailed Dashboard
```bash
python scripts/training/monitor_training.py
```

**Features:**
- Real-time progress bar
- Episode rewards and lengths
- Learning metrics (loss, entropy, learning rate)
- Training FPS
- Checkpoint status
- Auto-refreshes every 5 seconds

**Options:**
```bash
# Custom refresh interval
python scripts/training/monitor_training.py --refresh 10

# Monitor specific log directory
python scripts/training/monitor_training.py --log-dir data/logs/YOUR_RUN
```

### Watch Raw Training Output
```bash
tail -f /tmp/claude/-home-yonetoshi27-autonomous-drone-sim/tasks/b176685.output
```

---

## 📊 What to Monitor

### Key Metrics to Watch:

1. **Episode Reward (rollout/ep_rew_mean)**
   - Currently: -403
   - Target: > 0 (positive rewards)
   - Higher is better
   - Shows if drone is learning to complete tasks

2. **Success Rate (eval/success_rate)**
   - Currently: Being evaluated
   - Target: > 95%
   - Percentage of successfully completed episodes

3. **Episode Length (rollout/ep_len_mean)**
   - Currently: 263 steps
   - Varies by task
   - Shorter can mean faster goal completion

4. **Value Loss (train/value_loss)**
   - Should decrease over time
   - Indicates how well the value function is learning

5. **Policy Loss (train/policy_gradient_loss)**
   - Should stabilize near 0
   - Indicates policy optimization

6. **Training FPS**
   - Expected: 150-250 FPS with 8 envs
   - Higher = faster training

---

## 💾 Checkpoints & Outputs

### Checkpoint Directory
```
data/checkpoints/PPO_continued_20260110_180049/
```

**Contents:**
- `rl_model_XXXXX_steps.zip` - Regular checkpoints (every 50k steps)
- `best/best_model.zip` - Best performing model (based on evaluation)
- `eval/` - Evaluation logs
- `config.yaml` - Training configuration

### Log Directory
```
data/logs/20260110_180049/
```

**Contents:**
- `events.out.tfevents.*` - TensorBoard events
- `progress.csv` - Training metrics in CSV format
- Evaluation logs

---

## 🎯 Expected Training Timeline

With 8 parallel environments at ~200 FPS:

| Milestone | Steps | Estimated Time | Status |
|-----------|-------|----------------|--------|
| Starting Point | 770,000 | - | ✅ Complete |
| First 50k checkpoint | 820,000 | ~20-30 min | ⏳ In Progress |
| Halfway | 1,270,000 | ~1.5 hours | ⏳ Pending |
| 75% Complete | 1,520,000 | ~2.5 hours | ⏳ Pending |
| **Target** | 1,770,000 | ~3-4 hours | ⏳ Pending |

---

## 🛑 Stopping Training

### Graceful Stop (Recommended)
```bash
# Get process ID
ps aux | grep "continue_training" | grep -v grep

# Send interrupt signal (saves model)
kill -SIGINT <PID>
```

The model will save an `interrupted_model` checkpoint before stopping.

### Force Stop (Not Recommended)
```bash
kill -9 <PID>  # May lose current progress
```

---

## 📈 Analyzing Results

### After Training Completes

1. **Check Best Model:**
   ```bash
   ls -lh data/checkpoints/PPO_continued_20260110_180049/best/
   ```

2. **View Progress CSV:**
   ```bash
   cat data/logs/20260110_180049/progress.csv | column -t -s,
   ```

3. **Test Trained Model:**
   ```bash
   python examples/test_model.py \
       --model data/checkpoints/PPO_continued_20260110_180049/best/best_model.zip \
       --episodes 100
   ```

---

## 🐛 Troubleshooting

### Training Stopped Unexpectedly
```bash
# Check if still running
ps aux | grep "continue_training"

# Check last output
tail -100 /tmp/claude/-home-yonetoshi27-autonomous-drone-sim/tasks/b176685.output

# Check for errors
grep -i "error\|exception" /tmp/claude/-home-yonetoshi27-autonomous-drone-sim/tasks/b176685.output
```

### TensorBoard Not Loading
```bash
# Check if TensorBoard is running
netstat -tulpn | grep 6007

# Restart TensorBoard
pkill tensorboard
tensorboard --logdir=data/logs/20260110_180049 --port=6007 --host=0.0.0.0 &
```

### Low FPS / Slow Training
- Check CPU usage: `htop`
- Reduce number of parallel environments
- Close unnecessary applications

---

## 📝 Notes

- Training will automatically save checkpoints every 50k steps
- Best model is saved based on evaluation performance (every 10k steps)
- All monitoring tools show live data with minimal delay
- TensorBoard graphs may take a few minutes to appear initially

---

## 🎉 Quick Start

**To view your training right now:**

1. Open browser: http://localhost:6006 or http://localhost:6007
2. Run: `./scripts/training/quick_monitor.sh`
3. Watch live output: `tail -f /tmp/claude/-home-yonetoshi27-autonomous-drone-sim/tasks/b176685.output`

**Training will complete automatically in ~3-4 hours!** 🚀
