from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

if not settings.DATABASE_URL:
    raise RuntimeError("DATABASE_URL is required. Copy .env.example to .env and fill in your Supabase/Postgres connection string.")

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    with Session(engine) as session:
        yield session
