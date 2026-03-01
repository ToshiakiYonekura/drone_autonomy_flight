#!/usr/bin/env python3
"""
SITL Manager - Automated SITL lifecycle management

Handles starting, stopping, and monitoring ArduPilot SITL with proper
physics simulation for automated testing.
"""

import subprocess
import time
import signal
import sys
import os
from pathlib import Path
from pymavlink import mavutil


class SITLManager:
    """Manages ArduPilot SITL lifecycle."""

    def __init__(self, ardupilot_dir=None):
        """Initialize SITL manager."""
        if ardupilot_dir is None:
            ardupilot_dir = Path.home() / "ardupilot"
        self.ardupilot_dir = Path(ardupilot_dir)
        self.copter_dir = self.ardupilot_dir / "ArduCopter"
        self.sitl_process = None
        self.mavlink_conn = None

    def cleanup_old_processes(self):
        """Kill any existing SITL processes."""
        print("Cleaning up old SITL processes...")
        subprocess.run("pkill -9 -f arducopter 2>/dev/null || true", shell=True)
        subprocess.run("pkill -9 -f sim_vehicle 2>/dev/null || true", shell=True)
        subprocess.run("pkill -9 -f MAVProxy 2>/dev/null || true", shell=True)
        time.sleep(2)
        print("✅ Cleanup complete")

    def cleanup_old_files(self):
        """Remove old SITL artifacts."""
        print("Cleaning up old files...")
        os.chdir(self.copter_dir)
        for pattern in ['eeprom.bin', 'mav.tlog*', 'logs/*.BIN']:
            subprocess.run(f"rm -f {pattern} 2>/dev/null || true", shell=True)
        print("✅ Files cleaned")

    def start_sitl(self, wait_for_ekf=True, timeout=60):
        """
        Start SITL with physics simulator.

        Args:
            wait_for_ekf: Wait for EKF to initialize
            timeout: Maximum wait time for EKF (seconds)

        Returns:
            True if SITL started successfully, False otherwise
        """
        print("\n" + "="*70)
        print("Starting ArduPilot SITL")
        print("="*70)

        # Clean up first
        self.cleanup_old_processes()
        self.cleanup_old_files()

        # Change to ArduCopter directory
        os.chdir(self.copter_dir)

        # Start sim_vehicle.py
        print("\nStarting SITL...")
        cmd = [
            str(self.ardupilot_dir / "Tools" / "autotest" / "sim_vehicle.py"),
            "-v", "ArduCopter",
            "--no-mavproxy",  # No MAVProxy for automated testing
            "--out=127.0.0.1:14550",  # MAVLink output port
        ]

        # Start process with output redirected
        log_file = open('/tmp/sitl_manager.log', 'w')
        self.sitl_process = subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            cwd=self.copter_dir
        )

        print(f"✅ SITL process started (PID: {self.sitl_process.pid})")
        print("   Log: /tmp/sitl_manager.log")

        # Wait for SITL to be ready
        print("\nWaiting for SITL to initialize...")
        time.sleep(15)  # Give SITL time to start

        # Try to connect
        print("\nConnecting to SITL...")
        try:
            self.mavlink_conn = mavutil.mavlink_connection(
                'tcp:127.0.0.1:5760',
                source_system=255,
                timeout=10
            )
            self.mavlink_conn.wait_heartbeat(timeout=10)
            print(f"✅ Connected to system {self.mavlink_conn.target_system}")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            self.stop_sitl()
            return False

        if wait_for_ekf:
            print("\nWaiting for EKF to initialize...")
            if not self.wait_for_ekf(timeout=timeout):
                print("❌ EKF initialization timeout")
                self.stop_sitl()
                return False
            print("✅ EKF initialized")

        print("\n" + "="*70)
        print("✅ SITL READY FOR TESTING")
        print("="*70)
        return True

    def wait_for_ekf(self, timeout=60):
        """
        Wait for EKF to initialize and provide position data.

        Returns:
            True if EKF initialized, False if timeout
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            # Check for position data
            msg = self.mavlink_conn.recv_match(
                type='LOCAL_POSITION_NED',
                blocking=True,
                timeout=1.0
            )

            if msg:
                # Got position data - EKF is working
                print(f"   Position: [{msg.x:.2f}, {msg.y:.2f}, {msg.z:.2f}] m")
                return True

            # Also check GPS
            gps = self.mavlink_conn.recv_match(
                type='GPS_RAW_INT',
                blocking=False
            )
            if gps and gps.satellites_visible > 0:
                print(f"   GPS: {gps.satellites_visible} sats, fix={gps.fix_type}")

            time.sleep(1)

        return False

    def stop_sitl(self):
        """Stop SITL process."""
        print("\nStopping SITL...")

        if self.mavlink_conn:
            self.mavlink_conn.close()
            self.mavlink_conn = None

        if self.sitl_process:
            try:
                self.sitl_process.terminate()
                self.sitl_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.sitl_process.kill()
                self.sitl_process.wait()
            finally:
                self.sitl_process = None

        # Extra cleanup
        self.cleanup_old_processes()
        print("✅ SITL stopped")

    def is_running(self):
        """Check if SITL is running."""
        if self.sitl_process is None:
            return False
        return self.sitl_process.poll() is None

    def get_connection(self):
        """Get MAVLink connection."""
        return self.mavlink_conn

    def __enter__(self):
        """Context manager entry."""
        self.start_sitl()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_sitl()


def main():
    """Test the SITL manager."""
    print("SITL Manager Test")
    print("="*70)

    manager = SITLManager()

    # Set up signal handler for clean shutdown
    def signal_handler(sig, frame):
        print("\n\nShutdown requested...")
        manager.stop_sitl()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # Start SITL
    if not manager.start_sitl():
        print("❌ SITL startup failed")
        return 1

    # Keep running
    print("\nSITL is running. Press Ctrl+C to stop.")
    print("You can now run your tests in another terminal.")
    print("")

    try:
        while manager.is_running():
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        manager.stop_sitl()

    return 0


if __name__ == '__main__':
    sys.exit(main())
