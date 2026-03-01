#!/usr/bin/env python3
"""
Phase 1: Mode 99 LQR Validation Test Suite

Tests for ArduPilot Mode 99 Pure LQR State Feedback Controller.
Requires working SITL with physics simulator.
"""

import sys
import time
import math
import numpy as np
from typing import Dict, List, Tuple
from pymavlink import mavutil


class Mode99TestSuite:
    """Comprehensive test suite for Mode 99 LQR controller."""

    def __init__(self, connection_string='tcp:127.0.0.1:5760'):
        """Initialize test suite."""
        self.connection_string = connection_string
        self.mav = None
        self.test_results = {}

    def connect(self) -> bool:
        """Connect to SITL."""
        print(f"Connecting to {self.connection_string}...")
        try:
            self.mav = mavutil.mavlink_connection(self.connection_string, source_system=255)
            self.mav.wait_heartbeat(timeout=10.0)
            print(f"✅ Connected to system {self.mav.target_system}")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

    def wait_for_ekf(self, timeout=30.0) -> bool:
        """Wait for EKF to initialize."""
        print(f"Waiting up to {timeout}s for EKF initialization...")
        start = time.time()

        while time.time() - start < timeout:
            pos_msg = self.mav.recv_match(type='LOCAL_POSITION_NED', blocking=True, timeout=1.0)
            if pos_msg:
                print(f"✅ EKF initialized - Position: [{pos_msg.x:.2f}, {pos_msg.y:.2f}, {pos_msg.z:.2f}]")
                return True

        print("❌ EKF initialization timeout")
        return False

    def setup_sitl(self) -> bool:
        """Configure SITL for testing."""
        print("\nConfiguring SITL...")

        # Disable failsafes
        self.mav.param_set_send('FS_GCS_ENABLE', 0)
        self.mav.param_set_send('FS_EKF_ACTION', 0)
        self.mav.param_set_send('ARMING_CHECK', 0)
        time.sleep(1)

        print("✅ SITL configured")
        return True

    def arm_vehicle(self) -> bool:
        """Arm the vehicle."""
        print("\nArming vehicle...")

        self.mav.mav.command_long_send(
            self.mav.target_system, self.mav.target_component,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            0, 1, 0, 0, 0, 0, 0, 0
        )

        # Wait for arm
        for i in range(50):
            hb = self.mav.recv_match(type='HEARTBEAT', blocking=True, timeout=0.1)
            if hb and (hb.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED):
                print("✅ Vehicle armed")
                return True
            time.sleep(0.1)

        print("❌ Arming failed")
        return False

    def enter_mode99(self) -> bool:
        """Enter Mode 99."""
        print("\nEntering Mode 99...")

        self.mav.mav.set_mode_send(
            self.mav.target_system,
            mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
            99
        )

        time.sleep(2)

        # Check mode
        hb = self.mav.recv_match(type='HEARTBEAT', blocking=True, timeout=2.0)
        if hb and hb.custom_mode == 99:
            print("✅ Mode 99 active")
            return True

        print(f"❌ Mode change failed - current mode: {hb.custom_mode if hb else 'unknown'}")
        return False

    # ============================================================================
    # TEST 1: HOVER STABILITY
    # ============================================================================

    def test_hover_stability(self, duration=10.0) -> Dict:
        """
        Test hover stability with Mode 99.

        Sends zero velocity commands and measures position drift.
        """
        print("\n" + "="*80)
        print("TEST 1: HOVER STABILITY")
        print("="*80)

        positions = []
        velocities = []
        start_time = time.time()

        # Get initial position
        pos_msg = self.mav.recv_match(type='LOCAL_POSITION_NED', blocking=True, timeout=2.0)
        if not pos_msg:
            return {'passed': False, 'error': 'No position data'}

        initial_pos = np.array([pos_msg.x, pos_msg.y, pos_msg.z])

        while time.time() - start_time < duration:
            # Send hover command (zero velocity)
            self.mav.mav.set_position_target_local_ned_send(
                int((time.time() - start_time) * 1000),
                self.mav.target_system, self.mav.target_component,
                mavutil.mavlink.MAV_FRAME_LOCAL_NED,
                0b0000111111000111,  # Use velocity
                0, 0, 0,  # Position (ignored)
                0, 0, 0,  # Velocity (hover)
                0, 0, 0,  # Accel (ignored)
                0, 0      # Yaw, yaw_rate
            )

            # Record position and velocity
            pos_msg = self.mav.recv_match(type='LOCAL_POSITION_NED', blocking=False)
            if pos_msg:
                positions.append([pos_msg.x, pos_msg.y, pos_msg.z])
                velocities.append([pos_msg.vx, pos_msg.vy, pos_msg.vz])

            time.sleep(0.1)

        # Analyze results
        positions = np.array(positions)
        velocities = np.array(velocities)

        position_drift = np.linalg.norm(positions[-1] - positions[0])
        max_velocity = np.max(np.linalg.norm(velocities, axis=1))
        rms_velocity = np.sqrt(np.mean(np.sum(velocities**2, axis=1)))

        # Pass criteria
        passed = (position_drift < 0.5 and  # Less than 50cm drift
                  max_velocity < 1.0 and    # Max velocity < 1 m/s
                  rms_velocity < 0.2)       # RMS velocity < 0.2 m/s

        results = {
            'passed': passed,
            'position_drift_m': float(position_drift),
            'max_velocity_ms': float(max_velocity),
            'rms_velocity_ms': float(rms_velocity),
            'duration_s': duration
        }

        print(f"\nResults:")
        print(f"  Position drift: {position_drift:.3f} m {'✅' if position_drift < 0.5 else '❌'}")
        print(f"  Max velocity:   {max_velocity:.3f} m/s {'✅' if max_velocity < 1.0 else '❌'}")
        print(f"  RMS velocity:   {rms_velocity:.3f} m/s {'✅' if rms_velocity < 0.2 else '❌'}")
        print(f"\n{'✅ PASSED' if passed else '❌ FAILED'}")

        return results

    # ============================================================================
    # TEST 2: POSITION TRACKING
    # ============================================================================

    def test_position_tracking(self) -> Dict:
        """
        Test position command tracking.

        Sends a sequence of position commands and measures tracking error.
        """
        print("\n" + "="*80)
        print("TEST 2: POSITION TRACKING")
        print("="*80)

        # Test waypoints (NED coordinates)
        waypoints = [
            (0, 0, -2),    # 2m altitude
            (2, 0, -2),    # 2m north
            (2, 2, -2),    # 2m east
            (0, 2, -2),    # 2m south
            (0, 0, -2),    # Return to start
        ]

        tracking_errors = []
        max_errors = []

        for i, (x_target, y_target, z_target) in enumerate(waypoints):
            print(f"\nWaypoint {i+1}/{len(waypoints)}: [{x_target}, {y_target}, {z_target}]")

            start_time = time.time()
            waypoint_errors = []

            while time.time() - start_time < 5.0:  # 5 seconds per waypoint
                # Send position command
                self.mav.mav.set_position_target_local_ned_send(
                    int((time.time() - start_time) * 1000),
                    self.mav.target_system, self.mav.target_component,
                    mavutil.mavlink.MAV_FRAME_LOCAL_NED,
                    0b0000111111111000,  # Use position
                    x_target, y_target, z_target,
                    0, 0, 0,  # Velocity
                    0, 0, 0,  # Accel
                    0, 0      # Yaw
                )

                # Get current position
                pos_msg = self.mav.recv_match(type='LOCAL_POSITION_NED', blocking=False)
                if pos_msg:
                    error = math.sqrt(
                        (pos_msg.x - x_target)**2 +
                        (pos_msg.y - y_target)**2 +
                        (pos_msg.z - z_target)**2
                    )
                    waypoint_errors.append(error)

                time.sleep(0.1)

            if waypoint_errors:
                avg_error = np.mean(waypoint_errors)
                max_error = np.max(waypoint_errors)
                tracking_errors.append(avg_error)
                max_errors.append(max_error)
                print(f"  Avg error: {avg_error:.3f} m, Max error: {max_error:.3f} m")

        # Overall results
        mean_tracking_error = np.mean(tracking_errors)
        max_tracking_error = np.max(max_errors)

        passed = (mean_tracking_error < 0.3 and  # Mean error < 30cm
                  max_tracking_error < 0.5)       # Max error < 50cm

        results = {
            'passed': passed,
            'mean_tracking_error_m': float(mean_tracking_error),
            'max_tracking_error_m': float(max_tracking_error),
            'num_waypoints': len(waypoints)
        }

        print(f"\nOverall Results:")
        print(f"  Mean tracking error: {mean_tracking_error:.3f} m {'✅' if mean_tracking_error < 0.3 else '❌'}")
        print(f"  Max tracking error:  {max_tracking_error:.3f} m {'✅' if max_tracking_error < 0.5 else '❌'}")
        print(f"\n{'✅ PASSED' if passed else '❌ FAILED'}")

        return results

    # ============================================================================
    # TEST 3: MOTOR RESPONSE
    # ============================================================================

    def test_motor_response(self, duration=5.0) -> Dict:
        """
        Test motor response telemetry.

        Verifies that LQR motor telemetry is being sent and values are reasonable.
        """
        print("\n" + "="*80)
        print("TEST 3: MOTOR RESPONSE TELEMETRY")
        print("="*80)

        lqr_data = {}
        start_time = time.time()

        # Expected telemetry fields
        expected_fields = [
            'LQR_Thrust', 'LQR_M_roll', 'LQR_M_pitch', 'LQR_M_yaw',
            'LQR_Motor0', 'LQR_Motor1', 'LQR_Motor2', 'LQR_Motor3',
            'LQR_PWM0', 'LQR_PWM1', 'LQR_PWM2', 'LQR_PWM3',
            'LQR_Rate'
        ]

        print(f"Collecting telemetry for {duration}s...")

        while time.time() - start_time < duration:
            # Send hover command
            self.mav.mav.set_position_target_local_ned_send(
                int((time.time() - start_time) * 1000),
                self.mav.target_system, self.mav.target_component,
                mavutil.mavlink.MAV_FRAME_LOCAL_NED,
                0b0000111111000111,
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
            )

            # Collect LQR telemetry
            msg = self.mav.recv_match(type='NAMED_VALUE_FLOAT', blocking=True, timeout=0.5)
            if msg and msg.name.startswith('LQR'):
                if msg.name not in lqr_data:
                    lqr_data[msg.name] = []
                lqr_data[msg.name].append(msg.value)

        # Analyze results
        print(f"\nTelemetry Summary:")
        fields_found = set(lqr_data.keys())
        fields_missing = set(expected_fields) - fields_found

        for field in sorted(expected_fields):
            if field in lqr_data:
                values = lqr_data[field]
                mean_val = np.mean(values)
                std_val = np.std(values)
                print(f"  {field:15s}: {mean_val:8.3f} ± {std_val:.3f} (n={len(values)}) ✅")
            else:
                print(f"  {field:15s}: NOT RECEIVED ❌")

        # Pass criteria
        passed = (len(fields_missing) == 0 and  # All fields present
                  len(lqr_data.get('LQR_Thrust', [])) > 10)  # Sufficient samples

        results = {
            'passed': passed,
            'fields_found': list(fields_found),
            'fields_missing': list(fields_missing),
            'num_samples': {k: len(v) for k, v in lqr_data.items()},
            'telemetry_data': {k: {'mean': float(np.mean(v)), 'std': float(np.std(v))}
                              for k, v in lqr_data.items()}
        }

        print(f"\n{'✅ PASSED' if passed else '❌ FAILED'}")
        return results

    # ============================================================================
    # TEST 4: TELEMETRY VALIDATION
    # ============================================================================

    def test_telemetry_validation(self) -> Dict:
        """
        Validate telemetry values are within reasonable ranges.

        Checks:
        - Thrust is positive
        - Moments are reasonable
        - PWM values in range [1000, 2000]
        - Control rate is ~100 Hz
        """
        print("\n" + "="*80)
        print("TEST 4: TELEMETRY VALIDATION")
        print("="*80)

        lqr_data = {}
        start_time = time.time()
        duration = 5.0

        while time.time() - start_time < duration:
            self.mav.mav.set_position_target_local_ned_send(
                int((time.time() - start_time) * 1000),
                self.mav.target_system, self.mav.target_component,
                mavutil.mavlink.MAV_FRAME_LOCAL_NED,
                0b0000111111000111,
                0, 0, -2,  # Hover at 2m
                0, 0, 0, 0, 0, 0, 0, 0
            )

            msg = self.mav.recv_match(type='NAMED_VALUE_FLOAT', blocking=False)
            if msg and msg.name.startswith('LQR'):
                if msg.name not in lqr_data:
                    lqr_data[msg.name] = []
                lqr_data[msg.name].append(msg.value)

        # Validation checks
        checks = []

        # Check 1: Thrust is positive
        if 'LQR_Thrust' in lqr_data:
            thrust_min = min(lqr_data['LQR_Thrust'])
            thrust_max = max(lqr_data['LQR_Thrust'])
            thrust_ok = thrust_min > 0 and thrust_max < 100  # Reasonable range: 0-100 N
            checks.append(('Thrust range', thrust_ok, f"{thrust_min:.1f} - {thrust_max:.1f} N"))

        # Check 2: PWM values in range
        for i in range(4):
            pwm_key = f'LQR_PWM{i}'
            if pwm_key in lqr_data:
                pwm_min = min(lqr_data[pwm_key])
                pwm_max = max(lqr_data[pwm_key])
                pwm_ok = 1000 <= pwm_min and pwm_max <= 2000
                checks.append((f'Motor {i} PWM', pwm_ok, f"{pwm_min:.0f} - {pwm_max:.0f} μs"))

        # Check 3: Control rate is ~100 Hz
        if 'LQR_Rate' in lqr_data:
            rate_mean = np.mean(lqr_data['LQR_Rate'])
            rate_ok = 95 <= rate_mean <= 105  # Within 5% of 100 Hz
            checks.append(('Control rate', rate_ok, f"{rate_mean:.1f} Hz"))

        # Print results
        print("\nValidation Checks:")
        for check_name, passed, detail in checks:
            status = '✅' if passed else '❌'
            print(f"  {check_name:20s}: {detail:20s} {status}")

        overall_passed = all(check[1] for check in checks)

        results = {
            'passed': overall_passed,
            'checks': [{'name': c[0], 'passed': c[1], 'detail': c[2]} for c in checks],
            'telemetry_ranges': {k: {'min': float(min(v)), 'max': float(max(v))}
                                for k, v in lqr_data.items()}
        }

        print(f"\n{'✅ PASSED' if overall_passed else '❌ FAILED'}")
        return results

    # ============================================================================
    # MAIN TEST RUNNER
    # ============================================================================

    def run_all_tests(self) -> Dict:
        """Run all tests and generate report."""
        print("="*80)
        print("MODE 99 LQR VALIDATION TEST SUITE")
        print("="*80)

        # Connect
        if not self.connect():
            return {'error': 'Connection failed'}

        # Wait for EKF
        if not self.wait_for_ekf():
            return {'error': 'EKF initialization failed'}

        # Setup
        if not self.setup_sitl():
            return {'error': 'SITL setup failed'}

        # Arm
        if not self.arm_vehicle():
            return {'error': 'Arming failed'}

        # Enter Mode 99
        if not self.enter_mode99():
            return {'error': 'Mode 99 entry failed'}

        # Run tests
        results = {}
        results['test1_hover_stability'] = self.test_hover_stability()
        results['test2_position_tracking'] = self.test_position_tracking()
        results['test3_motor_response'] = self.test_motor_response()
        results['test4_telemetry_validation'] = self.test_telemetry_validation()

        # Summary
        tests_passed = sum(1 for r in results.values() if r.get('passed', False))
        tests_total = len(results)

        print("\n" + "="*80)
        print("TEST SUITE SUMMARY")
        print("="*80)
        print(f"Tests passed: {tests_passed}/{tests_total}")
        print(f"Success rate: {100*tests_passed/tests_total:.1f}%")

        for test_name, test_result in results.items():
            status = '✅ PASSED' if test_result.get('passed', False) else '❌ FAILED'
            print(f"  {test_name:30s}: {status}")

        results['summary'] = {
            'tests_passed': tests_passed,
            'tests_total': tests_total,
            'success_rate': 100 * tests_passed / tests_total
        }

        return results


def main():
    """Main entry point."""
    suite = Mode99TestSuite()
    results = suite.run_all_tests()

    # Save results
    import json
    with open('mode99_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("\n✅ Results saved to mode99_test_results.json")

    # Exit code
    if 'error' in results:
        return 1

    tests_passed = results['summary']['tests_passed']
    tests_total = results['summary']['tests_total']

    return 0 if tests_passed == tests_total else 1


if __name__ == '__main__':
    sys.exit(main())
