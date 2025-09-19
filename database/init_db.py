import logging
import sys
from sqlalchemy import text
from alembic import command
from alembic.config import Config
from database.database import engine, Base, SessionLocal, DATABASE_URL
from database import models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize the database with migrations"""
    if not DATABASE_URL:
        logger.error("DATABASE_URL is not set in environment variables")
        return False
    try:
        # Run Alembic migrations (this will create all tables)
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        logging.info("Database migrations applied successfully")
        
        # Test database connection
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
            db.commit()
        except Exception as e:
            logger.error(f"Database connection test failed: {str(e)}")
            return False
        finally:
            db.close()
            
        logger.info("Database initialization completed successfully")
        print("Database initialization completed successfully ✅")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        print(f"Error initializing database: {str(e)} ❌")
        return False

if __name__ == "__main__":
    success = init_database()
    if not success:
        sys.exit(1)
