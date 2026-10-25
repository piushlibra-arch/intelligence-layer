#!/usr/bin/env bash
# =============================================================================
# Adaptive Trader Risk Intelligence — EC2 Deployment Script
# =============================================================================
# Prerequisites:
#   - SSH access to EC2 instance
#   - Docker and Docker Compose installed on instance
#   - Security group allows ports 80, 443
#   - .env file prepared with production values
# =============================================================================
set -euo pipefail

# Configuration
EC2_HOST="${EC2_HOST:?Set EC2_HOST environment variable}"
EC2_USER="${EC2_USER:-ubuntu}"
SSH_KEY="${SSH_KEY:-~/.ssh/id_rsa}"
DEPLOY_DIR="/opt/trader-risk-intelligence"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=== Adaptive Trader Risk Intelligence Deployment ==="
echo "Target: ${EC2_USER}@${EC2_HOST}"
echo "Deploy dir: ${DEPLOY_DIR}"
echo ""

# Check SSH connectivity
echo "1. Testing SSH connectivity..."
ssh -i "${SSH_KEY}" -o ConnectTimeout=10 "${EC2_USER}@${EC2_HOST}" "echo 'SSH OK'" || {
    echo "ERROR: Cannot SSH to ${EC2_HOST}. Check SSH_KEY and security group."
    exit 1
}

# Check Docker on remote
echo "2. Checking Docker on remote..."
ssh -i "${SSH_KEY}" "${EC2_USER}@${EC2_HOST}" "docker --version && docker compose version" || {
    echo "ERROR: Docker not installed on remote. Run deploy/setup-ec2.sh first."
    exit 1
}

# Create deployment directory
echo "3. Creating deployment directory..."
ssh -i "${SSH_KEY}" "${EC2_USER}@${EC2_HOST}" "sudo mkdir -p ${DEPLOY_DIR} && sudo chown ${EC2_USER}:${EC2_USER} ${DEPLOY_DIR}"

# Sync project files (excluding node_modules, venv, git, etc.)
echo "4. Syncing project files..."
rsync -avz --delete \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='.venv' \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='.env' \
    --exclude='pgdata' \
    --exclude='.hypothesis' \
    --exclude='.pytest_cache' \
    --exclude='frontend/dist' \
    -e "ssh -i ${SSH_KEY}" \
    "${PROJECT_DIR}/" \
    "${EC2_USER}@${EC2_HOST}:${DEPLOY_DIR}/"

# Check .env exists on remote
echo "5. Checking .env configuration..."
ssh -i "${SSH_KEY}" "${EC2_USER}@${EC2_HOST}" "test -f ${DEPLOY_DIR}/.env" || {
    echo "WARNING: No .env file on remote. Copying .env.example..."
    scp -i "${SSH_KEY}" "${PROJECT_DIR}/.env.example" "${EC2_USER}@${EC2_HOST}:${DEPLOY_DIR}/.env"
    echo "IMPORTANT: Edit ${DEPLOY_DIR}/.env on the server with production values before continuing."
    echo "  ssh -i ${SSH_KEY} ${EC2_USER}@${EC2_HOST} 'nano ${DEPLOY_DIR}/.env'"
    exit 1
}

# Build and deploy
echo "6. Building Docker images..."
ssh -i "${SSH_KEY}" "${EC2_USER}@${EC2_HOST}" "cd ${DEPLOY_DIR} && docker compose build --no-cache"

# Run migrations
echo "7. Running database migrations..."
ssh -i "${SSH_KEY}" "${EC2_USER}@${EC2_HOST}" "cd ${DEPLOY_DIR} && docker compose run --rm migrate"

# Start services
echo "8. Starting services..."
ssh -i "${SSH_KEY}" "${EC2_USER}@${EC2_HOST}" "cd ${DEPLOY_DIR} && docker compose up -d backend frontend db"

# Wait for health checks
echo "9. Waiting for services to be healthy..."
sleep 10
ssh -i "${SSH_KEY}" "${EC2_USER}@${EC2_HOST}" "cd ${DEPLOY_DIR} && docker compose ps"

# Verify health
echo "10. Verifying application health..."
ssh -i "${SSH_KEY}" "${EC2_USER}@${EC2_HOST}" "curl -sf http://localhost:8000/api/v1/health || echo 'Backend health check failed'"
ssh -i "${SSH_KEY}" "${EC2_USER}@${EC2_HOST}" "curl -sf http://localhost/nginx-health || echo 'Frontend health check failed'"

echo ""
echo "=== Deployment Complete ==="
echo "Application URL: http://${EC2_HOST}"
echo "API Docs: http://${EC2_HOST}/docs"
echo ""
echo "Useful commands:"
echo "  View logs:    ssh -i ${SSH_KEY} ${EC2_USER}@${EC2_HOST} 'cd ${DEPLOY_DIR} && docker compose logs -f'"
echo "  Restart:      ssh -i ${SSH_KEY} ${EC2_USER}@${EC2_HOST} 'cd ${DEPLOY_DIR} && docker compose restart'"
echo "  Stop:         ssh -i ${SSH_KEY} ${EC2_USER}@${EC2_HOST} 'cd ${DEPLOY_DIR} && docker compose down'"
echo "  DB backup:    ssh -i ${SSH_KEY} ${EC2_USER}@${EC2_HOST} 'cd ${DEPLOY_DIR} && docker compose exec db pg_dump -U trader_risk trader_risk_intel > backup.sql'"
