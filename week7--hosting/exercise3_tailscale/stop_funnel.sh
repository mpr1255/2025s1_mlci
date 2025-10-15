#!/bin/bash

# Script to stop Tailscale Funnel
# WARNING: This will stop ALL funnels on this machine!

echo ""
echo "WARNING: This will stop ALL active Tailscale funnels!"
echo "Press CTRL+C now to cancel, or Enter to continue..."
read

echo ""
echo "Stopping all Tailscale Funnels..."
echo ""

# Turn off HTTPS funnel completely
tailscale funnel --https=443 off

echo ""
echo "SUCCESS: All funnels stopped!"
echo ""
echo "Note: If you had other funnels running, they were also stopped."
echo "You may need to restart them manually."
echo ""
