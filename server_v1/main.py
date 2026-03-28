from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.ingest import router as ingest_router
from api.retreive import router as retreive_router


app = FastAPI(title="Codebase RAG Service")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://.*",         
    allow_credentials=True,
    allow_methods=["*"],            
    allow_headers=["*"],            
)


# Register Routes
app.include_router(ingest_router, prefix="/api/ingest")
app.include_router(retreive_router, prefix="/api/retreive")


@app.get("/")
def home():
    return {"message" : "Coderag Services is Running"}

