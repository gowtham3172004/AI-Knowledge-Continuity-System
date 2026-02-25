# Deployment Guide: Supabase + Vercel + Render

Complete guide to deploy the AI Knowledge Continuity System using:
- **Supabase** — Authentication + PostgreSQL database
- **Vercel** — Frontend (React)
- **Render** — Backend (FastAPI)

---

## Step 1: Set Up Supabase

### 1.1 Create a Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign up / sign in
2. Click **"New Project"**
3. Fill in:
   - **Name**: `ai-knowledge-system`
   - **Database Password**: (save this somewhere safe)
   - **Region**: Choose closest to your users
4. Wait for the project to be provisioned (~2 minutes)

### 1.2 Get Your API Keys

1. Go to **Settings → API** in the Supabase dashboard
2. Copy these three values (you'll need them later):
   - **Project URL** → `SUPABASE_URL` (e.g., `https://abcdefgh.supabase.co`)
   - **anon public key** → `SUPABASE_ANON_KEY`
   - **service_role secret key** → `SUPABASE_SERVICE_ROLE_KEY`

### 1.3 Create Database Tables

1. Go to **SQL Editor** in the Supabase dashboard
2. Click **"New Query"**
3. Copy and paste the entire contents of [`setup_supabase.sql`](setup_supabase.sql)
4. Click **"Run"**
5. You should see "Success. No rows returned" — this means all tables and policies were created

### 1.4 Configure Authentication

1. Go to **Authentication → Providers** in the Supabase dashboard
2. **Email** provider should be enabled by default
3. Optionally, go to **Authentication → URL Configuration**:
   - Set **Site URL** to your Vercel frontend URL (after deploying)
   - Add redirect URLs if needed

> **Optional**: To disable email confirmation for testing:
> Go to **Authentication → Providers → Email** → Turn OFF "Confirm email"

---

## Step 2: Deploy Backend on Render

### 2.1 Push Code to GitHub

Make sure all changes are committed and pushed:

```bash
git add -A
git commit -m "Migrate to Supabase auth + Render deployment"
git push origin main
```

### 2.2 Create Render Web Service

1. Go to [render.com](https://render.com) and sign up / sign in
2. Click **"New +" → "Web Service"**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `ai-knowledge-continuity-api`
   - **Region**: Choose closest to your Supabase project
   - **Branch**: `main`
   - **Root Directory**: (leave empty — uses repo root)
   - **Runtime**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free (or Starter for better performance)

### 2.3 Set Environment Variables on Render

In Render dashboard → your service → **Environment**:

| Key | Value |
|-----|-------|
| `PYTHON_VERSION` | `3.12.0` |
| `GEMINI_API_KEY` | Your Gemini API key |
| `GEMINI_MODEL` | `gemini-2.5-flash` |
| `LLM_PROVIDER` | `gemini` |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` |
| `SUPABASE_URL` | Your Supabase Project URL |
| `SUPABASE_ANON_KEY` | Your Supabase anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | Your Supabase service_role key |

Click **"Save Changes"** — Render will redeploy automatically.

### 2.4 Verify Backend

After deployment completes, visit:
```
https://your-render-app.onrender.com/api/health
```

You should see:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": { ... }
}
```

> **Note**: On Render's free tier, the first request may take 30-60 seconds (cold start).

---

## Step 3: Deploy Frontend on Vercel

### 3.1 Import Project on Vercel

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click **"Add New..." → "Project"**
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: `Other` (or `Create React App`)
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `build`
   - **Install Command**: `npm ci --legacy-peer-deps`

### 3.2 Set Environment Variables on Vercel

In Vercel dashboard → your project → **Settings → Environment Variables**:

| Key | Value |
|-----|-------|
| `REACT_APP_SUPABASE_URL` | Your Supabase Project URL |
| `REACT_APP_SUPABASE_ANON_KEY` | Your Supabase anon key |
| `REACT_APP_API_URL` | Your Render backend URL (e.g., `https://ai-knowledge-continuity-api.onrender.com`) |

> **Important**: Do NOT add a trailing slash to `REACT_APP_API_URL`

### 3.3 Deploy

Click **"Deploy"**. Vercel will build and deploy the frontend.

### 3.4 Update Supabase Site URL

After deploying, go back to Supabase:
1. **Authentication → URL Configuration**
2. Set **Site URL** to your Vercel URL (e.g., `https://your-app.vercel.app`)

---

## Step 4: Verify Everything Works

### 4.1 Test the Flow

1. Open your Vercel frontend URL
2. Click **"Sign Up"** and create an account
3. You should be logged in and see the chat interface
4. Try asking a question (e.g., "What lessons were learned?")
5. Check the **Documents** page — upload a file
6. Check the **Dashboard** for knowledge health

### 4.2 Troubleshooting

**"Failed to fetch" or CORS errors:**
- Verify `REACT_APP_API_URL` in Vercel matches your Render URL exactly
- Check Render logs for startup errors
- Ensure backend is running (check `/api/health`)

**Authentication errors:**
- Verify `REACT_APP_SUPABASE_URL` and `REACT_APP_SUPABASE_ANON_KEY` in Vercel
- Verify `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in Render
- Check Supabase Auth logs in Dashboard → Authentication → Users

**"relation does not exist" errors:**
- Make sure you ran `setup_supabase.sql` in the Supabase SQL Editor

---

## Local Development

### Backend

```bash
# Navigate to project root
cd "AI Knowledge Continuity System"

# Create .env with your Supabase keys (see .env file)
# Set SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY

# Activate virtual environment
source .venv/bin/activate

# Start backend
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
# Navigate to frontend
cd frontend

# Create .env.local
cp .env.example .env.local
# Edit .env.local with your Supabase keys and API URL

# Install & start
npm install
npm start
```

The frontend runs at http://localhost:3000, backend at http://localhost:8000.

---

## Environment Variables Summary

### Backend (Render / Local .env)

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_ANON_KEY` | Supabase anon/public key | Yes |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key | Yes |
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `GEMINI_MODEL` | Gemini model name | No (default: gemini-2.5-flash) |
| `LLM_PROVIDER` | LLM provider | No (default: gemini) |
| `EMBEDDING_MODEL` | Embedding model | No (default: sentence-transformers/all-MiniLM-L6-v2) |

### Frontend (Vercel / Local .env.local)

| Variable | Description | Required |
|----------|-------------|----------|
| `REACT_APP_SUPABASE_URL` | Supabase project URL | Yes |
| `REACT_APP_SUPABASE_ANON_KEY` | Supabase anon/public key | Yes |
| `REACT_APP_API_URL` | Backend API URL (Render) | Yes |
