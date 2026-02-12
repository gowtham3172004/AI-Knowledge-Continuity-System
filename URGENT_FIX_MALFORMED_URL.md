# 🔧 URGENT FIX - Malformed URL Error

## The Problem
Your Vercel deployment is sending requests to a malformed URL:
```
https://ai-knowledge-continuity-system-56rOlc2io.vercel.app/ai-knowledge-continuity-system-production.up.railway.app/api/auth/register
```

Instead of:
```
https://ai-knowledge-continuity-system-production.up.railway.app/api/auth/register
```

## Root Cause
The `REACT_APP_API_URL` environment variable on Vercel is set incorrectly.

---

## ✅ Solution - 3 Steps

### Step 1: Fix Vercel Environment Variable

1. **Go to Vercel Dashboard**: https://vercel.com/dashboard
2. **Select your project**: Click on "ai-knowledge-continuity-system"
3. **Go to Settings** → **Environment Variables**
4. **Find** `REACT_APP_API_URL`
5. **Update its value to**:
   ```
   https://ai-knowledge-continuity-system-production.up.railway.app
   ```
   ⚠️ **IMPORTANT:**
   - Must start with `https://`
   - NO trailing slash
   - NO `/api` at the end
   - Just the Railway domain

6. **Save** the changes

### Step 2: Redeploy Frontend

After updating the environment variable:

1. Go to **Deployments** tab in Vercel
2. Click on the latest deployment
3. Click the **"..." menu** → **"Redeploy"**
4. Wait 2-3 minutes for deployment to complete

### Step 3: Commit and Push Local Changes

I've fixed the code to be more robust, so commit these changes:

```bash
cd "/Users/macbook/Documents/Final-Year Project/AI Knowledge Continuity System"

git add .
git commit -m "Fix: Add URL normalization to handle malformed API URLs"
git push origin main
```

This will auto-deploy to Vercel with the fixes.

---

## 🧪 Test After Fix

Visit your Vercel URL and test:

1. **Open Browser Console** (F12)
2. **Click "Sign Up"**
3. **Check Network Tab**
4. **Verify URL is**:
   ```
   https://ai-knowledge-continuity-system-production.up.railway.app/api/auth/register
   ```
   (Should NOT include the Vercel domain)

---

## 🔍 Debug: Check Current Environment Variable

To see what Vercel is currently using:

1. In Vercel Dashboard → Your Project
2. Settings → Environment Variables
3. Look at `REACT_APP_API_URL`
4. It might be set to one of these WRONG values:
   - ❌ `ai-knowledge-continuity-system-production.up.railway.app` (missing https://)
   - ❌ `https://ai-knowledge-continuity-system-production.up.railway.app/` (trailing slash)
   - ❌ `/ai-knowledge-continuity-system-production.up.railway.app` (starts with /)
   - ❌ Empty or undefined

5. It MUST be:
   - ✅ `https://ai-knowledge-continuity-system-production.up.railway.app`

---

## 📱 Alternative: Use Vercel CLI (Optional)

If you have Vercel CLI installed:

```bash
cd frontend

# Set environment variable
vercel env add REACT_APP_API_URL production
# When prompted, enter: https://ai-knowledge-continuity-system-production.up.railway.app

# Redeploy
vercel --prod
```

---

## ✨ What I Fixed in the Code

I added URL normalization to handle edge cases:

1. **`frontend/src/services/api.ts`**:
   - Added `normalizeBaseURL()` function
   - Automatically adds `https://` if missing
   - Removes trailing slashes
   - Prevents malformed URLs

2. **`frontend/src/contexts/AuthContext.tsx`**:
   - Added same normalization
   - Ensures auth requests use correct URL

3. **`frontend/.env.production`**:
   - Updated with correct Railway URL

These changes make the app more resilient to environment variable issues.

---

## 🚨 Common Mistakes to Avoid

When setting `REACT_APP_API_URL` on Vercel:

❌ **DON'T**:
- Include `/api` at the end
- Add trailing slash `/`
- Forget `https://` protocol
- Copy the Vercel URL instead of Railway URL
- Leave it empty

✅ **DO**:
- Use full Railway backend URL
- Include `https://` protocol
- No trailing characters
- Double-check for typos

---

## 🎯 Expected Result

After fixing, the network tab should show:

**Request URL**:
```
https://ai-knowledge-continuity-system-production.up.railway.app/api/auth/register
```

**Status**: `200 OK` (after successful signup)

**Response**: 
```json
{
  "token": "jwt-token-here",
  "user": {
    "id": 1,
    "email": "your@email.com",
    "full_name": "Your Name",
    "role": "developer"
  }
}
```

---

## 🆘 Still Not Working?

If you still get errors after following all steps:

1. **Check Railway backend is running**:
   - Visit: https://ai-knowledge-continuity-system-production.up.railway.app/api/health
   - Should return: `{"status":"healthy",...}`

2. **Clear browser cache**:
   - Press `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
   - Or use incognito mode

3. **Check CORS on backend**:
   - Railway logs should show no CORS errors
   - Backend allows `*.vercel.app` domains

4. **Verify both deployments finished**:
   - Railway backend: Running
   - Vercel frontend: Deployed

---

## 📞 Quick Checklist

- [ ] Updated Vercel environment variable
- [ ] Redeployed Vercel frontend
- [ ] Committed and pushed code changes
- [ ] Tested signup with browser console open
- [ ] Verified URL in network tab is correct
- [ ] Successfully created account

---

**Estimated Fix Time**: 5 minutes

Once you update the Vercel environment variable and redeploy, the issue will be resolved! 🎉
