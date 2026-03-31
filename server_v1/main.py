import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.ingest import router as ingest_router
from api.retreive import router as retreive_router
from api.ws import router as ws_router
from db.neo4j_client import get_neo4j_driver
from core.logging import get_logger
from core.websocket import manager

logger = get_logger("keepalive")

async def ping_neo4j_keepalive():
    """Background task to ping Neo4j every 36 hours to keep Aura Free alive."""
    # 36 hours = 1.5 days. Aura Free pauses after 3 days of inactivity.
    INTERVAL = 36 * 60 * 60 
    
    logger.info("Neo4j keepalive scheduler started (Interval: 36h)")
    
    while True:
        try:
            driver = get_neo4j_driver()
            with driver.session() as session:
                # Lightweight ping query
                session.run("RETURN 1")
            logger.info("Neo4j keepalive ping successful")
        except Exception as e:
            logger.error(f"Neo4j keepalive ping failed: {e}")
        
        await asyncio.sleep(INTERVAL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Retrieve main asyncio loop for synchronous handlers to dispatch async websocket updates
    manager.loop = asyncio.get_running_loop()
    # Startup: Start keepalive task
    keepalive_task = asyncio.create_task(ping_neo4j_keepalive())
    yield
    # Shutdown: Stop keepalive task
    keepalive_task.cancel()

app = FastAPI(title="Codebase RAG Service", lifespan=lifespan)

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
app.include_router(ws_router, prefix="/api/ws")

@app.get("/")
def home():
    return {"message" : "Coderag Services is Running"}
