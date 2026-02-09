# 🚀 FREE Deployment Guide - Vercel + Railway

Deploy your AI Knowledge Continuity System **completely free** using Vercel (frontend) and Railway (backend).

---

## 📦 Prerequisites

1. **GitHub Account** - https://github.com
2. **Vercel Account** - https://vercel.com/signup
3. **Railway Account** - https://railway.app
4. **Google Gemini API Key** - https://aistudio.google.com/app/apikey

---

## 🔧 Step 1: Prepare Your Code

### 1.1 Update Backend CORS Settings

Open `backend/core/config.py` and update CORS origins:

```python
CORS_ORIGINS = [
    "http://localhost:3000",
    "https://*.vercel.app",  # Allow all Vercel deployments
    "https://*.railway.app",  # Allow Railway backend
]
```

### 1.2 Create Frontend Environment File

Create `frontend/.env.production`:

```env
REACT_APP_API_URL=https://your-backend-url.railway.app
```

**Note:** You'll update this URL after deploying the backend in Step 3.

---

## 🗂️ Step 2: Push to GitHub

### 2.1 Initialize Git (if not done)

```bash
cd "/Users/macbook/Documents/Final-Year Project/AI Knowledge Continuity System"
git init
git add .
git commit -m "Initial commit - Ready for deployment"
```

### 2.2 Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `ai-knowledge-continuity-system`
3. Set to **Public** (required for free tiers)
4. **Don't** initialize with README (you already have files)
5. Click "Create repository"

### 2.3 Push Code to GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/ai-knowledge-continuity-system.git
git branch -M main
git push -u origin main
```

---

## 🐍 Step 3: Deploy Backend to Railway (FREE)

### 3.1 Sign Up for Railway

1. Go to https://railway.app
2. Click "Login" → Sign in with GitHub
3. Authorize Railway to access your repositories

### 3.2 Create New Project

1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose your `ai-knowledge-continuity-system` repository
4. Click "Deploy Now"

### 3.3 Configure Backend Service

1. Railway will auto-detect Python
2. Go to **Settings** tab:
   - **Root Directory:** Leave empty (use root)
   - **Start Command:** 
     ```bash
     uvicorn backend.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Watch Paths:** `backend/**,requirements.txt`

### 3.4 Add Environment Variables

Go to **Variables** tab and add:

```
GOOGLE_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
LLM_PROVIDER=gemini
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
PYTHON_VERSION=3.12
```

### 3.5 Generate Public Domain

1. Go to **Settings** tab
2. Scroll to **Networking**
3. Click "Generate Domain"
4. **Copy this URL** (e.g., `https://ai-knowledge-backend-production.up.railway.app`)
5. **Save it for Step 4**

### 3.6 Wait for Deployment

- Watch the **Deployments** tab
- First deployment takes 3-5 minutes
- Status should show "Success" with green checkmark

### 3.7 Test Backend

Visit: `https://your-backend-url.railway.app/api/health`

Should return:
```json
{
  "status": "healthy",
  "database": "connected",
  "vector_store": "ready"
}
```

---

## ⚛️ Step 4: Deploy Frontend to Vercel (FREE)

### 4.1 Sign Up for Vercel

1. Go to https://vercel.com/signup
2. Click "Continue with GitHub"
3. Authorize Vercel

### 4.2 Import Project

1. Click "Add New..." → "Project"
2. Import your `ai-knowledge-continuity-system` repository
3. Vercel will detect it as a monorepo

### 4.3 Configure Build Settings

**Framework Preset:** Create React App

**Root Directory:** `frontend` ⚠️ **IMPORTANT**

**Build Settings:**
- Build Command: `npm run build`
- Output Directory: `build`
- Install Command: `npm install`

### 4.4 Add Environment Variable

Click "Environment Variables" and add:

**Key:** `REACT_APP_API_URL`  
**Value:** `https://your-backend-url.railway.app` (from Step 3.5)

### 4.5 Deploy

1. Click "Deploy"
2. Wait 2-3 minutes
3. Vercel will show your live URL: `https://your-project.vercel.app`

---

## ✅ Step 5: Test Your Deployment

### 5.1 Open Your App

Visit your Vercel URL: `https://your-project.vercel.app`

### 5.2 Test Flow

1. **Create Account:**
   - Click "Sign Up"
   - Email: test@example.com
   - Password: Test123!
   - Full Name: Test User

2. **Upload Document:**
   - Go to "Documents" tab
   - Upload a text file (or use one from `data/` folder locally)
   - Wait for "Processing complete" message

3. **Test Chat:**
   - Go to "Chat" tab
   - Type: "Hi"
   - Should get helpful response (not error)
   - Ask about your uploaded document
   - Should get answer with sources

### 5.3 Check Browser Console

Press F12 → Console tab
- Should see no red errors
- Network tab should show successful API calls

---

## 🐛 Troubleshooting

### Issue: "CORS Error" in Browser Console

**Fix Backend:**
1. Go to Railway project
2. Add variable: `CORS_ORIGINS=https://your-project.vercel.app,https://*.vercel.app`
3. Redeploy

### Issue: "Network Error" or "Failed to Fetch"

**Check:**
1. Backend health: `https://your-backend-url.railway.app/api/health`
2. Frontend environment variable is correct
3. Backend Railway service is running (not sleeping)

**Fix:**
1. Vercel Dashboard → Your Project → Settings → Environment Variables
2. Update `REACT_APP_API_URL` to correct Railway URL
3. Redeploy: Deployments tab → "..." → "Redeploy"

### Issue: Backend Not Starting on Railway

**Check Logs:**
1. Railway Dashboard → Deployments → Click latest deployment
2. View logs for errors

**Common fixes:**
- Add `PORT` environment variable (Railway auto-provides)
- Verify `requirements.txt` has all dependencies
- Check Python version matches (3.12)

### Issue: "Module not found" Errors

**Frontend:**
```bash
cd frontend
npm install
git add package-lock.json
git commit -m "Update dependencies"
git push
```

**Backend:**
Verify `requirements.txt` includes all packages

---

## 💰 Free Tier Limits

### Vercel (Frontend)
- ✅ 100 GB bandwidth/month
- ✅ Unlimited projects
- ✅ Automatic HTTPS
- ✅ Global CDN

### Railway (Backend)
- ✅ $5 free credit/month (~500 hours)
- ✅ 512 MB RAM
- ✅ 1 GB disk
- ⚠️ Sleeps after 30 min inactivity (wakes on request)

**Note:** First request after sleep takes ~30 seconds. Subsequent requests are fast.

---

## 🔄 Continuous Deployment

Once set up, **automatic deployment** is enabled:

1. Make code changes locally
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Feature: Added new functionality"
   git push
   ```
3. **Vercel** auto-deploys frontend (2-3 min)
4. **Railway** auto-deploys backend (3-5 min)

---

## 🎯 Production Checklist

Before going live:

- [ ] Updated CORS origins in backend config
- [ ] Added GOOGLE_API_KEY to Railway
- [ ] Frontend REACT_APP_API_URL points to Railway backend
- [ ] Tested signup/login flow
- [ ] Tested document upload
- [ ] Tested chat with "Hi" (greeting handler)
- [ ] Tested real queries with document context
- [ ] Checked browser console for errors
- [ ] Verified all 3 pages work (Chat, Documents, Dashboard)
- [ ] Tested on mobile viewport
- [ ] Added custom domain (optional)

---

## 📊 Monitor Your Deployment

### Vercel Analytics (Free)
- Dashboard → Your Project → Analytics
- See page views, performance metrics

### Railway Metrics
- Dashboard → Metrics tab
- Monitor CPU, RAM, requests

---

## 🚀 Next Steps After Deployment

### Custom Domain (Optional)

**Vercel:**
1. Settings → Domains → Add Domain
2. Follow DNS instructions

**Railway:**
1. Settings → Networking → Custom Domain
2. Add CNAME record

### Upgrade Storage (When Needed)

**For production use with many documents:**
- Use **Supabase** (PostgreSQL) instead of SQLite (free tier available)
- Use **Pinecone** or **Qdrant Cloud** for vector storage (free tier available)

---

## 🎉 Congratulations!

Your AI Knowledge Continuity System is now live and accessible worldwide!

**Share your deployment:**
- Frontend: `https://your-project.vercel.app`
- Backend API: `https://your-backend.railway.app/docs` (Swagger UI)

---

## 📞 Need Help?

**Common Resources:**
- Vercel Docs: https://vercel.com/docs
- Railway Docs: https://docs.railway.app
- GitHub Issues: Report bugs in your repository

**Quick Debugging:**
1. Check Railway logs for backend errors
2. Check Vercel deployment logs
3. Check browser console (F12) for frontend errors
4. Test `/api/health` endpoint directly
