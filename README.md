<div align="center">

# 🎧 ShopNow Voice Agent

### AI-Powered Real-Time Customer Support Voice Agent

**Real-time Voice · Multilingual · Sentiment-Aware · Smart Escalation**

[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=flat-square&logo=streamlit)](https://streamlit.io)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?style=flat-square&logo=openai)](https://openai.com)
[![Sarvam AI](https://img.shields.io/badge/Sarvam_AI-STT+TTS-FF6B35?style=flat-square)](https://sarvam.ai)
[![FAISS](https://img.shields.io/badge/FAISS-RAG-00BFFF?style=flat-square)](https://faiss.ai)
[![License](https://img.shields.io/badge/License-MIT-brightgreen?style=flat-square)](LICENSE)



[**Features**](#-features) · [**Architecture**](#-architecture) · [**Setup**](#-setup) · [**Demo**](#-demo) · [**API**](#-api-endpoints) · [**Dashboard**](#-dashboard)

</div>

---

## 🎯 The Problem

ShopNow is a D2C brand processing **40,000+ orders/month** across India with 35 human agents available only **9 AM–9 PM**.

| Metric | Before AI |
|--------|-----------|
| ⏱ Average wait time | 8 minutes |
| ✅ First-contact resolution | 52% |
| ⭐ CSAT score | 3.1 / 5 |
| 🌙 After-hours support | ❌ None |
| 🌐 Multilingual support | ❌ None |

Most incoming calls are repetitive Tier-1 queries — order status, returns, payments, delivery — that require no human judgment but consume the bulk of agent time.

---

## 💡 The Solution

**Meet Priya** — ShopNow's AI voice support agent.

A real-time voice system that listens, understands context across multiple turns, detects when a customer is frustrated, and knows exactly when to step aside for a human.

| Metric | With ShopNow Voice Agent |
|--------|--------------------------|
| ⏱ Wait time | < 2 seconds |
| ✅ FCR (Tier-1) | 75%+ projected |
| ⭐ CSAT | 4.0+ projected |
| 🕐 Availability | 24/7 |
| 🌐 Languages | English, Hindi, Hinglish, Urdu, Urdilish |
| 💰 Cost reduction | 60–70% projected |

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎙️ **Real-Time Voice** | Bidirectional audio over WebSocket — customer speaks, Priya responds in < 2 seconds |
| 🌐 **Multilingual** | Auto-detects language — no "press 1 for Hindi" |
| 🧠 **5-Intent NLU** | OpenAI function calling classifies intent + extracts entities in one API call |
| 💾 **Multi-Turn Memory** | In-memory session tracks full conversation, intent, sentiment, order context |
| 📚 **RAG Knowledge Base** | LangChain + FAISS over 5 policy documents — grounded, not hallucinated |
| 😤 **Hybrid Sentiment** | Text (GPT-4o-mini) + Voice tone (librosa acoustic features) combined |
| 🚨 **Smart Escalation** | Multi-signal escalation engine with structured human handoff brief |
| 📊 **Live Dashboard** | Streamlit ops dashboard — FCR, escalations, sentiment trends, intent breakdown |
| 📝 **Call Summaries** | LLM-generated call summaries logged after every session |

---

## 🏗 Architecture

```
Customer Browser
      │
      │  WebSocket (real-time audio)
      ▼
┌──────────────────────────────────────────────┐
│               FastAPI Backend                │
│                                              │
│  ┌────────────┐      ┌──────────────────┐    │
│  │ Sarvam AI  │      │  Session Memory  │    │
│  │  STT       │─────▶│  (call_id keyed) │    │
│  └────────────┘      └────────┬─────────┘    │
│                               │              │
│                  ┌────────────▼───────────┐  │
│                  │   Intent Classifier    │  │
│                  │  (OpenAI func calling) │  │
│                  └────────────┬───────────┘  │
│                               │              │
│              ┌────────────────┴───────────┐  │
│              ▼                            ▼  │
│     ┌──────────────┐         ┌──────────────┐│
│     │  SQLite DB   │         │  FAISS RAG   ││
│     │  (Orders)    │         │  (5 docs)    ││
│     └──────┬───────┘         └──────┬───────┘│
│            └──────────┬─────────────┘        │
│                       ▼                      │
│        ┌──────────────────────────────┐      │
│        │   Hybrid Sentiment Analysis  │      │
│        │  Text (GPT) + Voice (librosa)│      │
│        └──────────────┬───────────────┘      │
│                       │                      │
│             ┌─────────┴──────────┐           │
│             ▼                    ▼           │
│       ┌──────────┐      ┌──────────────┐     │
│       │ Resolve  │      │  Escalate +  │     │
│       │ + Log    │      │    Brief     │     │
│       └────┬─────┘      └──────┬───────┘     │
│            └──────────┬────────┘             │
│                       ▼                      │
│            ┌────────────────────┐            │
│            │  Sarvam AI TTS     │            │
│            └────────────────────┘            │
└──────────────────────────────────────────────┘
      │
      │  Audio response
      ▼
Customer hears Priya
```

---

## 🛠 Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | FastAPI + Uvicorn | REST API + WebSocket server |
| **STT** | Sarvam AI Bulbul | Indian language speech-to-text |
| **TTS** | Sarvam AI Bulbul v2 | Natural Indian voice synthesis |
| **LLM** | OpenAI GPT-4o-mini | Intent classification + response generation |
| **Embeddings** | OpenAI text-embedding-3-small | Document vectorization for RAG |
| **Voice Sentiment** | librosa | Acoustic emotion detection |
| **Text Sentiment** | GPT-4o-mini | Utterance-level sentiment scoring |
| **Vector Store** | FAISS (CPU) | Policy document semantic retrieval |
| **Database** | SQLite + SQLAlchemy async | Orders, call logs, escalation records |
| **Frontend** | Streamlit + Plotly | Live dashboard + voice call interface |
| **Voice UI** | Embedded HTML/JS | Real-time browser mic + audio playback |
| **Session** | Python in-memory dict | Per-call multi-turn conversation state |
| **Logging** | Loguru | Structured application logging |

---

## 📁 Project Structure

```
shopNow-voice-agent/
│
├── backend/
│   ├── main.py                     # App entry point + lifespan
│   ├── config.py                   # Settings + env vars
│   ├── routes/
│   │   ├── call.py                 # POST /call/start /turn /end
│   │   ├── transcribe.py           # POST /transcribe  (STT)
│   │   ├── speak.py                # POST /speak       (TTS)
│   │   ├── report.py               # GET  /report/daily /escalation
│   │   └── websocket.py            # WS   /ws/{call_id}
│   ├── services/
│   │   ├── stt.py                  # Sarvam AI STT integration
│   │   ├── tts.py                  # Sarvam AI TTS integration
│   │   ├── intent.py               # OpenAI function calling classifier
│   │   ├── llm.py                  # LangChain conversation chain
│   │   ├── rag.py                  # FAISS retrieval logic
│   │   ├── sentiment.py            # Text sentiment (GPT-4o-mini)
│   │   ├── voice_sentiment.py      # Voice sentiment (librosa)
│   │   ├── sentiment_detection.py  # Hybrid fusion logic
│   │   └── escalation.py          # Multi-signal escalation engine
│   ├── handlers/
│   │   ├── order_status.py         # Order status DB handler
│   │   ├── returns.py              # Return/refund DB handler
│   │   ├── payment.py              # Payment issue DB handler
│   │   ├── delivery.py             # Delivery complaint handler
│   │   └── product.py              # Product query handler
│   ├── memory/
│   │   └── session.py              # In-memory session manager
│   ├── db/
│   │   ├── database.py             # Async SQLite connection
│   │   ├── models.py               # ORM models
│   │   └── seed.py                 # DB initialization + data load
│   └── utils/                      # Utility helpers
│
├── frontend/
│   ├── app.py                      # Streamlit entry point + navigation
│   ├── index.html                  # Embedded HTML/JS voice call UI
│   └── pages/
│       ├── dashboard.py            # Live ops dashboard
│       ├── escalations.py          # Escalation brief viewer
│       ├── report.py               # Daily ops report
│       └── test_agent.py           # Real-time voice call interface
│
├── rag_store/
│   ├── documents/
│   │   ├── cancellation.txt        # Cancellation policy
│   │   ├── return_policy.txt       # Return + refund policy
│   │   ├── shipping_faq.txt        # Delivery + tracking FAQ
│   │   ├── payment_faq.txt         # Payment methods + issues
│   │   └── product_info.txt        # Product catalogue info
│   └── index/                      # FAISS vector index (auto-generated)
│
├── data/
│   └── Orderlist.csv               # Order dataset
│
├── scripts/
│   └── build_rag.py                # One-time FAISS index builder
│
├── .env.example                    # Environment variables template
└── requirements.txt
```

---

## 🚀 Setup

### Prerequisites
- Python 3.10+
- OpenAI API key — [get one here](https://platform.openai.com)
- Sarvam AI API key — [get one here](https://sarvam.ai)

### Step 1 — Clone
```bash
git clone https://github.com/DeveloperVishal004/shopNow-voice-agent.git
cd shopNow-voice-agent
```

### Step 2 — Virtual environment
```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Configure environment
```bash
cp .env.example .env
```

Open `.env` and fill in your keys:
```env
openai_api_key=your_openai_api_key_here
sarvam_api_key=your_sarvam_api_key_here
DATABASE_URL=sqlite:///./shopnow.db
FAISS_INDEX_PATH=./rag_store/index/faiss.index
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
MAX_TOKENS=200
TTS_MODEL=tts-1
TTS_VOICE=nova
ESCALATION_NEGATIVE_TURNS=4
ESCALATION_SENTIMENT_THRESHOLD=-0.7
ESCALATION_MIN_TURNS=3
```

### Step 5 — Seed the database
```bash
python backend/db/seed.py
```

### Step 6 — Build RAG index
```bash
python scripts/build_rag.py
```

### Step 7 — Run

**Terminal 1 — Backend:**
```bash
uvicorn backend.main:app --reload
```

**Terminal 2 — Frontend:**
```bash
streamlit run frontend/app.py
```

Open **http://localhost:8501** in your browser.

> 📖 Interactive API docs at **http://localhost:8000/docs**

---

## 🎬 Demo

### Try these scenarios on the Test Agent page:

**Scenario 1 — English (order status):**
> *"Hi, where is my order ORD-1001?"*

**Scenario 2 — Hindi (return request):**
> *"Mera order wapas karna hai, item damage ho gaya tha"*

**Scenario 3 — Hinglish (payment issue):**
> *"Mera payment do baar cut gaya, ek refund karo"*

**Scenario 4 — Escalation trigger:**
> *"This is absolutely ridiculous, I want to speak to a manager right now"*

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Server health check |
| `POST` | `/call/start` | Create new call session → returns `call_id` |
| `POST` | `/call/turn` | Process one customer utterance → agent response |
| `POST` | `/call/end` | End call, log to database, clear session |
| `GET` | `/call/session/{id}` | Debug — view full live session state |
| `POST` | `/transcribe/` | STT — upload audio → transcribed text |
| `POST` | `/speak/` | TTS — text + language → mp3 audio |
| `GET` | `/report/daily` | Aggregated call stats for dashboard |
| `GET` | `/report/escalation/{id}` | Full handoff brief for human agent |
| `WS` | `/ws/{call_id}` | Real-time bidirectional voice stream |

### Example Requests

**Start a call:**
```json
POST /call/start
{ "customer_phone": "+919876543210" }
```

**Process a turn:**
```json
POST /call/turn
{
  "call_id": "your-call-id",
  "text": "Where is my order ORD-1001?",
  "language": "en"
}
```

---

## 📊 Dashboard

The Streamlit dashboard at `http://localhost:8501` has 4 pages:

### Live Dashboard
- Total calls handled
- AI resolution rate + FCR gauge vs 52% baseline
- Escalation count
- Average sentiment score
- Calls by intent (bar chart)
- Language breakdown (pie chart)

### Escalations
Lookup any escalated call by ID and view:
- Customer info + detected intent
- Recommended tone for human agent
- Sentiment history trend chart
- Last 6 turns of conversation
- Order context from database

### Daily Report
- Summary stats for support leadership
- Calls by intent table
- Resolution vs escalation breakdown

### Test Agent
- Real-time voice call interface
- Type or speak to Priya
- See live transcript with sentiment + intent labels

---

## 🚨 Escalation Logic

The escalation engine evaluates multiple signals every turn:

```
Rule 1: Explicit human request    → immediate escalation
        "manager", "agent", "human", "manav bulao"

Rule 2: Consecutive negative      → N consecutive negative/angry turns
        turns                       (configured via ESCALATION_NEGATIVE_TURNS)

Rule 3: Sentiment threshold       → avg score ≤ ESCALATION_SENTIMENT_THRESHOLD
                                    evaluated after ESCALATION_MIN_TURNS

Rule 4: Unresolved call length    → 8+ customer turns without resolution
```

**Handoff brief includes:**
```
✓ Customer name + phone
✓ Detected intent + issue summary
✓ Full sentiment history with label counts
✓ Last 6 turns of conversation
✓ Recommended tone (empathetic / professional / urgent)
✓ Order context from database
```

---

## 🧬 Hybrid Sentiment Detection

Standard text sentiment misses frustrated customers who use polite words with an angry tone.

```
Every utterance
      │
      ▼
 Text Sentiment (GPT-4o-mini)
      │
 ┌────┴────┐
 │         │
Non-neutral  Neutral
 │         │
 │         ▼
 │   Voice Sentiment (librosa)
 │   - RMS Energy     (loudness)
 │   - ZCR            (vocal tension)
 │   - Pitch Variance (emotional stability)
 │   - Tempo          (speaking rate)
 │         │
 └────┬────┘
      ▼
 Final Sentiment
 (positive / neutral / negative / angry)
```

Voice analysis only runs when text is neutral — optimizing latency while catching tone-based frustration.

---

## 🌐 Language Support

| Code | Language | Script |
|------|----------|--------|
| `en` | English | Latin |
| `hi` | Hindi | Devanagari (U+0900–U+097F) |
| `hinglish` | Hinglish | Roman (Hindi words) |
| `ur` | Urdu | Perso-Arabic (U+0600–U+06FF) |
| `urdilish` | Urdilish | Roman (Urdu words) |

---

## 📋 Supported Customer Intents

| Intent | Description |
|--------|-------------|
| `order_status` | Where is my order, when will it arrive |
| `return_refund` | I want to return an item, refund status |
| `payment_issue` | Payment failed, double charge, missing refund |
| `delivery_complaint` | Late delivery, damaged in transit, wrong address |
| `product_query` | Product details, availability, warranty, authenticity |

---

## ⚠️ Current Limitations

- Sessions are stored in memory — not suitable for multi-server deployment
- No authentication or authorization layer
- Multilingual behavior relies on prompt design and can be extended
- External API retry handling can be improved
- Reporting can be extended with SLA metrics and trend analysis

---

## 🔮 What's Next

- [ ] Tamil, Telugu, Kannada, Bengali full support
- [ ] Redis-based durable session storage
- [ ] Twilio / Exotel integration for real phone numbers
- [ ] CRM and ticketing platform integrations
- [ ] Post-call satisfaction capture
- [ ] Proactive outbound calls for at-risk orders
- [ ] Skill-based escalation routing by language and issue type

---

## 🤝 Contributing

```bash
# Create your feature branch
git checkout -b feature/your-feature

# Commit with a clear prefix
git commit -m "[FEATURE] Add Tamil language support"

# Push and open a PR against main
git push origin feature/your-feature
```

**Commit prefixes:** `[FEATURE]` `[BUGFIX]` `[PERF]` `[DOCS]`

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with ❤️**

⭐ Star this repo if you found it useful!

</div>
