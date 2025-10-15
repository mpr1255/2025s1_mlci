# Week 7: Hosting - Five Easy Pieces

## From Local Development to Public Access

Learn how to take your Python applications from running on your laptop to being accessible on the internet.

---

## Learning goals

By the end of this tutorial, you will be able to:

1. Explain what "hosting" means and the difference between local hosting (your computer) and cloud hosting (someone else's servers)
2. Run a REST API server locally and test it with curl and browser tools
3. Create an interactive web dashboard with Streamlit
4. Expose a local service to the public internet using Tailscale Funnel
5. Deploy a production application to Streamlit Community Cloud
6. Understand the security implications of each hosting method

**Skills you'll practice:**
- FastAPI for REST APIs
- Streamlit for interactive dashboards
- Git workflows for deployment
- Understanding ports, localhost, and network routing
- Reading and understanding deployment logs

---

## Prerequisites

Before starting this week's exercises, make sure you have:

### Required for all exercises
- **uv installed**: Python package manager (you should have this from Week 6)
  ```bash
  uv --version
  ```
  If not: `curl -LsSf https://astral.sh/uv/install.sh | sh`

- **Week 6 completed**: You should be familiar with SQLite databases and SQL queries

### Required for Piece 3 (Tailscale)
- **Tailscale installed**: For exposing your local app to the internet
  - macOS: `brew install tailscale`
  - Linux: `curl -fsSL https://tailscale.com/install.sh | sh`
  - Windows: Download from [tailscale.com/download](https://tailscale.com/download)

- **Tailscale account**: Free account (you'll create this when you first run `tailscale up`)
  - Can sign in with Google, GitHub, or Microsoft
  - [tailscale.com](https://tailscale.com)

### Required for Piece 4 (Cloud Deployment)
- **GitHub account**: For hosting your code
  - [github.com](https://github.com)

- **Streamlit Community Cloud account**: For deploying your app
  - [streamlit.io/cloud](https://streamlit.io/cloud)
  - Sign in with your GitHub account

---

## Getting started

### Fork the repository

Before you begin, you need to create your own copy of the course repository:

1. Go to https://github.com/mpr1255/2025s1_mlci
2. Click the **"Fork"** button in the top-right corner
3. This creates a copy under your GitHub account: `https://github.com/YOUR_USERNAME/2025s1_mlci`

### Clone YOUR fork

Now clone your forked repository (not the original):

```bash
# Replace YOUR_USERNAME with your actual GitHub username
git clone https://github.com/YOUR_USERNAME/2025s1_mlci.git
cd 2025s1_mlci/week7--hosting
```

Verify you're in the right place:
```bash
git remote -v
# Should show YOUR_USERNAME in the URL, not mpr1255
```

---

## The big picture: what is hosting?

You've built scripts that run on your computer. But what if you want others to use your work?

This week covers five pieces:

1. **Run a local API server**: FastAPI serving math endpoints on localhost
2. **Serve a local dashboard**: Streamlit dashboard running on your machine
3. **Expose to internet**: Tailscale funnel creates public URL to your localhost
4. **Deploy to cloud**: Streamlit Community Cloud hosts it 24/7
5. **Test auto-redeployment**: Push changes to GitHub, watch auto-deploy

### Key concepts

**Port**: A number (e.g., 8000, 8501) that identifies a service on a computer
- Think of it like an apartment number in a building
- Your computer is the building, ports are the apartments

**Localhost / 127.0.0.1**: Special address that means "this computer"
- `http://localhost:8000` = "connect to port 8000 on my own machine"
- `localhost` and `127.0.0.1` are basically the same, though there are subtle differences that you don't need to think about most of the time

**API (Application Programming Interface)**: A service that responds to requests
- You send a request (like opening a URL)
- It sends back data (usually JSON)
- Think of it like a vending machine: you press a button (request), get a snack (response)

**Endpoint**: A specific URL path on an API
- `/sum` = do addition
- `/hello` = get a greeting

---

## Piece 1: Setup & your first API server

### Navigate to the week7 folder

```bash
cd week7--hosting
```

### Check what you have

```bash
ls -la
```

You should see:
```
exercise1_api/       # Basic API server
exercise2_streamlit/ # Interactive dashboard
exercise3_tailscale/ # Expose to internet
exercise4_cloud/     # Deploy to cloud
data/                # Database file
```

### Verify uv is installed

```bash
uv --version
```

If not installed:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### What we're building

A simple math API with these endpoints:
- `/hello` - Says hello
- `/sum` - Adds two numbers
- `/subtract` - Subtracts two numbers
- `/multiply` - Multiplies two numbers
- `/divide` - Divides two numbers

### Step 1: Look at the code

```bash
cd exercise1_api
cat simple_api.py
```

**Key parts to understand:**

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/sum")
def add_numbers(a: float, b: float):
    result = a + b
    return {"result": result}
```

- `FastAPI()` - Creates a web application
- `@app.get("/sum")` - Says "when someone visits /sum, run this function"
- `a: float, b: float` - Takes two numbers from the URL
- `return {...}` - Sends back JSON data

### Step 2: Start the server

In Terminal 1:
```bash
./simple_api.py
```

[Why could it run like that, btw? Look at the shebang line at the top. Ask gpt about shebang lines to learn more]

You'll see:
```
Starting Simple Math API Server
Server running on: http://localhost:8000
API docs at: http://localhost:8000/docs
```

**You can now open these URLs in your browser:**
- http://localhost:8000 - Main API page
- http://localhost:8000/docs - Interactive API documentation

**What's happening?**
- Your script is now running and **waiting** for requests
- It's listening on port 8000
- It won't stop until you press Ctrl+C
- If you ping it, you'll see responses in the console

### Step 3: Test with curl

Open a **second terminal** (keep the server running in the first!):

```bash
# Get the homepage
curl http://localhost:8000/

# Add two numbers
curl "http://localhost:8000/sum?a=5&b=3"

# Say hello
curl "http://localhost:8000/hello?name=Alice"

# Divide numbers
curl "http://localhost:8000/divide?a=10&b=2"

# Try to divide by zero (should error!)
curl "http://localhost:8000/divide?a=10&b=0"
```

**Notice:**
- The URL includes parameters: `?a=5&b=3`
- Multiple parameters use `&`: `?name=Alice&age=25`
- The server responds with JSON: `{"result": 8}`

### Step 4: Use the interactive docs

**Open in your browser:** http://localhost:8000/docs

This is **Swagger/OpenAPI automatic documentation** - a standard API documentation kit that FastAPI provides out of the box. You can:
- See all endpoints with their expected inputs and outputs
- Test them interactively with a web form (click "Try it out")
- View the request/response schemas
- See example values and data types
- No need to write any documentation manually - FastAPI generates it from your code!

Try the `/sum` endpoint:
1. Click on `/sum` to expand it
2. Click "Try it out"
3. Enter values for `a` and `b` (e.g., 5 and 3)
4. Click "Execute"
5. See the result in the response section below

This is incredibly useful for testing APIs and sharing them with others - they can explore and test your API without needing curl or Postman!

### Stop the server

Go back to Terminal 1 and press **Ctrl+C**

---

## Piece 2: Interactive dashboard with Streamlit

### What we're building

A web dashboard that:
- Shows statistics from the SpeakGer database
- Displays random speeches
- Creates interactive visualizations
- All with Python - no HTML/CSS/JavaScript needed!

### Step 1: Look at the code

```bash
cd ../exercise2_streamlit
head -50 dashboard.py
```

**Key parts:**

```python
import streamlit as st

# Simple as writing Python!
st.title("My Dashboard")
st.button("Click me")
st.metric("Total", 1000)
```

Streamlit turns Python code into web interfaces automatically.

### Step 2: Inspect the run script

Before running the dashboard, let's understand what the script does:

```bash
cat run_dashboard.sh
```

This script:
- Sets environment variables if needed
- Configures Streamlit options (port, browser behavior, etc.)
- Launches the Streamlit server with the dashboard.py file

Understanding shell scripts like this helps you debug issues and customize behavior.

### Step 3: Run the dashboard

```bash
./run_dashboard.sh
```

You'll see:
```
You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.100:8501
```

**Your browser should open automatically.** If not, open: http://localhost:8501

### Step 4: Explore the dashboard

Try these features:
1. **Statistics page**: See database metrics
2. **Random Speech**: Click the button to get a random speech
3. **Visualizations**: Interactive charts with Plotly

**Behind the scenes:**
- Streamlit runs a web server on port 8501
- It automatically reloads when you save the file
- It handles all the web stuff - you just write Python!

### Step 5: Make a change (optional)

Edit `dashboard.py`:
```python
# Find the line:
st.title(" SpeakGer Parliamentary Speech Dashboard")

# Change it to:
st.title(" My Custom Dashboard")
```

Save the file. The dashboard will reload automatically.

### Understanding the database queries

The dashboard runs SQL queries like:

```python
query = """
    SELECT Party, COUNT(*) as count
    FROM speeches
    WHERE Party != '[]'
    GROUP BY Party
    ORDER BY count DESC
    LIMIT 10
"""
df = pd.read_sql_query(query, conn)
```

This:
1. Connects to the SQLite database
2. Runs a SQL query
3. Returns results as a Pandas dataframe
4. Displays it in the dashboard

---

## Piece 3: Expose to internet with Tailscale

### ⚠️ SECURITY WARNING ⚠️

**YOU ARE ABOUT TO SERVE CONTENT FROM YOUR OWN COMPUTER TO THE PUBLIC INTERNET**

**Understand what this means:**
- **The network route**: Internet → Tailscale servers → YOUR computer → your app
- **Your machine is the server**: You are exposing a service running on your personal computer to anyone with the URL
- **While Tailscale is secure**, you are still making your local service accessible from anywhere in the world
- **You can get a custom domain** and point it to your computer via Tailscale (but this is NOT recommended for production use)

**Why is this OK right now?**
- The URL includes a random 20-character path. Equivalent to an API key, google docs link
- Without the exact URL, people can't access the service
- Traffic goes through Tailscale's encrypted network
- You can stop the funnel anytime with Ctrl+C
- This is great for demos and sharing with colleagues, not for production deployments

**IMPORTANT LIMITATION**: Tailscale only allows ONE active funnel per machine at a time. Starting this will hijack any existing funnel you have running. All funnels use port 443 (HTTPS).

### What is Tailscale funnel?

**Problem**: Your dashboard runs on `localhost`. Only you can access it.

**Solution**: Tailscale Funnel creates a public URL that:
- Tunnels through Tailscale's network
- Works from anywhere (not just your network)
- Uses HTTPS automatically
- Is secure (only people with the URL can access it)

### Step 1: Install Tailscale

**macOS:**
```bash
brew install tailscale
```

**Linux:**
```bash
curl -fsSL https://tailscale.com/install.sh | sh
```

**Windows:**
Download from [tailscale.com/download](https://tailscale.com/download)

### Step 2: Log in to Tailscale

```bash
tailscale up
```

This will open your browser to authenticate. Sign in with:
- Google
- GitHub
- Microsoft
- Or create a new account (free!)

### Step 3: Start your Streamlit dashboard

In Terminal 1:
```bash
cd exercise2_streamlit
./run_dashboard.sh
```

Wait until you see: `You can now view your Streamlit app in your browser`

### Step 4: Start the Tailscale funnel

In Terminal 2:
```bash
cd ../exercise3_tailscale
./start_funnel.sh
```

You'll see something like:
```
Share this URL with your colleague:

https://your-machine.your-tailnet.ts.net/abc123def456...

Starting funnel in FOREGROUND mode...
Press CTRL+C to stop the funnel
```

The URL will be unique to your machine. Copy the entire URL (it's long!).

### Step 5: Share with a colleague

**Copy the full URL** (the https://... part) and send it to a classmate. They can:
- **Open it directly in their browser** - just paste the URL
- No Tailscale account needed
- Works from anywhere (coffee shop, home, different country, etc.)

**Test it yourself first:** Open the URL in your own browser to make sure it works before sharing!

**What's happening?**
1. Your Streamlit app runs on localhost:8501
2. Tailscale funnel exposes port 8501 to the internet
3. Requests to the public URL → Tailscale → your machine → your app
4. Responses travel back the same way

### Step 6: Stop the funnel

**Just press CTRL+C in the terminal** where the funnel is running. That's it!

(The funnel runs in the foreground so you can see what's happening and stop it easily.)

---

## Piece 4: Deploy to cloud

### What is Streamlit Community Cloud?

A **free hosting service** for Streamlit apps. It:
- Deploys directly from GitHub
- Handles all server management
- Provides a permanent public URL
- Auto-updates when you push to GitHub

**Key difference from Tailscale:**
- Tailscale: Your machine runs the app, Tailscale routes traffic
- Cloud: Their servers run the app, you don't need to keep your computer on

### Prerequisites

1. **GitHub Account**: [github.com](https://github.com)
2. **Streamlit Cloud Account**: [streamlit.io/cloud](https://streamlit.io/cloud)

### Step 1: Prepare the files

```bash
cd ../exercise4_cloud
ls -la
```

You should see:
```
app.py           # Streamlit application
requirements.txt # Python dependencies
speakger.db      # Database file
.streamlit/      # Configuration
```

**Key file: `requirements.txt`**
```
streamlit==1.45.1
pandas==2.2.3
plotly==5.24.1
```

This tells Streamlit Cloud what packages to install.

### Step 2: Verify files are in your GitHub fork

Make sure you forked the repository (not just cloned it!). Check your GitHub:

```bash
# Check your remote URL
git remote -v
```

You should see YOUR username in the URL:
```
origin  https://github.com/YOUR_USERNAME/2025s1_mlci.git
```

If you see the course repo URL instead, you need to fork it first (see "Getting Started" section).

### Step 3: Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **"New app"**
4. Fill in the deployment form:
   - **Repository**: Select your forked repo (should be `YOUR_USERNAME/2025s1_mlci`)
   - **Branch**: `main` (or `master` - check what your repo uses)
   - **Main file path**: `week7--hosting/exercise4_cloud/app.py`

     **IMPORTANT**: This is the FULL path from the repository root. The file is NOT in the repo root - you must navigate to it. The structure is:
     ```
     2025s1_mlci/                    (repo root)
     └── week7--hosting/             (folder)
         └── exercise4_cloud/        (subfolder)
             └── app.py              (the file)
     ```

     So the complete path is: `week7--hosting/exercise4_cloud/app.py`

     If you get deployment errors like "File not found", double-check this path matches your repository structure!

   - **App URL**: Choose a custom name (e.g., `speakger-dashboard`)
5. Click **"Deploy!"**

### Step 4: Wait for deployment

Streamlit Cloud will:
1. Clone your repository
2. Install packages from `requirements.txt`
3. Start your app
4. Provide a public URL

This takes 2-3 minutes.

### Step 5: Access your app

You'll get a URL like:
```
https://your-username-repo-name-speakger-dashboard.streamlit.app
```

**Open this URL in your browser!** The app is now live.

**This URL is:**
- **Public** - Anyone can access it
- **Permanent** - Stays online 24/7
- **Free** - For public repos
- **Auto-updating** - Push to GitHub and it redeploys automatically

---

## Piece 5: Testing auto-redeployment

Let's test that changes automatically redeploy. Make a small edit to `app.py`:

```bash
cd week7--hosting/exercise4_cloud
```

Edit `app.py` and find this line (around line 121):
```python
st.markdown("Explore German parliamentary speeches from the Bremen dataset")
```

Change it to:
```python
st.markdown("Alles Gut! Explore German parliamentary speeches from the Bremen dataset")
```

Save the file, then push to GitHub:

```bash
git add app.py
git commit -m "Add alles gut message"
git push
```

**Watch what happens:**
1. Go to your Streamlit Cloud dashboard
2. You'll see "App is updating..."
3. Wait 30-60 seconds
4. Refresh your app URL
5. You should see "Alles Gut!" at the top

That's automatic deployment in action - any git push triggers a redeploy!

### Share with the world

Send the URL to:
- Classmates
- Instructors
- Friends
- Anyone!

No authentication required. They just open the link.

### Making more changes

Any time you want to update your app, just:

```bash
cd week7--hosting/exercise4_cloud
# Edit app.py...
git add app.py
git commit -m "Your commit message"
git push
```

Or better, use the github desktop app. Bit saner.

Streamlit Cloud automatically redeploys within a minute!

### Cleanup: revoking GitHub permissions

When you're done with this tutorial, you can revoke Streamlit's access to your GitHub account:

1. Go to GitHub Settings → Applications → Authorized OAuth Apps
2. Find "Streamlit"
3. Click "Revoke" to remove access

You can always re-authorize later if you want to deploy more apps.

---

## Concepts review

### Ports

```
Your Computer (localhost / 127.0.0.1)
  Port 8000 → API Server (FastAPI)
  Port 8501 → Streamlit Dashboard
  Port 3000 → (could be another app)
  Port 5432 → (commonly used for PostgreSQL)
```

Each port can only be used by one application at a time.

### Client-server model

```
Client (you)            Server (your script)
     |                          |
     |----Request (curl)------->|
     |                          | (processes)
     |<---Response (JSON)-------|
```

Your API server is always waiting, ready to respond.

### Hosting layers

```
1. Local Development
   localhost:8000 (only you)

2. Local Network
   192.168.1.100:8000 (same WiFi)

3. Internet via Tunnel
   https://your-machine.tailnet.ts.net (anyone with URL)

4. Cloud Hosting
   https://your-app.streamlit.app (everyone)
```

### Comparison: three ways to host

| Method | Accessibility | Setup | Cost | Best For |
|--------|--------------|-------|------|----------|
| **Localhost** | Only you | Easy | Free | Development, testing |
| **Tailscale Funnel** | Anyone with URL | Medium | Free | Demos, sharing with colleagues |
| **Cloud (Streamlit)** | Everyone | Medium | Free* | Production, portfolios |

\* Streamlit Community Cloud is free for public repos. Private repos require paid plan.

---

## Next steps & extensions

### Ideas to explore

1. **Custom Domain**: Point `yourdomain.com` to your Streamlit app
2. **Authentication**: Add login with `streamlit-authenticator`
3. **Databases**: Use PostgreSQL or Supabase instead of SQLite
4. **APIs**: Create a FastAPI backend + Streamlit frontend
5. **Monitoring**: Add analytics with Google Analytics or Plausible
6. **Caching**: Optimize with `@st.cache_data` and `@st.cache_resource`

### Other hosting options

**For Python Web Apps:**
- [Render](https://render.com) - Free tier for web services
- [Railway](https://railway.app) - Easy deployment with GitHub
- [Fly.io](https://fly.io) - Global edge deployment
- [Heroku](https://heroku.com) - Classic PaaS (limited free tier)

**For Static Sites:**
- [Netlify](https://netlify.com) - Great for frontend apps
- [Vercel](https://vercel.com) - Optimized for Next.js
- [GitHub Pages](https://pages.github.com) - Free for static HTML

**For APIs:**
- [FastAPI → Render](https://render.com) - Full-featured API hosting
- [AWS Lambda](https://aws.amazon.com/lambda/) - Serverless functions
- [Google Cloud Run](https://cloud.google.com/run) - Containerized apps

---

## Troubleshooting

### "Address already in use"

**Error**: `OSError: [Errno 48] Address already in use`

**Cause**: Another app is using that port

**Fix**:
```bash
# Find what's using port 8000
lsof -i :8000

# Kill it (replace PID with the actual process ID from above)
kill -9 PID

# Or use a different port
uvicorn app:app --port 8001
```

### "Connection refused"

**Cause**: Server isn't running

**Fix**: Start the server first, then make requests

### "Module not found"

**Cause**: Missing dependencies

**Fix**:
```bash
# The uv shebang should handle this automatically
# But if not, install manually:
uv pip install fastapi uvicorn streamlit pandas
```

### Dashboard is blank

**Cause**: Database file not found

**Fix**:
```bash
# Check the path
ls -la data/speakger.db

# Verify it's where the script expects
grep "DB_PATH" exercise2_streamlit/dashboard.py
```

### Streamlit Cloud deployment issues

**"No such file: speakger.db"**
- Make sure the database is committed: `git ls-files | grep speakger.db`
- Check the file path in `app.py`

**"ModuleNotFoundError"**
- Verify `requirements.txt` lists all dependencies
- Check package versions are correct

**App is slow or times out**
- Database might be too large (1GB limit)
- Consider using a smaller sample
- Or host the database separately (PostgreSQL, Supabase)

**View logs:**
- In Streamlit Cloud dashboard, click "Manage app" → "Logs"
- Shows all errors and print statements

---

## Resources

### Documentation
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [Streamlit Docs](https://docs.streamlit.io)
- [Tailscale Funnel Guide](https://tailscale.com/kb/1223/funnel/)
- [Streamlit Cloud Docs](https://docs.streamlit.io/streamlit-community-cloud)

### Learning
- [FastAPI in 100 Seconds](https://www.youtube.com/watch?v=7t2alSnE2-I)
- [Streamlit in 12 Minutes](https://www.youtube.com/watch?v=R2nr1uZ8ffc)
- [How the Internet Works](https://developer.mozilla.org/en-US/docs/Learn/Common_questions/How_does_the_Internet_work)

### Tools
- [Postman](https://www.postman.com/) - Test APIs with a GUI
- [httpie](https://httpie.io/) - Better curl alternative
- [ngrok](https://ngrok.com/) - Alternative to Tailscale for tunneling

---

## Quick reference

### Run the API server
```bash
cd exercise1_api
./simple_api.py
```

### Run the Streamlit dashboard
```bash
cd exercise2_streamlit
./run_dashboard.sh
```

### Expose with Tailscale
```bash
# Terminal 1: Run dashboard
cd exercise2_streamlit
./run_dashboard.sh

# Terminal 2: Start funnel
cd ../exercise3_tailscale
./start_funnel.sh
```

### Deploy to cloud
1. Ensure files are in GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Deploy from `week7--hosting/exercise4_cloud/app.py`

---

## Summary

You now know how to:

✓ Run a local API server (FastAPI)
✓ Create an interactive dashboard (Streamlit)
✓ Expose localhost to the internet (Tailscale)
✓ Deploy to the cloud (Streamlit Community Cloud)

**Key Takeaway**: Hosting is just making your code accessible to others. You control the level of accessibility:
- Localhost → Local Network → Internet → Cloud

Each step makes your work more accessible, but also adds complexity.

---

**Week 7 Complete!**

Next week: We'll explore more advanced deployment patterns, containerization with Docker, and scaling applications.
