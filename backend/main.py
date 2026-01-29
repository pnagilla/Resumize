from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from dotenv import load_dotenv
import os
import time
from collections import defaultdict

from routers import analyze, auth

load_dotenv()

app = FastAPI(
    title="Resumize",
    description="AI-powered Resume + Job Description Matcher",
    version="1.0.0"
)

# --- CORS middleware ---
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


# --- Security headers middleware ---
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response

app.add_middleware(SecurityHeadersMiddleware)


# --- Rate limiting middleware ---
class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter for auth endpoints."""

    def __init__(self, app, max_requests: int = 10, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Only rate-limit auth endpoints
        if request.url.path.startswith("/api/auth/"):
            client_ip = request.client.host if request.client else "unknown"
            now = time.time()

            # Clean old entries
            self.requests[client_ip] = [
                t for t in self.requests[client_ip]
                if now - t < self.window_seconds
            ]

            if len(self.requests[client_ip]) >= self.max_requests:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests. Please try again later."}
                )

            self.requests[client_ip].append(now)

        return await call_next(request)

app.add_middleware(RateLimitMiddleware, max_requests=10, window_seconds=60)


# Include routers
app.include_router(analyze.router, prefix="/api", tags=["analyze"])
app.include_router(auth.router, prefix="/api", tags=["auth"])

# Create uploads directory if it doesn't exist
os.makedirs("../uploads", exist_ok=True)


@app.get("/")
async def root():
    return {"message": "Welcome to Resumize API", "docs": "/docs"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
