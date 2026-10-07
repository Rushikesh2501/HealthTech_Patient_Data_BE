"""Database engine configuration with connection pooling and health checks."""

import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

engine_kwargs = {
    "echo": settings.DEBUG and not settings.is_production(),
}

if "sqlite" in settings.DATABASE_URL:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs.update(
        {
            "pool_size": settings.DATABASE_POOL_SIZE,
            "max_overflow": settings.DATABASE_MAX_OVERFLOW,
            "pool_pre_ping": True,
            "pool_recycle": 1800,  # Recycle connections after 30 minutes
        }
    )
    # Supabase transaction pooler (port 6543 / Supavisor) compatibility
    if "pooler.supabase.com" in settings.DATABASE_URL or ":6543" in settings.DATABASE_URL:
        engine_kwargs.setdefault("connect_args", {})
        engine_kwargs["connect_args"]["prepare_threshold"] = None

engine = create_engine(
    settings.DATABASE_URL,
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


def check_db_connection() -> bool:
    """Verify that PostgreSQL is reachable and ready to serve queries."""
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
        return True
    except Exception as e:
        logger.error("Database healthcheck failed: %s", e)
        return False
