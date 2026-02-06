import fastapi
from fastapi.middleware.cors import CORSMiddleware
from app.api import router as api_router
from app.core.config import settings

app = fastapi.FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend for SMACs (Cell-Cell Interactions in Aging)",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, tags=["api"])

@app.get("/")
async def root():
    return {"message": "SMACs Backend Service Running"}
