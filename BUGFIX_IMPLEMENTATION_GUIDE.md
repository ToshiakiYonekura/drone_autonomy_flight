# Mode 99 & SITL - Bugfix Implementation Guide

**Date**: February 15, 2026
**Status**: Ready to implement
**Priority**: Critical → Medium → Low

---

## 🚨 **CRITICAL PRIORITY: Fix SITL Environment**

### Problem Summary

**Issue**: SITL doesn't initialize EKF, preventing Mode 99 testing
**Root Cause**: Physics simulator not running, no sensor data generated
**Impact**: Cannot test Mode 99 at all (complete blocker)

### Solution 1: Use Automated SITL Manager ⭐ **RECOMMENDED**

**File**: `sitl_manager.py` (already created)

**Usage**:
```bash
# Terminal 1: Start SITL
cd ~/autonomous_drone_sim
python3 sitl_manager.py

# Terminal 2: Run tests (once SITL is ready)
python3 tests/phase1_mode99_tests.py
```

**Advantages**:
- ✅ Fully automated
- ✅ Handles cleanup
- ✅ Waits for EKF
- ✅ Perfect for CI/CD
- ✅ Context manager support

**Example with context manager**:
```python
from sitl_manager import SITLManager

# Automatic startup and cleanup
with SITLManager() as manager:
    conn = manager.get_connection()
    # Run your tests here
    # SITL automatically stops when done
```

### Solution 2: Use Startup Script

**File**: `fix_sitl_startup.sh` (already created)

**Usage**:
```bash
bash fix_sitl_startup.sh
```

**Advantages**:
- ✅ Simple to use
- ✅ Interactive (can see MAVProxy console)
- ✅ Good for manual testing

**Note**: This starts MAVProxy in console mode. To test Mode 99:
```
MAV> param set FS_GCS_ENABLE 0
MAV> param set ARMING_CHECK 0
MAV> arm throttle
MAV> mode 99
```

### Solution 3: Docker-based SITL

**File**: `docker-compose-sitl.yml` (already created)

**Prerequisites**:
```bash
# Install Docker if not already installed
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Log out and back in

# Install docker-compose
sudo apt-get install docker-compose
```

**Usage**:
```bash
cd ~/autonomous_drone_sim
docker-compose -f docker-compose-sitl.yml up
```

**Advantages**:
- ✅ Most reliable (isolated environment)
- ✅ No dependency issues
- ✅ Reproducible
- ✅ Easy to reset

**Disadvantages**:
- ⚠️ Requires Docker installation
- ⚠️ Larger download (~1GB)

### Verification Steps

After starting SITL with any method, verify it's working:

```bash
# Test EKF initialization
python3 << 'EOF'
from pymavlink import mavutil
import time

mav = mavutil.mavlink_connection('tcp:127.0.0.1:5760', source_system=255)
mav.wait_heartbeat(timeout=10)
print("✅ Connected")

# Wait for position data
for i in range(30):
    msg = mav.recv_match(type='LOCAL_POSITION_NED', blocking=True, timeout=1.0)
    if msg:
        print(f"✅ EKF working! Position: [{msg.x:.2f}, {msg.y:.2f}, {msg.z:.2f}]")
        break
    time.sleep(1)
else:
    print("❌ No position data - EKF not initialized")
EOF
```

**Expected output**:
```
✅ Connected
✅ EKF working! Position: [0.00, 0.00, 0.00]
```

---

## ⚠️ **MEDIUM PRIORITY: Code Improvements**

### Fix 1: Add Safety Constants

**File**: `~/ardupilot/ArduCopter/mode_smartphoto99.h`

**Change**: Add these constants after line 56:
```cpp
// LQR thrust limits
static constexpr float MIN_THRUST_RATIO = 0.3f;    // 30% of hover thrust
static constexpr float MAX_THRUST_RATIO = 1.7f;    // 170% of hover thrust

// Moment limits (N·m)
static constexpr float MAX_ROLL_MOMENT_NM = 50.0f;
static constexpr float MAX_PITCH_MOMENT_NM = 50.0f;
static constexpr float MAX_YAW_MOMENT_NM = 20.0f;
```

**Why**: Eliminates magic numbers, improves maintainability

**Apply patch**:
```bash
cd ~/ardupilot/ArduCopter
patch -p0 < ~/autonomous_drone_sim/mode99_improvements.patch
# Or apply manually using the changes above
```

### Fix 2: Improve Parameter Validation

**File**: `~/ardupilot/ArduCopter/mode_smartphoto99.cpp`

**Location**: Function `mix_motors_from_lqr()`, around line 955

**Current code**:
```cpp
if (L <= 0.0f || kM <= 0.0f) {
    // Use defaults
}
```

**Improved code**:
```cpp
bool params_invalid = false;
float L_safe = L;
float kM_safe = kM;

// Validate ARM_LENGTH
if (L <= 0.0f || L < 0.05f || L > 1.0f) {
    gcs().send_text(MAV_SEVERITY_WARNING, "MODE99: Invalid ARM_LENGTH %.3f, using default", L);
    L_safe = 0.225f;  // Default
    params_invalid = true;
}

// Validate MOMENT_COEFF
if (kM <= 0.0f || kM < 0.005f || kM > 0.05f) {
    gcs().send_text(MAV_SEVERITY_WARNING, "MODE99: Invalid MOMENT_COEFF %.3f, using default", kM);
    kM_safe = 0.016f;  // Default
    params_invalid = true;
}

// Use L_safe and kM_safe in calculations
```

**Why**: Prevents issues from near-zero but non-zero values

**Testing**: After applying, rebuild and test:
```bash
cd ~/ardupilot
./waf copter
```

### Fix 3: Reduce Telemetry Overhead

**File**: `~/ardupilot/ArduCopter/mode_smartphoto99.cpp`

**Location**: Function `compute_lqr_state_feedback_control()`, around line 1108

**Current**: Sends 13 messages @ 100 Hz = 1300 msg/s

**Improved**: Send detailed telemetry @ 20 Hz:
```cpp
// Always send critical data at 100 Hz
gcs().send_named_float("LQR_Thrust", control_output[0]);

// Send detailed telemetry every 5th iteration (20 Hz)
if (state_feedback_counter % 5 == 0) {
    gcs().send_named_float("LQR_M_roll", control_output[1]);
    gcs().send_named_float("LQR_M_pitch", control_output[2]);
    gcs().send_named_float("LQR_M_yaw", control_output[3]);

    gcs().send_named_float("LQR_Motor0", motor_thrust[0]);
    gcs().send_named_float("LQR_Motor1", motor_thrust[1]);
    gcs().send_named_float("LQR_Motor2", motor_thrust[2]);
    gcs().send_named_float("LQR_Motor3", motor_thrust[3]);

    gcs().send_named_float("LQR_PWM0", (float)motor_pwm[0]);
    gcs().send_named_float("LQR_PWM1", (float)motor_pwm[1]);
    gcs().send_named_float("LQR_PWM2", (float)motor_pwm[2]);
    gcs().send_named_float("LQR_PWM3", (float)motor_pwm[3]);
}
```

**Impact**: Reduces telemetry from 23.4 kB/s to 5.2 kB/s

**Trade-off**: Slightly less frequent motor data (still sufficient for monitoring)

---

## 💡 **LOW PRIORITY: Optional Improvements**

### Improvement 1: Verify MOMENT_COEFF Parameter

**Current Value**: 0.016 m (in `sysid_params.txt`)

**Action**: Measure actual propeller torque-to-thrust ratio

**Methods**:

1. **From Propeller Datasheet**:
   - Find propeller model specifications
   - Look for kM/kF ratio or torque coefficient
   - Update `sysid_params.txt`

2. **Experimental Measurement**:
   - Mount propeller on test stand
   - Measure thrust (F) and torque (τ) at various RPMs
   - Calculate: kM/kF = τ/F
   - Typical range: 0.01 - 0.02 m

3. **Estimation** (if data unavailable):
   ```
   For 10-inch propellers:
   kM/kF ≈ 0.25 × propeller_radius
        ≈ 0.25 × 0.127m
        ≈ 0.032m

   But typical values are lower (0.015-0.020m) due to
   blade design and pitch.
   ```

**Update**:
```bash
# File: ~/ardupilot/ArduCopter/sysid_params.txt
MOMENT_COEFF=0.018  # Update with measured value
```

**Then rebuild**:
```bash
cd ~/ardupilot && ./waf copter
```

### Improvement 2: Add Motor Dead Zone Handling

**File**: `~/ardupilot/ArduCopter/mode_smartphoto99.cpp`

**Location**: Function `thrust_to_pwm()`, around line 1004

**Current**: Uses simple quadratic model throughout range

**Improved**: Add dead zone handling:
```cpp
for (int i = 0; i < 4; i++) {
    if (motor_thrust[i] < 0.05f * max_thrust) {
        // Below 5% thrust = motor off (dead zone)
        motor_pwm[i] = 1000;
    } else {
        // Apply quadratic model starting from 1100 μs
        float thrust_ratio = (motor_thrust[i] / max_thrust - 0.05f) / 0.95f;
        thrust_ratio = constrain_float(thrust_ratio, 0.0f, 1.0f);
        float pwm_float = 1100.0f + 900.0f * sqrtf(thrust_ratio);
        motor_pwm[i] = (uint16_t)constrain_float(pwm_float, 1100.0f, 2000.0f);
    }
}
```

**Why**: Better low-throttle performance

**When**: Only if you notice issues with hover stability

---

## 📋 **Implementation Checklist**

### Phase 1: Fix SITL (DO THIS FIRST) ✅

- [ ] Choose solution (Manager/Script/Docker)
- [ ] Test SITL startup
- [ ] Verify EKF initialization
- [ ] Confirm position data available

**Success Criteria**: Position data received within 30 seconds

### Phase 2: Run Tests

- [ ] Run Phase 1 tests: `python3 tests/phase1_mode99_tests.py`
- [ ] Verify all 4 tests pass
- [ ] Review test results JSON

**Success Criteria**: At least 3/4 tests pass

### Phase 3: Apply Code Improvements (Optional)

- [ ] Add safety constants
- [ ] Improve parameter validation
- [ ] Reduce telemetry overhead
- [ ] Rebuild: `cd ~/ardupilot && ./waf copter`
- [ ] Re-run tests

**Success Criteria**: Code compiles, tests still pass

### Phase 4: Verify MOMENT_COEFF (Optional)

- [ ] Obtain propeller specifications
- [ ] Measure or estimate kM/kF ratio
- [ ] Update `sysid_params.txt`
- [ ] Test yaw control performance

---

## 🛠️ **Quick Start Guide**

### For Immediate Testing

```bash
# 1. Start SITL (choose one method)
python3 ~/autonomous_drone_sim/sitl_manager.py

# OR
bash ~/autonomous_drone_sim/fix_sitl_startup.sh

# OR
cd ~/autonomous_drone_sim && docker-compose -f docker-compose-sitl.yml up

# 2. Wait for "SITL READY" message

# 3. In another terminal, run tests
cd ~/autonomous_drone_sim
python3 tests/phase1_mode99_tests.py

# 4. Check results
cat mode99_test_results.json
```

### Expected Timeline

| Task | Time | Difficulty |
|------|------|------------|
| Fix SITL | 5 min | Easy |
| Run tests | 3 min | Easy |
| Apply code fixes | 15 min | Medium |
| Verify parameters | 30 min | Medium-Hard |

**Total**: 30-60 minutes for complete bugfix

---

## 🐛 **Troubleshooting**

### Issue: SITL still doesn't provide position data

**Solution**:
1. Check if physics simulator (JSBSim) is running:
   ```bash
   ps aux | grep -i jsbsim
   ```

2. Check SITL log for errors:
   ```bash
   tail -100 /tmp/sitl_manager.log
   # or
   tail -100 /tmp/ArduCopter.log
   ```

3. Try starting with `--speedup 1`:
   ```bash
   cd ~/ardupilot/ArduCopter
   ../Tools/autotest/sim_vehicle.py -v ArduCopter --no-mavproxy --speedup 1
   ```

### Issue: Mode 99 still won't activate

**Check**:
1. Is Mode 99 compiled?
   ```bash
   grep -r "SMART_PHOTO" ~/ardupilot/ArduCopter/config.h
   ```
   Should show: `#define MODE_SMARTPHOTO_ENABLED 1`

2. Does sysid_params.txt exist?
   ```bash
   ls -la ~/ardupilot/ArduCopter/sysid_params.txt
   ```

3. Check for error messages:
   ```bash
   # In Python test script, add:
   status = mav.recv_match(type='STATUSTEXT', blocking=True, timeout=5.0)
   if status:
       print(f"Status: {status.text}")
   ```

### Issue: Tests fail with "Connection refused"

**Solution**:
```bash
# SITL not running - start it first
python3 sitl_manager.py

# Check if port is listening
netstat -ln | grep 5760
# Should show: tcp LISTEN 0.0.0.0:5760
```

---

## 📊 **Expected Results**

### After Fixing SITL

```
✅ SITL starts successfully
✅ EKF initializes within 30 seconds
✅ Position data available
✅ Can arm vehicle
✅ Mode 99 activates
✅ LQR telemetry received
```

### After Running Tests

```
Test Suite Summary
==================
Tests passed: 4/4
Success rate: 100.0%

✅ test1_hover_stability: PASSED
✅ test2_position_tracking: PASSED
✅ test3_motor_response: PASSED
✅ test4_telemetry_validation: PASSED
```

---

## 📚 **Reference Files**

| File | Purpose |
|------|---------|
| `sitl_manager.py` | Automated SITL lifecycle management |
| `fix_sitl_startup.sh` | Simple SITL startup script |
| `docker-compose-sitl.yml` | Docker-based SITL |
| `mode99_improvements.patch` | Code improvements patch |
| `tests/phase1_mode99_tests.py` | Automated test suite |
| `MODE99_TEST_REPORT.md` | Original issue analysis |
| `MODE99_CODE_REVIEW.md` | Detailed code review |

---

**Created**: February 15, 2026
**Last Updated**: February 15, 2026
**Status**: Ready for implementation

