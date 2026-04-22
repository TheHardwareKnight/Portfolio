# Control Panel — Setup Guide

## 1. Add to your GitHub repo
Drop this entire `control/` folder into the root of your portfolio repo and push it.

## 2. Create a KV namespace in Cloudflare
- Cloudflare Dashboard → Workers & Pages → KV → Create namespace
- Name it: `CONTROL_KV`
- Copy the **namespace ID**

## 3. Update wrangler.toml
Replace `YOUR_NAMESPACE_ID_HERE` with the ID you just copied.

## 4. Deploy the Worker
```bash
cd control
npx wrangler deploy
```
Wrangler will ask you to log in to Cloudflare the first time.

## 5. Add DNS record in Cloudflare
- Dashboard → your domain → DNS → Add record
- Type: `CNAME`
- Name: `control`
- Target: `control-panel.<your-account>.workers.dev`
- Proxied: ✅ Yes

---

## Sending data from your Pi

### Get your token (run this once on any machine)
```bash
echo -n "ehs508" | sha256sum
```
Copy the hash — that's your `X-Pi-Token`.

### Test it manually
```bash
curl -X POST https://control.myleskerschner.com/ingest \
  -H "Content-Type: application/json" \
  -H "X-Pi-Token: YOUR_HASH_HERE" \
  -d '{"temperature": "45.2C", "uptime": "2 days"}'
```

### Auto-sender script for the Pi
Save this as `/home/pi/send_stats.sh`:
```bash
#!/bin/bash
TOKEN="YOUR_HASH_HERE"
TEMP=$(vcgencmd measure_temp | grep -o '[0-9.]*')
UPTIME=$(uptime -p)
CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
MEM=$(free -m | awk 'NR==2{printf "%.0f%%", $3*100/$2}')

curl -s -X POST https://control.myleskerschner.com/ingest \
  -H "Content-Type: application/json" \
  -H "X-Pi-Token: $TOKEN" \
  -d "{\"temperature\":\"${TEMP}C\",\"uptime\":\"${UPTIME}\",\"cpu\":\"${CPU}%\",\"memory\":\"${MEM}\"}"
```

Make it executable and add to crontab:
```bash
chmod +x /home/pi/send_stats.sh

# Run every minute
crontab -e
# Add this line:
* * * * * /home/pi/send_stats.sh
```

---

## Login
Visit `https://control.myleskerschner.com` and enter your password.
