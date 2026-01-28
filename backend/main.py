from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os

from routers import analyze, auth

load_dotenv()

app = FastAPI(
    title="Resumize",
    description="AI-powered Resume + Job Description Matcher",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
