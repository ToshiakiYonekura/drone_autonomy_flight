# Comprehensive Test Suite for Autonomous Drone System

## Overview

This test suite provides automated validation for all phases of the autonomous drone system, from Mode 99 LQR controller to RL training convergence.

## Test Structure

```
tests/
├── phase1_mode99_tests.py          # Mode 99 LQR validation
├── phase2_pybullet_tests.py        # PyBullet standalone tests
├── phase3_integration_tests.py     # MAVLink integration
├── phase4_rl_training_tests.py     # RL training validation
├── test_runner.py                  # Main test orchestrator
└── TEST_SUITE_README.md            # This file
```

---

## Phase 1: Mode 99 LQR Validation

**File**: `phase1_mode99_tests.py`

**Requirements**:
- ArduPilot SITL running with physics simulator
- Mode 99 enabled and compiled
- MAVLink connection on TCP:5760

**Tests**:
1. **Hover Stability Test**
   - Duration: 10 seconds
   - Measures: Position drift, max velocity, RMS velocity
   - Pass criteria: Drift < 0.5m, max velocity < 1 m/s, RMS < 0.2 m/s

2. **Position Tracking Test**
   - Waypoints: 5-point square pattern
   - Measures: Tracking error at each waypoint
   - Pass criteria: Mean error < 0.3m, max error < 0.5m

3. **Motor Response Telemetry Test**
   - Duration: 5 seconds
   - Checks: All LQR telemetry fields present
   - Fields: LQR_Thrust, LQR_Motor0-3, LQR_PWM0-3, LQR_M_*, LQR_Rate

4. **Telemetry Validation Test**
   - Validates: Value ranges, control rate
   - Checks: Thrust > 0, PWM ∈ [1000, 2000], rate ≈ 100 Hz

**Usage**:
```bash
# Ensure SITL is running
cd ~/ardupilot/ArduCopter
../Tools/autotest/sim_vehicle.py --no-mavproxy

# Run tests (in another terminal)
cd ~/autonomous_drone_sim
python3 tests/phase1_mode99_tests.py
```

**Output**: `mode99_test_results.json`

---

## Phase 2: PyBullet Standalone Tests

**File**: `phase2_pybullet_tests.py`

**Requirements**:
- PyBullet installed
- Drone models in `drone_gym/assets/`
- No SITL required

**Tests**:
1. **Medium Quad Physics Test**
   - Loads medium_quad.urdf
   - Tests: Gravity, motor thrust, collision
   - Pass criteria: Physics behaves correctly

2. **Sensor Simulation Test**
   - LiDAR: 360 rays, 10m range
   - Camera: 64x64 RGB
   - Pass criteria: Valid sensor data generated

3. **Collision Detection Test**
   - Spawns obstacles
   - Tests collision reporting
   - Pass criteria: Collisions detected accurately

4. **Performance Test**
   - Measures: Simulation FPS, step time
   - Pass criteria: >30 FPS, <33ms/step

**Usage**:
```bash
python3 tests/phase2_pybullet_tests.py
```

**Output**: `pybullet_test_results.json`

---

## Phase 3: Integration Tests

**File**: `phase3_integration_tests.py`

**Requirements**:
- ArduPilot SITL running
- PyBullet environment
- MAVLink connection

**Tests**:
1. **MAVLink Communication Test**
   - Bidirectional message flow
   - Latency measurement
   - Pass criteria: Latency < 50ms, no packet loss

2. **Closed-Loop Control Test**
   - PyBullet sends commands → SITL responds
   - Full control loop at 20Hz
   - Pass criteria: Control loop stable

3. **Sensor Sync Test**
   - PyBullet sensors vs ArduPilot telemetry
   - Checks: Position, velocity agreement
   - Pass criteria: Error < 10cm, < 0.1 m/s

4. **Latency Profiling**
   - Measures: Command latency, telemetry latency
   - Pass criteria: Total latency < 100ms

**Usage**:
```bash
# Start SITL first
cd ~/ardupilot/ArduCopter
../Tools/autotest/sim_vehicle.py --no-mavproxy

# Run integration tests
python3 tests/phase3_integration_tests.py
```

**Output**: `integration_test_results.json`

---

## Phase 4: RL Training Validation

**File**: `phase4_rl_training_tests.py`

**Requirements**:
- Stable-Baselines3 installed
- Training environment configured
- Sufficient disk space for checkpoints

**Tests**:
1. **Environment Reset Test**
   - Tests: Environment reset functionality
   - Pass criteria: Clean reset, no memory leaks

2. **Reward Function Test**
   - Scenarios: Goal reached, collision, timeout
   - Pass criteria: Rewards computed correctly

3. **Training Convergence Test**
   - Short training run: 1000 steps
   - Measures: Reward trend, loss convergence
   - Pass criteria: Reward increases

4. **Model Checkpoint Test**
   - Tests: Save/load functionality
   - Pass criteria: Model loads correctly

**Usage**:
```bash
python3 tests/phase4_rl_training_tests.py
```

**Output**: `rl_training_test_results.json`

---

## Test Runner

**File**: `test_runner.py`

Orchestrates all test phases and generates comprehensive report.

**Usage**:
```bash
# Run all tests
python3 tests/test_runner.py --all

# Run specific phase
python3 tests/test_runner.py --phase 1
python3 tests/test_runner.py --phase 2
python3 tests/test_runner.py --phase 3
python3 tests/test_runner.py --phase 4

# Generate HTML report
python3 tests/test_runner.py --all --html
```

**Output**:
- `test_results_<timestamp>.json` - Full results
- `test_report_<timestamp>.html` - HTML report (if --html)

---

## Test Monitoring Dashboard

**Script**: `monitor_tests.sh`

Real-time monitoring of test execution.

**Usage**:
```bash
bash tests/monitor_tests.sh
```

Displays:
- Test progress
- Current test status
- Pass/fail counts
- Performance metrics

---

## Continuous Integration

**Script**: `run_ci_tests.sh`

Automated testing for CI/CD pipeline.

**Features**:
- Automatically starts/stops SITL
- Runs all test phases
- Generates JUnit XML for CI systems
- Exits with proper status codes

**Usage**:
```bash
bash tests/run_ci_tests.sh
```

**Output**: `test-results.xml` (JUnit format)

---

## Test Data & Logs

All test runs generate:
- JSON results files
- Detailed logs in `tests/logs/`
- Performance metrics in `tests/metrics/`
- Screenshots/videos in `tests/artifacts/` (if applicable)

**Cleanup**:
```bash
# Remove old test data
bash tests/cleanup_test_data.sh --older-than 7days

# Remove all test data
bash tests/cleanup_test_data.sh --all
```

---

## Expected Test Timeline

| Phase | Tests | Duration | Dependencies |
|-------|-------|----------|--------------|
| 1     | 4     | ~3 min   | SITL + Mode 99 |
| 2     | 4     | ~2 min   | PyBullet only |
| 3     | 4     | ~5 min   | SITL + PyBullet |
| 4     | 4     | ~10 min  | Training setup |
| **Total** | **16** | **~20 min** | All systems |

---

## Troubleshooting

### Phase 1 Fails - SITL Issues

**Problem**: EKF not initializing, no position data

**Solution**:
1. Check SITL is running with physics:
   ```bash
   ps aux | grep arducopter
   tail -50 /tmp/ArduCopter.log
   ```

2. Restart SITL properly:
   ```bash
   cd ~/ardupilot/ArduCopter
   ../Tools/autotest/sim_vehicle.py --no-mavproxy --console
   ```

3. Verify port 5760 is listening:
   ```bash
   netstat -ln | grep 5760
   ```

### Phase 2 Fails - PyBullet Issues

**Problem**: Models not loading, physics errors

**Solution**:
1. Check PyBullet installation:
   ```bash
   python3 -c "import pybullet; print(pybullet.__version__)"
   ```

2. Verify models exist:
   ```bash
   ls -l drone_gym/assets/*.urdf
   ```

3. Test PyBullet directly:
   ```bash
   python3 examples/test_medium_quad.py
   ```

### Phase 3 Fails - Integration Issues

**Problem**: MAVLink connection fails, timeouts

**Solution**:
1. Ensure SITL running and Phase 1 passes
2. Check firewall/network settings
3. Verify MAVLink version compatibility

### Phase 4 Fails - Training Issues

**Problem**: Out of memory, CUDA errors

**Solution**:
1. Reduce parallel environments: `--n-envs 1`
2. Use CPU-only: `--device cpu`
3. Check GPU memory: `nvidia-smi`

---

## Test Success Criteria Summary

### Overall System Health
- ✅ All Phase 1 tests pass → Mode 99 LQR working
- ✅ All Phase 2 tests pass → PyBullet simulation working
- ✅ All Phase 3 tests pass → Integration working
- ✅ All Phase 4 tests pass → Ready for RL training

### Minimum Viable System
- Phase 1: At least 3/4 tests pass
- Phase 2: At least 3/4 tests pass
- Phase 3: At least 2/4 tests pass (communication + control loop)
- Phase 4: At least 2/4 tests pass (environment + reward)

---

## Next Steps After Tests Pass

1. **If Phase 1 passes**: Mode 99 is validated, proceed to PyBullet integration
2. **If Phase 2 passes**: PyBullet is ready, integrate with SITL
3. **If Phase 3 passes**: Full integration works, start RL training
4. **If Phase 4 passes**: Training pipeline ready, run full training

---

## Support & Documentation

- Full implementation details: `MODE99_TEST_REPORT.md`
- PyBullet guide: `examples/README_PYBULLET.md`
- Training guide: `TRAINING_GUIDE.md`
- Issues: Report to development team

---

**Created**: February 15, 2026
**Last Updated**: February 15, 2026
**Version**: 1.0.0
