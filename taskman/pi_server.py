#!/usr/bin/env python3
"""
pi_server.py — Control Panel API Server
Run on your Raspberry Pi. Exposes an API that control.html talks to.

Install deps:  pip3 install flask flask-cors
Run:           python3 pi_server.py
"""

import os
import json
import time
import secrets
import hashlib
import datetime
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["https://myleskerschner.com", "http://localhost"])

# ── CONFIG ────────────────────────────────────────────────────────────────────
LOG_DIR   = Path.home() / "login"          # ~/login/
LOG_KEEP  = 7                              # days to keep logs
PORT      = 8080
# ─────────────────────────────────────────────────────────────────────────────

LOG_DIR.mkdir(exist_ok=True)

# In-memory state
devices   = {}    # { device_id: { name, os, processes, last_seen, cpu_total, mem_used_gb } }
tokens    = {}    # { token: { username, expires } }


# ── HELPERS ──────────────────────────────────────────────────────────────────

def load_users():
    """Load users from ~/login/users.json. Create default if missing."""
    users_file = LOG_DIR / "users.json"
    if not users_file.exists():
        # Default user: admin / ehs508
        default = {
            "admin": hashlib.sha256("ehs508".encode()).hexdigest()
        }
        users_file.write_text(json.dumps(default, indent=2))
        print(f"[INIT] Created default user 'admin'. Edit {users_file} to change.")
    return json.loads(users_file.read_text())


def log_event(username, event, detail=""):
    """Append a line to today's log file."""
    today = datetime.date.today().isoformat()
    log_file = LOG_DIR / f"{today}.log"
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    line = f"{ts}  {username:<20} {event:<20} {detail}\n"
    with open(log_file, "a") as f:
        f.write(line)
    purge_old_logs()


def purge_old_logs():
    """Delete log files older than LOG_KEEP days."""
    cutoff = datetime.date.today() - datetime.timedelta(days=LOG_KEEP)
    for f in LOG_DIR.glob("*.log"):
        try:
            date = datetime.date.fromisoformat(f.stem)
            if date < cutoff:
                f.unlink()
        except ValueError:
            pass


def check_token(req):
    """Return username if token is valid, else None."""
    auth = req.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:]
    entry = tokens.get(token)
    if not entry:
        return None
    if time.time() > entry["expires"]:
        del tokens[token]
        return None
    return entry["username"]


def require_auth(f):
    """Decorator that returns 401 if not authenticated."""
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = check_token(request)
        if not user:
            return jsonify({"error": "Unauthorized"}), 401
        request.username = user
        return f(*args, **kwargs)
    return wrapper


# ── AUTH ROUTES ───────────────────────────────────────────────────────────────

@app.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    username = (data.get("username") or "").strip().lower()
    password = data.get("password") or ""

    users = load_users()
    pw_hash = hashlib.sha256(password.encode()).hexdigest()

    if users.get(username) != pw_hash:
        log_event(username, "LOGIN_FAIL", request.remote_addr)
        return jsonify({"error": "Invalid username or password."}), 401

    token = secrets.token_hex(32)
    tokens[token] = {
        "username": username,
        "expires": time.time() + 86400  # 24 hours
    }
    log_event(username, "LOGIN_OK", request.remote_addr)
    return jsonify({"token": token, "username": username})


@app.route("/auth/logout", methods=["POST"])
@require_auth
def logout():
    auth = request.headers.get("Authorization", "")[7:]
    tokens.pop(auth, None)
    log_event(request.username, "LOGOUT")
    return jsonify({"ok": True})


# ── DEVICE ROUTES ─────────────────────────────────────────────────────────────

@app.route("/devices", methods=["GET"])
@require_auth
def list_devices():
    now = time.time()
    result = []
    for dev_id, d in devices.items():
        age = now - d.get("last_seen", 0)
        online = age < 15  # offline if no ping in 15s
        last_seen_str = "—"
        if not online and d.get("last_seen"):
            dt = datetime.datetime.fromtimestamp(d["last_seen"])
            last_seen_str = dt.strftime("%H:%M:%S")
        result.append({
            "id":            dev_id,
            "name":          d.get("name", dev_id),
            "os":            d.get("os", "Unknown"),
            "online":        online,
            "last_seen":     last_seen_str,
            "cpu_total":     round(d.get("cpu_total", 0), 1),
            "mem_used_gb":   round(d.get("mem_used_gb", 0), 2),
            "process_count": len(d.get("processes", []))
        })
    result.sort(key=lambda x: (not x["online"], x["name"]))
    return jsonify(result)


@app.route("/devices/<device_id>/processes", methods=["GET"])
@require_auth
def get_processes(device_id):
    dev = devices.get(device_id)
    if not dev:
        return jsonify({"error": "Device not found"}), 404
    return jsonify(dev.get("processes", []))


@app.route("/devices/<device_id>/kill", methods=["POST"])
@require_auth
def kill_process(device_id):
    dev = devices.get(device_id)
    if not dev:
        return jsonify({"error": "Device not found"}), 404

    data = request.get_json()
    pid = data.get("pid")
    if not pid:
        return jsonify({"error": "No PID provided"}), 400

    # Store kill request — agent polls for this
    if "pending_kills" not in dev:
        dev["pending_kills"] = []
    dev["pending_kills"].append({"pid": pid, "requested_at": time.time()})

    # Find process name for logging
    proc_name = next((p["name"] for p in dev.get("processes", []) if p["pid"] == pid), str(pid))
    log_event(request.username, "KILL", f"device={device_id} pid={pid} name={proc_name}")
    return jsonify({"ok": True})


# ── AGENT ROUTES (called by agent.py on each device) ─────────────────────────

@app.route("/agent/report", methods=["POST"])
def agent_report():
    """Windows agent POSTs its process list here every few seconds."""
    # Agents authenticate with a shared secret in the header
    secret = request.headers.get("X-Agent-Secret", "")
    expected = hashlib.sha256("ehs508".encode()).hexdigest()
    if secret != expected:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    device_id = data.get("device_id")
    if not device_id:
        return jsonify({"error": "No device_id"}), 400

    devices[device_id] = {
        "name":        data.get("name", device_id),
        "os":          data.get("os", "Windows"),
        "processes":   data.get("processes", []),
        "cpu_total":   data.get("cpu_total", 0),
        "mem_used_gb": data.get("mem_used_gb", 0),
        "last_seen":   time.time(),
        "pending_kills": devices.get(device_id, {}).get("pending_kills", [])
    }
    # Return any pending kill commands and clear them
    kills = devices[device_id].pop("pending_kills", [])
    # Clean up stale kill requests (older than 30s)
    kills = [k for k in kills if time.time() - k["requested_at"] < 30]
    return jsonify({"pending_kills": kills})


# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"[START] Control Panel API on port {PORT}")
    print(f"[START] Logs: {LOG_DIR}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
