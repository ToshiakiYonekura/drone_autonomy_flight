#!/bin/bash
# Live Training Watch - Auto-refreshing monitor
# Press Ctrl+C to exit

clear
echo "Starting live training monitor..."
echo "Press Ctrl+C to exit"
sleep 2

while true; do
    clear
    echo "======================================================================"
    echo "           🚁 DRONE RL TRAINING - LIVE MONITOR"
    echo "======================================================================"
    echo ""
    echo "⏰ Last Updated: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    # Check if training is running
    if ps aux | grep -q "[p]ython3.*continue_training"; then
        echo "✅ Status: TRAINING IN PROGRESS"
        TRAIN_PID=$(ps aux | grep "[p]ython3.*continue_training" | awk '{print $2}' | head -1)
        echo "   PID: $TRAIN_PID"
        CPU=$(ps aux | grep "[p]ython3.*continue_training" | awk '{print $3}' | head -1)
        MEM=$(ps aux | grep "[p]ython3.*continue_training" | awk '{print $4}' | head -1)
        echo "   CPU: ${CPU}% | Memory: ${MEM}%"
    else
        echo "❌ Status: NOT RUNNING"
    fi

    echo ""
    echo "----------------------------------------------------------------------"
    echo "📊 LATEST METRICS"
    echo "----------------------------------------------------------------------"

    # Get latest from training output
    LATEST_OUTPUT=$(tail -100 /tmp/claude/-home-yonetoshi27-autonomous-drone-sim/tasks/b176685.output 2>/dev/null | grep -E "total_timesteps|mean_reward|mean_ep_length|fps|New best" | tail -10)

    if [ ! -z "$LATEST_OUTPUT" ]; then
        echo "$LATEST_OUTPUT"
    else
        echo "⏳ Waiting for metrics..."
    fi

    echo ""
    echo "----------------------------------------------------------------------"
    echo "💾 CHECKPOINTS"
    echo "----------------------------------------------------------------------"

    CHECKPOINT_COUNT=$(ls -1 data/checkpoints/PPO_continued_20260110_180049/rl_model_*.zip 2>/dev/null | wc -l)
    if [ $CHECKPOINT_COUNT -gt 0 ]; then
        echo "   Total saved: $CHECKPOINT_COUNT"
        LATEST_CP=$(ls -1t data/checkpoints/PPO_continued_20260110_180049/rl_model_*.zip 2>/dev/null | head -1)
        echo "   Latest: $(basename $LATEST_CP)"
    else
        echo "   No checkpoints yet"
    fi

    # Check best model timestamp
    if [ -f data/checkpoints/PPO_continued_20260110_180049/best/best_model.zip ]; then
        BEST_TIME=$(stat -c %y data/checkpoints/PPO_continued_20260110_180049/best/best_model.zip 2>/dev/null | cut -d'.' -f1)
        echo "   Best model: $BEST_TIME"
    fi

    echo ""
    echo "======================================================================"
    echo "  TensorBoard: http://localhost:6007"
    echo "  Auto-refreshing every 10 seconds... (Ctrl+C to exit)"
    echo "======================================================================"

    sleep 10
done
