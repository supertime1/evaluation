from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.api.v1 import router as api_v1_router

settings = get_settings()

app = FastAPI(title=settings.app_name)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend domain
    allow_credentials=True,  # This is important for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 router
app.include_router(api_v1_router.router, prefix="/api/v1")

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"} 