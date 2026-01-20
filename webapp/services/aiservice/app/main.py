from fastapi import FastAPI

# Dynamic import for local vs docker execution
try:
    # Docker import
    from app.routers.detect_smell import router as detect_smell_router
except ImportError:
    # Local import
    from webapp.services.aiservice.app.routers.detect_smell import (
        router as detect_smell_router,
    )

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Analysis Service")

# Middleware for CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the router
app.include_router(detect_smell_router)
