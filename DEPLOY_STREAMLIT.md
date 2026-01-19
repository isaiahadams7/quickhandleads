# Deploy to Streamlit Cloud - Complete Guide

Your code is ready to deploy! Follow these steps to get your dashboard live for your team.

---

## 📋 Prerequisites

- [x] Code is ready (✅ Done!)
- [ ] GitHub account
- [ ] Google API credentials (you already have these)

---

## 🚀 Step-by-Step Deployment

### **Step 1: Create GitHub Repository** (2 minutes)

1. Go to [github.com](https://github.com) and log in
2. Click the **"+"** icon (top right) → **"New repository"**
3. Fill in:
   - **Repository name**: `real-estate-leads`
   - **Description**: "Real estate lead finder with Google Custom Search"
   - **Visibility**: Choose **Private** (recommended) or Public
   - **DO NOT** initialize with README (we already have code)
4. Click **"Create repository"**

---

### **Step 2: Push Your Code to GitHub** (2 minutes)

Copy the commands from your new GitHub repo page, or run these in your terminal:

```bash
cd /Users/Isaiah/Desktop/Desktop\ -\ Mac/CodingProjects/quickhandleads

# Add your GitHub repo URL (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/real-estate-leads.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**Example:**
If your GitHub username is `isaiah123`, the command would be:
```bash
git remote add origin https://github.com/isaiah123/real-estate-leads.git
```

---

### **Step 3: Sign Up for Streamlit Cloud** (1 minute)

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"Sign up"** or **"Continue with GitHub"**
3. Authorize Streamlit to access your GitHub
4. You'll be redirected to your Streamlit dashboard

---

### **Step 4: Deploy Your App** (3 minutes)

1. In Streamlit Cloud dashboard, click **"New app"**

2. Fill in the deployment form:
   ```
   Repository: YOUR_USERNAME/real-estate-leads
   Branch: main
   Main file path: app_v2.py
   ```

3. Click **"Advanced settings"** (IMPORTANT!)

4. In the **"Secrets"** section, paste this:
   ```toml
   GOOGLE_API_KEY = "AIzaSyCZYo9B4VpIEa6nVYfWOuLAAr8DPAszw84"
   GOOGLE_CSE_ID = "b3d095c7721fa47e0"
   ```

5. Click **"Save"**

6. Click **"Deploy!"**

---

### **Step 5: Wait for Deployment** (2-3 minutes)

You'll see:
```
🔨 Building app...
📦 Installing dependencies...
🚀 Starting app...
✅ Your app is live!
```

---

### **Step 6: Get Your App URL**

Once deployed, your app will be at:
```
https://YOUR_APP_NAME.streamlit.app
```

Example: `https://real-estate-leads.streamlit.app`

**Share this URL with your team!**

---

## 👥 Sharing With Your Team

### **Option 1: Public Link (Easiest)**
Just share the URL - anyone can access it:
```
https://your-app.streamlit.app
```

### **Option 2: Add Team Members (More Secure)**
1. In Streamlit Cloud dashboard, click your app
2. Go to **"Settings"** → **"Sharing"**
3. Add team member emails
4. They'll get access to the private app

---

## 🔄 Updating Your App

Whenever you make changes:

```bash
# Make your changes to the code
# Then commit and push:

git add .
git commit -m "Updated features"
git push

# Streamlit Cloud automatically redeploys!
```

---

## 🎯 What Your Team Will See

Once deployed, your team can:
- ✅ Access the dashboard from any browser
- ✅ Run searches for leads
- ✅ View results in real-time
- ✅ Download Excel/CSV files
- ✅ Browse the lead database
- ✅ See duplicate detection in action

---

## ⚡ Quick Commands Reference

```bash
# Navigate to your project
cd /Users/Isaiah/Desktop/Desktop\ -\ Mac/CodingProjects/quickhandleads

# Add GitHub remote (do this once)
git remote add origin https://github.com/YOUR_USERNAME/real-estate-leads.git

# Push to GitHub (first time)
git branch -M main
git push -u origin main

# Future updates
git add .
git commit -m "Your update message"
git push
```

---

## 💰 Costs

**Everything is FREE:**
- Streamlit Cloud: Free forever for public apps
- Streamlit Cloud: Free for 1 private app
- Google API: 100 queries/day free
- GitHub: Free for unlimited private repos

**If you need more:**
- Streamlit Cloud Pro: $20/month (more private apps)
- Google API: $5 per 1,000 queries beyond free tier

---

## 🔒 Security Notes

**Your API keys are safe:**
- ✅ Stored in Streamlit Secrets (encrypted)
- ✅ Not visible in your code
- ✅ Not in GitHub (thanks to .gitignore)
- ✅ Only accessible by your app

**Database:**
- Stored on Streamlit's servers
- Persists between sessions
- Each deployment has its own database

---

## 🐛 Troubleshooting

### **"Module not found" error**
- Check that `requirements.txt` is committed
- All packages should be listed

### **"API credentials not found"**
- Make sure you added secrets in Streamlit Cloud
- Format must be exact (no extra spaces)

### **App won't start**
- Check logs in Streamlit Cloud dashboard
- Look for red error messages
- Common issue: missing dependencies

### **Database not persisting**
- This is normal - Streamlit Cloud has ephemeral storage
- For permanent storage, upgrade to Streamlit Cloud Pro or use external database

---

## 🎉 Next Steps

After deployment:

1. **Test the app** - Run a search to make sure everything works
2. **Share with team** - Send them the URL
3. **Set up a routine** - Daily searches for new leads
4. **Monitor usage** - Keep track of API quota

---

## 📞 Need Help?

- **Streamlit Docs**: [docs.streamlit.io](https://docs.streamlit.io)
- **Streamlit Forum**: [discuss.streamlit.io](https://discuss.streamlit.io)
- **GitHub Issues**: Use your repo's Issues tab

---

## 🚀 Ready to Deploy?

1. Create GitHub repo
2. Push code: `git push -u origin main`
3. Go to [share.streamlit.io](https://share.streamlit.io)
4. Click "New app"
5. Add your secrets
6. Click "Deploy"

**Your team will have access in ~5 minutes!** 🎉
