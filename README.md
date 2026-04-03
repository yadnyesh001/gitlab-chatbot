# GitLab Handbook Chatbot

A RAG-powered chatbot that answers questions using **only** the GitLab Handbook and Direction pages. Built with FastAPI, LangChain, Gemini, Supabase (pgvector), and React.

## Architecture

```
User → React UI → FastAPI Backend → Supabase (vector search) → Gemini LLM → Response + Sources
```

**Data Pipeline:** Scrape GitLab pages → Clean & Chunk → Embed with Gemini → Store in Supabase pgvector

## Tech Stack

| Component     | Technology                        |
|---------------|-----------------------------------|
| Backend       | Python, FastAPI                   |
| LLM           | Google Gemini 2.0 Flash           |
| Embeddings    | Gemini `text-embedding-004`       |
| Vector DB     | Supabase (pgvector)               |
| RAG Framework | LangChain                         |
| Frontend      | React, Vite, Tailwind CSS         |
| Deployment    | Render (backend) + Vercel (frontend) |

## Project Structure

```
gitlab-chatbot/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py          # Settings & env vars
│   │   │   ├── vector_store.py    # Supabase pgvector search
│   │   │   └── rag.py             # RAG pipeline (retrieve + generate)
│   │   ├── api/
│   │   │   └── routes.py          # FastAPI endpoints
│   │   └── main.py                # App entrypoint
│   ├── scripts/
│   │   ├── scraper.py             # GitLab page scraper
│   │   ├── chunker.py             # Text chunking pipeline
│   │   ├── embed_and_store.py     # Embedding + Supabase storage
│   │   └── supabase_schema.sql    # Database schema
│   ├── requirements.txt
│   ├── Dockerfile
│   └── render.yaml
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatMessage.jsx
│   │   │   ├── ChatInput.jsx
│   │   │   └── SuggestedQuestions.jsx
│   │   ├── hooks/
│   │   │   └── useChat.js
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── vercel.json
├── .env.example
├── .gitignore
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.11+
- Node.js 18+
- Google AI API key ([get one here](https://aistudio.google.com/apikey))
- Supabase account ([sign up](https://supabase.com))

### 1. Clone & Configure

```bash
git clone https://github.com/your-username/gitlab-chatbot.git
cd gitlab-chatbot
cp .env.example backend/.env
```

Edit `backend/.env` with your actual keys.

### 2. Set Up Supabase

1. Create a new project at [supabase.com](https://supabase.com)
2. Go to **SQL Editor** → **New Query**
3. Paste the contents of `backend/scripts/supabase_schema.sql` and run it
4. Copy your project URL and service role key from **Settings** → **API**

### 3. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Data Ingestion (run once)

```bash
cd backend/scripts

# Step 1: Scrape GitLab pages
python scraper.py

# Step 2: Chunk the content
python chunker.py

# Step 3: Embed and store in Supabase
python embed_and_store.py
```

This will scrape up to 500 pages, chunk them, generate embeddings, and store everything in Supabase.

### 5. Start Backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

API docs at: http://localhost:8000/docs

### 6. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Opens at: http://localhost:3000

## API Endpoints

| Method | Endpoint                  | Description              |
|--------|---------------------------|--------------------------|
| POST   | `/api/chat`               | Send question, get answer |
| GET    | `/api/health`             | Health check             |
| GET    | `/api/suggested-questions`| Get suggested questions  |

### Example Request

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What are GitLab company values?"}'
```

### Example Response

```json
{
  "answer": "GitLab's company values are known as CREDIT...",
  "sources": [
    {
      "title": "GitLab Values | GitLab Handbook",
      "url": "https://handbook.gitlab.com/handbook/values/",
      "similarity": 0.89
    }
  ],
  "context_used": true
}
```

## Deployment

### Backend → Render

1. Push code to GitHub
2. Go to [render.com](https://render.com) → **New Web Service**
3. Connect your repo, set root directory to `backend`
4. Build command: `pip install -r requirements.txt`
5. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Add env vars: `GOOGLE_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `CORS_ORIGINS`

### Frontend → Vercel

1. Go to [vercel.com](https://vercel.com) → **Import Project**
2. Set root directory to `frontend`
3. Framework: Vite
4. Add env var: `VITE_API_URL=https://your-backend.onrender.com`
5. Update `vercel.json` rewrite destination with your Render URL

## Example Queries to Test

1. "What is GitLab's mission?"
2. "How does GitLab approach remote work?"
3. "What is GitLab's product direction for AI?"
4. "How does GitLab handle incident management?"
5. "What are GitLab's company values?"
6. "Tell me about GitLab's pricing model" (tests guardrails if not in handbook)
7. "What is the weather today?" (tests out-of-scope rejection)

## Push to GitHub

```bash
cd gitlab-chatbot
git init
git add .
git commit -m "Initial commit: GitLab Handbook RAG Chatbot"
git branch -M main
git remote add origin https://github.com/your-username/gitlab-chatbot.git
git push -u origin main
```
