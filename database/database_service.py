import logging
from sqlalchemy import text
from datetime import datetime
from sqlalchemy.orm import Session
from database.database import SessionLocal
from typing import List, Optional, Dict, Any
from utils.url_normalize import normalize_rss_url
from database.models import User, UserAsset, UserNewsSource


class DatabaseService:
    """Service layer for database operations with fallback mechanisms"""
    
    def __init__(self):
        self.session: Optional[Session] = None
    
    def __enter__(self):
        logging.info("Initializing database session")
        try:
            self.session = SessionLocal()
            # Test the connection
            self.session.execute(text("SELECT 1"))
            logging.info("Database connection successful")
            return self
        except Exception as e:
            logging.error(f"Failed to initialize database session: {str(e)}", exc_info=True)
            if self.session:
                self.session.close()
            raise
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            try:
                if exc_type is None:
                    logging.info("Committing database transaction")
                    self.session.commit()
                    logging.info("Database transaction committed successfully")
                else:
                    logging.warning(f"Rolling back transaction due to error: {str(exc_val)}")
                    self.session.rollback()
            except Exception as e:
                logging.error(f"Error during session cleanup: {str(e)}", exc_info=True)
                self.session.rollback()
                raise
            finally:
                logging.info("Closing database session")
                self.session.close()
                self.session = None

    def get_or_create_user(self, telegram_id: str, username: str = None) -> User:
        """Get existing user or create new one"""
        try:
            logging.info(f"Starting get_or_create_user for telegram_id: {telegram_id}")
            
            # First try to find the existing user
            logging.info(f"Querying for user with telegram_id: {telegram_id}")
            user = self.session.query(User).filter(User.telegram_id == telegram_id).first()
            
            if not user:
                logging.info(f"User {telegram_id} not found, creating new user")
                try:
                    # Create new user
                    user = User(
                        telegram_id=telegram_id,
                        username=username,
                        created_at=datetime.now(),
                        last_seen=datetime.now()
                    )
                    self.session.add(user)
                    # Flush to get the ID and check for any immediate errors
                    self.session.flush()
                    logging.info(f"Created new user with ID: {user.id}")
                except Exception as e:
                    logging.error(f"Error creating new user: {str(e)}", exc_info=True)
                    self.session.rollback()
                    raise
            else:
                # Always update last_seen and username for existing users
                logging.info(f"Found existing user with telegram_id: {telegram_id}")
                if username and user.username != username:
                    logging.info(f"Updating username from {user.username} to {username}")
                    user.username = username
                user.update_last_seen()  # Using the model's method to update last_seen
            
            # Commit the transaction
            try:
                self.session.commit()
                logging.info(f"Successfully committed user operation for telegram_id: {telegram_id}")
            except Exception as e:
                logging.error(f"Error committing transaction: {str(e)}", exc_info=True)
                self.session.rollback()
                raise
            
            return user
            
        except Exception as e:
            logging.error(f"Database error in get_or_create_user: {str(e)}", exc_info=True)
            self.session.rollback()
            raise

    def update_user_last_seen(self, telegram_id: str):
        """Update user's last seen timestamp"""
        try:
            user = self.session.query(User).filter(User.telegram_id == telegram_id).first()
            if user:
                user.last_seen = datetime.now()
                self.session.commit()
        except Exception as e:
            logging.error(f"Database error in update_user_last_seen: {str(e)}")
            self.session.rollback()

    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users with their latest activity"""
        try:
            users = self.session.query(User).all()
            return [
                {
                    'id': user.telegram_id,
                    'username': user.username,
                    'created_at': user.created_at,
                    'last_seen': user.last_seen
                }
                for user in users
            ]
        except Exception as e:
            logging.error(f"Database error in get_all_users: {str(e)}")
            return []

    def add_user_asset(self, telegram_id: str, symbol: str) -> bool:
        """Add crypto asset tracking for user"""
        try:
            user = self.get_or_create_user(telegram_id)
            existing = self.session.query(UserAsset).filter(
                UserAsset.user_id == user.id,
                UserAsset.symbol == symbol
            ).first()
            
            if not existing:
                asset = UserAsset(user_id=user.id, symbol=symbol)
                self.session.add(asset)
                self.session.commit()
            return True
        except Exception as e:
            logging.error(f"Database error in add_user_asset: {str(e)}")
            self.session.rollback()
            return False

    def get_user_assets(self, telegram_id: str) -> List[str]:
        """Get user's tracked crypto assets"""
        try:
            user = self.session.query(User).filter(User.telegram_id == telegram_id).first()
            if user:
                return [asset.symbol for asset in user.assets]
            return []
        except Exception as e:
            logging.error(f"Database error in get_user_assets: {str(e)}")
            return []

    def add_news_source(self, telegram_id: str, url: str) -> bool:
        """Add RSS feed source for user"""
        try:
            user = self.get_or_create_user(telegram_id)
            existing = self.session.query(UserNewsSource).filter(
                UserNewsSource.user_id == user.id,
                UserNewsSource.url == url
            ).first()
            
            if not existing:
                source = UserNewsSource(user_id=user.id, url=url)
                self.session.add(source)
                self.session.commit()
            return True
        except Exception as e:
            logging.error(f"Database error in add_news_source: {str(e)}")
            self.session.rollback()
            return False

    def get_user_news_sources(self, telegram_id: str) -> List[str]:
        """Get user's tracked news sources"""
        try:
            user = self.session.query(User).filter(User.telegram_id == telegram_id).first()
            if user:
                return [source.url for source in user.news_sources]
            return []
        except Exception as e:
            logging.error(f"Database error in get_user_news_sources: {str(e)}")
            return []

    def get_recent_users(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get users active within the last X hours"""
        try:
            from datetime import timedelta
            cutoff = datetime.now() - timedelta(hours=hours)
            recent_users = self.session.query(User).filter(User.last_seen >= cutoff).all()
            return [
                {
                    'id': user.telegram_id,
                    'username': user.username,
                    'last_seen': user.last_seen
                }
                for user in recent_users
            ]
        except Exception as e:
            logging.error(f"Database error in get_recent_users: {str(e)}")
            return []
    

    def remove_user_asset(self, telegram_id: str, symbol: str) -> bool:
        """Remove crypto asset tracking for user"""
        try:
            user = self.session.query(User).filter(User.telegram_id == telegram_id).first()
            if user:
                deleted = self.session.query(UserAsset).filter(
                    UserAsset.user_id == user.id,
                    UserAsset.symbol == symbol
                ).delete(synchronize_session=False)
                self.session.commit()
                self.session.expire_all()
                return deleted > 0
            return False
        except Exception as e:
            logging.error(f"Database error in remove_user_asset: {str(e)}")
            self.session.rollback()
            return False

    def remove_news_source(self, telegram_id: str, url: str) -> bool:
        """Remove RSS feed source for user"""
        try:
            user = self.session.query(User).filter(User.telegram_id == telegram_id).first()
            if user:
                # normalize input
                normalized = normalize_rss_url(url)

                # try exact match first
                deleted = self.session.query(UserNewsSource).filter(
                    UserNewsSource.user_id == user.id,
                    UserNewsSource.url == normalized
                ).delete(synchronize_session=False)

                # fallback: try loose match if nothing deleted
                if deleted == 0:
                    deleted = self.session.query(UserNewsSource).filter(
                        UserNewsSource.user_id == user.id,
                        UserNewsSource.url.ilike(f"%{url.strip()}%")
                    ).delete(synchronize_session=False)

                self.session.commit()
                self.session.expire_all()
                return deleted > 0
            return False
        except Exception as e:
            logging.error(f"Database error in remove_news_source: {str(e)}", exc_info=True)
            self.session.rollback()
            return False
