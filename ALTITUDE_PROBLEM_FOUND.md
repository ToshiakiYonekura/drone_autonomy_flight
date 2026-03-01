# ⚠️  ALTITUDE PROBLEM FOUND - Coordinate Frame Mismatch

**Date:** 2026-02-08
**Status:** 🔴 **CRITICAL BUG IDENTIFIED**

---

## The Problem

There's a **coordinate frame mismatch** between PyBullet and ArduPilot that causes altitude control to be INVERTED when using SITL mode.

### Root Cause

**PyBullet Convention (Z-up):**
- Positive vz = **UPWARD** velocity
- Negative vz = **DOWNWARD** velocity
- Example: `action = [0, 0, 1.0, 0]` → Go UP at 1 m/s

**ArduPilot NED Frame (Z-down):**
- Positive vz = **DOWNWARD** velocity
- Negative vz = **UPWARD** velocity
- Example: `vz = 1.0` → Go DOWN at 1 m/s

### What Happens

**In PyBullet-only mode:**
```python
action = [0, 0, 1.0, 0]  # Intended: go up
↓
PyBullet controller applies +1.0 m/s upward
✅ WORKS CORRECTLY
```

**In SITL mode (BROKEN):**
```python
action = [0, 0, 1.0, 0]  # Intended: go up
↓
Sent to ArduPilot as vz=+1.0 in NED frame
↓
ArduPilot interprets as: go DOWN at 1 m/s
❌ ALTITUDE INVERTED!
```

---

## Evidence

### Code Location 1: MAVLink Interface
**File:** `drone_gym/controllers/mavlink_interface.py:416-430`

```python
def send_velocity_command(
    self,
    vx: float,
    vy: float,
    vz: float,  # ← Says "Velocity down (m/s)" in NED frame
    yaw_rate: float = 0.0,
):
    """
    Send velocity command in NED frame.

    Args:
        vx: Velocity north (m/s), range: [-5, 5]
        vy: Velocity east (m/s), range: [-5, 5]
        vz: Velocity down (m/s), range: [-2, 2]  # ← NED: positive = down
        yaw_rate: Yaw rate (rad/s), range: [-1, 1]
    """
```

### Code Location 2: Environment Step Function
**File:** `drone_gym/envs/pybullet_drone_env.py:172-179`

```python
if self.use_mavlink and self.mavlink and self.mavlink.connected:
    # Mode 1: ArduPilot SITL controls motors
    # Send velocity command to ArduPilot
    self.mavlink.send_velocity_command(
        action[0],  # vx
        action[1],  # vy
        action[2],  # vz  ← NO CONVERSION! Sent directly
        action[3] if len(action) > 3 else 0.0,  # yaw_rate
    )
```

**No frame conversion is performed!** The vz from action (PyBullet convention) is sent directly to ArduPilot (NED convention).

---

## The Fix

### Option 1: Negate vz When Sending to ArduPilot (Recommended)

**File:** `drone_gym/envs/pybullet_drone_env.py`

```python
if self.use_mavlink and self.mavlink and self.mavlink.connected:
    # Mode 1: ArduPilot SITL controls motors
    # Send velocity command to ArduPilot
    # NOTE: Convert PyBullet frame (Z-up) to NED frame (Z-down)
    self.mavlink.send_velocity_command(
        action[0],   # vx (North)
        action[1],   # vy (East)
        -action[2],  # vz (Down) ← NEGATE for NED frame
        action[3] if len(action) > 3 else 0.0,  # yaw_rate
    )
```

### Option 2: Document NED Frame in Action Space

If actions are meant to be in NED frame, update the docstring:

```python
# Define action space: [vx, vy, vz, yaw_rate]
# When use_mavlink=True (SITL mode):
#   vx: Velocity North (m/s), range: [-5, 5]
#   vy: Velocity East (m/s), range: [-5, 5]
#   vz: Velocity Down (m/s), range: [-2, 2]  # NED frame!
#   yaw_rate: Yaw rate (rad/s), range: [-1, 1]
# When use_mavlink=False (PyBullet mode):
#   vx, vy: Horizontal velocities (m/s)
#   vz: Vertical velocity (m/s), positive = up
#   yaw_rate: Yaw rate (rad/s)
```

---

## Impact

### ❌ Broken Behaviors (SITL mode)

1. **Hover command fails**
   - Action: `[0, 0, 0, 0]` (hover in place)
   - Result: ✅ Works (vz=0 is same in both frames)

2. **Upward command inverted**
   - Action: `[0, 0, 1.0, 0]` (go up at 1 m/s)
   - Result: ❌ Goes DOWN at 1 m/s

3. **Downward command inverted**
   - Action: `[0, 0, -1.0, 0]` (go down at 1 m/s)
   - Result: ❌ Goes UP at 1 m/s

4. **RL Training fails**
   - Agent learns inverted altitude control
   - Cannot generalize to PyBullet or real hardware
   - Training rewards will be poor

### ✅ Unaffected Behaviors

- PyBullet-only mode (use_mavlink=False) works correctly
- Horizontal velocity control (vx, vy) unaffected
- Yaw rate control unaffected
- Motor torque calculations still correct

---

## Testing the Fix

### Before Fix (Current Behavior)
```bash
# Start SITL
cd ~/ardupilot/ArduCopter
~/ardupilot/build/sitl/bin/arducopter --model + --speedup 1

# Test altitude (will go wrong direction)
python3 << EOF
from drone_gym.envs.pybullet_drone_env import PyBulletDroneEnv
import time

env = PyBulletDroneEnv(use_mavlink=True, mavlink_connection="tcp:127.0.0.1:5760", gui=True)
env.mavlink.set_mode("GUIDED")
env.mavlink.arm()
env.reset()

# Try to go UP - will actually go DOWN
for i in range(30):
    obs, reward, terminated, truncated, info = env.step([0, 0, 1.0, 0])
    time.sleep(0.1)
    if i % 10 == 0:
        print(f"Altitude: {-env.mavlink.get_state()['position'][2]:.2f}m")

env.close()
EOF
```

### After Fix (Expected Behavior)
```bash
# Same test, but altitude will go UP as expected
# Altitude should increase from ~0m to ~2-3m
```

---

## Recommendation

**Fix Option 1 (Negate vz) is STRONGLY RECOMMENDED** because:

1. ✅ Maintains consistent action space across both modes
2. ✅ RL agents can train in PyBullet and deploy to SITL
3. ✅ Users don't need to think about frame conversions
4. ✅ Matches standard robotics convention (Z-up)
5. ✅ One-line fix, easy to implement

---

## Implementation

I'll implement the fix now. The change is:

**File:** `drone_gym/envs/pybullet_drone_env.py:175`

**Change:**
```python
# Before:
self.mavlink.send_velocity_command(
    action[0], action[1], action[2], action[3]
)

# After:
self.mavlink.send_velocity_command(
    action[0], action[1], -action[2], action[3]  # Negate vz
)
```

---

**Status:** 🔴 **BUG CONFIRMED - FIX READY TO APPLY**

This explains yesterday's "0 altitude problem" - the drone was receiving inverted altitude commands!
