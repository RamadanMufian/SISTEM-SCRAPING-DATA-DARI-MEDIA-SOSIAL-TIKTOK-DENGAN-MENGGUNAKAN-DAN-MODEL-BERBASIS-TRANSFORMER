# database.py
"""
Database configuration and manager for tiktok_db1
Consolidated from database_config.py and old database.py
"""

import os
import sys
import io
import json
import traceback
from datetime import datetime, timedelta
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from models_db import Base, Video, Comment, SentimentAnalysis, ViralTopic, ViralPrediction, DailyTrend, Alert, ScrapingLog, User

# =====================================================
# DATABASE CONFIGURATION
# =====================================================

DB_NAME = 'tiktok_db1'

DB_CONFIGS = [
    {'host': 'localhost', 'user': 'root', 'password': '', 'database': DB_NAME, 'charset': 'utf8mb4', 'port': 3306},
    {'host': 'localhost', 'user': 'root', 'password': 'root', 'database': DB_NAME, 'charset': 'utf8mb4', 'port': 3306},
    {'host': 'localhost', 'user': 'root', 'password': '', 'database': DB_NAME, 'charset': 'utf8mb4', 'port': 3307},
    {'host': '127.0.0.1', 'user': 'root', 'password': '', 'database': DB_NAME, 'charset': 'utf8mb4', 'port': 3306},
]

DB_CONFIG_FINAL = None
engine = None

for config in DB_CONFIGS:
    try:
        url = f"mysql+pymysql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}?charset={config['charset']}"
        test_engine = create_engine(url, pool_pre_ping=True)
        with test_engine.connect() as conn:
            conn.execute(func.select(1))
            DB_CONFIG_FINAL = config
            engine = test_engine
            print(f"[OK] Database connected: {config['host']}:{config['port']} (Database: {DB_NAME})")
            break
    except Exception:
        continue

if DB_CONFIG_FINAL is None:
    print(f"[WARN] Could not connect to {DB_NAME}. Using default credentials for engine creation.")
    config = DB_CONFIGS[0]
    DATABASE_URL = f"mysql+pymysql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}?charset={config['charset']}"
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db_session = scoped_session(SessionLocal)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =====================================================
# DATABASE MANAGER CLASS
# =====================================================

class DatabaseManager:
    """Consolidated Database Manager for all operations"""
    
    def __init__(self):
        self.engine = engine
        self.session = db_session
    
    def init_db(self):
        """Create all tables"""
        Base.metadata.create_all(bind=self.engine)
        print("✅ Database tables initialized")
    
    # ========== VIDEO OPERATIONS ==========
    
    def save_video(self, video_data):
        try:
            existing = self.session.query(Video).filter_by(video_id=video_data.get('video_id')).first()
            if existing:
                return existing.id
            
            video = Video(
                video_id=video_data.get('video_id'),
                platform=video_data.get('platform', 'tiktok'),
                url=video_data.get('url'),
                title=video_data.get('title', ''),
                description=video_data.get('description', ''),
                author_username=video_data.get('author_username', 'unknown'),
                author_followers=video_data.get('author_followers', 0),
                views_count=video_data.get('views_count', 0),
                likes_count=video_data.get('likes_count', 0),
                comments_count=video_data.get('comments_count', 0),
                shares_count=video_data.get('shares_count', 0),
                saves_count=video_data.get('saves_count', 0),
                published_date=video_data.get('published_date'),
                scraped_date=video_data.get('scraped_date', datetime.now()),
                category=video_data.get('category'),
                tags=json.dumps(video_data.get('tags', [])) if video_data.get('tags') else None
            )
            self.session.add(video)
            self.session.commit()
            return video.id
        except Exception as e:
            self.session.rollback()
            print(f"❌ Error save_video: {e}")
            return None

    # ========== COMMENT OPERATIONS ==========
    
    def save_comment(self, comment_data):
        try:
            existing = self.session.query(Comment).filter_by(comment_id=comment_data.get('comment_id')).first()
            if existing:
                return existing.id
            
            comment = Comment(
                video_id=comment_data['video_id'],
                comment_id=comment_data.get('comment_id'),
                parent_comment_id=comment_data.get('parent_comment_id'),
                raw_text=comment_data.get('raw_text', ''),
                clean_text=comment_data.get('clean_text', ''),
                username=comment_data.get('username', 'anonymous'),
                display_name=comment_data.get('display_name', ''),
                bio=comment_data.get('bio', ''),
                user_followers=comment_data.get('user_followers', 0),
                like_count=comment_data.get('like_count', 0),
                reply_count=comment_data.get('reply_count', 0),
                comment_date=comment_data.get('comment_date', datetime.now()),
                detected_province=comment_data.get('province'),
                detected_city=comment_data.get('city'),
                detected_island=comment_data.get('island'),
                location_confidence=comment_data.get('location_confidence', 0),
                detection_method=comment_data.get('detection_method'),
                detection_source=comment_data.get('source')
            )
            self.session.add(comment)
            self.session.flush()
            
            if comment_data.get('sentiment'):
                sentiment = SentimentAnalysis(
                    comment_id=comment.id,
                    sentiment=comment_data['sentiment'],
                    sentiment_score=comment_data.get('sentiment_score', 0.5),
                    positive_score=comment_data.get('positive_score', 0),
                    negative_score=comment_data.get('negative_score', 0),
                    neutral_score=comment_data.get('neutral_score', 0),
                    keywords=json.dumps(comment_data.get('keywords', [])),
                    emotional_words=json.dumps(comment_data.get('emotional_words', []))
                )
                self.session.add(sentiment)
            
            self.session.commit()
            return comment.id
        except Exception as e:
            self.session.rollback()
            print(f"❌ Error save_comment: {e}")
            return None

    # ========== STATS & TRENDS ==========

    def get_regional_stats(self, days=30):
        cutoff_date = datetime.now() - timedelta(days=days)
        stats = self.session.query(
            Comment.detected_province,
            func.count(Comment.id).label('total'),
            func.sum(func.case((SentimentAnalysis.sentiment == 'Positif', 1), else_=0)).label('positive'),
            func.sum(func.case((SentimentAnalysis.sentiment == 'Negatif', 1), else_=0)).label('negative')
        ).outerjoin(SentimentAnalysis, Comment.id == SentimentAnalysis.comment_id).filter(
            Comment.detected_province.isnot(None),
            Comment.comment_date >= cutoff_date
        ).group_by(Comment.detected_province).all()
        
        return [{
            'province': s.detected_province,
            'total': s.total,
            'positive': s.positive or 0,
            'negative': s.negative or 0,
            'positive_pct': round((s.positive or 0) / s.total * 100, 1) if s.total > 0 else 0
        } for s in stats]

    def get_viral_topics(self, limit=10):
        return self.session.query(ViralTopic).filter_by(is_active=True).order_by(ViralTopic.viral_score.desc()).limit(limit).all()

    def get_viral_predictions(self):
        return self.session.query(ViralPrediction).order_by(ViralPrediction.predicted_viral_score.desc()).limit(10).all()

    def get_alerts(self, unread_only=True):
        query = self.session.query(Alert).order_by(Alert.created_at.desc())
        if unread_only:
            query = query.filter_by(is_read=False)
        return query.limit(20).all()

if __name__ == "__main__":
    db = DatabaseManager()
    db.init_db()