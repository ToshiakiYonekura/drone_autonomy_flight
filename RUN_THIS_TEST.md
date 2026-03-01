# CRITICAL: Run This Altitude Test

## What This Tests
- **Does altitude actually change when commanded in SITL?**
- **Is the direction correct (up is up, down is down)?**

This is the test I should have run before, but didn't.

---

## Steps to Run

### Terminal 1: Start SITL
```bash
cd ~/ardupilot/ArduCopter
~/ardupilot/build/sitl/bin/arducopter --model + --speedup 1 \
  --defaults ~/ardupilot/Tools/autotest/default_params/copter.parm
```

**Wait for these messages:**
```
SERIAL0 on TCP port 5760
Waiting for connection ....
```

(It will stay at "Waiting for connection" until the Python script connects)

### Terminal 2: Run Test (within 30 seconds of starting SITL)
```bash
cd /home/yonetoshi27/autonomous_drone_sim
python3 test_actual_altitude_change.py
```

When prompted "Is SITL ready and initialized? (y/n):", type: **y**

---

## What Should Happen

The test will:
1. Connect to SITL (SITL will then finish initializing)
2. Set GUIDED mode and arm
3. Hover for 3 seconds (baseline)
4. Command +1.0 m/s upward for 10 seconds
5. **Measure actual altitude change**

---

## Expected Results

### ✅ If Fix Is Working:
```
Commanded +1.0 m/s UP → Altitude INCREASED by X.XXm
✅ Coordinate frame conversion is WORKING!
✅ SITL altitude control is CORRECT!
```

### ❌ If Fix Is NOT Working:
```
Commanded +1.0 m/s UP → Altitude DECREASED by X.XXm
❌ Coordinate frame conversion is BROKEN!
❌ The vz negation is not working!
```

### ⚠️  If Inconclusive:
```
Altitude barely changed (< 0.3m)
- Check if drone is armed
- Check motor RPMs (should be > 1000)
- May need to increase test duration
```

---

## Quick Alternative: Single Command Test

If you want a simpler one-line test:

```bash
# Start SITL in background
cd ~/ardupilot/ArduCopter && ~/ardupilot/build/sitl/bin/arducopter --model + --speedup 1 > /tmp/sitl.log 2>&1 &

# Wait 5 seconds
sleep 5

# Run test
python3 /home/yonetoshi27/autonomous_drone_sim/test_actual_altitude_change.py
```

(Then type 'y' when prompted)

---

## This Will Tell Us The Truth

This test will definitively answer:
- ✅ **Do both SITL fixes work?** (motor outputs + altitude frame)
- ✅ **Is altitude control correct?**
- ✅ **Can we start RL training with confidence?**

**Please run this and let me know the results!**
