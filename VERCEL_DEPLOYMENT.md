# 🚀 Vercel Deployment Guide

## Complete Production Deployment to Vercel

This guide covers deploying both **frontend (React)** and **backend (FastAPI)** to Vercel.

---

## 📦 Part 1: Frontend Deployment (Main App)

### Prerequisites
- Vercel account (free tier works)
- GitHub repository (optional but recommended)

### Option A: Deploy via Vercel CLI (Fastest)

1. **Install Vercel CLI**:
   ```bash
   npm install -g vercel
   ```

2. **Navigate to frontend**:
   ```bash
   cd frontend
   ```

3. **Login to Vercel**:
   ```bash
   vercel login
   ```

4. **Deploy**:
   ```bash
   # For preview deployment
   vercel
   
   # For production
   vercel --prod
   ```

5. **Set environment variables**:
   ```bash
   vercel env add REACT_APP_API_URL production
   # When prompted, enter your backend URL: https://your-backend.vercel.app
   ```

### Option B: Deploy via Vercel Dashboard

1. **Push code to GitHub**:
   ```bash
   git add .
   git commit -m "Production ready deployment"
   git push origin main
   ```

2. **Import to Vercel**:
   - Go to https://vercel.com/new
   - Click "Import Project"
   - Select your repository
   - Framework: **Create React App**
   - Root Directory: `frontend`

3. **Configure Build Settings**:
   - Build Command: `npm run build`
   - Output Directory: `build`
   - Install Command: `npm install`

4. **Add Environment Variables**:
   - Go to Project Settings → Environment Variables
   - Add: `REACT_APP_API_URL` = `https://your-backend.vercel.app`

5. **Deploy**: Click "Deploy"

---

## 🔧 Part 2: Backend Deployment (API)

### Option 1: Serverless Functions (Recommended for Vercel)

Create `backend/api/index.py`:
```python
from backend.main import app

# Vercel serverless function handler
def handler(request, context):
    return app(request, context)
```

### Option 2: Deploy to Separate Platform

**Better options for FastAPI:**
- **Railway** - Easiest for Python apps
- **Render** - Free tier available
- **Google Cloud Run** - Best for Gemini API
- **Fly.io** - Good performance

### Backend on Railway (Recommended)

1. **Go to https://railway.app**
2. Click "Start a New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Configure:
   - Root Directory: `/`
   - Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
6. Add Environment Variables:
   ```
   GOOGLE_API_KEY=your_api_key
   PORT=8000
   ```
7. Deploy!

### Backend on Render

1. **Go to https://render.com**
2. Click "New +" → "Web Service"
3. Connect GitHub repository
4. Configure:
   - Name: `ai-knowledge-backend`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. Add Environment Variables:
   ```
   GOOGLE_API_KEY=your_api_key
   PYTHON_VERSION=3.11
   ```
6. Create Web Service

---

## 🔗 Part 3: Connect Frontend to Backend

After backend is deployed, update frontend environment:

### Update Frontend Environment Variable

**Via Vercel Dashboard**:
1. Go to your frontend project
2. Settings → Environment Variables
3. Edit `REACT_APP_API_URL`
4. Set value to your backend URL (e.g., `https://ai-knowledge-backend.up.railway.app`)
5. Redeploy: Deployments → Click "..." → "Redeploy"

**Via Vercel CLI**:
```bash
vercel env add REACT_APP_API_URL production
# Enter: https://your-backend-url.com
vercel --prod
```

---

## ✅ Part 4: Verification

### Test Your Deployment

1. **Frontend Health**:
   - Open your Vercel URL: `https://your-app.vercel.app`
   - Check if UI loads correctly
   - Look for green health indicator in header

2. **Backend Health**:
   - Visit: `https://your-backend-url.com/api/health`
   - Should return JSON: `{"status": "healthy"}`

3. **End-to-End Test**:
   - Send a query from the UI
   - Verify you get a response
   - Check all three knowledge features work

### Debug Connection Issues

**If frontend can't reach backend**:

1. Check CORS in `backend/core/config.py`:
   ```python
   CORS_ORIGINS = [
       "http://localhost:3000",
       "https://your-app.vercel.app",  # Add this
       "https://*.vercel.app",          # Allow all Vercel preview deployments
   ]
   ```

2. Redeploy backend after CORS update

3. Check browser console for errors

---

## 📊 Part 5: Production Optimizations

### Frontend Optimizations

1. **Enable Gzip Compression** (Automatic on Vercel)

2. **Add Custom Domain** (Optional):
   - Vercel Dashboard → Settings → Domains
   - Add your custom domain

3. **Configure Caching**:
   - Already configured in `vercel.json`
   - Static assets cached for 1 year

### Backend Optimizations

1. **Add Rate Limiting**:
   ```python
   # In backend/main.py
   from slowapi import Limiter
   from slowapi.util import get_remote_address
   
   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   ```

2. **Enable Response Compression**:
   ```python
   from fastapi.middleware.gzip import GZipMiddleware
   app.add_middleware(GZipMiddleware, minimum_size=1000)
   ```

3. **Add Monitoring**:
   - Use Sentry for error tracking
   - Use Datadog or New Relic for performance

---

## 🔐 Part 6: Security Checklist

### Frontend
- [x] Environment variables not exposed in code
- [x] HTTPS enabled (automatic on Vercel)
- [x] No API keys in frontend code
- [x] CSP headers configured

### Backend
- [x] CORS configured for production domain only
- [x] API keys stored in environment variables
- [x] Rate limiting enabled
- [x] Input validation on all endpoints
- [x] Error messages don't expose internals

---

## 🎯 Part 7: Post-Deployment

### Monitor Your Application

1. **Vercel Analytics**:
   - Automatic on Vercel
   - View in Dashboard → Analytics

2. **Error Tracking**:
   - Add Sentry to both frontend and backend
   - Get alerts for production errors

3. **Performance Monitoring**:
   - Check Vercel Speed Insights
   - Monitor API response times

### Update Deployment

**Frontend Updates**:
```bash
# Make changes, then:
git add .
git commit -m "Update feature X"
git push origin main
# Vercel auto-deploys
```

**Backend Updates**:
- Push to GitHub
- Railway/Render auto-deploys

---

## 💰 Cost Estimates

### Free Tier Limits

**Vercel (Frontend)**:
- 100 GB bandwidth/month
- Unlimited deployments
- Custom domains
- ✅ More than enough for this app

**Railway (Backend)**:
- $5 free credit/month
- ~500 hours of runtime
- ✅ Sufficient for development/testing

**Render (Backend)**:
- Free tier available
- Spins down after inactivity
- ✅ Good for side projects

**Gemini API**:
- Free tier: 60 requests/minute
- Paid: $0.00025 per 1K characters
- ✅ Very affordable

### Paid Options (If Needed)

**Vercel Pro**: $20/month
- 1 TB bandwidth
- Advanced analytics
- Team collaboration

**Railway**: Pay-as-you-go
- $0.000231 per GB-second
- ~$10-20/month for steady traffic

---

## 🚨 Troubleshooting

### Common Issues

**1. "Module not found" on Vercel**
- Solution: Ensure all dependencies in `package.json`
- Run `npm install` locally first

**2. "Failed to fetch" from backend**
- Solution: Check CORS settings
- Verify `REACT_APP_API_URL` is correct

**3. Backend timeout**
- Solution: Increase timeout in `vercel.json`:
  ```json
  {
    "functions": {
      "api/**/*.py": {
        "maxDuration": 60
      }
    }
  }
  ```

**4. Build fails on Vercel**
- Solution: Check build logs
- Ensure TypeScript compiles locally: `npm run build`

**5. 502 Bad Gateway**
- Solution: Backend is down or unreachable
- Check backend health endpoint

---

## 📝 Environment Variables Summary

### Frontend (.env.production)
```env
REACT_APP_API_URL=https://your-backend-url.com
REACT_APP_NAME=AI Knowledge Continuity System
REACT_APP_VERSION=1.0.0
```

### Backend (Railway/Render)
```env
GOOGLE_API_KEY=your_gemini_api_key
PORT=8000
DEBUG=false
LOG_LEVEL=INFO
VECTOR_STORE_PATH=vector_store/faiss_index
ENABLE_KNOWLEDGE_FEATURES=true
```

---

## ✅ Deployment Checklist

### Before Deployment
- [ ] All tests pass
- [ ] Build succeeds locally
- [ ] Environment variables documented
- [ ] CORS configured for production domain
- [ ] API keys secured
- [ ] README updated with live URLs

### After Deployment
- [ ] Frontend accessible
- [ ] Backend API responding
- [ ] Health checks passing
- [ ] End-to-end query works
- [ ] All three knowledge features operational
- [ ] Error tracking configured
- [ ] Monitoring set up
- [ ] Custom domain configured (if applicable)

---

## 🎊 Success!

Your AI Knowledge Continuity System is now live in production!

**Next Steps**:
1. Share the URL with your team
2. Monitor usage and errors
3. Gather user feedback
4. Plan v2 features

**Your URLs**:
- Frontend: `https://your-app.vercel.app`
- Backend: `https://your-backend.railway.app`
- API Docs: `https://your-backend.railway.app/docs`

---

**Need Help?**
- Vercel Docs: https://vercel.com/docs
- Railway Docs: https://docs.railway.app
- FastAPI Deployment: https://fastapi.tiangolo.com/deployment/

**Version**: 1.0.0  
**Last Updated**: January 2026  
**Status**: ✅ Production Ready
