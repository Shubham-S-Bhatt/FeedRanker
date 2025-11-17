"""
Database configuration with SQLAlchemy ORM models.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import settings

# Database engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ─────────────────────────────────────────────────
# ORM Models
# ─────────────────────────────────────────────────

class RankingRequest(Base):
    """Track individual ranking requests for auditing."""
    __tablename__ = "ranking_requests"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), nullable=False, index=True)
    item_ids = Column(String, nullable=False)  # JSON-serialized list
    request_data = Column(String, nullable=True)  # Full request JSON
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class RankingMetric(Base):
    """Store ranking performance metrics for monitoring."""
    __tablename__ = "ranking_metrics"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), nullable=False, index=True)
    num_items = Column(Integer, nullable=False)
    latency_ms = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Composite index for time-series queries
    __table_args__ = (
        Index("idx_user_time", "user_id", "created_at"),
        Index("idx_latency_time", "latency_ms", "created_at"),
    )


class ModelMetadata(Base):
    """Store model versioning and performance info."""
    __tablename__ = "model_metadata"

    id = Column(Integer, primary_key=True)
    model_name = Column(String(100), nullable=False)  # 'lambdamart' or 'ctr'
    version = Column(String(50), nullable=False)
    accuracy = Column(Float, nullable=True)
    ndcg_at_10 = Column(Float, nullable=True)
    deployed_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserFeedback(Base):
    """Store user feedback on ranking quality."""
    __tablename__ = "user_feedback"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), nullable=False, index=True)
    item_id = Column(String(255), nullable=False)
    feedback_score = Column(Integer, nullable=False)  # 1-5
    feedback_text = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
