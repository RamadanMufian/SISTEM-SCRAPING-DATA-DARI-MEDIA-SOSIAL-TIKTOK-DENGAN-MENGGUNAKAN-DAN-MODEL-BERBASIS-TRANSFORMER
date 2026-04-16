# models_db.py
"""
SQLAlchemy models untuk database tiktok_db1 - COMPLETE VERSION
Semua model tabel didefinisikan di sini.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, Index
try:
    from sqlalchemy.orm import declarative_base
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


# =====================================================
# MODEL: VIDEO
# =====================================================

class Video(Base):
    """Model untuk menyimpan data video TikTok"""
    __tablename__ = 'videos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(String(100), unique=True, nullable=False)
    platform = Column(String(50), default='tiktok')
    url = Column(String(500))
    title = Column(String(500))
    description = Column(Text)
    author_username = Column(String(200))
    author_followers = Column(Integer, default=0)

    # Stats
    views_count = Column(Integer, default=0)
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    shares_count = Column(Integer, default=0)
    saves_count = Column(Integer, default=0)

    # Metadata
    published_date = Column(DateTime)
    scraped_date = Column(DateTime, default=datetime.now)
    last_updated = Column(DateTime, onupdate=datetime.now)
    category = Column(String(100))
    tags = Column(Text)
    is_viral = Column(Boolean, default=False)
    viral_score = Column(Float, default=0)

    # Relationships
    comments = relationship("Comment", back_populates="video", cascade="all, delete-orphan")
    predictions = relationship("ViralPrediction", back_populates="video", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_video_id', 'video_id'),
        Index('idx_platform', 'platform'),
        Index('idx_published', 'published_date'),
        Index('idx_viral', 'is_viral'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'video_id': self.video_id,
            'platform': self.platform,
            'url': self.url,
            'title': self.title,
            'author_username': self.author_username,
            'views_count': self.views_count,
            'likes_count': self.likes_count,
            'comments_count': self.comments_count,
            'scraped_date': self.scraped_date.isoformat() if self.scraped_date else None,
            'is_viral': self.is_viral,
            'viral_score': self.viral_score
        }


# =====================================================
# MODEL: COMMENT
# =====================================================

class Comment(Base):
    """
    Model untuk menyimpan komentar dengan informasi lengkap
    termasuk deteksi lokasi multi-layer
    """
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(Integer, ForeignKey('videos.id', ondelete='CASCADE'))
    comment_id = Column(String(100), unique=True)
    parent_comment_id = Column(String(100))

    # Content
    raw_text = Column(Text, nullable=False)
    clean_text = Column(Text)

    # User Info (untuk deteksi lokasi)
    username = Column(String(200), index=True)
    display_name = Column(String(200))
    bio = Column(Text)
    user_followers = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    reply_count = Column(Integer, default=0)

    # Dates
    comment_date = Column(DateTime, index=True)
    scraped_date = Column(DateTime, default=datetime.now)

    # Hasil Deteksi Lokasi
    detected_province = Column(String(100), index=True)
    detected_city = Column(String(100))
    detected_island = Column(String(50))
    location_confidence = Column(Float, default=0)
    detection_method = Column(String(50))
    detection_source = Column(String(50))

    # Action flags
    replied = Column(Boolean, default=False)
    reported = Column(Boolean, default=False)
    liked = Column(Boolean, default=False)

    # AI responses
    reply_text = Column(Text)
    report_text = Column(Text)

    # Relationships
    video = relationship("Video", back_populates="comments")
    sentiment = relationship("SentimentAnalysis", uselist=False, back_populates="comment", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_video_date', 'video_id', 'comment_date'),
        Index('idx_username', 'username'),
        Index('idx_location', 'detected_province', 'detected_city'),
        Index('idx_source', 'detection_source'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'video_id': self.video_id,
            'comment_id': self.comment_id,
            'raw_text': self.raw_text[:200] + '...' if self.raw_text and len(self.raw_text) > 200 else self.raw_text,
            'username': self.username,
            'display_name': self.display_name,
            'bio': self.bio[:100] + '...' if self.bio and len(self.bio) > 100 else self.bio,
            'like_count': self.like_count,
            'comment_date': self.comment_date.isoformat() if self.comment_date else None,
            'detected_province': self.detected_province,
            'detected_city': self.detected_city,
            'detected_island': self.detected_island,
            'location_confidence': self.location_confidence,
            'detection_source': self.detection_source,
            'detection_method': self.detection_method,
            'sentiment': self.sentiment.sentiment if self.sentiment else None,
            'sentiment_score': self.sentiment.sentiment_score if self.sentiment else None
        }

    def get_location_info(self):
        return {
            'province': self.detected_province,
            'city': self.detected_city,
            'island': self.detected_island,
            'confidence': self.location_confidence,
            'source': self.detection_source,
            'method': self.detection_method
        }


# =====================================================
# MODEL: SENTIMENT ANALYSIS
# =====================================================

class SentimentAnalysis(Base):
    """Model untuk menyimpan hasil analisis sentimen"""
    __tablename__ = 'sentiment_analysis'

    id = Column(Integer, primary_key=True, autoincrement=True)
    comment_id = Column(Integer, ForeignKey('comments.id', ondelete='CASCADE'), unique=True)

    sentiment = Column(String(20), index=True)   # 'Positif', 'Negatif', 'Netral'
    sentiment_score = Column(Float)               # 0-1 confidence
    positive_score = Column(Float, default=0)
    negative_score = Column(Float, default=0)
    neutral_score = Column(Float, default=0)

    analyzed_by = Column(String(50), default='roberta')
    analyzed_date = Column(DateTime, default=datetime.now)

    keywords = Column(Text)                       # JSON array kata kunci
    emotional_words = Column(Text)                # JSON array kata emosional

    is_flagged = Column(Boolean, default=False)
    flag_reason = Column(String(200))

    # Relationships
    comment = relationship("Comment", back_populates="sentiment")

    __table_args__ = (
        Index('idx_sentiment', 'sentiment'),
        Index('idx_analyzed', 'analyzed_date'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'comment_id': self.comment_id,
            'sentiment': self.sentiment,
            'sentiment_score': self.sentiment_score,
            'analyzed_date': self.analyzed_date.isoformat() if self.analyzed_date else None
        }

    def get_scores_dict(self):
        return {
            'positif': self.positive_score,
            'negatif': self.negative_score,
            'netral': self.neutral_score,
            'sentiment': self.sentiment,
            'confidence': self.sentiment_score
        }


# =====================================================
# MODEL: VIRAL PREDICTION
# =====================================================

class ViralPrediction(Base):
    """Model untuk menyimpan prediksi viral"""
    __tablename__ = 'viral_predictions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(Integer, ForeignKey('videos.id', ondelete='CASCADE'))

    predicted_viral_score = Column(Float)
    confidence = Column(Float)
    predicted_peak_date = Column(DateTime)

    comment_velocity = Column(Float)
    sentiment_shift = Column(Float)
    geographic_spread = Column(Integer)
    influencer_count = Column(Integer)

    prediction_features = Column(Text)
    prediction_model = Column(String(100))

    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    video = relationship("Video", back_populates="predictions")

    __table_args__ = (
        Index('idx_prediction_video', 'video_id'),
        Index('idx_prediction_score', 'predicted_viral_score'),
    )


# =====================================================
# MODEL: VIRAL TOPIC
# =====================================================

class ViralTopic(Base):
    """Model untuk topik viral"""
    __tablename__ = 'viral_topics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_name = Column(String(200), nullable=False)
    topic_slug = Column(String(200), unique=True)

    category = Column(String(100))
    region_focus = Column(String(100))

    mention_count = Column(Integer, default=0)
    positive_mentions = Column(Integer, default=0)
    negative_mentions = Column(Integer, default=0)
    neutral_mentions = Column(Integer, default=0)

    viral_score = Column(Float, default=0)
    velocity = Column(Float, default=0)
    peak_date = Column(DateTime)

    first_seen = Column(DateTime)
    last_seen = Column(DateTime)
    is_active = Column(Boolean, default=True)

    related_keywords = Column(Text)
    sample_comments = Column(Text)

    __table_args__ = (
        Index('idx_topic_name', 'topic_name'),
        Index('idx_topic_active', 'is_active'),
        Index('idx_topic_score', 'viral_score'),
    )


# =====================================================
# MODEL: REGIONAL STAT
# =====================================================

class RegionalStat(Base):
    """Model untuk statistik regional (heatmap)"""
    __tablename__ = 'regional_stats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    stat_date = Column(DateTime, nullable=False, index=True)

    province = Column(String(100), nullable=False, index=True)
    island = Column(String(50))
    city = Column(String(100))

    total_comments = Column(Integer, default=0)
    positive_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
    neutral_count = Column(Integer, default=0)
    positive_pct = Column(Float, default=0)

    latitude = Column(Float)
    longitude = Column(Float)

    top_topics = Column(Text)   # JSON

    __table_args__ = (
        Index('idx_region_date', 'province', 'city', 'stat_date'),
        Index('idx_stat_date', 'stat_date'),
    )

    def update_percentages(self):
        if self.total_comments > 0:
            self.positive_pct = round(self.positive_count / self.total_comments * 100, 1)

    def to_heatmap_point(self):
        return {
            'province': self.province,
            'lat': self.latitude,
            'lon': self.longitude,
            'value': self.positive_pct,
            'total': self.total_comments,
            'positive': self.positive_count,
            'negative': self.negative_count,
            'neutral': self.neutral_count
        }


# =====================================================
# MODEL: DAILY TREND
# =====================================================

class DailyTrend(Base):
    """Model untuk tren harian"""
    __tablename__ = 'daily_trends'

    id = Column(Integer, primary_key=True, autoincrement=True)
    trend_date = Column(DateTime, nullable=False, unique=True, index=True)

    total_comments = Column(Integer, default=0)
    total_videos = Column(Integer, default=0)
    unique_users = Column(Integer, default=0)

    positive_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
    neutral_count = Column(Integer, default=0)
    positive_pct = Column(Float, default=0)

    total_likes = Column(Integer, default=0)
    avg_likes_per_comment = Column(Float, default=0)

    viral_potential_score = Column(Float, default=0)
    top_keywords = Column(Text)   # JSON

    def calculate_pct(self):
        if self.total_comments > 0:
            self.positive_pct = round(self.positive_count / self.total_comments * 100, 1)


# =====================================================
# MODEL: ALERT
# =====================================================

class Alert(Base):
    """Model untuk alert dan notifikasi"""
    __tablename__ = 'alerts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_type = Column(String(50))

    title = Column(String(200), nullable=False)
    description = Column(Text)
    severity = Column(String(20), default='info')   # 'info', 'warning', 'critical'

    video_id = Column(Integer, ForeignKey('videos.id', ondelete='SET NULL'), nullable=True)
    topic_id = Column(Integer, ForeignKey('viral_topics.id', ondelete='SET NULL'), nullable=True)
    region = Column(String(100))

    current_value = Column(Float)
    threshold_value = Column(Float)

    is_read = Column(Boolean, default=False)
    is_notified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        Index('idx_alert_type', 'alert_type'),
        Index('idx_alert_read', 'is_read'),
        Index('idx_alert_created', 'created_at'),
    )


# =====================================================
# MODEL: SCRAPING LOG
# =====================================================

class ScrapingLog(Base):
    """Model untuk log aktivitas scraping"""
    __tablename__ = 'scraping_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(String(100))
    platform = Column(String(50))

    status = Column(String(20), default='success')   # 'success', 'failed', 'partial'
    comments_fetched = Column(Integer, default=0)
    comments_total = Column(Integer, default=0)

    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration_seconds = Column(Integer)

    error_message = Column(Text)

    used_cookies = Column(Boolean, default=False)
    ip_address = Column(String(50))
    user_agent = Column(Text)

    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        Index('idx_log_video', 'video_id'),
        Index('idx_log_status', 'status'),
        Index('idx_log_created', 'created_at'),
    )


# =====================================================
# MODEL: USER (AUTENTIKASI)
# =====================================================

class User(Base):
    """Model untuk akun pengguna sistem"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(200), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(200))
    role = Column(String(50), default='analyst')   # 'admin', 'analyst', 'viewer'
    is_active = Column(Boolean, default=True)
    avatar_url = Column(String(500))
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)

    __table_args__ = (
        Index('idx_user_username', 'username'),
        Index('idx_user_email', 'email'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# =====================================================
# FUNGSI HELPER UNTUK SCHEMA UPDATE
# =====================================================

def get_db_schema_updates():
    """Daftar ALTER TABLE untuk migrasi database lama"""
    updates = [
        "ALTER TABLE comments ADD COLUMN IF NOT EXISTS display_name VARCHAR(200)",
        "ALTER TABLE comments ADD COLUMN IF NOT EXISTS bio TEXT",
        "ALTER TABLE comments ADD COLUMN IF NOT EXISTS detection_source VARCHAR(50)",
        "ALTER TABLE comments ADD COLUMN IF NOT EXISTS replied BOOLEAN DEFAULT FALSE",
        "ALTER TABLE comments ADD COLUMN IF NOT EXISTS reported BOOLEAN DEFAULT FALSE",
        "ALTER TABLE comments ADD COLUMN IF NOT EXISTS liked BOOLEAN DEFAULT FALSE",
        "ALTER TABLE comments ADD COLUMN IF NOT EXISTS reply_text TEXT",
        "ALTER TABLE comments ADD COLUMN IF NOT EXISTS report_text TEXT",
    ]
    return updates


# =====================================================
# VERIFIKASI MODEL (TESTING)
# =====================================================

if __name__ == "__main__":
    print("=" * 60)
    print("MODELS_DB.PY - VERIFIKASI SEMUA MODEL")
    print("=" * 60)

    from sqlalchemy import create_engine, inspect

    _engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(_engine)

    _inspector = inspect(_engine)

    print("\nTABEL YANG BERHASIL DIBUAT:")
    for _table in _inspector.get_table_names():
        _cols = _inspector.get_columns(_table)
        print(f"  - {_table} ({len(_cols)} kolom)")
        for _c in _cols:
            print(f"      {_c['name']}: {_c['type']}")

    print(f"\nTotal {len(_inspector.get_table_names())} tabel berhasil diverifikasi!")