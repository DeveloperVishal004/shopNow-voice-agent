ShopNow Voice Agent
AI-powered customer support voice agent — GC Open Soft, IIT Kharagpur 2026.

Tech Stack
Backend: FastAPI + Python 3.14
LLM: OpenAI GPT-4o-mini + Realtime API
STT/TTS: OpenAI Whisper + TTS
RAG: LangChain + FAISS
Frontend: Streamlit
Database: SQLite
Setup — run these after cloning
1. Create virtual environment
python -m venv venv source venv/bin/activate # macOS venv\Scripts\activate # Windows

2. Install dependencies
pip install -r requirements.txt

3. Add your OpenAI API key
cp .env.example .env

open .env and add your key
4. Load data
python scripts/load_csv_data.py

5. Build RAG index
python scripts/build_rag.py

6. Run backend
uvicorn backend.main:app --reload --port 8000

7. Run frontend (new terminal)
streamlit run frontend/app.py

Important Notes
shopnow.db is not committed — seeds automatically on startup
rag_store/index/ is not committed — run build_rag.py to regenerate
Never commit .env — add your own OpenAI key locally
temp_audio/ is not committed — created automatically on first run
