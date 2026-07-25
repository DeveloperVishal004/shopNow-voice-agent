<div align="center">

# 🎧 ShopNow Voice Agent

### AI-Powered Real-Time Customer Support Voice Agent

**Real-time Voice · Multilingual · Sentiment-Aware · Smart Escalation**

[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![HTML/JS](https://img.shields.io/badge/HTML%2FJS-Frontend-E34F26?style=flat-square&logo=html5)](https://developer.mozilla.org/en-US/docs/Web/HTML)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?style=flat-square&logo=openai)](https://openai.com)
[![Sarvam AI](https://img.shields.io/badge/Sarvam_AI-STT+TTS-FF6B35?style=flat-square)](https://sarvam.ai)
[![FAISS](https://img.shields.io/badge/FAISS-RAG-00BFFF?style=flat-square)](https://faiss.ai)
[![License](https://img.shields.io/badge/License-MIT-brightgreen?style=flat-square)](LICENSE)



[**Features**](#-features) · [**Architecture**](#-architecture) · [**Setup**](#-setup) · [**Demo**](#-demo) · [**API**](#-api-endpoints) · [**Dashboard**](#-dashboard)

</div>

---
Video :-  [https://youtu.be/LwRGCmb9hB4](https://youtu.be/LwRGCmb9hB4)
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
| 🌐 Languages | 11 Indian languages — replies in the caller's own language |
| 💰 Cost reduction | 60–70% projected |

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎙️ **Real-Time Voice** | Bidirectional audio over WebSocket — customer speaks, Priya responds in < 2 seconds |
| 🌐 **Multilingual** | Auto-detects language and replies in the caller's own — understands in English, responds in their language (direct generation, or Sarvam Mayura translation for low-resource languages) |
| 🧠 **5-Intent NLU** | OpenAI function calling classifies intent + extracts entities in one API call |
| 💾 **Multi-Turn Memory** | In-memory session tracks full conversation, intent, sentiment, order context |
| 📚 **RAG Knowledge Base** | LangChain + FAISS over 5 policy documents — grounded, not hallucinated |
| 😤 **Sentiment-Aware** | Utterance-level sentiment (GPT-4o-mini) adapts Priya's tone and drives escalation |
| 🚨 **Smart Escalation** | Multi-signal escalation engine with structured human handoff brief |
| 📊 **Live Dashboard** | HTML/JS dashboard — FCR, escalations, sentiment trends, intent breakdown |
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
│        │  Utterance Sentiment (GPT-4o) │      │
│        │   drives tone + escalation    │      │
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
| **STT** | Sarvam AI Saaras v3 | Indian language speech-to-text (transcribes + translates to English) |
| **TTS** | Sarvam AI Bulbul v2 | Natural Indian voice synthesis (streaming) |
| **Translation** | Sarvam AI Mayura | Reply translation for low-resource languages |
| **LLM** | OpenAI GPT-4o-mini | Intent classification + response generation |
| **Embeddings** | OpenAI text-embedding-3-small | Document vectorization for RAG |
| **Sentiment** | GPT-4o-mini | Utterance-level sentiment scoring — tone adaptation + escalation |
| **Vector Store** | FAISS (CPU) | Policy document semantic retrieval |
| **Database** | SQLite + SQLAlchemy async | Orders, call logs, escalation records |
| **Frontend** | Plain HTML, CSS, JavaScript | Live dashboard + voice call interface |
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
│   │   ├── sentiment.py            # Utterance sentiment (GPT-4o-mini)
│   │   └── escalation.py           # Multi-signal escalation engine
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
│   └── index.html                  # Single-page HTML/CSS/JS console —
│                                   #   call UI + dashboard, escalations & report views
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
ESCALATION_SENTIMENT_THRESHOLD=-0.4
ESCALATION_MIN_TURNS=3
ESCALATION_MAX_TURNS=8
ESCALATION_DATA_NOT_FOUND_LIMIT=2
ESCALATION_UNKNOWN_INTENT_LIMIT=3
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

**Frontend:**
Double click and open `frontend/index.html` in your browser.

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

The HTML dashboard can be accessed by opening `frontend/index.html` in your browser. It includes:

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
        (whole-word match, last 3 turns)

Rule 2: Data not found            → order lookup fails
        (repeated)                  ESCALATION_DATA_NOT_FOUND_LIMIT times (default 2)
                                    — a successful lookup resets the counter

Rule 3: Long conversation         → ESCALATION_MAX_TURNS customer turns
                                    without resolution (default 8)

Rule 4: Repeated unclassified     → ESCALATION_UNKNOWN_INTENT_LIMIT unmatched
        intent + frustration        turns (default 3) AND recent negative/angry
                                    sentiment — calm gibberish is held off
                                    (prank-safe)

Rule 5: Consecutive negative      → ≥ 70% of the last ESCALATION_NEGATIVE_TURNS
        sentiment                   turns are negative/angry (default 4)

Rule 6: Sentiment threshold       → avg score ≤ ESCALATION_SENTIMENT_THRESHOLD
                                    (default -0.4), after ESCALATION_MIN_TURNS
```

Capability rules (1–4) fire regardless of mood; emotional rules (5–6) only
after a short warm-up. Every escalation is **persisted to the
`escalation_logs` table** for audit and is retrievable via
`/report/escalation/{call_id}` after the call ends.

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

## 🧬 Sentiment-Aware Responses

Every customer utterance is scored for sentiment, and that signal is used twice — to shape Priya's tone and to feed the escalation engine.

```
Every utterance
      │
      ▼
 Sentiment (GPT-4o-mini)
 positive / neutral / negative / angry
      │
 ┌────┴──────────────┐
 ▼                   ▼
 Tone adaptation     Escalation engine
 empathetic reply    consecutive-negative
 when negative       & average-sentiment rules
```

The sentiment label is injected into the response prompt as a tone directive, so an angry customer gets an apology-first, extra-empathetic reply — while the running sentiment history decides when the call is handed to a human.

---

## 🌐 Language Support

The agent **understands in one language and replies in the caller's**. Sarvam
STT (`saaras`) transcribes *and translates* the customer's speech to English,
so intent classification, RAG, and sentiment all reason in English. The reply
is then delivered in the caller's own language:

- **Direct generation** for languages the LLM handles fluently — English,
  Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati.
- **Translate-then-speak** for lower-resource languages — the reply is
  generated in English and translated with **Sarvam Mayura** before TTS
  (Odia, Kannada, Malayalam, Punjabi).
- **Graceful fallback** to English if a detected language isn't supported by
  the voice model.

The detected language is captured once and used consistently for the LLM
reply, the TTS voice, and the call log — so spoken audio and generated text
never disagree.

**Supported voice languages:** English, Hindi, Bengali, Gujarati, Kannada,
Malayalam, Marathi, Odia, Punjabi, Tamil, Telugu.

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

- [x] Tamil, Telugu, Bengali, Kannada, Odia, Malayalam, Punjabi, Marathi, Gujarati support
- [ ] Native-speaker review of low-resource language translations
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
