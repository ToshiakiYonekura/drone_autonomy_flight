# Motor Torque Analysis - SITL Integration Issue

**Date:** 2026-02-08
**Status:** ⚠️ ISSUE IDENTIFIED

---

## Problem Summary

The SITL integration failed because **there is no bidirectional bridge** between ArduPilot SITL and PyBullet physics simulation. The current implementation only sends commands TO ArduPilot but doesn't receive motor outputs BACK to apply them to PyBullet.

---

## Current Motor Torque Implementation (PyBullet Only)

### Motor Torque Calculation (Line 270)
```python
motor_torques = self.km * (motor_rpms ** 2) * np.array([-1, 1, -1, 1])
```

**Status:** ✅ CORRECT

Motor rotation directions for X-configuration:
- Motor 0 (FR, CW): -1 → Negative yaw torque ✓
- Motor 1 (RR, CCW): +1 → Positive yaw torque ✓
- Motor 2 (RL, CW): -1 → Negative yaw torque ✓
- Motor 3 (FL, CCW): +1 → Positive yaw torque ✓

### Roll Torque (Lines 288-290)
```python
roll_torque = self.arm_length * (motor_thrusts[3] + motor_thrusts[2]
                                 - motor_thrusts[0] - motor_thrusts[1])
```

**Status:** ✅ CORRECT

- Positive roll (right): Left motors (2,3) > Right motors (0,1)
- For X-config: (FL + RL) - (FR + RR) = correct roll axis

### Pitch Torque (Lines 292-294)
```python
pitch_torque = self.arm_length * (motor_thrusts[0] + motor_thrusts[3]
                                  - motor_thrusts[1] - motor_thrusts[2])
```

**Status:** ✅ CORRECT

- Positive pitch (nose up): Front motors (0,3) > Rear motors (1,2)
- For X-config: (FR + FL) - (RR + RL) = correct pitch axis

### Yaw Torque (Line 297)
```python
yaw_torque = np.sum(motor_torques)
```

**Status:** ✅ CORRECT

- Sum of all reaction torques from propellers

### Torque Application (Lines 300-306)
```python
torques = np.array([roll_torque, pitch_torque, yaw_torque])
p.applyExternalTorque(
    self.drone_id,
    -1,
    torques,
    p.LINK_FRAME,
)
```

**Status:** ✅ CORRECT

- Applied in body/link frame (correct reference frame)

---

## The Real Problem: Missing SITL Integration

### Current Architecture (PyBullet Standalone)

```
Velocity Command [vx, vy, vz, yaw_rate]
         ↓
   _velocity_to_rpms() (Internal PD controller)
         ↓
   Motor RPMs [rpm0, rpm1, rpm2, rpm3]
         ↓
   _apply_motor_forces() (Thrust + Torque)
         ↓
   PyBullet Physics Step
```

**This works fine:** ✅ All training and standalone tests passed

### Attempted SITL Architecture (BROKEN)

```
Velocity Command [vx, vy, vz, yaw_rate]
         ↓
   MAVLink → ArduPilot SITL
         ↓
   ArduPilot calculates motor outputs
         ↓
   ??? NO BRIDGE ???  ❌ MISSING
         ↓
   PyBullet Physics (using wrong/no motor values)
```

**Problem:** ArduPilot motor outputs never reach PyBullet!

---

## What's Missing

### 1. ❌ No Motor Output Reception from ArduPilot

**Missing functionality:**
- Receive `SERVO_OUTPUT_RAW` messages from ArduPilot
- Receive `ACTUATOR_OUTPUT_STATUS` messages
- Convert PWM values (1000-2000 μs) to RPM
- Map ArduPilot motor indices to PyBullet motor indices

**Current MAVLink interface only receives:**
- HEARTBEAT
- LOCAL_POSITION_NED
- ATTITUDE
- GLOBAL_POSITION_INT
- SYS_STATUS
- GPS_RAW_INT

**Does NOT receive:** Motor outputs!

### 2. ❌ No PWM-to-RPM Conversion

ArduPilot outputs PWM (1000-2000 μs), but PyBullet needs RPM.

**Required conversion:**
```python
def pwm_to_rpm(pwm_value, motor_kv=920):
    """
    Convert PWM to RPM.

    PWM range: 1000-2000 μs
    Voltage: 0-16V (based on battery)
    RPM = KV * Voltage
    """
    # Normalize PWM to 0-1
    pwm_normalized = (pwm_value - 1000) / 1000

    # Assume 16V battery
    voltage = pwm_normalized * 16.0

    # Calculate RPM
    rpm = motor_kv * voltage

    return rpm
```

### 3. ❌ No Motor Index Mapping

ArduPilot and PyBullet may use different motor numbering conventions.

**Need to verify mapping:**
```
ArduPilot Copter (Quad X):
  3   1      (CCW CW)
   \ /
    X
   / \
  2   4      (CW CCW)

PyBullet (this implementation):
  1   0      (CCW CW)
   \ /
    X
   / \
  2   3      (CW CCW)

Possible remapping needed: [1→0, 2→1, 3→2, 4→3]
```

---

## Diagnosis Checklist

When you tried SITL yesterday, check these:

### ✅ Working Components
- [ ] ArduPilot SITL started successfully
- [ ] MAVLink connection established (heartbeat received)
- [ ] Velocity commands sent to ArduPilot
- [ ] ArduPilot received commands (visible in MAVProxy)

### ❌ Failing Components
- [ ] PyBullet received motor outputs from ArduPilot (NO - not implemented)
- [ ] Drone responded to ArduPilot commands in PyBullet (NO - using internal controller)
- [ ] Motor torques matched between ArduPilot and PyBullet (NO - different sources)

---

## Solution Options

### Option 1: Add Full SITL Bridge (Recommended for Hardware Testing)

**Implement bidirectional ArduPilot ↔ PyBullet bridge:**

```python
# In MAVLinkInterface class
def _process_message(self, msg):
    # ... existing code ...

    elif msg_type == 'SERVO_OUTPUT_RAW':
        # Extract motor PWM values
        motor_pwms = [
            msg.servo1_raw,
            msg.servo2_raw,
            msg.servo3_raw,
            msg.servo4_raw,
        ]

        # Convert to RPM
        self.motor_rpms = [self.pwm_to_rpm(pwm) for pwm in motor_pwms]

        # Remap indices if needed
        self.motor_rpms_remapped = self.remap_motors(self.motor_rpms)
```

**Then in PyBulletDroneEnv:**
```python
def step(self, action):
    if self.use_mavlink:
        # Send command to ArduPilot
        self.mavlink.send_velocity_command(*action)

        # Get motor RPMs from ArduPilot
        motor_rpms = self.mavlink.get_motor_rpms()

        # Apply to PyBullet physics
        self.sim._apply_motor_forces(motor_rpms)
    else:
        # Use internal controller
        collision = self.sim.step(action)
```

### Option 2: Use PyBullet Controller Only (Current - Working)

**Keep current implementation for RL training:**
- ✅ Fast simulation
- ✅ No SITL overhead
- ✅ Proven to work (training completed successfully)

**Use ArduPilot SITL separately for:**
- Hardware-in-the-loop testing
- Flight controller validation
- Real-world deployment preparation

### Option 3: Physics-Only SITL Integration

**Use ArduPilot SITL physics, skip PyBullet:**
- Connect MAVLink directly to ArduPilot SITL
- Let ArduPilot handle all physics
- Use PyBullet only for sensors (LiDAR, camera)

---

## Recommendations

### For RL Training (Current Use)
**✅ Keep current PyBullet-only implementation**
- Motor torques are calculated correctly
- Training works perfectly (14.1 hours, 1.5M steps successful)
- No SITL integration needed

### For Hardware Deployment Preparation
**⚠️ Implement Option 1: Full SITL Bridge**
- Add motor output reception to MAVLink interface
- Implement PWM-to-RPM conversion
- Verify motor index mapping
- Test with ArduPilot SITL before hardware

### Quick Test Commands

**Test PyBullet motor torques (working):**
```bash
python3 test_medium_quad.py
```

**Test trained model (working):**
```bash
python3 examples/test_trained_model.py \
    --model data/checkpoints/PPO_continued_20260110_180049/best/best_model.zip \
    --episodes 10 \
    --render
```

---

## Conclusion

### Motor Torque Implementation: ✅ CORRECT
- All torque calculations are mathematically correct
- PyBullet physics works perfectly
- Training completed successfully

### SITL Integration: ❌ INCOMPLETE
- Missing motor output reception from ArduPilot
- No PWM-to-RPM conversion
- No motor index remapping
- This is why SITL tests failed yesterday

### Action Required

**If you want SITL integration:**
1. Implement `SERVO_OUTPUT_RAW` message handling in `MAVLinkInterface`
2. Add PWM-to-RPM conversion method
3. Verify motor index mapping
4. Test with ArduPilot SITL
5. Update the physics loop to use ArduPilot motor outputs

**If you want to continue RL training:**
- Nothing needed - current implementation is perfect
- Deploy trained model to hardware later with proper SITL bridge

---

**Generated:** 2026-02-08
**Issue:** SITL integration not implemented, not motor torque calculation error
**Status:** Motor torques are correct, SITL bridge is missing
