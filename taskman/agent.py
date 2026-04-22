#!/usr/bin/env python3
"""
agent.py — Windows Process Agent
Runs on each Windows machine. Reports processes to your Pi server.
Also receives and executes kill commands from the Pi.

Install:  pip install psutil requests
Run:      python agent.py
"""

import os
import sys
import time
import socket
import hashlib
import platform
import requests
import psutil

# ── CONFIG ────────────────────────────────────────────────────────────────────
# Your Pi's Cloudflare tunnel URL
PI_URL = "https://controlapi.myleskerschner.com"

# Human-readable name for this device (shows in the dashboard)
DEVICE_NAME = socket.gethostname()

# Must match what's in pi_server.py — SHA256 of your password
AGENT_SECRET = hashlib.sha256("ehs508".encode()).hexdigest()

# How often to report (seconds)
INTERVAL    = 5
# ─────────────────────────────────────────────────────────────────────────────

DEVICE_ID = socket.gethostname().lower().replace(" ", "-")
HEADERS   = {
    "Content-Type":    "application/json",
    "X-Agent-Secret":  AGENT_SECRET
}


def get_processes():
    """Return a list of running processes with CPU/memory info."""
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_info', 'status']):
        try:
            info = p.info
            mem_bytes = info['memory_info'].rss if info['memory_info'] else 0
            procs.append({
                "pid":    info['pid'],
                "name":   info['name'] or "Unknown",
                "user":   (info['username'] or "").split("\\")[-1],  # strip domain
                "cpu":    round(info['cpu_percent'] or 0.0, 1),
                "mem_mb": round(mem_bytes / 1024 / 1024, 1),
                "status": info['status'] or "running"
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return procs


def get_system_stats():
    """CPU and memory totals."""
    mem = psutil.virtual_memory()
    return {
        "cpu_total":   psutil.cpu_percent(interval=None),
        "mem_used_gb": round(mem.used / 1024**3, 2)
    }


def kill_pid(pid):
    """Kill a process by PID."""
    try:
        p = psutil.Process(pid)
        name = p.name()
        p.terminate()
        time.sleep(0.5)
        if p.is_running():
            p.kill()
        print(f"[KILL] Killed {name} (PID {pid})")
        return True
    except psutil.NoSuchProcess:
        print(f"[KILL] PID {pid} already gone")
        return True
    except psutil.AccessDenied:
        print(f"[KILL] Access denied for PID {pid} — try running agent as Administrator")
        return False


def report():
    """Send process list to Pi, handle any kill commands returned."""
    procs  = get_processes()
    stats  = get_system_stats()
    payload = {
        "device_id": DEVICE_ID,
        "name":      DEVICE_NAME,
        "os":        f"Windows {platform.version()}",
        "processes": procs,
        **stats
    }
    try:
        res = requests.post(
            PI_URL + "/agent/report",
            json=payload,
            headers=HEADERS,
            timeout=8
        )
        if res.status_code == 200:
            data = res.json()
            for kill in data.get("pending_kills", []):
                kill_pid(kill["pid"])
        elif res.status_code == 401:
            print("[ERROR] Authentication failed. Check AGENT_SECRET.")
        else:
            print(f"[WARN] Server returned {res.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"[WARN] Can't reach {PI_URL} — will retry")
    except Exception as e:
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    print(f"[START] Agent running on {DEVICE_NAME} ({DEVICE_ID})")
    print(f"[START] Reporting to {PI_URL} every {INTERVAL}s")
    # Warm up CPU percent (first call always returns 0.0)
    psutil.cpu_percent(interval=1)
    while True:
        report()
        time.sleep(INTERVAL)
