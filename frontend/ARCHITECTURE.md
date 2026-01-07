# Frontend Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                    AI KNOWLEDGE CONTINUITY SYSTEM                        │
│                         Frontend Architecture                            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                              PRESENTATION LAYER                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                          ChatPage.tsx                            │  │
│  │                     (Main Application Page)                      │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│           │                       │                       │             │
│           ▼                       ▼                       ▼             │
│  ┌─────────────────┐    ┌──────────────────┐   ┌──────────────────┐   │
│  │     Header      │    │   ChatWindow     │   │   SourcePanel    │   │
│  │  - Logo         │    │  - Messages      │   │  - Documents     │   │
│  │  - Role Select  │    │  - Input Field   │   │  - Metadata      │   │
│  │  - Health       │    │  - Empty State   │   │  - Expand/Show   │   │
│  └─────────────────┘    └──────────────────┘   └──────────────────┘   │
│           │                       │                                     │
│  ┌─────────────────┐    ┌──────────────────┐                          │
│  │    Sidebar      │    │  MessageBubble   │                          │
│  │  - Conversations│    │  - User/AI       │                          │
│  │  - History      │    │  - Timestamp     │                          │
│  │  - Delete       │    │  - Metadata      │                          │
│  └─────────────────┘    └──────────────────┘                          │
│                                   │                                     │
│                          ┌────────┴────────┐                           │
│                          │                 │                           │
│              ┌───────────▼──────┐  ┌──────▼─────────────┐             │
│              │ Knowledge Features│  │  Loading/Error    │             │
│              │  Components       │  │    States         │             │
│              └───────────────────┘  └───────────────────┘             │
│                      │                                                 │
│     ┌────────────────┼────────────────┐                               │
│     │                │                │                               │
│     ▼                ▼                ▼                               │
│ ┌────────────┐ ┌──────────────┐ ┌───────────────┐                    │
│ │  Tacit     │ │  Decision    │ │  Knowledge    │                    │
│ │  Insight   │ │  Trace       │ │  Gap Alert    │                    │
│ │  Badge     │ │  Panel       │ │               │                    │
│ └────────────┘ └──────────────┘ └───────────────┘                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                             STATE MANAGEMENT                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌────────────────────────┐         ┌─────────────────────────┐        │
│  │      useChat Hook      │         │   useKnowledge Hook     │        │
│  │                        │         │                         │        │
│  │  • conversations       │         │  • systemHealth         │        │
│  │  • activeConversation  │         │  • isHealthy            │        │
│  │  • isLoading           │         │  • lastChecked          │        │
│  │  • sendMessage()       │         │  • checkHealth()        │        │
│  │  • createConversation()│         │  • getInfo()            │        │
│  │  • deleteConversation()│         │                         │        │
│  └────────────────────────┘         └─────────────────────────┘        │
│            │                                    │                       │
│            └────────────┬───────────────────────┘                       │
│                         ▼                                               │
│              ┌──────────────────────┐                                   │
│              │   localStorage       │                                   │
│              │  (Persistence)       │                                   │
│              └──────────────────────┘                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                              SERVICE LAYER                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                        api.ts (API Client)                       │  │
│  │                                                                  │  │
│  │  • query(request)              → POST /api/query                │  │
│  │  • ingest(request)             → POST /api/ingest               │  │
│  │  • healthCheck()               → GET  /api/health               │  │
│  │  • readinessCheck()            → GET  /api/health/ready         │  │
│  │  • getSystemInfo()             → GET  /api/health/info          │  │
│  │                                                                  │  │
│  │  Features:                                                       │  │
│  │  • Request/Response interceptors                                │  │
│  │  • Error formatting                                             │  │
│  │  • Logging                                                       │  │
│  │  • 60s timeout for LLM responses                                │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                   │                                     │
│                                   ▼                                     │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    Axios HTTP Client                             │  │
│  │                  (baseURL: localhost:8000)                       │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                              TYPE SYSTEM                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                        api.ts (TypeScript)                       │  │
│  │                                                                  │  │
│  │  Enums:                        Interfaces:                      │  │
│  │  • KnowledgeType               • QueryRequest                   │  │
│  │  • QueryRole                   • QueryResponse                  │  │
│  │  • GapSeverity                 • SourceDocument                 │  │
│  │                                • DecisionTrace                  │  │
│  │                                • KnowledgeGapInfo               │  │
│  │                                • Message                        │  │
│  │                                • Conversation                   │  │
│  │                                • HealthResponse                 │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                          STYLING & THEMING                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    Tailwind CSS Configuration                    │  │
│  │                                                                  │  │
│  │  Color Palette:                                                  │  │
│  │  • primary (blue-gray)    → Trust, stability                    │  │
│  │  • accent (indigo)        → Intelligence, interaction           │  │
│  │  • tacit (green)          → Experience, growth                  │  │
│  │  • decision (purple)      → Traceability, authority             │  │
│  │  • warning (amber)        → Caution, gaps                       │  │
│  │                                                                  │  │
│  │  Typography:                                                     │  │
│  │  • Inter font (Google Fonts)                                    │  │
│  │  • System font fallbacks                                        │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                      global.css (Custom)                         │  │
│  │                                                                  │  │
│  │  • Custom scrollbar styling                                     │  │
│  │  • Focus state accessibility                                    │  │
│  │  • Smooth transitions                                           │  │
│  │  • Animation keyframes                                          │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                            BACKEND API                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                  FastAPI Backend (Port 8000)                     │  │
│  │                                                                  │  │
│  │  Endpoints:                                                      │  │
│  │  • POST /api/query    → Query knowledge system                  │  │
│  │  • POST /api/ingest   → Ingest new documents                    │  │
│  │  • GET  /api/health   → Health check                            │  │
│  │                                                                  │  │
│  │  Features:                                                       │  │
│  │  • Tacit Knowledge Extraction                                   │  │
│  │  • Decision Traceability                                        │  │
│  │  • Knowledge Gap Detection                                      │  │
│  │  • RAG Pipeline (FAISS + Gemini)                                │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

═════════════════════════════════════════════════════════════════════════

DATA FLOW EXAMPLE: User Query

1. User types question in ChatWindow
   ↓
2. useChat.sendMessage() called
   ↓
3. api.query() sends POST to backend
   ↓
4. Backend processes with RAG pipeline
   ↓
5. Response includes:
   • answer
   • sources
   • knowledge_type_used
   • decision_trace (if applicable)
   • knowledge_gap info
   • warnings
   ↓
6. Response flows back through:
   • API client
   • useChat hook
   • ChatWindow
   • MessageBubble
   ↓
7. UI renders:
   • Message with answer
   • TacitInsightBadge (if tacit)
   • DecisionTracePanel (if decision)
   • KnowledgeGapAlert (if gap detected)
   • SourcePanel with documents

═════════════════════════════════════════════════════════════════════════

COMPONENT DEPENDENCIES

ChatPage
  ├─ Header (role, health)
  ├─ Sidebar (conversations)
  ├─ ChatWindow
  │   ├─ MessageBubble
  │   │   ├─ TacitInsightBadge
  │   │   ├─ DecisionTracePanel
  │   │   └─ KnowledgeGapAlert
  │   └─ Input controls
  └─ SourcePanel (documents)

═════════════════════════════════════════════════════════════════════════
