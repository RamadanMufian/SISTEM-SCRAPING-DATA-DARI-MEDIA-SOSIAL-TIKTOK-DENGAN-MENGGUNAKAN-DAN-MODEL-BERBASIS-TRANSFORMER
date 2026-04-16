# scraper_db.py
"""
Scraper dengan integrasi database - ENHANCED VERSION
"""

from database import DatabaseManager
from sentiment import analyze_sentiment
from geo_sentiment import GeoLocationDetector
import pandas as pd
from datetime import datetime
import re
from sqlalchemy import func, case

class TikTokScraperWithDB:
    """
    Kelas untuk scraping TikTok dengan penyimpanan otomatis ke database
    Mendukung deteksi lokasi multi-layer dan analisis sentimen
    """
    
    def __init__(self):
        """Inisialisasi koneksi database dan detector"""
        self.db = DatabaseManager()
        self.geo = GeoLocationDetector()
        self.stats = {
            'comments_scraped': 0,
            'comments_saved': 0,
            'locations_detected': 0,
            'start_time': None,
            'end_time': None
        }
    
    def scrape_and_save(self, video_url, max_comments=1000, save_sentiment=True):
        """
        Scrape TikTok dan simpan ke database dengan analisis lengkap
        
        Args:
            video_url: URL video TikTok
            max_comments: Jumlah maksimal komentar
            save_sentiment: Jika True, lakukan analisis sentimen
        
        Returns:
            video_id: ID video di database, atau None jika gagal
        """
        self.stats['start_time'] = datetime.now()
        self.stats['comments_scraped'] = 0
        self.stats['comments_saved'] = 0
        self.stats['locations_detected'] = 0
        
        print("\n" + "="*70)
        print("🚀 TIKTOK SCRAPER WITH DATABASE")
        print("="*70)
        print(f"📱 URL: {video_url}")
        print(f"📊 Max Comments: {max_comments}")
        print(f"💾 Save Sentiment: {save_sentiment}")
        print("-"*70)
        
        # 1. Scrape comments (pake scraper yang sudah ada)
        try:
            from scraper import scrape_tiktok_comments
            comments = scrape_tiktok_comments(video_url, max_comments, save_to_db=False)
        except Exception as e:
            print(f"❌ Error scraping: {e}")
            return None
        
        if not comments:
            print("❌ Tidak ada komentar ditemukan")
            return None
        
        self.stats['comments_scraped'] = len(comments)
        print(f"✅ Mendapatkan {len(comments)} komentar")
        
        # 2. Extract video info
        video_id = self._extract_video_id(video_url)
        if not video_id:
            video_id = f"video_{int(datetime.now().timestamp())}"
        
        video_data = {
            'video_id': video_id,
            'url': video_url,
            'platform': 'tiktok',
            'title': f"Video {video_id}",
            'author_username': self._extract_username(video_url),
            'scraped_date': datetime.now(),
            'comments_count': len(comments)
        }
        
        # 3. Save video ke database
        try:
            db_video_id = self.db.save_video(video_data)
            print(f"💾 Video tersimpan dengan ID: {db_video_id}")
        except Exception as e:
            print(f"⚠️ Gagal simpan video: {e}")
            db_video_id = None
        
        # 4. Proses setiap komentar
        print("\n📝 MEMPROSES KOMENTAR...")
        print("-"*70)
        
        for i, comment in enumerate(comments, 1):
            try:
                # Ambil teks komentar
                comment_text = comment.get('comment', comment.get('text', ''))
                if not comment_text:
                    continue
                
                # Analisis sentimen
                if save_sentiment:
                    try:
                        sentiment, confidence = analyze_sentiment(comment_text, return_confidence=True)
                    except Exception as e:
                        print(f"⚠️ Error sentimen: {e}")
                        sentiment, confidence = "Netral", 50.0
                else:
                    sentiment, confidence = None, None
                
                # Deteksi lokasi dengan metode comprehensive
                location = self.geo.detect_location_comprehensive(
                    username=comment.get('username', ''),
                    display_name=comment.get('display_name', ''),
                    bio=comment.get('bio', ''),
                    comment_text=comment_text
                )
                
                if location['province']:
                    self.stats['locations_detected'] += 1
                
                # Data komentar lengkap untuk database
                comment_data = {
                    'video_id': db_video_id,
                    'comment_id': comment.get('comment_id') or f"cmt_{int(datetime.now().timestamp())}_{i}",
                    'raw_text': comment_text,
                    'clean_text': self._clean_text(comment_text),
                    'username': comment.get('username', 'anonymous'),
                    'display_name': comment.get('display_name', ''),
                    'bio': comment.get('bio', ''),
                    'like_count': comment.get('likes', 0),
                    'comment_date': comment.get('date') or datetime.now(),
                    'sentiment': sentiment,
                    'sentiment_score': confidence,
                    'province': location['province'],
                    'city': location['city'],
                    'island': location['island'],
                    'location_confidence': location['confidence'],
                    'detection_method': location['detection_method'],
                    'source': location.get('source', 'unknown')
                }
                
                # Simpan ke database
                if db_video_id:
                    try:
                        self.db.save_comment(comment_data)
                        self.stats['comments_saved'] += 1
                    except Exception as e:
                        print(f"⚠️ Gagal simpan komentar {i}: {e}")
                
                # Progress report
                if i % 50 == 0 or i == len(comments):
                    print(f"  Progress: {i}/{len(comments)} komentar")
                    print(f"     Lokasi terdeteksi: {self.stats['locations_detected']}")
                    
            except Exception as e:
                print(f"⚠️ Error processing comment {i}: {e}")
                continue
        
        # 5. Update regional stats
        if db_video_id:
            try:
                self._update_regional_stats(db_video_id)
                print("\n📊 Regional stats updated")
            except Exception as e:
                print(f"⚠️ Gagal update regional stats: {e}")
        
        # 6. Final stats
        self.stats['end_time'] = datetime.now()
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        print("\n" + "="*70)
        print("📊 SCRAPING COMPLETE - STATISTICS")
        print("="*70)
        print(f"📊 Komentar discrape: {self.stats['comments_scraped']}")
        print(f"💾 Komentar tersimpan: {self.stats['comments_saved']}")
        print(f"📍 Lokasi terdeteksi: {self.stats['locations_detected']} ({self.stats['locations_detected']/self.stats['comments_scraped']*100:.1f}%)")
        print(f"⏱️  Waktu proses: {duration:.2f} detik")
        print(f"⚡ Kecepatan: {self.stats['comments_scraped']/duration:.1f} komentar/detik")
        print("="*70)
        
        return db_video_id
    
    def _update_regional_stats(self, video_id):
        """
        Update statistik regional setelah scraping
        Menggunakan SQLAlchemy untuk query agregasi
        """
        try:
            from models_db import Comment, SentimentAnalysis, RegionalStat
            
            # Hitung statistik per provinsi
            stats = self.db.session.query(
                Comment.detected_province,
                func.count(Comment.id).label('total'),
                func.sum(case((SentimentAnalysis.sentiment == 'Positif', 1), else_=0)).label('positive'),
                func.sum(case((SentimentAnalysis.sentiment == 'Negatif', 1), else_=0)).label('negative')
            ).outerjoin(
                SentimentAnalysis, Comment.id == SentimentAnalysis.comment_id
            ).filter(
                Comment.video_id == video_id,
                Comment.detected_province.isnot(None)
            ).group_by(
                Comment.detected_province
            ).all()
            
            # Simpan ke regional_stats
            today = datetime.now().date()
            for stat in stats:
                if stat.detected_province and stat.total > 0:
                    # Cek apakah sudah ada data untuk hari ini
                    existing = self.db.session.query(RegionalStat).filter_by(
                        stat_date=today,
                        province=stat.detected_province
                    ).first()
                    
                    if existing:
                        # Update yang sudah ada
                        existing.total_comments += stat.total
                        existing.positive_count += stat.positive or 0
                        existing.negative_count += stat.negative or 0
                    else:
                        # Buat baru
                        regional = RegionalStat(
                            stat_date=today,
                            province=stat.detected_province,
                            total_comments=stat.total,
                            positive_count=stat.positive or 0,
                            negative_count=stat.negative or 0,
                            latitude=self._get_province_lat(stat.detected_province),
                            longitude=self._get_province_lon(stat.detected_province)
                        )
                        self.db.session.add(regional)
            
            self.db.session.commit()
            print(f"✅ Regional stats updated for {len(stats)} provinces")
            
        except Exception as e:
            print(f"⚠️ Error updating regional stats: {e}")
            self.db.session.rollback()
    
    def _get_province_lat(self, province):
        """Dapatkan latitude provinsi dari database atau default"""
        from regions import INDONESIAN_REGIONS
        for code, prov in INDONESIAN_REGIONS["provinsi"].items():
            if prov["nama"] == province:
                return prov["lat"]
        return -2.5
    
    def _get_province_lon(self, province):
        """Dapatkan longitude provinsi dari database atau default"""
        from regions import INDONESIAN_REGIONS
        for code, prov in INDONESIAN_REGIONS["provinsi"].items():
            if prov["nama"] == province:
                return prov["lon"]
        return 118.0
    
    def _extract_video_id(self, url):
        """Extract video ID dari URL TikTok"""
        import re
        # Format: https://www.tiktok.com/@username/video/1234567890
        match = re.search(r'/video/(\d+)', url)
        if match:
            return match.group(1)
        
        # Format: https://vt.tiktok.com/ZSxxxxx/
        match = re.search(r'tiktok\.com/@[\w\.]+/video/(\d+)', url)
        if match:
            return match.group(1)
        
        # Format angka 19 digit
        match = re.search(r'(\d{19})', url)
        return match.group(1) if match else None
    
    def _extract_username(self, url):
        """Extract username dari URL TikTok"""
        import re
        match = re.search(r'@([\w\.]+)', url)
        return match.group(1) if match else "unknown"
    
    def _clean_text(self, text):
        """Clean text untuk analisis"""
        if not text:
            return ""
        import re
        text = re.sub(r'http\S+', '', text)
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def get_scraping_stats(self):
        """Dapatkan statistik scraping terakhir"""
        return self.stats
    
    def batch_scrape(self, urls, comments_per_url=500, delay_between=60):
        """
        Scrape multiple video sekaligus
        
        Args:
            urls: List URL video
            comments_per_url: Jumlah komentar per video
            delay_between: Delay antar video (detik)
        
        Returns:
            List of video_ids
        """
        import time
        
        results = []
        total_urls = len(urls)
        
        print("\n" + "="*70)
        print(f"🚀 BATCH SCRAPING {total_urls} VIDEOS")
        print("="*70)
        
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{total_urls}] Processing: {url[:60]}...")
            
            try:
                video_id = self.scrape_and_save(url, max_comments=comments_per_url)
                if video_id:
                    results.append(video_id)
                
                if i < total_urls:
                    print(f"\n⏳ Waiting {delay_between} seconds before next video...")
                    time.sleep(delay_between)
                    
            except Exception as e:
                print(f"❌ Error on video {i}: {e}")
                continue
        
        print("\n" + "="*70)
        print(f"✅ BATCH COMPLETE: {len(results)}/{total_urls} videos saved")
        print("="*70)
        
        return results


# ===============================
# STANDALONE FUNCTION
# ===============================
def scrape_and_save_to_db(video_url, max_comments=1000):
    """
    Fungsi standalone untuk scraping dan simpan ke database
    """
    scraper = TikTokScraperWithDB()
    return scraper.scrape_and_save(video_url, max_comments)


def batch_scrape_to_db(urls, comments_per_url=500, delay=60):
    """
    Fungsi standalone untuk batch scraping
    """
    scraper = TikTokScraperWithDB()
    return scraper.batch_scrape(urls, comments_per_url, delay)


# ===============================
# TESTING
# ===============================
if __name__ == "__main__":
    print("\n" + "="*70)
    print("🧪 TESTING TIKTOK SCRAPER WITH DATABASE")
    print("="*70)
    
    # Test single video
    test_url = input("\n📱 Masukkan URL TikTok untuk testing: ").strip()
    
    if test_url:
        try:
            max_cmt = int(input("📊 Jumlah komentar (default 100): ") or "100")
        except:
            max_cmt = 100
        
        scraper = TikTokScraperWithDB()
        result = scraper.scrape_and_save(test_url, max_comments=max_cmt)
        
        if result:
            print(f"\n✅ SUCCESS! Video ID: {result}")
        else:
            print("\n❌ FAILED!")
    
    # Test batch
    test_batch = input("\n📦 Test batch scraping? (y/n): ").lower()
    if test_batch == 'y':
        urls = [
            "https://www.tiktok.com/@helmi_hasan/video/7609639854879608085",
            "https://www.tiktok.com/@helmi_hasan/video/7608157296195112213"
        ]
        results = batch_scrape_to_db(urls, comments_per_url=50, delay=30)
        print(f"\n✅ Batch results: {results}")