# viral_analyzer.py
"""
Analisis untuk mendeteksi potensi viral
"""

import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
import joblib

class ViralAnalyzer:
    def __init__(self, db_manager):
        self.db = db_manager
        self.model = None
    
    def calculate_viral_score(self, video_id):
        """Hitung viral score untuk video"""
        
        # Ambil data video
        from models_db import Comment, SentimentAnalysis
        
        comments = self.db.session.query(Comment).filter_by(video_id=video_id).all()
        
        if len(comments) < 10:
            return 0
        
        # Faktor-faktor viral
        factors = {
            'comment_velocity': self._get_comment_velocity(comments),
            'sentiment_spread': self._get_sentiment_spread(comments),
            'geographic_spread': self._get_geographic_spread(comments),
            'engagement_rate': self._get_engagement_rate(comments),
            'influencer_count': self._get_influencer_count(comments)
        }
        
        # Bobot masing-masing faktor
        weights = {
            'comment_velocity': 0.3,
            'sentiment_spread': 0.2,
            'geographic_spread': 0.25,
            'engagement_rate': 0.15,
            'influencer_count': 0.1
        }
        
        # Hitung score
        score = sum(factors[k] * weights[k] for k in factors)
        
        return min(100, score * 100)  # Scale to 0-100
    
    def _get_comment_velocity(self, comments):
        """Kecepatan komentar per jam"""
        if len(comments) < 2:
            return 0
        
        dates = [c.comment_date for c in comments if c.comment_date]
        if not dates:
            return 0
        
        time_span = (max(dates) - min(dates)).total_seconds() / 3600  # hours
        if time_span < 1:
            time_span = 1
        
        velocity = len(comments) / time_span
        return min(1, velocity / 100)  # Normalize
    
    def _get_sentiment_spread(self, comments):
        """Keragaman sentimen"""
        from models_db import SentimentAnalysis
        
        sentiments = []
        for c in comments:
            if c.sentiment:
                sentiments.append(c.sentiment.sentiment)
        
        if not sentiments:
            return 0
        
        # Hitung entropy (semakin beragam semakin tinggi)
        pos = sentiments.count('Positif') / len(sentiments)
        neg = sentiments.count('Negatif') / len(sentiments)
        neu = sentiments.count('Netral') / len(sentiments)
        
        # Entropy = -sum(p * log(p))
        entropy = 0
        for p in [pos, neg, neu]:
            if p > 0:
                entropy -= p * np.log2(p)
        
        return entropy / 1.5  # Normalize (max entropy ~1.5)
    
    def _get_geographic_spread(self, comments):
        """Penyebaran geografis"""
        provinces = set()
        for c in comments:
            if c.detected_province:
                provinces.add(c.detected_province)
        
        # Semakin banyak provinsi semakin tinggi
        return min(1, len(provinces) / 10)  # Normalize, target 10 provinsi
    
    def _get_engagement_rate(self, comments):
        """Rata-rata like per komentar"""
        total_likes = sum(c.like_count for c in comments)
        avg_likes = total_likes / len(comments) if comments else 0
        
        return min(1, avg_likes / 50)  # Normalize
    
    def _get_influencer_count(self, comments):
        """Jumlah influencer yang berkomentar"""
        # Sederhana: user dengan followers > 10000 dianggap influencer
        influencers = sum(1 for c in comments if c.user_followers and c.user_followers > 10000)
        
        return min(1, influencers / 5)  # Normalize
    
    def predict_viral_potential(self, video_data):
        """Prediksi potensi viral menggunakan ML"""
        
        # Load model atau buat baru
        if self.model is None:
            self._train_model()
        
        # Ekstrak features
        features = self._extract_features(video_data)
        
        # Prediksi
        if self.model:
            score = self.model.predict([features])[0]
            return min(100, max(0, score))
        
        return 50  # Default
    
    def _train_model(self):
        """Train model prediksi (contoh sederhana)"""
        # Di real implementation, pakai data historis
        self.model = RandomForestRegressor(n_estimators=100)
        
        # Dummy training
        X = np.random.rand(100, 5)
        y = np.random.rand(100) * 100
        self.model.fit(X, y)
    
    def _extract_features(self, video_data):
        """Ekstrak features untuk prediksi"""
        features = [
            video_data.get('views_count', 0) / 1000000,  # views in millions
            video_data.get('likes_count', 0) / 100000,   # likes in 100k
            video_data.get('comments_count', 0) / 10000, # comments in 10k
            video_data.get('author_followers', 0) / 1000000,
            len(video_data.get('tags', [])) / 10
        ]
        return features