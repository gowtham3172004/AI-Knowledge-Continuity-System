# AI Knowledge Continuity System - Frontend

**Production-grade React + TypeScript UI** for the AI Knowledge Continuity System.

## 🎯 Overview

This is an **enterprise internal knowledge platform** UI, not a toy chatbot. It provides:

- **Professional Chat Interface** with knowledge-type awareness
- **Tacit Knowledge Insights** - Visual badges for experience-based knowledge
- **Decision Traceability** - Full audit trail for organizational decisions
- **Knowledge Gap Detection** - Transparent warnings when knowledge is missing
- **Source Attribution** - Clear document provenance and relevance scores

## 🏗️ Architecture

```
src/
├── components/
│   ├── Chat/
│   │   ├── ChatWindow.tsx          # Main chat interface
│   │   ├── MessageBubble.tsx       # Individual messages with metadata
│   │   └── SourcePanel.tsx         # Source document attribution
│   ├── Knowledge/
│   │   ├── DecisionTracePanel.tsx  # Decision audit trail (Feature #2)
│   │   ├── TacitInsightBadge.tsx   # Experience-based knowledge indicator
│   │   └── KnowledgeGapAlert.tsx   # Missing knowledge warnings (Feature #3)
│   └── Layout/
│       ├── Header.tsx               # Top nav with role selector
│       └── Sidebar.tsx              # Conversation history
├── pages/
│   └── ChatPage.tsx                 # Main application page
├── services/
│   └── api.ts                       # Centralized API client
├── hooks/
│   ├── useChat.ts                   # Chat state management
│   └── useKnowledge.ts              # System health & metadata
├── types/
│   └── api.ts                       # TypeScript contracts
└── styles/
    └── global.css                   # Tailwind + custom styles
```

## 🎨 Design System

### Color Palette
- **Primary (Blue-Gray)**: Trust, stability, enterprise feel
- **Accent (Indigo)**: Interactive elements, CTAs
- **Tacit (Green)**: Experience-based insights
- **Decision (Purple)**: Decision traceability
- **Warning (Amber)**: Knowledge gaps, staleness

### Typography
- **Font**: Inter (Google Fonts)
- **Hierarchy**: Clear distinction between UI chrome and content

### Components
- Clean, minimal, professional
- Subtle animations (no gimmicks)
- Accessibility-friendly (focus states, ARIA labels)

## 🚀 Quick Start

### Prerequisites
- Node.js 16+ and npm
- Backend API running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Set environment variables (optional)
cp .env.example .env

# Start development server
npm start
```

The app will open at `http://localhost:3000`.

### Build for Production

```bash
npm run build
```

Output will be in the `build/` directory.

## 🔌 API Integration

The frontend communicates with the FastAPI backend via REST API:

### Endpoints Used
- `POST /api/query` - Submit questions
- `GET /api/health` - System health check

### Configuration
Set the backend URL in `.env`:

```env
REACT_APP_API_URL=http://localhost:8000
```

## ✨ Key Features

### 1. Knowledge-Type Aware UI
Messages are visually differentiated based on knowledge type:
- **Explicit** - Standard response
- **Tacit** - Green badge: "Experience-Based Insight"
- **Decision** - Purple expandable panel with full audit trail

### 2. Decision Traceability Panel
When decision documents are used, shows:
- Decision title, author, date
- Rationale and context
- Alternatives considered
- Trade-offs accepted

Feels like an **audit log**, not plain text.

### 3. Knowledge Gap Handling
When `knowledge_gap_detected === true`:
- Prominent warning banner (not an error)
- Clear message: "This knowledge is currently missing"
- Confidence score displayed
- **No hallucinated content shown**
- Trust and safety communicated

### 4. Source Attribution
- Dedicated source panel (right sidebar)
- Expandable source cards
- Knowledge type badges
- Relevance scores
- Full document path

### 5. Role Selector
Choose your role for contextual responses:
- General User
- Developer
- Manager
- Analyst
- Executive

### 6. Conversation History
- Persistent conversation management
- Saved to localStorage
- Quick switching between conversations
- Delete conversations

## 🔧 Development

### Project Structure
```
frontend/
├── public/              # Static assets
├── src/
│   ├── components/      # Reusable React components
│   ├── pages/           # Page-level components
│   ├── services/        # API and external services
│   ├── hooks/           # Custom React hooks
│   ├── types/           # TypeScript type definitions
│   └── styles/          # Global styles
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── .env
```

### Code Quality
- **TypeScript** for type safety
- **ESLint** for code quality (built into CRA)
- **Prettier** (recommended for formatting)

### Testing
```bash
npm test
```

## 📦 Dependencies

### Core
- `react` - UI framework
- `react-dom` - DOM rendering
- `typescript` - Type safety

### UI/UX
- `tailwindcss` - Utility-first CSS
- `lucide-react` - Icon library
- `date-fns` - Date formatting

### Data Management
- `axios` - HTTP client
- `uuid` - Unique ID generation

## 🎯 Production Checklist

Before deploying to production:

- [ ] Set production API URL in `.env`
- [ ] Build optimized bundle: `npm run build`
- [ ] Test API connectivity
- [ ] Verify all knowledge features work
- [ ] Test responsive design
- [ ] Run accessibility audit
- [ ] Enable error monitoring (Sentry, etc.)
- [ ] Configure CDN for assets
- [ ] Set up CI/CD pipeline

## 🔒 Security

- API URL configured via environment variables
- No sensitive data in frontend code
- HTTPS recommended for production
- CORS configured on backend

## 📝 License

Part of the AI Knowledge Continuity System project.

## 🤝 Contributing

This is an enterprise internal tool. Follow the organization's contribution guidelines.

---

**Built with React + TypeScript + Tailwind CSS**  
*Enterprise Knowledge Platform • Decision Traceability • AI-Powered*
