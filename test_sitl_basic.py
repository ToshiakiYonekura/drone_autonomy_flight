#!/usr/bin/env python3
"""
Basic SITL connection test - no mode changes, just connect
"""

import time
from pymavlink import mavutil

print("Connecting to SITL...")
master = mavutil.mavlink_connection('tcp:127.0.0.1:5760', source_system=255)

print("Waiting for heartbeat...")
heartbeat = master.wait_heartbeat(timeout=10.0)
if heartbeat:
    print(f"✅ Connected to system {master.target_system}")
else:
    print("❌ No heartbeat")
    exit(1)

print("\nListening for messages for 10 seconds...")
start = time.time()
while time.time() - start < 10:
    msg = master.recv_match(blocking=False)
    if msg:
        msg_type = msg.get_type()
        if msg_type in ['HEARTBEAT', 'SYS_STATUS', 'STATUSTEXT']:
            print(f"  {msg_type}: {msg}")
    time.sleep(0.1)

print("\n✅ Test complete - SITL didn't crash!")
master.close()
