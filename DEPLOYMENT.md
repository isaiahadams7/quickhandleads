# Deploying to Streamlit Cloud

This guide will walk you through deploying your Real Estate Lead Finder dashboard to Streamlit Cloud (free hosting).

## Prerequisites

- GitHub account
- Your Google API credentials (API Key and CSE ID)
- This project code

---

## Step 1: Push Your Code to GitHub

### 1.1 Create a GitHub Repository

1. Go to [github.com](https://github.com) and log in
2. Click the "+" icon in the top right → "New repository"
3. Name it: `real-estate-lead-finder` (or any name you want)
4. Set to **Private** (to keep your code private)
5. Click "Create repository"

### 1.2 Push Your Code

Open terminal in your project folder and run:

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - Real Estate Lead Finder"

# Add your GitHub repo as remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/real-estate-lead-finder.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**Important:** Make sure your `.env` file is in `.gitignore` so your API keys don't get pushed to GitHub!

---

## Step 2: Sign Up for Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "Sign up" or "Continue with GitHub"
3. Authorize Streamlit to access your GitHub account
4. You'll be taken to your Streamlit Cloud dashboard

---

## Step 3: Deploy Your App

### 3.1 Create New App

1. Click "New app" button
2. Fill in the form:
   - **Repository**: Select `YOUR_USERNAME/real-estate-lead-finder`
   - **Branch**: `main`
   - **Main file path**: `app.py`
3. Click "Deploy"

### 3.2 Add Your API Secrets

**Before the app fully deploys:**

1. Click on "Advanced settings" (or go to your app settings after deployment)
2. Find the "Secrets" section
3. Add your API credentials in TOML format:

```toml
GOOGLE_API_KEY = "AIzaSyCZYo9B4VpIEa6nVYfWOuLAAr8DPAszw84"
GOOGLE_CSE_ID = "b3d095c7721fa47e0"
```

4. Click "Save"
5. The app will restart automatically

---

## Step 4: Access Your Dashboard

Your app will be live at:
```
https://YOUR_APP_NAME.streamlit.app
```

You can share this URL with your team!

---

## Step 5: Manage Your App

### Update Your App

Any time you push changes to GitHub, your app will automatically redeploy:

```bash
git add .
git commit -m "Updated features"
git push
```

### App Settings

In Streamlit Cloud dashboard, you can:
- **Restart app** - If something goes wrong
- **View logs** - See errors and debug issues
- **Change secrets** - Update API keys
- **Delete app** - Remove the deployment

### Share With Your Team

1. Go to your app settings
2. Add team member emails under "Sharing"
3. They'll get access to view/use the app

---

## Troubleshooting

### "Module not found" Error
- Make sure `requirements.txt` includes all dependencies
- Check that file names match exactly (case-sensitive)

### API Credentials Not Working
- Verify secrets are added correctly in Streamlit Cloud settings
- No quotes around values in secrets
- Format must be: `KEY = "value"`

### App Won't Start
- Check logs in Streamlit Cloud dashboard
- Make sure `app.py` is at the root of your repo
- Verify all import statements work

### Rate Limit Issues
- Remember: 100 API queries/day on free tier
- Use lower result counts during testing
- Consider upgrading Google API if needed

---

## Local Development

To run the dashboard locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

---

## Features of Your Dashboard

### What Users Can Do:
- ✅ Select from 11 search templates
- ✅ Enter multiple locations
- ✅ Choose which social media sites to search
- ✅ Adjust max results (10-100)
- ✅ View results in a table
- ✅ Download results as Excel or CSV
- ✅ See search history
- ✅ Track API quota usage

### Security Features:
- 🔒 API keys stored securely in Streamlit secrets
- 🔒 Private GitHub repository
- 🔒 Can restrict access to team members only

---

## Cost Breakdown

### Free Tier (Great for small teams):
- **Streamlit Cloud**: Free for public/private apps
- **Google Custom Search API**: 100 queries/day free
- **GitHub**: Free for private repos
- **Total: $0/month**

### If You Need More:
- Google API: $5 per 1,000 extra queries
- Streamlit Cloud: Free tier is usually enough
- GitHub: Free tier is usually enough

---

## Pro Tips

1. **Set default locations** - Edit the default locations in `app.py` to your target areas
2. **Bookmark the URL** - Share with team for easy access
3. **Monitor API usage** - Keep track of your daily quota
4. **Test with small results** - Use 10-20 results when testing
5. **Schedule searches** - Do your big searches at the start of each day
6. **Export regularly** - Download results to your CRM/spreadsheet

---

## Next Steps

Once deployed, you can:
1. **Add authentication** - Use Streamlit authentication if needed
2. **Add database** - Store search history permanently (Supabase/Firebase)
3. **Add CRM integration** - Push leads directly to HubSpot/Salesforce
4. **Add scheduling** - Auto-run searches daily
5. **Add analytics** - Track which templates perform best

---

## Need Help?

- **Streamlit Docs**: [docs.streamlit.io](https://docs.streamlit.io)
- **Streamlit Community**: [discuss.streamlit.io](https://discuss.streamlit.io)
- **This Project Issues**: Check GitHub issues for common problems

---

## Security Note

⚠️ **Never commit your `.env` file or API keys to GitHub!**

Always use:
- `.gitignore` for local development
- Streamlit Secrets for deployment
- Environment variables for production

Your `.gitignore` should include:
```
.env
*.pyc
__pycache__/
.streamlit/secrets.toml
```
