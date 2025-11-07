import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from skillbridge.utils.config import DATABASE_URL

# --- Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Global Variables ---
engine = None
SessionLocal = None

# --- Main Connection Logic ---
if not DATABASE_URL:
    # Fail fast if the database URL is not configured.
    raise ValueError("DATABASE_URL environment variable is not set in your .env file.")

try:
    # This block handles the SSL configuration for connecting to TiDB Cloud securely.
    # It intelligently switches between the local certificate path and the container path.
    
    # Define the path to your local CA certificate, assuming it's in the project root.
    local_ca_path = os.path.join(os.path.dirname(__file__), '..', '..', 'isrgrootx1.pem')
    
    # Define the fixed path where the certificate is placed inside the Modal container.
    container_ca_path = "/root/isrgrootx1.pem"

    # Check if the local file exists; otherwise, assume we are in the container.
    ca_path = local_ca_path if os.path.exists(local_ca_path) else container_ca_path
    
    # These arguments are passed directly to the underlying DBAPI (PyMySQL).
    connect_args = {
        "ssl_ca": ca_path,
        "ssl_verify_cert": True,
        "ssl_verify_identity": True
    }
    
    # Create the central SQLAlchemy engine for the application.
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Checks if connections are alive before handing them out.
        pool_recycle=300,    # Recycles connections every 5 minutes to prevent timeouts.
        connect_args=connect_args
    )
    
    # Create a configured "Session" class. This is the factory for all DB sessions.
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    logger.info("Successfully created database engine and SessionLocal.")

except Exception as e:
    # If any part of the connection setup fails, log the error.
    # The 'engine' and 'SessionLocal' will remain None, causing dependent parts of the app to fail clearly.
    logger.error(f"Failed to create database engine: {e}")


def get_db_session():
    """
    A generator function to be used as a dependency.
    It provides a database session and ensures it's closed afterward.
    """
    if SessionLocal is None:
        raise RuntimeError(
            "Database connection failed during startup. "
            "Please check your DATABASE_URL and SSL configuration."
        )
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()