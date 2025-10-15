#!/bin/bash

# Exercise 3: Tailscale Funnel Script
# This script helps you set up a Tailscale funnel to expose your local application

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Generate random endpoint path (20 characters)
RANDOM_PATH=$(openssl rand -hex 10)

# Configuration
PORT=8501  # Streamlit default port
SERVICE_NAME="speakger-dashboard"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Tailscale Funnel Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Tailscale is installed
if ! command -v tailscale &> /dev/null; then
    echo -e "${RED}ERROR: Tailscale is not installed!${NC}"
    echo ""
    echo "Please install Tailscale first:"
    echo "  macOS:   brew install tailscale"
    echo "  Linux:   curl -fsSL https://tailscale.com/install.sh | sh"
    echo "  Windows: Download from https://tailscale.com/download"
    echo ""
    exit 1
fi

# Check if logged in to Tailscale
if ! tailscale status &> /dev/null; then
    echo -e "${YELLOW}WARNING: Not logged in to Tailscale${NC}"
    echo ""
    echo "Please log in first:"
    echo "  tailscale up"
    echo ""
    exit 1
fi

# Get tailnet name properly
DEVICE_DNS=$(tailscale status --json | python3 -c "import sys, json; print(json.load(sys.stdin)['Self']['DNSName'])")
DEVICE_NAME=$(echo "$DEVICE_DNS" | cut -d'.' -f1)
TAILNET_NAME=$(echo "$DEVICE_DNS" | cut -d'.' -f2-)

echo -e "${GREEN}SUCCESS: Tailscale is installed and running${NC}"
echo -e "   Device DNS: ${FULL_DNS}"
echo ""

# Funnel URL - use the full DNS name minus the trailing dot
FULL_DNS=$(echo "$DEVICE_DNS" | sed 's/\.$//')
FUNNEL_URL="https://${FULL_DNS}/${RANDOM_PATH}"

echo -e "${BLUE}Setting up Tailscale Funnel...${NC}"
echo ""
echo -e "   Local port: ${YELLOW}${PORT}${NC}"
echo -e "   Public URL: ${GREEN}${FUNNEL_URL}${NC}"
echo ""

# Check if application is running on the port
if ! lsof -i :$PORT &> /dev/null; then
    echo -e "${RED}WARNING: No application is running on port ${PORT}${NC}"
    echo ""
    echo "Please start your Streamlit dashboard first:"
    echo "  cd ../exercise2_streamlit"
    echo "  ./dashboard.py"
    echo ""
    echo "Then run this script again in a separate terminal."
    echo ""
    exit 1
fi

echo -e "${GREEN}SUCCESS: Application detected on port ${PORT}${NC}"
echo ""

# Save configuration
cat > .funnel_config << EOF
# Tailscale Funnel Configuration
PORT=${PORT}
RANDOM_PATH=${RANDOM_PATH}
FUNNEL_URL=${FUNNEL_URL}
CREATED=$(date)
EOF

echo -e "${BLUE}Starting Tailscale Funnel...${NC}"
echo ""
echo -e "${YELLOW}Press CTRL+C to stop the funnel${NC}"
echo ""
echo "─────────────────────────────────────────"
echo ""
echo -e "Share this URL with your colleague:"
echo ""
echo -e "   ${GREEN}${FUNNEL_URL}${NC}"
echo ""
echo "─────────────────────────────────────────"
echo ""

# First, reset any existing funnel configuration
echo ""
echo -e "${YELLOW}Clearing any existing funnel configuration...${NC}"
tailscale funnel --https=443 off 2>/dev/null || true
sleep 1

# Start the funnel (runs in FOREGROUND so you can see what's happening)
# Note: This exposes the local port via Tailscale funnel
# Press CTRL+C to stop the funnel
echo ""
echo -e "${GREEN}Starting funnel in FOREGROUND mode...${NC}"
echo ""
echo "Your dashboard will be accessible at:"
echo -e "   ${GREEN}${FUNNEL_URL}${NC}"
echo ""
echo -e "${YELLOW}Press CTRL+C to stop the funnel${NC}"
echo ""

# This runs in foreground - when you press CTRL+C, it will stop
tailscale funnel ${PORT}
