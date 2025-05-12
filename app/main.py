from fastapi import FastAPI
from app.core.config import get_settings
from app.api.v1 import router as api_v1_router

settings = get_settings()

app = FastAPI(title=settings.app_name)

# Include API v1 router
app.include_router(api_v1_router.router, prefix="/api/v1")

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"} 