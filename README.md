# Resumize

**Live:** https://resumize.nagilla.me | **GitHub:** https://github.com/pnagilla/Resumize

> Full-stack ATS resume analyzer with layered NLP + GenAI scoring architecture.

---

## Quick Overview (Interview Pitch)

- Built an **AI-powered resume analyzer** that scores resumes against job descriptions
- Uses **two-layer architecture**: deterministic NLP scoring + semantic GenAI adjustment
- **Why two layers?** NLP is fast/reliable, AI adds semantic understanding (graceful degradation)
- Deployed on **Render.com** with Docker, custom domain, and CI/CD from GitHub

---

## Architecture Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER FLOW                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   [Upload Resume + JD] → [Parse PDF/DOCX] → [Extract Text]      │
│                                    ↓                             │
│   ┌────────────────────────────────────────────────────────┐    │
│   │              LAYER 1: NLP ENGINE (Deterministic)        │    │
│   │  • Skill Matching (40%) - regex + keyword lists         │    │
│   │  • Keyword Density (25%) - JD coverage in resume        │    │
│   │  • Experience Alignment (20%) - years extraction        │    │
│   │  • Formatting Quality (15%) - sections, contact info    │    │
│   │                         ↓                                │    │
│   │                  NLP Score: 72/100                       │    │
│   └────────────────────────────────────────────────────────┘    │
│                                    ↓                             │
│   ┌────────────────────────────────────────────────────────┐    │
│   │              LAYER 2: GenAI (Semantic)                  │    │
│   │  • Model: Llama 3.3 70B via Groq API                    │    │
│   │  • Analyzes implied skills, context, role fit           │    │
│   │  • Returns: adjustment (±15), gaps, rewritten bullets   │    │
│   │                         ↓                                │    │
│   │              AI Adjustment: +8 points                    │    │
│   └────────────────────────────────────────────────────────┘    │
│                                    ↓                             │
│                     FINAL SCORE: 80/100                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Why? |
|-------|------------|------|
| **Backend** | FastAPI (Python) | Async, fast, auto OpenAPI docs, type hints |
| **Frontend** | Vanilla JS/HTML/CSS | No build step, fast load, demonstrates core skills |
| **Database** | SQLite | Simple, no server needed, good for demo |
| **AI** | Groq (Llama 3.3 70B) | Free tier, fast inference, powerful model |
| **Auth** | bcrypt + server tokens | Secure password hashing, easy logout |
| **Deployment** | Docker + Render.com | Containerized, auto-deploy from GitHub |

---

## Key Features

### 1. Layered Scoring Architecture
- **NLP Layer**: Always works, instant results, explainable scores
- **GenAI Layer**: Semantic understanding, can fail gracefully
- **Combined**: Reliable + Intelligent

### 2. Authentication System
- bcrypt password hashing (not plain SHA256)
- Server-side token storage (easy logout)
- Rate limiting (10 req/min on auth endpoints)
- Auto-logout on token expiration

### 3. Security
- CORS restricted to specific origins
- Security headers (X-Frame-Options, XSS protection)
- SQL injection prevention (parameterized queries)
- File upload validation (UUID names, path traversal check)

### 4. GenAI Integration
- Prompt engineering with structured JSON output
- Graceful degradation (app works if AI fails)
- Score adjustment capped at ±15 points

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/signup` | No | Create account |
| POST | `/api/auth/login` | No | Get auth token |
| POST | `/api/auth/logout` | Yes | Invalidate token |
| GET | `/api/auth/me` | Yes | Validate token |
| POST | `/api/analyze` | Yes | Analyze resume |
| GET | `/api/history` | Yes | Get past analyses |

---

## Project Structure

```
Resumize/
├── backend/
│   ├── main.py                 # FastAPI app + middleware
│   ├── routers/
│   │   ├── analyze.py          # /api/analyze endpoint
│   │   └── auth.py             # /api/auth/* endpoints
│   ├── services/
│   │   ├── nlp_service.py      # Deterministic scoring
│   │   ├── genai_service.py    # Groq/Llama integration
│   │   ├── score_combiner.py   # Merges NLP + AI
│   │   ├── parser_service.py   # PDF/DOCX extraction
│   │   ├── auth_service.py     # User auth logic
│   │   └── db_service.py       # SQLite operations
│   └── models/schemas.py       # Pydantic models
├── frontend/
│   ├── index.html              # Single page app
│   ├── app.js                  # All JS logic
│   └── styles.css              # Styling
├── Dockerfile                  # Container build
├── render.yaml                 # Render deployment config
└── INTERVIEW_GUIDE.md          # Detailed interview prep
```

---

## Key Technical Decisions

### Why NLP + GenAI instead of just AI?

| Approach | Pros | Cons |
|----------|------|------|
| AI Only | Semantic understanding | Slow, can fail, expensive, "black box" |
| NLP Only | Fast, reliable, explainable | Misses context, literal matching only |
| **Both** | Reliable + intelligent | More complex architecture |

**Answer:** NLP provides fast, explainable baseline. AI adds semantic understanding as enhancement. If AI fails, users still get useful results.

### Why server-side tokens (not JWT)?

- **Easy logout**: Delete token from DB, done
- **Simpler**: No signing/verification logic
- **Trade-off**: Requires DB lookup per request

### Why SQLite (not PostgreSQL)?

- **Demo/portfolio**: Simple, no server needed
- **Trade-off**: Data resets on Render Free tier
- **Production**: Would use PostgreSQL

### Why Groq (not OpenAI)?

- **Free tier**: Llama 3.3 70B available
- **Fast**: Groq has very fast inference
- **Cost**: OpenAI would add cost for portfolio project

---

## Graceful Degradation

```python
# If GenAI fails, NLP still works
def run_genai_analysis(...):
    try:
        response = groq_client.chat.completions.create(...)
        return parse_response(response)
    except Exception as e:
        logger.error(f"GenAI failed: {e}")
        return None  # NLP score used alone
```

---

## Security Measures

1. **Password Hashing**: bcrypt with salt
2. **SQL Injection**: Parameterized queries (`?` placeholders)
3. **Path Traversal**: UUID filenames, path validation
4. **CORS**: Restricted to production domain
5. **Rate Limiting**: 10 req/min on auth endpoints
6. **Security Headers**: X-Frame-Options, XSS Protection

---

## Local Development

```bash
# Clone and setup
git clone https://github.com/pnagilla/Resumize.git
cd Resumize/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Add API key
echo "GROQ_API_KEY=your_key_here" > .env

# Run
uvicorn main:app --reload
# Open http://localhost:8000
```

---

## Deployment (Render.com)

1. **Push to GitHub** → Auto-deploys via Render
2. **Docker build** → Uses Dockerfile
3. **Environment variables** → Set in Render dashboard
4. **Custom domain** → resumize.nagilla.me (CNAME to Render)

---

## What I Would Improve

| Improvement | Why |
|-------------|-----|
| PostgreSQL | Persistent data on Free tier |
| Redis caching | Cache repeated JD analysis |
| pytest tests | Automated testing |
| GitHub Actions | CI/CD pipeline |
| Sentry | Error monitoring |
| Resume versioning | Compare multiple versions |

---

## Interview Quick Reference

### "Tell me about this project"
> I built an ATS resume analyzer with a two-layer architecture. The first layer is a deterministic NLP engine that scores skill matching, keyword density, and formatting. The second layer uses Llama 3.3 via Groq to add semantic understanding. This gives users reliable scores plus AI-powered suggestions for improvement.

### "Why two scoring systems?"
> Reliability and intelligence. NLP always works and is explainable. AI adds semantic understanding but can fail. By combining them, users always get results, and AI enhances when available.

### "How do you handle auth?"
> bcrypt for password hashing, server-side tokens stored in SQLite. On login, generate UUID token, store in DB, return to client. Each request validates token against DB. Logout deletes token.

### "What happens if Groq API is down?"
> Graceful degradation. The app catches exceptions in the GenAI layer and returns None. The score combiner detects this and uses NLP-only scoring. Users see "AI analysis unavailable" but still get useful results.

### "Security measures?"
> bcrypt password hashing, parameterized SQL queries to prevent injection, UUID filenames with path validation for uploads, CORS restricted to production domain, rate limiting on auth endpoints, security headers.

---

## Files Reference

| File | Key Concepts |
|------|--------------|
| `main.py` | Middleware stack, static file serving |
| `nlp_service.py` | Regex skill matching, weighted scoring |
| `genai_service.py` | Prompt engineering, JSON parsing |
| `score_combiner.py` | Score merging logic |
| `auth.py` | Validation, bcrypt, token flow |
| `app.js` | localStorage, fetch API, state management |

---

## License

MIT

---

*See [INTERVIEW_GUIDE.md](INTERVIEW_GUIDE.md) for detailed technical deep dives and [BEGINNER_GUIDE.md](BEGINNER_GUIDE.md) for comprehensive explanations.*
