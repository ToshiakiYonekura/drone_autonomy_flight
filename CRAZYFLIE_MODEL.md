# Crazyflie 2.x Physical Model Implementation

This document describes the implementation of the Crazyflie 2.x quadcopter physical model in PyBullet.

## Overview

The project now includes a realistic quadcopter model based on the **Bitcraze Crazyflie 2.x** nano-quadrotor, replacing the previous simple sphere geometry. This model provides accurate mass, inertia, and motor dynamics for realistic drone simulation.

## Model Specifications

### Physical Properties
- **Mass**: 0.027 kg (27 grams)
- **Arm length**: 0.0397 m (39.7 mm)
- **Thrust-to-weight ratio**: 2.25
- **Configuration**: X-configuration quadcopter

### Motor Properties
- **Thrust coefficient (kf)**: 3.16e-10 N/(RPM²)
- **Torque coefficient (km)**: 7.94e-12 Nm/(RPM²)
- **Maximum RPM**: 21,702
- **Hover RPM**: ~14,476 per motor

### Inertia Properties
- **Ixx**: 1.4e-5 kg⋅m²
- **Iyy**: 1.4e-5 kg⋅m²
- **Izz**: 2.17e-5 kg⋅m²

## File Structure

```
drone_gym/
├── assets/
│   ├── cf2x.urdf          # Crazyflie 2.x URDF model
│   └── cf2.dae            # 3D mesh file (visual geometry)
└── physics/
    └── pybullet_drone.py  # Updated with motor dynamics

examples/
├── test_crazyflie_headless.py  # Headless test script
├── test_crazyflie_simple.py    # GUI test script
└── test_crazyflie_model.py     # Full integration test
```

## Motor Layout

The quadcopter uses an X-configuration with the following motor layout:

```
      Front
   1(CCW)  0(CW)
      \ /
       X
      / \
  2(CW)  3(CCW)
      Rear

Motor 0: Front-Right (Clockwise)
Motor 1: Rear-Right (Counter-Clockwise)
Motor 2: Rear-Left (Clockwise)
Motor 3: Front-Left (Counter-Clockwise)
```

## Motor Dynamics

The implementation includes realistic quadcopter physics:

### Thrust Calculation
Each motor produces thrust according to:
```
F = kf × RPM²
```

### Torque Calculation
Each motor produces reaction torque:
```
T = km × RPM²
```
- CW motors (0, 2): negative yaw torque
- CCW motors (1, 3): positive yaw torque

### Motor Mixing
The velocity commands [vx, vy, vz, yaw_rate] are converted to motor RPMs using:

1. **Altitude control**: PD controller for vertical velocity
2. **Horizontal control**: Velocity errors converted to roll/pitch commands
3. **Yaw control**: Yaw rate converted to differential torque
4. **Motor mixing**: Commands distributed across 4 motors based on X-configuration

## Control Interface

The drone accepts velocity commands as numpy arrays:
```python
action = np.array([vx, vy, vz, yaw_rate])
# vx, vy: horizontal velocities [-5, 5] m/s
# vz: vertical velocity [-2, 2] m/s
# yaw_rate: yaw angular velocity [-1, 1] rad/s
```

## Changes Made

### 1. URDF Model Files
- Downloaded Crazyflie 2.x URDF from `gym-pybullet-drones` repository
- Includes:
  - Base link with accurate mass and inertia
  - 4 propeller links at correct positions
  - Collision geometry (cylinder)
  - Visual geometry (3D mesh)

### 2. Updated `PyBulletDrone` Class

#### New Parameters
```python
self.mass = 0.027                    # kg
self.arm_length = 0.0397             # m
self.thrust_to_weight = 2.25
self.kf = 3.16e-10                   # thrust coefficient
self.km = 7.94e-12                   # torque coefficient
self.max_rpm = 21702
self.motor_rpms = np.zeros(4)        # current motor states
```

#### New Methods
- `_create_drone()`: Loads URDF instead of creating simple sphere
- `_velocity_to_rpms(action)`: Converts velocity commands to motor RPMs
- `_apply_motor_forces(motor_rpms)`: Applies thrust and torque from motors

#### Modified Methods
- `step(action)`: Now uses motor dynamics instead of direct force application

## Testing

### Run Tests

1. **Headless test** (no GUI required):
   ```bash
   python3 examples/test_crazyflie_headless.py
   ```

2. **GUI test** (requires display):
   ```bash
   python3 examples/test_crazyflie_simple.py
   ```

3. **Full integration test**:
   ```bash
   python3 examples/test_crazyflie_model.py
   ```

### Test Results

All tests passed successfully:
- ✓ URDF loads correctly
- ✓ Mass matches expected value (0.027 kg)
- ✓ Inertia properties loaded from URDF
- ✓ 4 propeller joints created
- ✓ Physics simulation runs correctly
- ✓ Hover dynamics work as expected
- ✓ Motor equations produce realistic values

## Usage Example

```python
from drone_gym.physics.pybullet_drone import PyBulletDrone
import numpy as np

# Create drone with Crazyflie model
drone = PyBulletDrone(gui=False, drone_model="cf2x")
drone.connect()

# Hover command (zero velocity)
hover_action = np.array([0.0, 0.0, 0.0, 0.0])
collision = drone.step(hover_action)

# Forward flight at 1 m/s
forward_action = np.array([1.0, 0.0, 0.0, 0.0])
collision = drone.step(forward_action)

# Get current state
state = drone.get_state()
print(f"Position: {state['position']}")
print(f"Motor RPMs: {drone.motor_rpms}")

# Cleanup
drone.disconnect()
```

## References

1. **gym-pybullet-drones**: https://github.com/utiasDSL/gym-pybullet-drones
   - Source of Crazyflie 2.x URDF model
   - Paper: "Learning to Fly—a Gym Environment with PyBullet Physics for Reinforcement Learning of Multi-agent Quadcopter Control" (IROS 2021)

2. **Bitcraze Crazyflie 2.x**: https://www.bitcraze.io/products/crazyflie-2-1/
   - Official nano-quadcopter platform
   - Open-source hardware and firmware

3. **Academic References** (embedded in URDF):
   - https://arxiv.org/pdf/1608.05786.pdf
   - https://www.research-collection.ethz.ch/handle/20.500.11850/214143
   - http://groups.csail.mit.edu/robotics-center/public_papers/Landry15.pdf

## Future Improvements

Potential enhancements:
1. Ground effect modeling (parameter already in URDF)
2. Aerodynamic drag forces (coefficients in URDF)
3. Downwash effects (parameters in URDF)
4. Battery dynamics
5. Wind disturbances
6. Sensor noise modeling
7. More accurate motor response delays

## Compatibility

- ✓ Works with existing `PyBulletDroneEnv` Gym environment
- ✓ Compatible with MAVLink interface
- ✓ Drop-in replacement for previous simple model
- ✓ No changes required to training code
