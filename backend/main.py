"""
FastAPI wrapper for FeedRanker gRPC service with REST API, monitoring, and async support.
"""

from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import datetime
import logging

from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import grpc
import asyncio

import feed_ranker_pb2
import feed_ranker_pb2_grpc
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional database import
try:
    from database import engine, SessionLocal, Base, RankingRequest, RankingMetric
    Base.metadata.create_all(bind=engine)
    DB_ENABLED = True
    logger.info("Database connected successfully")
except Exception as e:
    logger.warning(f"Database not available: {e}. Running without database.")
    DB_ENABLED = False
    SessionLocal = None


# ─────────────────────────────────────────────────
# Pydantic models for API
# ─────────────────────────────────────────────────

class ItemScore(BaseModel):
    item_id: str
    score: float


class RankingResponse(BaseModel):
    ranked_items: List[ItemScore]
    latency_ms: float
    timestamp: datetime


class RankingPayload(BaseModel):
    user_id: str
    item_ids: List[str] = Field(..., min_items=1, max_items=1000)
    user_features: Optional[dict] = Field(default_factory=dict)
    context_features: Optional[dict] = Field(default_factory=dict)


class ModelStatus(BaseModel):
    lambdamart_loaded: bool
    ctr_loaded: bool
    gRPC_connected: bool
    last_request_at: Optional[datetime]
    total_requests: int
    avg_latency_ms: float


class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    version: str


# ─────────────────────────────────────────────────
# gRPC client setup
# ─────────────────────────────────────────────────

grpc_channel = None
grpc_stub = None
model_status_cache = {
    "total_requests": 0,
    "total_latency_ms": 0.0,
    "last_request_at": None,
}


async def init_grpc():
    """Initialize gRPC channel to ranking service."""
    global grpc_channel, grpc_stub
    try:
        # Use insecure channel for local development
        grpc_channel = grpc.aio.insecure_channel(settings.GRPC_HOST)
        grpc_stub = feed_ranker_pb2_grpc.FeedRankerStub(grpc_channel)
        logger.info(f"gRPC connected to {settings.GRPC_HOST}")
    except Exception as e:
        logger.error(f"Failed to connect to gRPC: {e}")
        grpc_stub = None


async def close_grpc():
    """Close gRPC channel."""
    global grpc_channel
    if grpc_channel:
        await grpc_channel.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifecycle: startup and shutdown."""
    await init_grpc()
    yield
    await close_grpc()


# ─────────────────────────────────────────────────
# FastAPI app setup
# ─────────────────────────────────────────────────

app = FastAPI(
    title="FeedRanker API",
    description="Scalable feed ranking service with LambdaMART + Deep CTR ensemble",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)


# ─────────────────────────────────────────────────
# Database dependency
# ─────────────────────────────────────────────────

def get_db():
    if not DB_ENABLED or SessionLocal is None:
        yield None
        return
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─────────────────────────────────────────────────
# API Routes
# ─────────────────────────────────────────────────

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    return HealthCheck(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0",
    )


@app.get("/status", response_model=ModelStatus)
async def model_status(db: Session = Depends(get_db)):
    """Get current model and service status."""
    avg_latency = (
        model_status_cache["total_latency_ms"] / max(model_status_cache["total_requests"], 1)
    )
    return ModelStatus(
        lambdamart_loaded=grpc_stub is not None,
        ctr_loaded=grpc_stub is not None,
        gRPC_connected=grpc_stub is not None,
        last_request_at=model_status_cache["last_request_at"],
        total_requests=model_status_cache["total_requests"],
        avg_latency_ms=avg_latency,
    )


@app.post("/rank", response_model=RankingResponse)
async def rank_items(
    payload: RankingPayload,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Rank items using ensemble of LambdaMART and Deep CTR models.
    
    Args:
        payload: RankingPayload with user_id, item_ids, and optional features
        
    Returns:
        RankingResponse with ranked items and latency
    """
    if grpc_stub is None:
        raise HTTPException(status_code=503, detail="Ranking service unavailable")

    try:
        import time
        start_time = time.time()

        # Build gRPC request
        request = feed_ranker_pb2.RankRequest(
            user_id=payload.user_id,
            item_ids=payload.item_ids,
            user_features=payload.user_features or {},
            context_features=payload.context_features or {},
        )

        # Call gRPC service
        response = await grpc_stub.Rank(request)

        latency_ms = (time.time() - start_time) * 1000

        # Update cache
        model_status_cache["total_requests"] += 1
        model_status_cache["total_latency_ms"] += latency_ms
        model_status_cache["last_request_at"] = datetime.utcnow()

        # Store request in database asynchronously (if enabled)
        if DB_ENABLED and db:
            background_tasks.add_task(
                store_ranking_request,
                db,
                payload.user_id,
                payload.item_ids,
                latency_ms,
            )

        ranked_items = [
            ItemScore(item_id=item.item_id, score=item.score)
            for item in response.ranked_items
        ]

        return RankingResponse(
            ranked_items=ranked_items,
            latency_ms=latency_ms,
            timestamp=datetime.utcnow(),
        )

    except grpc.RpcError as e:
        logger.error(f"gRPC error: {e}")
        raise HTTPException(status_code=503, detail="Ranking service error")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/metrics/latency")
async def get_latency_metrics(
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    if not DB_ENABLED or db is None:
        return {"error": "Database not available", "metrics": []}
    """Get recent ranking request latencies."""
    metrics = db.query(RankingMetric).order_by(
        RankingMetric.created_at.desc()
    ).limit(limit).all()
    
    return {
        "metrics": [
            {
                "latency_ms": m.latency_ms,
                "timestamp": m.created_at,
                "user_id": m.user_id,
            }
            for m in metrics
        ],
        "count": len(metrics),
    }


@app.get("/metrics/summary")
async def get_metrics_summary(db: Session = Depends(get_db)):
    if not DB_ENABLED or db is None:
        return {
            "total_requests": model_status_cache["total_requests"],
            "avg_latency_ms": model_status_cache["total_latency_ms"] / max(model_status_cache["total_requests"], 1),
            "min_latency_ms": 0,
            "max_latency_ms": 0
        }
    """Get summary statistics of ranking requests."""
    from sqlalchemy import func
    
    summary = db.query(
        func.count(RankingMetric.id).label("total_requests"),
        func.avg(RankingMetric.latency_ms).label("avg_latency"),
        func.min(RankingMetric.latency_ms).label("min_latency"),
        func.max(RankingMetric.latency_ms).label("max_latency"),
    ).first()

    return {
        "total_requests": summary.total_requests or 0,
        "avg_latency_ms": round(float(summary.avg_latency) or 0, 2),
        "min_latency_ms": round(float(summary.min_latency) or 0, 2),
        "max_latency_ms": round(float(summary.max_latency) or 0, 2),
        "timestamp": datetime.utcnow(),
    }


# ─────────────────────────────────────────────────
# Background tasks
# ─────────────────────────────────────────────────

def store_ranking_request(
    db: Session,
    user_id: str,
    item_ids: List[str],
    latency_ms: float,
):
    """Store ranking request in database for auditing and analytics."""
    try:
        metric = RankingMetric(
            user_id=user_id,
            num_items=len(item_ids),
            latency_ms=latency_ms,
        )
        db.add(metric)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to store metric: {e}")
        db.rollback()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )
