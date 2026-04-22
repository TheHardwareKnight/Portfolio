#!/bin/bash
# setup_pi.sh — Run once on your Pi to install and start the server

echo "Installing dependencies..."
pip3 install flask flask-cors

echo ""
echo "Setting up systemd service so server starts on boot..."

SERVICE_FILE="/etc/systemd/system/ctrl-panel.service"
SCRIPT_PATH="$(realpath pi_server.py)"
PYTHON_PATH="$(which python3)"

sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Control Panel API
After=network.target

[Service]
ExecStart=$PYTHON_PATH $SCRIPT_PATH
WorkingDirectory=$(dirname $SCRIPT_PATH)
Restart=always
User=$USER
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ctrl-panel
sudo systemctl start ctrl-panel

echo ""
echo "Done! Server is running on port 8080."
echo "Status: sudo systemctl status ctrl-panel"
echo "Logs:   sudo journalctl -u ctrl-panel -f"
