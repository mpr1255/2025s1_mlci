# Exercise 3: Tailscale Funnel

## What is Tailscale Funnel?

Tailscale Funnel allows you to expose a local service to the public internet securely through Tailscale's network. It's perfect for:
- Sharing development work with colleagues
- Quick demos without complex deployment
- Testing applications from different networks

## IMPORTANT LIMITATIONS

- **Only ONE funnel active at a time per machine** - Starting a new funnel will hijack any existing funnel
- **All funnels use port 443 (HTTPS)** - You can't run multiple funnels simultaneously
- If you have other services using Tailscale funnel, this script will take them over

## Prerequisites

1. **Install Tailscale**
   - macOS: `brew install tailscale`
   - Linux: `curl -fsSL https://tailscale.com/install.sh | sh`
   - Windows: Download from [tailscale.com/download](https://tailscale.com/download)

2. **Log in to Tailscale**
   ```bash
   tailscale up
   ```

3. **Enable HTTPS** (required for funnel)
   ```bash
   tailscale cert $(tailscale status --json | jq -r '.Self.DNSName')
   ```

## Usage

### Step 1: Start your Streamlit dashboard

In one terminal:
```bash
cd ../exercise2_streamlit
./dashboard.py
```

Wait for the message: `You can now view your Streamlit app in your browser.`

### Step 2: Start the Tailscale funnel

In a second terminal:
```bash
cd ../exercise3_tailscale
./start_funnel.sh
```

This will:
- Check if Tailscale is installed and running
- Verify your app is running on port 8501
- Generate a random URL path for security
- Start the funnel
- Display the public URL

### Step 3: Share with a colleague

Copy the URL displayed (it will look like):
```
https://your-device.your-tailnet.ts.net/abc123def456789
```

Send this to a colleague. They can access your dashboard in their browser without any special setup!

### Step 4: Stop the funnel

When you're done:
```bash
./stop_funnel.sh
```

## Security Notes

- The URL includes a random 20-character path to prevent easy guessing
- Only people with the exact URL can access your service
- You can stop the funnel at any time
- The funnel goes through Tailscale's secure network

## Troubleshooting

**Error: "Tailscale is not installed"**
- Install Tailscale using the instructions above

**Error: "Not logged in to Tailscale"**
- Run: `tailscale up`

**Error: "No application is running on port 8501"**
- Start your Streamlit dashboard first (see Step 1)

**Colleague can't access the URL**
- Check that the funnel is still running
- Verify you sent the complete URL (including the random path)
- Make sure you didn't stop your Streamlit app
