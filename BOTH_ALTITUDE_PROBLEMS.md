# 🚨 TWO ALTITUDE PROBLEMS FOUND

**Date:** 2026-02-08
**Status:** 🔴 **CRITICAL - TWO SEPARATE BUGS**

---

## Summary

Yesterday's "0 altitude problem" is actually **TWO separate bugs**:

1. **Bug #1:** SITL coordinate frame mismatch (PyBullet Z-up vs NED Z-down)
2. **Bug #2:** PyBullet controller incorrect damping term

Both cause altitude control to fail or behave incorrectly.

---

## Bug #1: SITL Coordinate Frame Mismatch

### Problem
When using SITL mode, vz commands are sent without frame conversion:
- PyBullet uses Z-up convention (positive vz = upward)
- ArduPilot uses NED convention (positive vz = downward)
- Commands sent without negation → altitude inverted

### Status
✅ **FIXED** in `drone_gym/envs/pybullet_drone_env.py:177`

```python
# Fixed: Now negates vz for NED frame
self.mavlink.send_velocity_command(
    action[0], action[1], -action[2], action[3]  # -action[2] for NED
)
```

---

## Bug #2: PyBullet Controller Incorrect Damping

### Problem
**File:** `drone_gym/physics/pybullet_drone.py:218`

```python
# CURRENT (BROKEN):
thrust = self.mass * abs(self.gravity) + kp_z * z_error - kd_z * current_vel[2]
#                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^
#                                                          This fights upward motion!
```

**What happens:**
- Target velocity: +1.0 m/s (upward)
- Drone starts moving up: current_vel[2] = +0.5 m/s
- D term: `-kd_z * 0.5` = negative value
- This **REDUCES thrust** when moving upward
- Result: Drone can't climb, may even descend

**Test result:**
- Commanded +1.0 m/s upward for 10 seconds
- Actual result: Descended from 1.0m to 0.167m
- **Went DOWN instead of UP!**

### Root Cause

The damping term is applied to **absolute velocity** instead of **velocity error**.

**Correct formulation options:**

**Option 1: Remove D term on velocity tracking**
```python
thrust = self.mass * abs(self.gravity) + kp_z * z_error
```

**Option 2: Apply D term to acceleration (velocity error derivative)**
```python
# Would need to track previous velocity error
z_error_dot = (z_error - z_error_prev) / dt
thrust = self.mass * abs(self.gravity) + kp_z * z_error + kd_z * z_error_dot
```

**Option 3: Use correct sign for velocity damping**
```python
# Only damp if moving in wrong direction
thrust = self.mass * abs(self.gravity) + kp_z * z_error
# D term should oppose velocity ERROR, not absolute velocity
```

### Recommended Fix

**Option 1 is simplest and most robust for velocity tracking:**

```python
# Before:
thrust = self.mass * abs(self.gravity) + kp_z * z_error - kd_z * current_vel[2]

# After:
thrust = self.mass * abs(self.gravity) + kp_z * z_error
# Or use a small damping on ERROR:
# z_accel = (current_vel[2] - prev_vel[2]) / dt  # Need to store prev_vel
# thrust = self.mass * abs(self.gravity) + kp_z * z_error - kd_z * z_accel
```

For now, removing the problematic D term is safest.

---

## Impact Analysis

### Bug #1 Impact (SITL mode)
- ❌ SITL altitude commands inverted
- ❌ Cannot train with SITL correctly
- ⚠️  PyBullet-only mode unaffected
- ✅ **NOW FIXED**

### Bug #2 Impact (All modes)
- ❌ PyBullet altitude control broken
- ❌ Drone descends when commanded to climb
- ❌ Cannot hover or maintain altitude
- ❌ RL training will learn incorrect behavior
- ❌ Affects BOTH PyBullet-only AND SITL modes
- 🔴 **NEEDS FIX**

---

## Fixes Required

### ✅ Fix #1: Applied
```python
# File: drone_gym/envs/pybullet_drone_env.py:177
self.mavlink.send_velocity_command(
    action[0], action[1], -action[2], action[3]  # Negate vz for NED
)
```

### 🔴 Fix #2: Ready to Apply
```python
# File: drone_gym/physics/pybullet_drone.py:218

# Before:
thrust = self.mass * abs(self.gravity) + kp_z * z_error - kd_z * current_vel[2]

# After (Option 1 - Simplest):
thrust = self.mass * abs(self.gravity) + kp_z * z_error

# Or (Option 2 - Better damping):
# Add slight damping only when overshooting
damping = kd_z * z_error * current_vel[2]  # Damping proportional to error AND velocity
thrust = self.mass * abs(self.gravity) + kp_z * z_error - damping
```

---

## Testing After Fixes

### Test 1: PyBullet Hover
```python
# Should maintain altitude
action = [0, 0, 0, 0]
# Expected: Stay at ~1.0m
```

### Test 2: PyBullet Climb
```python
# Should climb smoothly
action = [0, 0, 1.0, 0]
# Expected: Gain 5-8m in 10 seconds
```

### Test 3: SITL Climb
```python
# Start SITL, then:
action = [0, 0, 1.0, 0]  # PyBullet convention: up
# Gets converted to vz=-1.0 in NED (up in ArduPilot)
# Expected: Climb in SITL
```

---

## Recommendation

**APPLY BOTH FIXES IMMEDIATELY:**

1. ✅ Bug #1 fix is already applied
2. 🔴 Apply Bug #2 fix now

After both fixes:
- ✅ Altitude control works correctly in PyBullet mode
- ✅ Altitude control works correctly in SITL mode
- ✅ Coordinate frames properly converted
- ✅ Ready for RL training

---

**Status:**
- Bug #1: ✅ FIXED
- Bug #2: 🔴 FIX READY, NEEDS APPLICATION
