
from datetime import datetime
from database.database import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, func

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    assets = relationship("UserAsset", back_populates="user", cascade="all, delete-orphan")
    news_sources = relationship("UserNewsSource", back_populates="user", cascade="all, delete-orphan")
    
    def update_last_seen(self):
        """Update the last_seen timestamp"""
        self.last_seen = datetime.now()
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.telegram_id,
            'username': self.username,
            'created_at': self.created_at,
            'last_seen': self.last_seen,
            'assets': [asset.symbol for asset in self.assets],
            'news_sources': [source.url for source in self.news_sources]
        }


class UserAsset(Base):
    __tablename__ = "user_assets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="assets")

    __table_args__ = (
        UniqueConstraint("user_id", "symbol", name="uix_user_asset"),
    )


class UserNewsSource(Base):
    __tablename__ = "user_news_sources"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    url = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="news_sources")

    __table_args__ = (
        UniqueConstraint("user_id", "url", name="uix_user_news"),
    )
