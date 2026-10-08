"""Database engine configuration with connection pooling and health checks."""

import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_normalized_database_url() -> str:
    url = settings.DATABASE_URL.strip()
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)

    # Route direct IPv6 Supabase host to IPv4 session pooler automatically if provided
    if "db.mrlllffauafpdjqvaxts.supabase.co" in url:
        url = url.replace("db.mrlllffauafpdjqvaxts.supabase.co", "aws-0-ap-south-1.pooler.supabase.com")
        if "postgres:" in url and "postgres.mrlllffauafpdjqvaxts" not in url:
            url = url.replace("postgres:", "postgres.mrlllffauafpdjqvaxts:", 1)

    return url


normalized_db_url = get_normalized_database_url()

engine_kwargs = {
    "echo": settings.DEBUG and not settings.is_production(),
}

if "sqlite" in normalized_db_url:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
elif os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
    # In Serverless environments, use NullPool to avoid stale pooled sockets across freezes
    engine_kwargs["poolclass"] = NullPool
    if "pooler.supabase.com" in normalized_db_url or ":6543" in normalized_db_url:
        engine_kwargs.setdefault("connect_args", {})
        engine_kwargs["connect_args"]["prepare_threshold"] = None
else:
    engine_kwargs.update(
        {
            "pool_size": settings.DATABASE_POOL_SIZE,
            "max_overflow": settings.DATABASE_MAX_OVERFLOW,
            "pool_pre_ping": True,
            "pool_recycle": 1800,  # Recycle connections after 30 minutes
        }
    )
    if "pooler.supabase.com" in normalized_db_url or ":6543" in normalized_db_url:
        engine_kwargs.setdefault("connect_args", {})
        engine_kwargs["connect_args"]["prepare_threshold"] = None

engine = create_engine(
    normalized_db_url,
    **engine_kwargs,
)

if settings.USE_AWS_IAM_AUTH:
    import boto3
    from sqlalchemy import event

    @event.listens_for(engine, "do_connect")
    def receive_do_connect(dialect, conn_rec, cargs, cparams):
        """Dynamically generate fresh 15-minute IAM auth tokens for RDS pooled connections."""
        rds_client = boto3.client("rds", region_name=settings.AWS_REGION)
        token = rds_client.generate_db_auth_token(
            DBHostname=cparams.get("host"),
            Port=int(cparams.get("port", 5432)),
            DBUsername=cparams.get("user", "postgres"),
        )
        cparams["password"] = token


# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def check_db_connection() -> tuple[bool, str]:
    """Verify that PostgreSQL is reachable and ready to serve queries."""
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
        return True, "connected"
    except Exception as e:
        logger.error("Database healthcheck failed: %s", e)
        return False, str(e)
