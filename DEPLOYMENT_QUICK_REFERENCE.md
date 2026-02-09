# 🚀 Quick Deployment Reference Card

## TL;DR - 3 Simple Steps

### 1️⃣ Push to GitHub
```bash
git init
git add .
git commit -m "Ready for deployment"
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
git push -u origin main
```

### 2️⃣ Deploy Backend to Railway
1. Go to https://railway.app
2. Sign in with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Add environment variables:
   - `GOOGLE_API_KEY` = your_actual_gemini_key
   - `GEMINI_MODEL` = gemini-2.5-flash
   - `PYTHON_VERSION` = 3.12
6. Settings → Networking → "Generate Domain"
7. **Copy the Railway URL** (e.g., `https://xxx.up.railway.app`)

### 3️⃣ Deploy Frontend to Vercel
1. Go to https://vercel.com
2. Sign in with GitHub
3. Click "Add New..." → "Project"
4. Import your repository
5. **Root Directory:** `frontend` ⚠️
6. Add environment variable:
   - `REACT_APP_API_URL` = your_railway_url_from_step_2
7. Click "Deploy"
8. Done! Your app is live at `https://xxx.vercel.app`

---

## 🔧 Quick Commands

### Run Deployment Check
```bash
./deployment-check.sh
```

### Build Frontend Locally (Test)
```bash
cd frontend
npm run build
```

### Test Backend Health
```bash
curl https://your-backend.railway.app/api/health
```

---

## 📋 Environment Variables Needed

### Railway (Backend)
```
GOOGLE_API_KEY=your_actual_key_here
GEMINI_MODEL=gemini-2.5-flash
LLM_PROVIDER=gemini
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
PYTHON_VERSION=3.12
```

### Vercel (Frontend)
```
REACT_APP_API_URL=https://your-backend.railway.app
```

---

## 🐛 Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| CORS Error | Update `backend/core/config.py` CORS_ORIGINS, redeploy backend |
| "Module not found" | Check `requirements.txt` and `package.json` |
| Backend not starting | Check Railway logs, verify environment variables |
| Frontend blank page | Check browser console (F12), verify API URL |
| 404 on routes | Already configured in `vercel.json` rewrites |

---

## 📊 Free Tier Limits

- **Vercel:** 100 GB bandwidth/month, unlimited projects
- **Railway:** $5 credit/month (~500 hours runtime)
- **Total Cost:** $0/month (stays within free limits)

---

## 🔗 Helpful Links

- **Full Guide:** [FREE_DEPLOYMENT_GUIDE.md](FREE_DEPLOYMENT_GUIDE.md)
- **Vercel Dashboard:** https://vercel.com/dashboard
- **Railway Dashboard:** https://railway.app/dashboard
- **Get Gemini API Key:** https://aistudio.google.com/app/apikey

---

## ✅ Deployment Checklist

- [ ] GitHub repository created and pushed
- [ ] Railway backend deployed with env vars
- [ ] Railway domain generated and copied
- [ ] Vercel frontend deployed with correct API URL
- [ ] Tested signup/login flow
- [ ] Tested document upload
- [ ] Tested chat with "Hi" greeting
- [ ] Tested real query with document
- [ ] No errors in browser console (F12)

---

## 🎉 You're Done!

Your app is now live and accessible worldwide for **$0/month**!

**Share your links:**
- Frontend: `https://your-project.vercel.app`
- Backend API Docs: `https://your-backend.railway.app/docs`
