# Exercise 4: Streamlit Community Cloud Deployment

## What is Streamlit Community Cloud?

Streamlit Community Cloud is a free hosting platform for Streamlit apps. It:
- Automatically deploys from your GitHub repository
- Provides free hosting for public apps
- Handles all the infrastructure for you
- Updates automatically when you push to GitHub

## Prerequisites

1. **GitHub Account** - Sign up at [github.com](https://github.com)
2. **Streamlit Community Cloud Account** - Sign up at [streamlit.io/cloud](https://streamlit.io/cloud)
3. **Database file** - Copy `speakger.db` to this folder

## Setup Steps

### Step 1: Prepare your files

Copy the database to this directory:
```bash
cp ../data/speakger.db .
```

Verify you have these files:
```
exercise4_cloud/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── speakger.db        # Your database file
├── .streamlit/
│   └── config.toml    # Streamlit configuration
└── README.md          # This file
```

### Step 2: Push to GitHub

If this is already in your course repository, you're done! If not:

```bash
# Initialize git (if not already done)
git init

# Add files
git add .

# Commit
git commit -m "Add week7 hosting exercises"

# Push to GitHub
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

**Important**: Make sure `speakger.db` is committed and pushed!

### Step 3: Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Select your repository
4. Set these values:
   - **Branch**: `main` (or your default branch)
   - **Main file path**: `week7--hosting/exercise4_cloud/app.py`
   - **App URL**: Choose a custom URL (optional)
5. Click "Deploy!"

Streamlit will:
- Clone your repository
- Install dependencies from `requirements.txt`
- Run your `app.py`
- Provide a public URL

### Step 4: Access your app

After deployment (usually 2-3 minutes), you'll get a URL like:
```
https://your-username-your-repo-name.streamlit.app
```

Share this URL with anyone - no login required!

## File Explanations

### `app.py`
The main Streamlit application. Differences from Exercise 2:
- Uses `@st.cache_resource` for database connections
- Uses `@st.cache_data` to cache query results
- Database path is relative to the app file
- Optimized for cloud deployment

### `requirements.txt`
Lists all Python packages needed. Streamlit Cloud reads this file and installs everything automatically.

Format:
```
package==version
```

### `.streamlit/config.toml`
Configuration for Streamlit. Sets:
- Theme colors
- Server settings
- Port configuration

## Troubleshooting

### "No such file: speakger.db"
- Make sure you copied the database file
- Verify it's committed to git: `git ls-files | grep speakger.db`
- Check the file path in `app.py` is correct

### "ModuleNotFoundError"
- Check `requirements.txt` has all dependencies
- Verify package versions are correct
- Try deploying again (sometimes transient network issues)

### App crashes on startup
- Check the logs in Streamlit Cloud dashboard
- Verify database file is not corrupted
- Test locally first: `streamlit run app.py`

### Database is too large
- Streamlit Cloud has a 1GB limit for files
- If your database is larger, consider:
  - Using a smaller sample
  - Hosting the database separately (e.g., on Supabase)
  - Using a cloud database (PostgreSQL, MySQL)

## Updating Your App

To update the deployed app:

1. Make changes to your files
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update dashboard"
   git push
   ```
3. Streamlit Cloud will automatically redeploy!

## Advanced: Using Secrets

If you need to store API keys or passwords:

1. In Streamlit Cloud dashboard, go to App settings → Secrets
2. Add secrets in TOML format:
   ```toml
   [database]
   password = "your-secret-password"
   ```
3. Access in your app:
   ```python
   import streamlit as st
   password = st.secrets["database"]["password"]
   ```

## Cost

Streamlit Community Cloud is **free** for public apps!

Limitations:
- Public repositories only
- 1GB storage per app
- Reasonable resource limits (CPU/RAM)

For private apps or more resources, see [Streamlit Cloud pricing](https://streamlit.io/cloud).

## Resources

- [Streamlit Documentation](https://docs.streamlit.io)
- [Streamlit Cloud Docs](https://docs.streamlit.io/streamlit-community-cloud)
- [Example Apps Gallery](https://streamlit.io/gallery)
