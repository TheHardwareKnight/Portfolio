# Control Panel — Setup Guide

## Architecture
```
Windows PC (agent.py) ──POST every 5s──► Pi Flask Server (pi_server.py)
                                                 │
                          Cloudflare Tunnel ◄────┘
                                 │
                    myleskerschner.com/control (control.html)
```

---

## 1. Pi Server Setup

Copy `pi_server.py` and `setup_pi.sh` to your Pi, then:

```bash
chmod +x setup_pi.sh
./setup_pi.sh
```

This installs Flask, creates a systemd service, and starts the server on port 8080.

**Default login:** `admin` / `ehs508`
To change or add users, edit `~/login/users.json` (passwords are SHA-256 hashed):
```bash
python3 -c "import hashlib; print(hashlib.sha256('yourpassword'.encode()).hexdigest())"
```

---

## 2. Cloudflare Tunnel

Point your tunnel at the Pi's Flask server:

```bash
# In your cloudflared config.yml
ingress:
  - hostname: api.myleskerschner.com
    service: http://localhost:8080
  - service: http_status:404
```

Then add a DNS record:
- Type: `CNAME`, Name: `api`, Target: your tunnel ID, Proxied: ✅

---

## 3. control.html → Your GitHub Repo

1. Drop `control.html` into the root of your portfolio repo
2. Open `control.html` and confirm the API URL at the top:
   ```js
   const API = 'https://api.myleskerschner.com';
   ```
3. Push to GitHub — Cloudflare Pages deploys it automatically
4. Visit `https://myleskerschner.com/control`

---

## 4. Windows Agent Setup

On each Windows machine:

1. Copy `agent.py` and `install_agent.bat`
2. Open `agent.py` and set `DEVICE_NAME` to something friendly (e.g. `"Gaming PC"`)
3. Run `install_agent.bat` as Administrator (installs deps + adds to startup)
4. Or just run manually: `python agent.py`

---

## Log Files

Login events are stored on the Pi at `~/login/YYYY-MM-DD.log`
Logs older than 7 days are automatically deleted.

```
cat ~/login/2026-04-22.log
# 14:32:01  admin                LOGIN_OK             192.168.1.50
# 14:35:10  admin                KILL                 device=gaming-pc pid=1234 name=chrome.exe
```
