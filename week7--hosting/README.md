# Week 7: Hosting & Deployment

Learn how to take your Python applications from local development to public deployment.

## Quick Start

```bash
# Clone the repository
git clone [GITHUB_URL_WILL_BE_PROVIDED]
cd [REPO_NAME]/week7--hosting
```

## Contents

- **[TUTORIAL.md](TUTORIAL.md)** - Complete step-by-step guide (start here!)
- **exercise1_api/** - Basic API server with FastAPI
- **exercise2_streamlit/** - Interactive dashboard
- **exercise3_tailscale/** - Expose to internet with Tailscale
- **exercise4_cloud/** - Deploy to Streamlit Community Cloud
- **data/** - SpeakGer database (1000 speeches)

## Exercises

### 1. Basic API Server
Run a local API with math endpoints (`/sum`, `/divide`, etc.)

```bash
cd exercise1_api
./simple_api.py
```

Test in another terminal:
```bash
curl "http://localhost:8000/sum?a=5&b=3"
```

Or open http://localhost:8000/docs in your browser for interactive testing!

### 2. Streamlit Dashboard
Create an interactive web dashboard to explore parliamentary speeches

```bash
cd exercise2_streamlit
./run_dashboard.sh
```

Opens automatically in your browser at http://localhost:8501

### 3. Tailscale Funnel
Expose your local dashboard to the internet

```bash
# Terminal 1: Run dashboard
cd exercise2_streamlit
./run_dashboard.sh

# Terminal 2: Start funnel
cd ../exercise3_tailscale
./start_funnel.sh
```

### 4. Streamlit Community Cloud
Deploy to the cloud for permanent hosting

See [exercise4_cloud/README.md](exercise4_cloud/README.md) for instructions.

## Prerequisites

### Required for All Exercises
- **uv**: Python package manager (you should have this from Week 6)
  ```bash
  uv --version
  ```
  If not: `curl -LsSf https://astral.sh/uv/install.sh | sh`

- **Week 6 completed**: You should be familiar with SQLite databases and SQL queries

### Required for Exercise 3 (Tailscale)
- **Tailscale installed**: For exposing your local app to the internet
  - macOS: `brew install tailscale`
  - Linux: `curl -fsSL https://tailscale.com/install.sh | sh`
  - Windows: Download from [tailscale.com/download](https://tailscale.com/download)

- **Tailscale account**: Free account (you'll create this when you first run `tailscale up`)
  - Can sign in with Google, GitHub, or Microsoft

### Required for Exercise 4 (Cloud Deployment)
- **GitHub account**: For hosting your code - [github.com](https://github.com)

- **Streamlit Community Cloud account**: For deploying your app
  - [streamlit.io/cloud](https://streamlit.io/cloud)
  - Sign in with your GitHub account

## Learning Path

This week progressively builds your understanding:

1. **Local API** → Understand servers and endpoints
2. **Local Dashboard** → Build interactive web apps
3. **Internet Tunnel** → Share with colleagues
4. **Cloud Deployment** → Make it permanent

## Troubleshooting

**"Address already in use"**
```bash
lsof -i :8000  # Find what's using the port
kill -9 PID    # Kill it (replace PID with actual process ID)
```

**"Module not found"**
The `uv` shebang should handle dependencies automatically. If not:
```bash
uv pip install fastapi uvicorn streamlit pandas plotly
```

**Database not found**
```bash
ls -la data/speakger.db  # Verify it exists
```

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Streamlit Documentation](https://docs.streamlit.io)
- [Tailscale Funnel Guide](https://tailscale.com/kb/1223/funnel/)
- [Streamlit Cloud Docs](https://docs.streamlit.io/streamlit-community-cloud)

## Next Steps

After completing these exercises, try:
- Customizing the dashboard with your own queries
- Adding authentication to your Streamlit app
- Deploying a FastAPI backend to Render or Railway
- Creating a custom domain for your Streamlit app

---

**Read [TUTORIAL.md](TUTORIAL.md) for the complete guide!**
