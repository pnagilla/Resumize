# Resumize - Beginner's Guide

A detailed walkthrough of the Resumize project for beginners. This guide explains every concept, file, and decision in simple terms.

---

## Table of Contents

1. [What is Resumize?](#what-is-resumize)
2. [Project Structure](#project-structure)
3. [How the App Works (User Flow)](#how-the-app-works-user-flow)
4. [Backend Explained](#backend-explained)
5. [Frontend Explained](#frontend-explained)
6. [Database Explained](#database-explained)
7. [Authentication Explained](#authentication-explained)
8. [NLP Scoring Explained](#nlp-scoring-explained)
9. [GenAI Integration Explained](#genai-integration-explained)
10. [Deployment Explained](#deployment-explained)
11. [Common Terms Glossary](#common-terms-glossary)

---

## What is Resumize?

Resumize is an **ATS (Applicant Tracking System) Resume Analyzer**.

### What is an ATS?
When you apply for a job online, your resume often goes through software called an ATS before a human sees it. This software scans your resume for keywords, skills, and formatting to decide if you're a good match.

### What does Resumize do?
1. **Upload your resume** (PDF or DOCX)
2. **Optionally paste a job description** you're applying to
3. **Get a score** (0-100) showing how well your resume matches
4. **See detailed feedback** on what to improve
5. **Get AI-powered suggestions** for better bullet points

### Why two scoring systems (NLP + AI)?

| NLP (Rule-Based) | AI (Semantic) |
|------------------|---------------|
| Fast, instant results | Slower, needs API call |
| Always works | Can fail if API is down |
| Checks exact keywords | Understands meaning |
| "Do you have 'Python' written?" | "You worked with Django, so you probably know Python" |

By combining both, we get **reliable + intelligent** analysis.

---

## Project Structure

```
Resumize/
├── backend/                    # Python server code
│   ├── main.py                 # App entry point
│   ├── routers/                # API endpoints
│   │   ├── analyze.py          # Resume analysis endpoints
│   │   └── auth.py             # Login/signup endpoints
│   ├── services/               # Business logic
│   │   ├── nlp_service.py      # Rule-based scoring
│   │   ├── genai_service.py    # AI-powered analysis
│   │   ├── score_combiner.py   # Merges NLP + AI scores
│   │   ├── parser_service.py   # PDF/DOCX text extraction
│   │   ├── auth_service.py     # User authentication
│   │   └── db_service.py       # Database operations
│   ├── models/
│   │   └── schemas.py          # Data structure definitions
│   └── requirements.txt        # Python dependencies
├── frontend/                   # Browser code
│   ├── index.html              # Main HTML page
│   ├── app.js                  # JavaScript logic
│   └── styles.css              # CSS styling
├── Dockerfile                  # Container build instructions
├── render.yaml                 # Render.com deployment config
└── .dockerignore               # Files to exclude from Docker
```

### What is each folder for?

**`backend/`** - The server that runs on a computer (or cloud). It:
- Receives your resume file
- Processes it (extracts text, analyzes)
- Sends back results

**`frontend/`** - The webpage you see in your browser. It:
- Shows the upload form
- Displays results nicely
- Handles login/signup UI

**`routers/`** - Define the URLs (endpoints) your app responds to:
- `/api/analyze` - Analyze a resume
- `/api/auth/login` - Log in
- `/api/auth/signup` - Create account

**`services/`** - The actual work happens here. Routers are like receptionists (they receive requests), services are like workers (they do the job).

---

## How the App Works (User Flow)

### Step 1: User visits the website
```
Browser → https://resumize.nagilla.me
         ↓
Server sends index.html, app.js, styles.css
         ↓
Browser renders the landing page
```

### Step 2: User signs up
```
User fills form → clicks "Sign Up"
         ↓
Frontend sends POST /api/auth/signup
{name, username, email, password}
         ↓
Backend:
  1. Validates input (email format, password strength)
  2. Hashes password with bcrypt
  3. Stores user in database
  4. Returns success message
         ↓
Frontend shows "Account created! Please log in."
```

### Step 3: User logs in
```
User enters email + password → clicks "Login"
         ↓
Frontend sends POST /api/auth/login
         ↓
Backend:
  1. Finds user by email
  2. Compares password hash
  3. Creates auth token (random string)
  4. Stores token in database
  5. Returns {user, token}
         ↓
Frontend:
  1. Saves token in localStorage
  2. Shows logged-in UI
```

### Step 4: User analyzes resume
```
User uploads resume.pdf + pastes job description
         ↓
Frontend sends POST /api/analyze
  - Headers: Authorization: Bearer <token>
  - Body: FormData with file + job_description
         ↓
Backend:
  1. Validates token
  2. Saves file temporarily
  3. Extracts text from PDF
  4. Runs NLP analysis → score: 75
  5. Runs GenAI analysis → adjustment: +5
  6. Combines: final score = 80
  7. Deletes temp file
  8. Returns full results
         ↓
Frontend displays:
  - Score circle (80)
  - NLP breakdown bars
  - AI suggestions
  - Rewritten bullets
```

---

## Backend Explained

### What is FastAPI?

FastAPI is a Python framework for building web APIs. An **API** (Application Programming Interface) is how different programs talk to each other.

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/hello")
def say_hello():
    return {"message": "Hello, World!"}
```

When you visit `http://localhost:8000/hello`, you get:
```json
{"message": "Hello, World!"}
```

### main.py - The Entry Point

```python
# main.py simplified

from fastapi import FastAPI
from routers import analyze, auth

app = FastAPI(title="Resumize")

# Middleware: code that runs on EVERY request
app.add_middleware(CORSMiddleware, ...)      # Allow cross-origin requests
app.add_middleware(SecurityHeadersMiddleware) # Add security headers
app.add_middleware(RateLimitMiddleware)       # Prevent spam

# Routes: connect URLs to handler functions
app.include_router(analyze.router, prefix="/api")
app.include_router(auth.router, prefix="/api")

# Health check: Render.com pings this to know app is alive
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Serve frontend files
app.mount("/", StaticFiles(directory="../frontend"))
```

### What is Middleware?

Middleware is like a security checkpoint. Every request passes through it.

```
Request → [CORS] → [Security Headers] → [Rate Limit] → Your Code → Response
```

**CORS (Cross-Origin Resource Sharing):**
- By default, browsers block requests from one website to another
- CORS says "it's okay for resumize.nagilla.me to call our API"

**Security Headers:**
- `X-Frame-Options: DENY` - Prevents your site from being embedded in iframes (clickjacking protection)
- `X-XSS-Protection` - Helps browsers detect cross-site scripting attacks

**Rate Limiting:**
- Prevents abuse by limiting requests per IP
- Example: Max 10 login attempts per minute

### Routers vs Services

**Router** = Handles HTTP requests, validates input, returns responses
**Service** = Does the actual work (database queries, calculations, API calls)

```python
# routers/analyze.py - Router (thin layer)
@router.post("/analyze")
async def analyze_resume(resume: UploadFile, job_description: str):
    # 1. Validate input
    # 2. Call services
    result = analyze_service.process(resume, job_description)
    # 3. Return response
    return result

# services/nlp_service.py - Service (business logic)
def calculate_skill_score(resume_skills, jd_skills):
    matched = set(resume_skills) & set(jd_skills)
    return len(matched) / len(jd_skills) * 100
```

This separation makes code:
- **Testable** - You can test services without HTTP
- **Reusable** - Multiple routes can use the same service
- **Organized** - Easy to find where logic lives

---

## Frontend Explained

### HTML Structure (index.html)

```html
<!-- Simplified structure -->
<body>
    <!-- Navigation bar -->
    <nav>
        <div class="logo">Resumize</div>
        <div class="nav-buttons">
            <button onclick="openModal('loginModal')">Login</button>
            <button onclick="openModal('signupModal')">Sign Up</button>
        </div>
    </nav>

    <!-- Landing section (shown when logged out) -->
    <section id="landing">
        <h1>AI-Powered Resume Analysis</h1>
        <button>Get Started</button>
    </section>

    <!-- Analysis section (shown when logged in) -->
    <section id="analyze">
        <form id="analyzeForm">
            <input type="file" id="resume" accept=".pdf,.docx">
            <textarea id="jobDescription"></textarea>
            <button type="submit">Analyze</button>
        </form>
    </section>

    <!-- Results section (shown after analysis) -->
    <section id="results">
        <div class="score-circle">85</div>
        <div class="nlp-breakdown">...</div>
        <div class="ai-suggestions">...</div>
    </section>

    <!-- Modals (popups) -->
    <div id="loginModal" class="modal">...</div>
    <div id="signupModal" class="modal">...</div>
</body>
```

### JavaScript Logic (app.js)

#### Managing State

```javascript
// Global state
let currentUser = null;  // Stores logged-in user info

// On page load
document.addEventListener('DOMContentLoaded', () => {
    checkAuthState();  // Check if user is already logged in
});

// Check if user has a valid session
async function checkAuthState() {
    const token = localStorage.getItem('resumize_token');

    if (token) {
        // Verify token with server
        const response = await fetch('/api/auth/me', {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            // Token valid - show logged in UI
            currentUser = await response.json();
            updateUIForLoggedInUser();
        } else {
            // Token invalid - clear and show login
            localStorage.removeItem('resumize_token');
            updateUIForLoggedOutUser();
        }
    }
}
```

#### Making API Calls

```javascript
// Fetch API - modern way to make HTTP requests

// GET request (retrieve data)
const response = await fetch('/api/auth/me');
const data = await response.json();

// POST request (send data)
const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
});

// POST with file upload
const formData = new FormData();
formData.append('resume', fileInput.files[0]);
formData.append('job_description', 'Looking for Python developer...');

const response = await fetch('/api/analyze', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData  // Don't set Content-Type for FormData!
});
```

#### localStorage - Persisting Data

```javascript
// localStorage stores data in the browser (survives page refresh)

// Save data
localStorage.setItem('resumize_token', 'abc123');
localStorage.setItem('resumize_user', JSON.stringify({name: 'John'}));

// Retrieve data
const token = localStorage.getItem('resumize_token');
const user = JSON.parse(localStorage.getItem('resumize_user'));

// Remove data
localStorage.removeItem('resumize_token');
```

### CSS Concepts (styles.css)

#### Flexbox - Layout Tool

```css
/* Center items horizontally and vertically */
.container {
    display: flex;
    justify-content: center;  /* horizontal */
    align-items: center;      /* vertical */
}

/* Space items evenly */
.nav {
    display: flex;
    justify-content: space-between;
}
```

#### CSS Variables - Reusable Values

```css
:root {
    --primary-color: #2A9D8F;  /* Mint green */
    --text-color: #264653;
    --background: #F8FAF9;
}

.button {
    background-color: var(--primary-color);
    color: white;
}
```

#### Modal (Popup) Pattern

```css
.modal {
    display: none;           /* Hidden by default */
    position: fixed;         /* Stays in place when scrolling */
    top: 0; left: 0;
    width: 100%; height: 100%;
    background: rgba(0,0,0,0.5);  /* Semi-transparent overlay */
}

.modal.active {
    display: flex;           /* Show when active class added */
    justify-content: center;
    align-items: center;
}

.modal-content {
    background: white;
    padding: 20px;
    border-radius: 8px;
}
```

---

## Database Explained

### What is SQLite?

SQLite is a simple database that stores everything in a single file (`resumize.db`). No separate database server needed!

**Pros:**
- Zero configuration
- Perfect for small apps
- Easy to backup (just copy the file)

**Cons:**
- Not good for many concurrent users
- Can't scale horizontally

### Database Tables

```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Auth tokens table
CREATE TABLE auth_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Analysis history table
CREATE TABLE analysis_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    job_title TEXT,
    final_score INTEGER,
    result_json TEXT,  -- Full results stored as JSON string
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Database Operations (CRUD)

```python
# db_service.py simplified

import sqlite3

def get_connection():
    conn = sqlite3.connect('resumize.db')
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

# CREATE - Insert new data
def create_user(name, email, password_hash):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name, email, password_hash)  # ? prevents SQL injection!
    )
    conn.commit()
    return cursor.lastrowid

# READ - Retrieve data
def get_user_by_email(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    return cursor.fetchone()

# UPDATE - Modify data
def update_user_name(user_id, new_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET name = ? WHERE id = ?",
        (new_name, user_id)
    )
    conn.commit()

# DELETE - Remove data
def delete_token(token):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM auth_tokens WHERE token = ?", (token,))
    conn.commit()
```

### SQL Injection (and how we prevent it)

**BAD (vulnerable):**
```python
# If email = "'; DROP TABLE users; --"
# This would DELETE your entire users table!
query = f"SELECT * FROM users WHERE email = '{email}'"
cursor.execute(query)
```

**GOOD (safe):**
```python
# Using ? placeholders - the database treats input as data, not code
cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
```

---

## Authentication Explained

### What is Authentication?

**Authentication** = Proving who you are (login)
**Authorization** = What you're allowed to do (permissions)

### Password Hashing with bcrypt

Never store passwords in plain text! If your database is hacked, all passwords are exposed.

```python
import bcrypt

# When user signs up
password = "mypassword123"
salt = bcrypt.gensalt()  # Random data added to password
password_hash = bcrypt.hashpw(password.encode(), salt)
# Store password_hash in database

# When user logs in
entered_password = "mypassword123"
stored_hash = get_hash_from_database()
if bcrypt.checkpw(entered_password.encode(), stored_hash):
    print("Password correct!")
else:
    print("Wrong password!")
```

**Why bcrypt?**
- **Salting** - Same password = different hash each time (prevents rainbow tables)
- **Slow on purpose** - Makes brute force attacks impractical
- **Adaptive** - Can increase difficulty as computers get faster

### Token-Based Authentication

```
1. User logs in with email + password
         ↓
2. Server verifies credentials
         ↓
3. Server generates random token: "a1b2c3d4e5f6..."
         ↓
4. Server stores token in database (linked to user)
         ↓
5. Server sends token to frontend
         ↓
6. Frontend stores token in localStorage
         ↓
7. For every future request:
   Frontend sends: Authorization: Bearer a1b2c3d4e5f6...
         ↓
8. Server looks up token in database
   - Found? → Allow request
   - Not found? → Return 401 Unauthorized
```

### Why not store user info in the token (like JWT)?

**Our approach (server-side tokens):**
- Token is just a random string
- Server looks up token in database to get user info
- To logout, delete token from database

**JWT approach:**
- Token contains user info (encoded, signed)
- Server verifies signature, doesn't need database lookup
- Harder to invalidate (logout) - token is valid until it expires

We chose server-side tokens for **simplicity** and **easy logout**.

---

## NLP Scoring Explained

### What is NLP?

**NLP (Natural Language Processing)** = Making computers understand human language.

Our NLP is simple: pattern matching and counting keywords. Not fancy machine learning.

### Scoring Components

#### 1. Skill Matching (40% weight)

```python
# skills.py - List of known skills
SKILLS = [
    'python', 'javascript', 'react', 'node.js', 'sql',
    'aws', 'docker', 'kubernetes', 'git', 'agile',
    # ... hundreds more
]

# Extract skills from text
def extract_skills(text):
    text_lower = text.lower()
    found = []
    for skill in SKILLS:
        if skill in text_lower:
            found.append(skill)
    return found

# Calculate score
resume_skills = extract_skills(resume_text)  # ['python', 'sql', 'git']
jd_skills = extract_skills(job_description)   # ['python', 'sql', 'java', 'aws']

matched = set(resume_skills) & set(jd_skills)  # {'python', 'sql'}
missing = set(jd_skills) - set(resume_skills)  # {'java', 'aws'}

score = len(matched) / len(jd_skills) * 100  # 2/4 = 50%
```

#### 2. Keyword Density (25% weight)

How many important words from the JD appear in the resume?

```python
def calculate_keyword_density(resume, jd):
    # Extract important words (nouns, verbs) from JD
    jd_keywords = extract_keywords(jd)  # ['develop', 'team', 'software', ...]

    # Count how many appear in resume
    resume_lower = resume.lower()
    found = sum(1 for kw in jd_keywords if kw in resume_lower)

    return found / len(jd_keywords) * 100
```

#### 3. Experience Alignment (20% weight)

Does your experience level match?

```python
def extract_years_experience(text):
    # Look for patterns like "5 years", "5+ years", "five years"
    patterns = [
        r'(\d+)\+?\s*years?',
        r'(one|two|three|four|five|six|seven|eight|nine|ten)\s*years?'
    ]
    # Find and return the highest number found
    ...

resume_years = extract_years_experience(resume)  # 3
jd_required = extract_years_experience(jd)       # 5

if resume_years >= jd_required:
    score = 100
else:
    score = (resume_years / jd_required) * 100  # 3/5 = 60%
```

#### 4. Formatting Quality (15% weight)

Is the resume well-structured?

```python
def check_formatting(text):
    score = 0

    # Has contact info?
    if re.search(r'[\w\.-]+@[\w\.-]+', text):  # Email pattern
        score += 20
    if re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text):  # Phone
        score += 20

    # Has sections?
    sections = ['experience', 'education', 'skills', 'summary']
    for section in sections:
        if section in text.lower():
            score += 15

    return min(score, 100)
```

### Combining Scores

```python
def calculate_final_score(skill, keyword, experience, formatting):
    return (
        skill * 0.40 +       # 40% weight
        keyword * 0.25 +     # 25% weight
        experience * 0.20 +  # 20% weight
        formatting * 0.15    # 15% weight
    )

# Example:
# skill=70, keyword=60, experience=80, formatting=90
# Final = 70*0.4 + 60*0.25 + 80*0.2 + 90*0.15
#       = 28 + 15 + 16 + 13.5 = 72.5
```

---

## GenAI Integration Explained

### What is Groq?

Groq is a company that provides fast AI inference (running AI models). We use their API to access **Llama 3.3 70B**, a powerful open-source language model.

### How it Works

```python
from groq import Groq

client = Groq(api_key="your-api-key")

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "user", "content": "Analyze this resume: ..."}
    ],
    temperature=0.3,  # Lower = more focused/deterministic
    max_tokens=4096   # Maximum response length
)

answer = response.choices[0].message.content
```

### Our Prompt Engineering

```python
PROMPT = """You are an ATS analysis assistant.

NLP Score: {nlp_score}/100
Matched Skills: {matched_skills}
Missing Skills: {missing_skills}

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Return JSON with:
- score_adjustment: -15 to +15 (adjust NLP score based on semantic understanding)
- semantic_skills: skills implied but not explicitly stated
- gap_analysis: what's missing and how to fix it
- rewritten_bullets: improved versions of resume bullets
- positioning_advice: how to better target this role
"""
```

### Why ±15 Point Adjustment?

We limit AI adjustment to ±15 points because:
- NLP score is the **foundation** (reliable, explainable)
- AI can **nudge** the score based on deeper understanding
- Prevents AI from making wild/unreliable scores

```
NLP Score: 65
AI sees: "You have Django experience, which implies Python knowledge"
AI adjustment: +8
Final Score: 73
```

### Error Handling (Graceful Degradation)

```python
def run_genai_analysis(resume, jd, nlp_result):
    try:
        # Call Groq API
        response = client.chat.completions.create(...)
        return parse_response(response)

    except Exception as e:
        # Log error but don't crash
        logger.error(f"GenAI failed: {e}")
        return None  # NLP score still works!
```

If AI fails, users still get NLP results. The app never crashes due to AI issues.

---

## Deployment Explained

### What is Docker?

Docker packages your app with everything it needs (Python, libraries, code) into a **container**. This container runs the same way everywhere.

**Without Docker:**
- "It works on my machine!"
- Install Python, pip, all dependencies manually on server
- Version conflicts

**With Docker:**
- Define everything in a Dockerfile
- Build once, run anywhere
- Same environment in dev and production

### Dockerfile Explained

```dockerfile
# Start with Python 3.11 (slim version = smaller)
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements first (for caching - explained below)
COPY backend/requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Change to backend directory
WORKDIR /app/backend

# Tell Docker this app uses port 8000
EXPOSE 8000

# Command to run when container starts
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Layer Caching

Docker builds images in layers. If a layer hasn't changed, it uses cache.

```dockerfile
# These rarely change - cached
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

# These change often - rebuilt each time
COPY backend/ ./backend/
COPY frontend/ ./frontend/
```

By copying requirements.txt first, we don't reinstall packages when only code changes.

### render.yaml Explained

```yaml
services:
  - type: web                        # Web service (HTTP)
    name: resumize                   # Service name
    runtime: docker                  # Use Docker
    dockerfilePath: ./Dockerfile     # Where's the Dockerfile
    region: oregon                   # Server location
    plan: free                       # Pricing tier

    envVars:                         # Environment variables
      - key: DATABASE_PATH
        value: /tmp/resumize.db
      - key: GROQ_API_KEY
        sync: false                  # Set manually in dashboard (secret)

    customDomains:
      - name: resumize.nagilla.me    # Custom domain
```

### Environment Variables

Environment variables are settings that can change between environments (dev vs production).

```python
import os

# In code - read from environment
DATABASE_PATH = os.getenv("DATABASE_PATH", "../data/resumize.db")
#                         ↑ name           ↑ default if not set

# Local development: uses default "../data/resumize.db"
# Production: uses "/tmp/resumize.db" (set in render.yaml)
```

**Why use environment variables?**
- Don't hardcode secrets (API keys) in code
- Same code works in different environments
- Easy to change without redeploying

---

## Common Terms Glossary

| Term | Meaning |
|------|---------|
| **API** | Application Programming Interface - how programs talk to each other |
| **REST API** | API that uses HTTP methods (GET, POST, PUT, DELETE) |
| **Endpoint** | A specific URL that accepts requests (e.g., `/api/analyze`) |
| **Frontend** | The part users see (browser) |
| **Backend** | The server part (processes requests) |
| **Database** | Where data is stored permanently |
| **Token** | A secret string that proves you're logged in |
| **Hash** | One-way transformation (password → scrambled text) |
| **CORS** | Security feature controlling cross-site requests |
| **Middleware** | Code that runs on every request |
| **Docker** | Tool to package apps in containers |
| **Container** | Isolated environment running your app |
| **Deployment** | Making your app available on the internet |
| **Environment Variable** | Settings that can change per environment |
| **NLP** | Natural Language Processing |
| **LLM** | Large Language Model (like GPT, Llama) |
| **Prompt** | Instructions given to an AI model |
| **Graceful Degradation** | App still works when a component fails |

---

## Running Locally

### Prerequisites
- Python 3.9+
- pip (Python package manager)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/pnagilla/Resumize.git
cd Resumize

# 2. Create virtual environment
cd backend
python -m venv venv

# 3. Activate virtual environment
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create .env file with your API key
echo "GROQ_API_KEY=your_api_key_here" > .env

# 6. Run the server
uvicorn main:app --reload

# 7. Open http://localhost:8000 in your browser
```

### Common Issues

**Port already in use:**
```bash
lsof -ti:8000 | xargs kill -9  # Kill process on port 8000
```

**Module not found:**
```bash
pip install -r requirements.txt  # Reinstall dependencies
```

**GROQ_API_KEY not set:**
- Create a `.env` file in `/backend` with your key
- Get a free key at https://console.groq.com/keys

---

## Next Steps for Learning

1. **Read the code** - Start with `main.py`, then `routers/`, then `services/`
2. **Add a feature** - Try adding resume history viewing
3. **Write tests** - Add pytest tests for NLP scoring
4. **Deploy your own** - Fork the repo, deploy to Render
5. **Upgrade the database** - Switch from SQLite to PostgreSQL

Happy coding! 🚀
