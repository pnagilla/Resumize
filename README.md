# Resumize

AI-powered Resume & Job Description Matcher that helps you optimize your resume for ATS (Applicant Tracking Systems).

## Features

- **Match Score**: Get a percentage score showing how well your resume matches a job description
- **Missing Skills Detection**: Identify skills from the job posting that aren't in your resume
- **ATS-Optimized Bullets**: Get rewritten bullet points with relevant keywords and strong action verbs
- **History Tracking**: Access your past analyses

## Tech Stack

- **Backend**: FastAPI (Python)
- **AI**: Google Gemini API (FREE)
- **Frontend**: HTML/CSS/JavaScript
- **Storage**: SQLite

## Getting Started

### Prerequisites

- Python 3.9+
- Google Gemini API key (free)

### Get Your Free Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy your API key

That's it! No billing required - Gemini has a generous free tier.

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Resumize.git
   cd Resumize
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cd ..
   cp .env.example .env
   # Edit .env and add your GOOGLE_API_KEY
   ```

5. **Start the backend**
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

6. **Open the frontend**

   Open `frontend/index.html` in your browser, or serve it:
   ```bash
   # From project root
   python -m http.server 3000 --directory frontend
   ```
   Then visit http://localhost:3000

## Usage

1. Upload your resume (PDF or DOCX)
2. Paste the job description
3. Optionally add the job title
4. Click "Analyze Resume"
5. Review your match score, missing skills, and optimized bullets
6. Copy the improved bullet points to your resume

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/analyze` | Analyze resume against job description |
| GET | `/api/history` | Get analysis history |
| GET | `/api/analysis/{id}` | Get specific analysis |

## Project Structure

```
Resumize/
├── backend/
│   ├── main.py              # FastAPI entry point
│   ├── routers/
│   │   └── analyze.py       # API endpoints
│   ├── services/
│   │   ├── claude_service.py    # Gemini API integration
│   │   ├── parser_service.py    # PDF/DOCX parsing
│   │   └── db_service.py        # SQLite operations
│   ├── models/
│   │   └── schemas.py       # Pydantic models
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── data/                    # SQLite database
├── uploads/                 # Temp file uploads
└── README.md
```

## License

MIT
