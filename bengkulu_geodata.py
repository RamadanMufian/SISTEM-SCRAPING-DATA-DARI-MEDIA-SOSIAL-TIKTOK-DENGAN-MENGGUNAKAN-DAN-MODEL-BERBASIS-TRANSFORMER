# bengkulu_geodata.py (UPDATE - Gunakan analyzer baru)
"""
Generator heatmap untuk Provinsi Bengkulu dengan analisis sentimen akurat
"""

from bengkulu_data_static import (
    BENGKULU_REGIONS, 
    BPS_STATS,
    get_all_kabupaten,
    get_summary_stats
)
from bengkulu_sentiment_analyzer import BengkuluBatchAnalyzer, BengkuluLocationDetector
from database import DatabaseManager
from models_db import Comment, SentimentAnalysis
import pandas as pd
from datetime import datetime


class BengkuluHeatmapGenerator:
    """
    Generator heatmap untuk Provinsi Bengkulu dengan analisis akurat
    """
    
    def __init__(self):
        self.regions = BENGKULU_REGIONS
        self.stats = BPS_STATS
        self.batch_analyzer = BengkuluBatchAnalyzer()
        self.location_detector = BengkuluLocationDetector()
        print("✅ Bengkulu Heatmap Generator siap (dengan analisis akurat)")
    
    def get_all_regions(self):
        """Dapatkan semua wilayah di Bengkulu"""
        return get_all_kabupaten()
    
    def get_kecamatan_by_kabupaten(self, kabupaten_name):
        """Dapatkan daftar kecamatan berdasarkan kabupaten"""
        from bengkulu_data_static import KECAMATAN_DATA
        return KECAMATAN_DATA.get(kabupaten_name.upper(), [])
    
    def get_social_data(self, region_name):
        """Dapatkan data sosial dari BPS"""
        return self.stats.get(region_name, {})
    
    def get_summary_stats(self):
        """Dapatkan statistik ringkasan"""
        return get_summary_stats()
    
    def analyze_comments_from_db(self, limit=5000):
        """
        Analisis komentar dari database dengan metode akurat
        
        Returns:
            tuple: (results, stats, sentiment_by_region)
        """
        db = DatabaseManager()
        
        # Ambil komentar yang terdeteksi di Bengkulu atau yang mengandung kata kunci Bengkulu
        comments = db.session.query(Comment).filter(
            (Comment.detected_province == 'BENGKULU') |
            (Comment.raw_text.like('%bengkulu%')) |
            (Comment.raw_text.like('%curup%')) |
            (Comment.raw_text.like('%manna%')) |
            (Comment.raw_text.like('%argamakmur%'))
        ).limit(limit).all()
        
        print(f"📊 Komentar Bengkulu yang akan dianalisis: {len(comments)}")
        
        if not comments:
            return [], {}, {}
        
        # Siapkan data untuk batch analyzer
        comment_data = []
        for c in comments:
            comment_data.append({
                'id': c.id,
                'text': c.raw_text,
                'username': c.username
            })
        
        # Analisis batch
        print("🔍 Menganalisis sentimen dengan metode akurat...")
        results = self.batch_analyzer.analyze_batch(comment_data)
        
        # Dapatkan statistik
        stats = self.batch_analyzer.get_summary(results)
        regional_stats = self.batch_analyzer.get_regional_stats(results)
        
        # Format untuk heatmap
        sentiment_by_region = {}
        for region, stat in regional_stats.items():
            sentiment_by_region[region] = {
                "positive_pct": stat.get("positive_pct", 0),
                "negative_pct": stat.get("negative_pct", 0),
                "positive": stat.get("positive", 0),
                "negative": stat.get("negative", 0),
                "neutral": stat.get("neutral", 0),
                "total": stat.get("total", 0),
                "avg_confidence": stat.get("avg_confidence", 0)
            }
        
        return results, stats, sentiment_by_region
    
    def generate_heatmap_data(self, sentiment_data):
        """
        Generate data heatmap dengan integrasi sentimen dan data sosial
        
        Args:
            sentiment_data: dict dari hasil analisis
        
        Returns:
            list of dict untuk heatmap
        """
        heatmap_data = []
        
        for region in self.get_all_regions():
            region_name = region["nama"]
            
            # Data sentimen (dari analisis akurat)
            sentiment = sentiment_data.get(region_name, {
                "positive_pct": 0,
                "total": 0,
                "avg_confidence": 0
            })
            
            # Data sosial dari BPS
            social = self.get_social_data(region_name)
            
            # Hitung skor komposit (0-100)
            sentiment_score = sentiment.get("positive_pct", 0)
            ipm_score = social.get("ipm", 0)
            gdp = social.get("gdp", 0)
            gdp_score = min(100, (gdp / 15000) * 100) if gdp > 0 else 0
            poverty = social.get("kemiskinan", 0)
            poverty_score = max(0, 100 - poverty * 2)
            
            # Bobot: sentimen 50%, IPM 20%, PDRB 15%, kemiskinan 15%
            composite_score = (
                sentiment_score * 0.5 +
                ipm_score * 0.2 +
                gdp_score * 0.15 +
                poverty_score * 0.15
            )
            
            # Tentukan warna berdasarkan skor
            if composite_score >= 80:
                color = "#22c55e"
                status = "Sangat Positif"
            elif composite_score >= 60:
                color = "#86efac"
                status = "Positif"
            elif composite_score >= 40:
                color = "#9ca3af"
                status = "Netral"
            elif composite_score >= 20:
                color = "#f87171"
                status = "Negatif"
            else:
                color = "#dc2626"
                status = "Sangat Negatif"
            
            heatmap_data.append({
                "region": region_name,
                "type": region["type"],
                "kode": region["kode"],
                "lat": region["lat"],
                "lon": region["lon"],
                "sentiment_score": round(sentiment_score, 1),
                "sentiment_confidence": sentiment.get("avg_confidence", 0),
                "ipm": social.get("ipm", 0),
                "gdp": social.get("gdp", 0),
                "poverty": social.get("kemiskinan", 0),
                "population": social.get("penduduk", 0),
                "education": social.get("pendidikan", 0),
                "health": social.get("kesehatan", 0),
                "composite_score": round(composite_score, 1),
                "status": status,
                "color": color,
                "total_comments": sentiment.get("total", 0),
                "positive_count": sentiment.get("positive", 0),
                "negative_count": sentiment.get("negative", 0),
                "neutral_count": sentiment.get("neutral", 0),
                "kecamatan_count": region.get("kecamatan", 0),
                "desa_count": region.get("desa", 0)
            })
        
        # Urutkan berdasarkan skor komposit
        heatmap_data.sort(key=lambda x: x["composite_score"], reverse=True)
        
        return heatmap_data
    
    def get_statistics_summary(self, heatmap_data):
        """Dapatkan ringkasan statistik dari data heatmap"""
        if not heatmap_data:
            return {}
        
        total_population = sum(d["population"] for d in heatmap_data)
        total_comments = sum(d["total_comments"] for d in heatmap_data)
        avg_ipm = sum(d["ipm"] for d in heatmap_data) / len(heatmap_data)
        avg_sentiment = sum(d["sentiment_score"] for d in heatmap_data) / len(heatmap_data)
        avg_composite = sum(d["composite_score"] for d in heatmap_data) / len(heatmap_data)
        
        best_region = max(heatmap_data, key=lambda x: x["composite_score"])
        worst_region = min(heatmap_data, key=lambda x: x["composite_score"])
        
        # Kategorisasi
        sangat_positif = [d for d in heatmap_data if d["composite_score"] >= 80]
        positif = [d for d in heatmap_data if 60 <= d["composite_score"] < 80]
        netral = [d for d in heatmap_data if 40 <= d["composite_score"] < 60]
        negatif = [d for d in heatmap_data if 20 <= d["composite_score"] < 40]
        sangat_negatif = [d for d in heatmap_data if d["composite_score"] < 20]
        
        return {
            "total_population": total_population,
            "total_comments": total_comments,
            "avg_ipm": round(avg_ipm, 1),
            "avg_sentiment": round(avg_sentiment, 1),
            "avg_composite": round(avg_composite, 1),
            "best_region": {
                "name": best_region["region"],
                "score": best_region["composite_score"],
                "sentiment": best_region["sentiment_score"],
                "ipm": best_region["ipm"]
            },
            "worst_region": {
                "name": worst_region["region"],
                "score": worst_region["composite_score"],
                "sentiment": worst_region["sentiment_score"],
                "ipm": worst_region["ipm"]
            },
            "total_regions": len(heatmap_data),
            "categories": {
                "sangat_positif": len(sangat_positif),
                "positif": len(positif),
                "netral": len(netral),
                "negatif": len(negatif),
                "sangat_negatif": len(sangat_negatif)
            }
        }


if __name__ == "__main__":
    print("="*60)
    print("🗺️  BENGKULU HEATMAP GENERATOR (AKURAT)")
    print("="*60)
    
    generator = BengkuluHeatmapGenerator()
    
    # Test dengan data dummy
    sample_sentiment = {
        "BENGKULU": {"positive_pct": 78, "total": 150, "avg_confidence": 85},
        "REJANG LEBONG": {"positive_pct": 68, "total": 80, "avg_confidence": 82},
        "BENGKULU UTARA": {"positive_pct": 55, "total": 60, "avg_confidence": 75},
        "SELUMA": {"positive_pct": 45, "total": 40, "avg_confidence": 70},
    }
    
    heatmap = generator.generate_heatmap_data(sample_sentiment)
    
    print("\n📊 HEATMAP DATA:")
    for item in heatmap[:5]:
        print(f"   {item['region']}: Score={item['composite_score']} | Sentiment={item['sentiment_score']}% | Conf={item['sentiment_confidence']}%")
    
    stats = generator.get_statistics_summary(heatmap)
    print(f"\n📈 STATISTICS:")
    print(f"   Total Komentar: {stats['total_comments']}")
    print(f"   Avg Sentiment: {stats['avg_sentiment']}%")
    print(f"   Best: {stats['best_region']['name']} ({stats['best_region']['score']})")
    print(f"   Worst: {stats['worst_region']['name']} ({stats['worst_region']['score']})")