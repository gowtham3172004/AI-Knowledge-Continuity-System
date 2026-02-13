# 🚨 RAILWAY BACKEND IS DOWN - Complete Fix Guide

**Problem:** Railway backend returns 502 Bad Gateway - backend crashed/not running  
**Impact:** CORS errors appear because backend isn't responding at all  
**Solution:** Fix Railway deployment configuration

---

## 🔍 Step 1: Check Railway Deployment Logs

### Go to Railway Dashboard
1. Open: https://railway.app/dashboard
2. Find project: **"ai-knowledge-continuity-system"**
3. Click on the **backend service**
4. Click **"Deployments"** tab
5. Click the latest deployment
6. Click **"View Logs"**

### Look for These Common Errors:

#### Error 1: Missing Dependencies
```
ModuleNotFoundError: No module named 'pyjwt'
ModuleNotFoundError: No module named 'passlib'
ModuleNotFoundError: No module named 'bcrypt'
```

#### Error 2: Import Errors
```
ImportError: cannot import name 'xyz'
SyntaxError: invalid syntax
```

#### Error 3: Port/Startup Errors
```
Address already in use
Failed to bind to port
```

#### Error 4: Environment Variable Errors
```
KeyError: 'GOOGLE_API_KEY'
Configuration error
```

---

## ✅ Solution 1: Use Correct Start Command

Railway needs the exact start command. In Railway dashboard:

### Settings → Deploy
**Start Command:**
```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

**Or if that doesn't work:**
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

**Watch Paths:**
```
backend/**
requirements.txt
config/**
core/**
rag/**
```

---

## ✅ Solution 2: Verify Environment Variables

Railway → Settings → Variables

**Required Variables:**
```env
GOOGLE_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp
LLM_PROVIDER=gemini
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
PYTHON_VERSION=3.12
PORT=8000
```

**Important:**
- `PORT` should be auto-set by Railway (don't manually set it unless needed)
- `GOOGLE_API_KEY` MUST be your actual Gemini API key

---

## ✅ Solution 3: Fix requirements.txt

If dependencies are missing, update requirements.txt:

```bash
cd "/Users/macbook/Documents/Final-Year Project/AI Knowledge Continuity System"
source .venv/bin/activate
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update requirements.txt with all dependencies"
git push origin main
```

Wait for Railway to auto-deploy.

---

## ✅ Solution 4: Create Railway Configuration File

Create a `railway.json` in the project root:

**File: `railway.json`**
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn backend.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

Then commit and push.

---

## ✅ Solution 5: Create Procfile (Alternative)

Some platforms need a Procfile:

**File: `Procfile`**
```
web: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

---

## ✅ Solution 6: Simplify CORS (Temporary Test)

If backend starts but CORS still fails, temporarily use this simpler CORS:

Edit `backend/main.py`:

```python
# Configure CORS - Temporarily allow all
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

This disables credentials but allows testing. After confirming backend works, we can add proper CORS with credentials.

---

## 🧪 Test Locally First

Before deploying to Railway, verify backend works locally:

```bash
cd "/Users/macbook/Documents/Final-Year Project/AI Knowledge Continuity System"
source .venv/bin/activate

# Test if backend starts
.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000

# In another terminal, test health
curl http://localhost:8000/api/health

# Should return: {"status":"healthy",...}
```

If local backend works, the code is fine - it's a Railway config issue.

---

## 🔄 Alternative: Deploy Backend on Render.com (Free)

If Railway continues to fail, try Render (also free):

### Step 1: Go to Render
1. Visit: https://render.com
2. Sign up with GitHub
3. Click **"New +"** → **"Web Service"**

### Step 2: Connect Repository
1. Select your GitHub repo
2. Name: `ai-knowledge-backend`
3. **Root Directory:** Leave empty
4. **Environment:** Python
5. **Region:** Select closest to you

### Step 3: Configure
**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

**Environment Variables:**
```
GOOGLE_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.0-flash-exp
```

### Step 4: Deploy
Click **"Create Web Service"**

Wait 5-10 minutes for deployment.

### Step 5: Update Frontend
Get your Render URL (e.g., `https://ai-knowledge-backend.onrender.com`)

Update `frontend/src/config/api.config.ts`:
```typescript
const PRODUCTION_API_URL = 'https://ai-knowledge-backend.onrender.com';
```

Commit and push.

---

## 📋 Debugging Checklist

- [ ] Railway logs show no errors
- [ ] All environment variables are set
- [ ] Start command is correct: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- [ ] requirements.txt includes: pyjwt, passlib, bcrypt, fastapi, uvicorn
- [ ] Backend works locally on port 8000
- [ ] Health endpoint returns 200: `curl https://your-backend.railway.app/api/health`
- [ ] Railway service status is "Running" (not "Crashed")

---

## 🎯 Quick Fix Steps (In Order)

1. **Check Railway logs** - Find the actual error
2. **Fix the error** - Usually missing env var or dependency
3. **Redeploy** - Railway auto-deploys on git push
4. **Test health endpoint** - `curl https://your-backend.railway.app/api/health`
5. **If healthy, test signup** - Should work now

---

## 🆘 If Nothing Works

**Nuclear Option: Fresh Railway Deployment**

1. Delete the Railway project
2. Create new Railway project
3. Deploy from GitHub (select your repo)
4. Configure environment variables
5. Set start command
6. Deploy

Sometimes a fresh start fixes weird caching/config issues.

---

## 📞 Next Steps

1. **Go to Railway Dashboard NOW**
2. **Check the deployment logs**
3. **Find the error message**
4. **Share the error here**
5. I'll help you fix it immediately

---

**The backend MUST be running before CORS will work!** 🎯

Once backend returns 200 on `/api/health`, the CORS fix I already pushed will work perfectly.
