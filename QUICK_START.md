# 🚀 Quick Start Guide

## Run the Complete System in 5 Minutes

### Prerequisites
- Python 3.12+ with virtual environment
- Node.js 16+ and npm
- Google Gemini API key

---

## Step 1: Start the Backend API

```bash
# Navigate to project root
cd "/Users/macbook/Documents/Final-Year Project/AI Knowledge Continuity System"

# Activate virtual environment
# Recommended: Python 3.12 for local embedding support
source .venv312/bin/activate 

# Start FastAPI server
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**Verify**: Open http://localhost:8000 - you should see:
```json
{
  "message": "AI Knowledge Continuity System API",
  "version": "1.0.0",
  "docs": "/docs"
}
```

**API Documentation**: http://localhost:8000/docs

---

## Step 2: Start the Frontend UI

Open a **new terminal**:

```bash
# Navigate to frontend directory
cd "/Users/macbook/Documents/Final-Year Project/AI Knowledge Continuity System/frontend"

# Install dependencies (first time only)
npm install

# Start development server
npm start
```

**Verify**: Browser will open at http://localhost:3000

You should see:
- Professional header with "Knowledge Continuity System"
- Sidebar with "New Conversation" button
- Empty chat state with guidance
- System health indicator showing "Online"

---

## Step 3: Test the System

### Basic Query Test
1. Click "New Conversation" in sidebar
2. Type in chat: `"What lessons were learned from the backend project?"`
3. Press Enter

Expected response:
- ✅ AI answer appears
- ✅ Source documents shown in right panel
- ✅ Confidence score displayed
- ✅ Processing time shown

### Tacit Knowledge Test
Ask: `"What were the challenges faced by the team?"`

Look for:
- 🟢 Green badge: "Experience-Based Insight"

### Decision Traceability Test
Ask: `"What technology decisions were made?"`

Look for:
- 🟣 Purple "Decision Trace Available" panel
- Expandable panel with rationale, alternatives, trade-offs

### Knowledge Gap Test
Ask: `"What is the quantum computing strategy?"`

Look for:
- ⚠️ Yellow/amber warning: "Knowledge Gap Detected"
- Confidence score
- Clear message about missing knowledge

---

## Step 4: Explore Features

### Role Selector
1. Click dropdown in header (default: "General User")
2. Try different roles: Developer, Manager, Analyst, Executive
3. Notice how responses adapt to your role

### Conversation History
1. Create multiple conversations
2. Click between them in sidebar
3. Each conversation maintains its own history
4. Delete conversations with trash icon

### Source Attribution
1. Check right sidebar after any query
2. Expand source cards
3. See knowledge type badges
4. View relevance scores

---

## Troubleshooting

### Backend Not Starting
**Problem**: `ModuleNotFoundError` or import errors

**Solution**:
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Frontend "Failed to fetch"
**Problem**: Can't reach backend

**Solutions**:
1. Check backend is running on port 8000
2. Verify `.env` has `REACT_APP_API_URL=http://localhost:8000`
3. Check browser console for CORS errors

### Tailwind Styles Not Working
**Problem**: Plain HTML, no styling

**Solution**:
```bash
cd frontend
npm install
rm -rf node_modules/.cache
npm start
```

### Slow LLM Responses
**Problem**: 30+ second delays

**Explanation**: This is normal for Gemini API. First response takes longer.

---

## Architecture Overview

```
┌─────────────────────────────────────────┐
│  Frontend (React + TypeScript)          │
│  Port: 3000                              │
│  - Professional enterprise UI            │
│  - Knowledge-aware components            │
│  - Real-time updates                     │
└───────────────┬─────────────────────────┘
                │
                │ HTTP/JSON
                │ axios
                ▼
┌─────────────────────────────────────────┐
│  Backend API (FastAPI)                   │
│  Port: 8000                              │
│  - RESTful endpoints                     │
│  - Request validation                    │
│  - Error handling                        │
└───────────────┬─────────────────────────┘
                │
                │ Python
                │
                ▼
┌─────────────────────────────────────────┐
│  RAG Pipeline                            │
│  - FAISS vector store                    │
│  - Sentence transformers (embeddings)    │
│  - Google Gemini 2.5-flash (LLM)        │
│  - Knowledge features:                   │
│    * Tacit knowledge extraction          │
│    * Decision traceability               │
│    * Knowledge gap detection             │
└─────────────────────────────────────────┘
```

---

## Example Queries to Try

### For Tacit Knowledge
- "What challenges did the team face?"
- "What lessons were learned?"
- "What would you do differently?"

### For Decision Traceability
- "Why was Python chosen?"
- "What technology decisions were made?"
- "Why use FastAPI?"

### For Knowledge Gaps
- "What is the cloud migration strategy?" (if not documented)
- "How do we handle data privacy in Europe?"
- "What's our AI governance policy?"

---

## Next Steps

1. **Add Your Own Documents**
   ```bash
   # Place documents in data/ folder
   python main.py --ingest
   ```

2. **Customize Frontend**
   - Edit colors in `frontend/tailwind.config.js`
   - Modify logo in `frontend/src/components/Layout/Header.tsx`
   - Add features in respective component files

3. **Deploy to Production**
   - See `frontend/DEPLOYMENT.md`
   - Configure environment variables
   - Set up HTTPS
   - Deploy backend and frontend

4. **Monitor Usage**
   - Check backend logs
   - Monitor API response times
   - Track knowledge gap detections

---

## Support

- **Backend Issues**: Check `logs/` directory
- **Frontend Issues**: Check browser console (F12)
- **API Documentation**: http://localhost:8000/docs
- **Project Documentation**: See README.md files

---

## Success Indicators

✅ Backend shows "Application startup complete"  
✅ Frontend shows "Compiled successfully"  
✅ System health indicator is green  
✅ Queries return answers within 10-15 seconds  
✅ Sources appear in right panel  
✅ Knowledge badges display correctly  

---

**You're all set! Start exploring your AI Knowledge Continuity System.**

🎉 The system is fully functional and production-ready!
