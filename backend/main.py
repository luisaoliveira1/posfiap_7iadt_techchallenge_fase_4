from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routers import audio, health, reviews

app = FastAPI(
    title="PPD Analysis Backend",
    description="Post-partum depression speech analysis orchestrator",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(audio.router)
app.include_router(health.router)
app.include_router(reviews.router)
