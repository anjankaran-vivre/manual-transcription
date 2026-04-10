"""Database connection and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import settings
from app.logging.log_streamer import log_streamer

# Construct MSSQL connection string
SQLALCHEMY_DATABASE_URL = (
    f"mssql+pyodbc://@{settings.DB_HOST}\\{settings.DB_SERVER}/{settings.DB_NAME}"
    "?driver=ODBC+Driver+18+for+SQL+Server&trusted_connection=yes"
    "&TrustServerCertificate=yes&charset=utf8"
)

log_streamer.info("Database", f"🗄️ Database URL: {settings.DB_NAME} on {settings.DB_HOST}\\{settings.DB_SERVER}")


class DatabaseManager:
    """Singleton class to manage database connection and sessions."""

    _instance = None
    _engine = None
    _session_factory = None
    _base = declarative_base()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the database engine and session factory."""
        try:
            self._engine = create_engine(
                SQLALCHEMY_DATABASE_URL,
                pool_size=20,
                max_overflow=40,
                pool_pre_ping=True,
                pool_recycle=3600,
                connect_args={
                    "charset": "utf8",
                    "timeout": 30,
                    "login_timeout": 30,
                },
            )

            self._session_factory = sessionmaker(
                autocommit=False, autoflush=False, bind=self._engine
            )
            
            log_streamer.info("Database", "✅ Database connection initialized")
        except Exception as e:
            log_streamer.error("Database", f"❌ Failed to initialize database: {str(e)}")
            raise

    @property
    def base(self):
        return self._base

    @property
    def engine(self):
        return self._engine

    def get_session(self) -> Session:
        """Create and return a new database session."""
        return self._session_factory()

    def init_db(self):
        """Import all schemas and create tables."""
        try:
            self._base.metadata.create_all(self._engine)
            log_streamer.info("Database", "✅ Database tables initialized")
        except Exception as e:
            log_streamer.error("Database", f"❌ Failed to initialize database tables: {str(e)}")
            raise


db_manager = DatabaseManager()
Base = db_manager.base


def get_db():
    """FastAPI dependency that yields a database session."""
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()