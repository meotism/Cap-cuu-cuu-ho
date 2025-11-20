#!/bin/bash

# SOS Emergency Map Server - Systemd Service Installer

SERVICE_NAME="sos-emergency-server"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
WORK_DIR=$(pwd)
VENV_PYTHON="${WORK_DIR}/venv/bin/python3"

echo "=========================================="
echo "🔧 Installing SOS Emergency Server Service"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Get the current user
ACTUAL_USER=${SUDO_USER:-$USER}
ACTUAL_GROUP=$(id -gn $ACTUAL_USER)

echo "Configuration:"
echo "  Service: $SERVICE_NAME"
echo "  User: $ACTUAL_USER"
echo "  Group: $ACTUAL_GROUP"
echo "  Directory: $WORK_DIR"
echo ""

# Create systemd service file
cat > $SERVICE_FILE << EOF
[Unit]
Description=SOS Emergency Map Server
After=network.target

[Service]
Type=simple
User=$ACTUAL_USER
Group=$ACTUAL_GROUP
WorkingDirectory=$WORK_DIR
Environment="PATH=$WORK_DIR/venv/bin"
ExecStart=$VENV_PYTHON $WORK_DIR/map_server.py
Restart=always
RestartSec=10

# Logging
StandardOutput=append:/var/log/${SERVICE_NAME}.log
StandardError=append:/var/log/${SERVICE_NAME}.error.log

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Service file created: $SERVICE_FILE"

# Create log files
touch /var/log/${SERVICE_NAME}.log
touch /var/log/${SERVICE_NAME}.error.log
chown $ACTUAL_USER:$ACTUAL_GROUP /var/log/${SERVICE_NAME}.log
chown $ACTUAL_USER:$ACTUAL_GROUP /var/log/${SERVICE_NAME}.error.log

echo "✅ Log files created"

# Reload systemd
systemctl daemon-reload
echo "✅ Systemd reloaded"

echo ""
echo "=========================================="
echo "✅ Installation Complete!"
echo "=========================================="
echo ""
echo "Usage commands:"
echo "  Start:   sudo systemctl start $SERVICE_NAME"
echo "  Stop:    sudo systemctl stop $SERVICE_NAME"
echo "  Restart: sudo systemctl restart $SERVICE_NAME"
echo "  Status:  sudo systemctl status $SERVICE_NAME"
echo "  Enable:  sudo systemctl enable $SERVICE_NAME  (auto-start on boot)"
echo "  Logs:    sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "Start the service now? (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    systemctl start $SERVICE_NAME
    systemctl enable $SERVICE_NAME
    echo ""
    echo "✅ Service started and enabled!"
    echo ""
    systemctl status $SERVICE_NAME
fi
