=================================================================
NEXT WEEK PLAN - RL Training Strategy (7 Days from Now)
=================================================================

Date Created: 2026-02-15
Return Date: 2026-02-22 (1 week later)

=================================================================
FINAL STATUS - 5M Training (STOPPED)
=================================================================

Training Duration: 10.5 hours
Progress: 819,200 / 5,000,000 timesteps (16.4%)
Final Reward: 22.28
Episode Length: 199 steps

Checkpoints Saved:
  ✅ 200k steps (1.5 MB)
  ✅ 400k steps (1.5 MB)
  ✅ 600k steps (1.5 MB)
  ✅ 800k steps (1.5 MB)

Performance Trajectory:
  - 600k steps: -113.8 reward (bad phase)
  - 760k steps: -136.2 reward (worst point)
  - 800k steps: +98.5 reward (sudden recovery!)
  - 819k steps: +22.3 reward (stable)

Assessment: Training was improving but very unstable

=================================================================
WHAT YOU HAVE NOW
=================================================================

Option A: 1M Working Model (PROVEN) ⭐ RECOMMENDED
  Location: ppo_PyBulletDrone-v0_20260214_174923/best_model/
  Timesteps: 1,000,000
  Performance:
    - Reward: 39.4
    - Success Rate: ~25%
    - Consistency: Moderate
  Status: READY TO USE
  Grade: C+ (Proven, reliable baseline)

Option B: 800k Checkpoint (UNPROVEN)
  Location: ppo_PyBulletDrone-v0_20260214_191830/ppo_model_800000_steps.zip
  Timesteps: 800,000
  Performance:
    - Reward: 98.5 (best in this run!)
    - Success Rate: Unknown
    - Consistency: Unknown (might be lucky spike)
  Status: NEEDS EVALUATION
  Grade: Unknown (could be A or F)

=================================================================
NEXT WEEK STRATEGY - RECOMMENDED APPROACH
=================================================================

PHASE 1: Evaluate What You Have (30 minutes)
─────────────────────────────────────────────

Step 1.1: Test 1M Model (Baseline)
```bash
docker exec -it drone_sim python3 << 'EOF'
from stable_baselines3 import PPO
from stable_baselines3.common.evaluation import evaluate_policy
import gymnasium as gym
import drone_gym

# Load 1M model
model = PPO.load("data/checkpoints/ppo_PyBulletDrone-v0_20260214_174923/best_model/best_model")
env = gym.make("PyBulletDrone-v0")

# Evaluate over 50 episodes
mean_reward, std_reward = evaluate_policy(model, env, n_eval_episodes=50)
print(f"1M Model - Mean reward: {mean_reward:.2f} +/- {std_reward:.2f}")
env.close()
EOF
```

Expected Result: Reward ~40, Success ~25%

Step 1.2: Test 800k Checkpoint (Potential Winner)
```bash
docker exec -it drone_sim python3 << 'EOF'
from stable_baselines3 import PPO
from stable_baselines3.common.evaluation import evaluate_policy
import gymnasium as gym
import drone_gym

# Load 800k checkpoint
model = PPO.load("data/checkpoints/ppo_PyBulletDrone-v0_20260214_191830/ppo_model_800000_steps")
env = gym.make("PyBulletDrone-v0")

# Evaluate over 50 episodes
mean_reward, std_reward = evaluate_policy(model, env, n_eval_episodes=50)
print(f"800k Model - Mean reward: {mean_reward:.2f} +/- {std_reward:.2f}")
env.close()
EOF
```

Expected Result: Could be 50-80 reward (good) or -50 (bad)

Step 1.3: Compare Results
- If 800k > 1M: Use 800k as starting point ✅
- If 1M > 800k: Use 1M as starting point ✅


PHASE 2: Continue Training (3-5 hours)
──────────────────────────────────────

Strategy A: Continue from 1M Model (SAFEST) ⭐ RECOMMENDED
```bash
docker exec -d drone_sim bash -c "cd /workspace && python3 << 'EOF'
from stable_baselines3 import PPO
import gymnasium as gym
import drone_gym

# Load proven 1M model
model = PPO.load('data/checkpoints/ppo_PyBulletDrone-v0_20260214_174923/best_model/best_model')

# Train 4M more steps (total 5M)
model.learn(
    total_timesteps=4000000,
    log_interval=1,
    tb_log_name='continued_from_1M',
    progress_bar=True
)

# Save final model
model.save('data/checkpoints/final_5M_from_1M')
print('Training complete! Final model saved.')
EOF
" > /workspace/data/training_final_output.log 2>&1
```

Expected:
  - Duration: ~4 hours
  - Final Reward: 60-80
  - Success Rate: 60-80%
  - Risk: Low (proven starting point)

Strategy B: Continue from 800k Checkpoint (IF IT'S GOOD)
```bash
# Only use if 800k evaluation shows reward > 50
docker exec -d drone_sim bash -c "cd /workspace && python3 << 'EOF'
from stable_baselines3 import PPO
import gymnasium as gym
import drone_gym

# Load 800k checkpoint
model = PPO.load('data/checkpoints/ppo_PyBulletDrone-v0_20260214_191830/ppo_model_800000_steps')

# Train 4.2M more steps (total 5M)
model.learn(
    total_timesteps=4200000,
    log_interval=1,
    tb_log_name='continued_from_800k',
    progress_bar=True
)

# Save final model
model.save('data/checkpoints/final_5M_from_800k')
print('Training complete! Final model saved.')
EOF
" > /workspace/data/training_final_output.log 2>&1
```

Expected:
  - Duration: ~4 hours
  - Final Reward: 70-90 (potentially better)
  - Success Rate: 70-85%
  - Risk: Medium (unproven starting point)

Strategy C: Fresh Start with Better Parameters (LAST RESORT)
```bash
# Only if both 1M and 800k don't meet expectations
docker exec -d drone_sim python3 scripts/training/train_ppo.py \
  --env PyBulletDrone-v0 \
  --timesteps 5000000 \
  --n-envs 8 \
  --learning-rate 0.0001 \
  --save-freq 100000 \
  --save-dir /workspace/data/checkpoints \
  --log-dir /workspace/data/logs \
  > /workspace/data/training_fresh_output.log 2>&1 &
```

Expected:
  - Duration: ~5 hours
  - Final Reward: Unknown
  - Risk: High (starting from scratch)


PHASE 3: Evaluate Final Model (30 minutes)
──────────────────────────────────────────

Step 3.1: Quantitative Evaluation
```bash
docker exec -it drone_sim python3 << 'EOF'
from stable_baselines3 import PPO
from stable_baselines3.common.evaluation import evaluate_policy
import gymnasium as gym
import drone_gym

# Load final model
model = PPO.load("data/checkpoints/final_5M_from_1M")  # or final_5M_from_800k
env = gym.make("PyBulletDrone-v0")

# Comprehensive evaluation
mean_reward, std_reward = evaluate_policy(model, env, n_eval_episodes=100)
print(f"Mean reward: {mean_reward:.2f} +/- {std_reward:.2f}")

# Success rate calculation
success_count = 0
for _ in range(100):
    obs, _ = env.reset()
    done = False
    while not done:
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, _ = env.step(action)
        done = terminated or truncated
    if reward > 50:  # Goal reached
        success_count += 1

print(f"Success rate: {success_count}%")
env.close()
EOF
```

Step 3.2: Visual Testing
```bash
docker exec -it drone_sim python3 << 'EOF'
from stable_baselines3 import PPO
import gymnasium as gym
import drone_gym

model = PPO.load("data/checkpoints/final_5M_from_1M")
env = gym.make("PyBulletDrone-v0", render_mode="human", gui=True)

obs, _ = env.reset()
for _ in range(3000):  # ~10 episodes
    action, _ = model.predict(obs, deterministic=True)
    obs, reward, done, truncated, _ = env.step(action)
    if done or truncated:
        print(f"Episode reward: {reward}")
        obs, _ = env.reset()
env.close()
EOF
```

Step 3.3: Grade Final Model
  - Reward > 70, Success > 60%: Grade A (Deploy ready) ✅
  - Reward 50-70, Success 40-60%: Grade B (Good progress) 📈
  - Reward 30-50, Success 20-40%: Grade C (Needs more training) ⚠️
  - Reward < 30, Success < 20%: Grade D (Major issues) ❌


PHASE 4: Hardware Deployment Planning (1 hour)
──────────────────────────────────────────────

If Model Grade = A or B:

Step 4.1: Prepare Hardware Test Environment
  - Flash Mode 99 to real drone (~/ardupilot/build/sitl/bin/arducopter)
  - Set up Raspberry Pi companion computer
  - Configure MAVLink communication
  - Test failsafes in controlled environment

Step 4.2: Create Safety Protocol
  - Start with small movements (±1m position commands)
  - Test emergency LAND mode transition
  - Monitor battery, GPS, EKF closely
  - Have manual RC override ready

Step 4.3: First Flight Test Plan
  1. Arm and takeoff in STABILIZE mode
  2. Switch to Mode 99 at 2m altitude
  3. Send simple position commands via Raspberry Pi
  4. Monitor for 30 seconds
  5. Land in Mode 99
  6. Analyze logs

=================================================================
DECISION TREE FOR NEXT WEEK
=================================================================

START
  │
  ├─> Evaluate 1M model (baseline)
  │   └─> Result: ~40 reward, 25% success ✅
  │
  ├─> Evaluate 800k checkpoint
  │   ├─> If reward > 50: Use 800k ⭐
  │   └─> If reward < 40: Use 1M ⭐
  │
  ├─> Continue training (4M more steps)
  │   ├─> Monitor TensorBoard: http://localhost:6006
  │   └─> Wait ~4 hours
  │
  ├─> Evaluate final model (100 episodes)
  │   ├─> Grade A (>70 reward): Deploy to hardware ✅
  │   ├─> Grade B (50-70): More training or deploy ⚠️
  │   └─> Grade C/D (<50): Debug or restart ❌
  │
  └─> If Grade A/B: Plan hardware testing
      If Grade C/D: Investigate hyperparameters

=================================================================
SUCCESS CRITERIA FOR NEXT WEEK
=================================================================

Minimum Success (Must Achieve):
  ✅ Final model with reward > 50
  ✅ Success rate > 40%
  ✅ Consistent performance (std < 50)

Target Success (Ideal Goal):
  ⭐ Final model with reward > 70
  ⭐ Success rate > 60%
  ⭐ Ready for hardware deployment

Stretch Goal (Exceptional):
  🚀 Reward > 80
  🚀 Success rate > 75%
  🚀 Smooth trajectories, efficient paths

=================================================================
RISK MITIGATION
=================================================================

Risk 1: Training Diverges Again
  Mitigation: Use proven 1M model as starting point
  Fallback: Stop early if reward decreases consistently

Risk 2: 800k Checkpoint is Lucky Spike
  Mitigation: Evaluate over 50+ episodes before using
  Fallback: Use 1M model instead

Risk 3: Final Model Underperforms
  Mitigation: Save checkpoints every 500k steps
  Fallback: Use best checkpoint, not final

Risk 4: Hardware Deployment Issues
  Mitigation: Extensive SITL testing first (if possible)
  Fallback: Mode 99 provides LQR safety backup

=================================================================
QUICK COMMANDS FOR NEXT WEEK
=================================================================

# Monitor training
docker exec -it drone_sim tail -f /workspace/data/training_final_output.log

# TensorBoard
http://localhost:6006

# Check progress
docker exec drone_sim ps aux | grep python3

# Evaluate model quickly (10 episodes)
docker exec -it drone_sim python3 -c "
from stable_baselines3 import PPO
from stable_baselines3.common.evaluation import evaluate_policy
import gymnasium as gym
import drone_gym
model = PPO.load('data/checkpoints/final_5M_from_1M')
env = gym.make('PyBulletDrone-v0')
r, s = evaluate_policy(model, env, n_eval_episodes=10)
print(f'Reward: {r:.1f} +/- {s:.1f}')
env.close()
"

=================================================================
FILES TO READ NEXT WEEK
=================================================================

Priority 1 (Must Read):
  1. NEXT_WEEK_PLAN.md (this file)
  2. START_HERE_MONDAY.txt (quick overview)

Reference (If Needed):
  3. WEEKEND_STATUS_REPORT.md (detailed history)
  4. RL_TRAINING_GUIDE.md (technical details)
  5. TRAINING_5M_STATUS.md (monitoring guide)

=================================================================
TIMELINE ESTIMATE (NEXT WEEK)
=================================================================

Day 1 (Monday):
  - Hour 1: Evaluate 1M and 800k models
  - Hour 2: Start continued training (4M steps)
  - Hour 3-6: Training runs (monitor periodically)

Day 2 (Tuesday):
  - Hour 1: Training completes, evaluate final model
  - Hour 2: Visual testing and validation
  - Hour 3: Decide on deployment readiness

Day 3-5 (Wed-Fri):
  - If Grade A/B: Hardware deployment preparation
  - If Grade C/D: Investigate and restart training

=================================================================
EXPECTED OUTCOME
=================================================================

Most Likely Scenario:
  ✅ Continue from 1M model
  ✅ Train 4M more steps (~4 hours)
  ✅ Achieve reward 60-75, success 50-70%
  ✅ Grade: B+ (Good, ready for cautious deployment)
  ✅ Next step: Hardware testing with Mode 99

Best Case Scenario:
  ⭐ 800k checkpoint is excellent (reward >50)
  ⭐ Continue to 5M total
  ⭐ Achieve reward 80+, success 75%+
  ⭐ Grade: A (Excellent, deploy confidently)

Worst Case Scenario:
  ❌ Both models perform poorly
  ❌ Need to restart with adjusted hyperparameters
  ❌ Delay hardware deployment

=================================================================

Created: 2026-02-15
For Use: 2026-02-22 (Next Week)

Have a great week off!
Return ready to complete the RL training! 🚁

=================================================================
