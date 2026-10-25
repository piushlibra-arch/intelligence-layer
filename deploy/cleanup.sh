#!/usr/bin/env bash
# =============================================================================
# Cleanup Script — Remove AWS resources created by this project
# =============================================================================
set -euo pipefail

EC2_HOST="${EC2_HOST:?Set EC2_HOST}"
EC2_USER="${EC2_USER:-ubuntu}"
SSH_KEY="${SSH_KEY:-~/.ssh/id_rsa}"
DEPLOY_DIR="/opt/trader-risk-intelligence"

echo "=== Cleanup: Adaptive Trader Risk Intelligence ==="
echo ""
echo "This will:"
echo "  1. Stop all Docker containers"
echo "  2. Remove Docker volumes (including database data)"
echo "  3. Remove project files from the server"
echo ""
read -p "Are you sure? (type 'yes' to confirm): " confirm
if [[ "${confirm}" != "yes" ]]; then
    echo "Aborted."
    exit 0
fi

echo "1. Stopping containers..."
ssh -i "${SSH_KEY}" "${EC2_USER}@${EC2_HOST}" \
    "cd ${DEPLOY_DIR} 2>/dev/null && docker compose down -v || echo 'No running containers'"

echo "2. Removing project files..."
ssh -i "${SSH_KEY}" "${EC2_USER}@${EC2_HOST}" \
    "sudo rm -rf ${DEPLOY_DIR}"

echo "3. Pruning unused Docker resources..."
ssh -i "${SSH_KEY}" "${EC2_USER}@${EC2_HOST}" \
    "docker system prune -af --volumes || true"

echo ""
echo "=== Cleanup Complete ==="
echo ""
echo "If you created an EC2 instance for this project, terminate it manually:"
echo "  aws ec2 terminate-instances --instance-ids <INSTANCE_ID>"
echo ""
echo "Check for any remaining resources:"
echo "  - EC2 instances"
echo "  - Security groups (named trader-risk-*)"
echo "  - EBS volumes"
echo "  - Elastic IPs"
