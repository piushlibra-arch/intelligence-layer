#!/usr/bin/env bash
# =============================================================================
# EC2 Instance Setup Script
# Run this once on a fresh Ubuntu 22.04/24.04 LTS EC2 instance
# =============================================================================
set -euo pipefail

echo "=== Setting up EC2 for Adaptive Trader Risk Intelligence ==="

# Update system
echo "1. Updating system packages..."
sudo apt-get update -y
sudo apt-get upgrade -y

# Install Docker
echo "2. Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker "${USER}"
    echo "Docker installed. You may need to log out and back in for group changes."
else
    echo "Docker already installed: $(docker --version)"
fi

# Install Docker Compose plugin
echo "3. Checking Docker Compose..."
if docker compose version &> /dev/null; then
    echo "Docker Compose already available: $(docker compose version)"
else
    sudo apt-get install -y docker-compose-plugin
fi

# Install useful tools
echo "4. Installing utilities..."
sudo apt-get install -y \
    curl \
    wget \
    jq \
    htop \
    unzip \
    fail2ban

# Configure firewall (if ufw available)
echo "5. Configuring firewall..."
if command -v ufw &> /dev/null; then
    sudo ufw allow 22/tcp   # SSH
    sudo ufw allow 80/tcp   # HTTP
    sudo ufw allow 443/tcp  # HTTPS
    sudo ufw --force enable
    echo "UFW configured."
fi

# Configure fail2ban
echo "6. Configuring fail2ban..."
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Create application directory
echo "7. Creating application directory..."
sudo mkdir -p /opt/trader-risk-intelligence
sudo chown "${USER}:${USER}" /opt/trader-risk-intelligence

# Configure Docker log rotation
echo "8. Configuring Docker log rotation..."
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    }
}
EOF
sudo systemctl restart docker

echo ""
echo "=== EC2 Setup Complete ==="
echo "Next steps:"
echo "  1. Copy .env.example to /opt/trader-risk-intelligence/.env"
echo "  2. Edit .env with production values"
echo "  3. Run deploy/deploy-ec2.sh from your local machine"
