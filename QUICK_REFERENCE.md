# Quick Reference Card

## 🚀 Training Status

**Session**: PPO_20251228_161158
**Started**: 16:11 JST
**Duration**: 1-2 hours
**Status**: Check with `./monitor_training.sh`

---

## 📊 Monitor Commands (Copy & Paste)

```bash
# Quick status check
./monitor_training.sh

# TensorBoard (best visualization)
docker exec -it drone_sim tensorboard --logdir=/workspace/data/logs --host=0.0.0.0 --port=6006
# Then open: http://localhost:6006

# Live logs
docker logs drone_sim --tail 50 --follow

# Check if running
docker exec drone_sim ps aux | grep train_pybullet

# View checkpoints
docker exec drone_sim ls -lh /workspace/data/checkpoints/PPO_20251228_161158/
```

---

## 🎯 After Training Completes

```bash
# 1. Find best model
docker exec drone_sim ls /workspace/data/checkpoints/PPO_20251228_161158/best/

# 2. Evaluate (100 episodes)
docker exec drone_sim python3 /workspace/examples/test_pybullet_rl.py \
    /workspace/data/checkpoints/PPO_20251228_161158/best/best_model.zip \
    --algorithm PPO \
    --n-episodes 100 \
    --gui

# 3. Expected results
# Success rate: >95%
# Average reward: 40-50+
# Goal accuracy: <0.5m
```

---

## 📁 Important Files

```
Training logs:
  data/logs/PPO_20251228_161158/

Model checkpoints:
  data/checkpoints/PPO_20251228_161158/best/best_model.zip

Documentation:
  TRAINING_IN_PROGRESS.md  (full details)
  COMPLETE_DEMONSTRATION.md (system overview)
  BUILD_COMPLETE.md (setup summary)
```

---

## ⏱️ Timeline

| Time | Steps | What's Happening |
|------|-------|------------------|
| Now | 0k | Starting |
| +15min | 150k | Learning basics |
| +30min | 300k | 50% success |
| +1hr | 600k | 80% success |
| +1.5hr | 900k | 90% success |
| +2hr | 1M | **DONE!** 95%+ |

---

## 🎓 What To Watch in TensorBoard

| Metric | Should... | Good Value |
|--------|-----------|------------|
| `ep_rew_mean` | Increase | >40 |
| `ep_len_mean` | Stabilize | 200-400 |
| `policy_loss` | Decrease | Small |
| `value_loss` | Decrease | <0.5 |
| `explained_variance` | Increase | >0.7 |

---

## ✅ Success Indicators

Training is working if you see:
- ✓ CPU usage ~150-250%
- ✓ Memory ~6-7 GB
- ✓ Checkpoints being created
- ✓ Reward increasing in TensorBoard
- ✓ No error messages

---

## 📞 Quick Help

**Training stuck?**
```bash
docker exec drone_sim ps aux | grep python
```

**Restart training?**
```bash
docker exec drone_sim python3 /workspace/examples/train_pybullet_rl.py \
    --algorithm PPO --total-timesteps 1000000 --n-envs 8
```

**Check disk space?**
```bash
df -h
du -sh data/*
```

---

**Current Time**: 16:15 JST
**Completion**: ~17:15-18:15 JST
**Status**: ✅ Running normally
