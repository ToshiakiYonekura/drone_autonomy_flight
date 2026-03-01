#!/bin/bash
# Quick Training Monitor

echo "======================================================================"
echo "           DRONE RL TRAINING - QUICK MONITOR"
echo "======================================================================"
echo ""

# Check if training is running
if ps aux | grep -q "[p]ython3.*continue_training"; then
    echo "Status: RUNNING"
    TRAIN_PID=$(ps aux | grep "[p]ython3.*continue_training" | awk '{print $2}' | head -1)
    echo "PID: $TRAIN_PID"
else
    echo "Status: NOT RUNNING"
fi

echo ""
echo "Latest Training Metrics:"
echo "----------------------------------------------------------------------"
tail -30 /tmp/claude/-home-yonetoshi27-autonomous-drone-sim/tasks/b176685.output | grep -E "total_timesteps|mean_reward|mean_ep_length" | tail -6

echo ""
echo "Checkpoints:"
ls -lh data/checkpoints/PPO_continued_20260110_180049/*.zip 2>/dev/null | tail -3

echo ""
echo "TensorBoard URLs:"
echo "  - http://localhost:6006 (Docker - all logs)"
echo "  - http://localhost:6007 (This training run)"
echo ""
echo "======================================================================"
