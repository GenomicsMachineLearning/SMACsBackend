import fastapi
from fastapi.middleware.cors import CORSMiddleware
from app.api import router as api_router

app = fastapi.FastAPI(
    title="SMACs Backend",
    description="Backend for SMACs (Cell-Cell Interactions in Aging)",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for now as per pilot setup
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, tags=["api"])

@app.get("/")
async def root():
    return {"message": "SMACs Backend Service Running"}
