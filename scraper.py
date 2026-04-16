# scraper.py
import requests
import re
import time
import random
import sys
from datetime import datetime
import os
from dotenv import load_dotenv

# ===============================
# FUNGSI PRINT DENGAN FLUSH (REALTIME LOG)
# ===============================
def print_flush(*args, **kwargs):
    """Print dengan auto-flush untuk output realtime"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Fallback if unicode fails on Windows console
        clean_args = [str(arg).encode('ascii', 'ignore').decode('ascii') for arg in args]
        print(*clean_args, **kwargs)
    sys.stdout.flush()

# ===============================
# IMPORT UNTUK DATABASE
# ===============================
try:
    from database import DatabaseManager
    from sentiment import analyze_sentiment
    from geo_sentiment import GeoLocationDetector
    DB_AVAILABLE = True
    print_flush("DATABASE MODULES LOADED SUCCESSFULLY")
except ImportError as e:
    print_flush(f"DATABASE MODULES NOT AVAILABLE: {e}")
    DB_AVAILABLE = False
except Exception as e:
    print_flush(f"DATABASE INITIALIZATION ERROR: {e}")
    DB_AVAILABLE = False

load_dotenv()

# HEADERS yang lebih lengkap
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.tiktok.com/",
    "Origin": "https://www.tiktok.com",
    "Sec-Fetch-Site": "same-site",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
}

# ===============================
# COOKIE MANAGEMENT
# ===============================
def load_cookies_from_file(filepath="cookies.txt"):
    """
    Membaca cookie dari file cookies.txt format Netscape
    """
    cookies = {}
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith('#') or not line.strip():
                    continue
                
                parts = line.strip().split('\t')
                if len(parts) >= 7:
                    name = parts[5]
                    value = parts[6]
                    cookies[name] = value
        print_flush(f"✅ Loaded {len(cookies)} cookies from {filepath}")
    except FileNotFoundError:
        print_flush(f"⚠️ File {filepath} tidak ditemukan, menggunakan cookie dari environment")
        cookie_str = os.getenv("COOKIE_STRING", "")
        if cookie_str:
            for item in cookie_str.split('; '):
                if '=' in item:
                    key, value = item.split('=', 1)
                    cookies[key] = value
    except Exception as e:
        print_flush(f"⚠️ Error loading cookies: {e}")
    
    return cookies

# Load cookies saat import
COOKIES = load_cookies_from_file()

def update_cookies(new_cookie_string):
    """
    Update cookies dari string (untuk manual input)
    """
    global COOKIES
    for item in new_cookie_string.split('; '):
        if '=' in item:
            key, value = item.split('=', 1)
            COOKIES[key] = value
    print_flush(f"✅ Cookies updated: {len(COOKIES)} cookies")

def extract_video_id(url):
    """Ekstrak video ID dari URL TikTok"""
    match = re.search(r"/video/(\d+)", url)
    if match:
        return match.group(1)
    
    match = re.search(r"(\d{19})", url)
    return match.group(1) if match else None

def get_comment_replies(comment_id, video_id, max_replies=20):
    """Ambil balasan dari sebuah komentar"""
    replies = []
    reply_cursor = 0
    
    while len(replies) < max_replies:
        reply_url = (
            f"https://www.tiktok.com/api/comment/list/reply/"
            f"?aid=1988&aweme_id={video_id}&comment_id={comment_id}"
            f"&count=20&cursor={reply_cursor}"
        )
        
        try:
            res = requests.get(
                reply_url, 
                headers=HEADERS, 
                cookies=COOKIES,
                timeout=10
            )
            
            if res.status_code != 200:
                break
                
            data = res.json()
            reply_items = data.get("comments", [])
            
            if not reply_items:
                break
                
            for r in reply_items:
                reply_time = r.get("create_time", 0)
                replies.append({
                    "comment": r.get("text", ""),
                    "date": datetime.fromtimestamp(reply_time).strftime("%Y-%m-%d") if reply_time else "Unknown",
                    "likes": r.get("digg_count", 0),
                    "username": r.get("user", {}).get("nickname", "unknown"),
                    "is_reply": True,
                    "parent_id": comment_id
                })
            
            reply_cursor = data.get("cursor", reply_cursor + 20)
            time.sleep(random.uniform(0.5, 1.5))
            
        except Exception as e:
            print_flush(f"⚠️ Error mengambil reply: {e}")
            break
    
    return replies

# ===============================
# FUNGSI UTAMA SCRAPING
# ===============================
def scrape_tiktok_comments(url, max_comments=1000, save_to_db=False):
    """
    Scrape komentar TikTok dengan data profil lengkap
    
    Args:
        url: URL video TikTok
        max_comments: Jumlah maksimal komentar
        save_to_db: Jika True, simpan ke database
    """
    video_id = extract_video_id(url)
    if not video_id:
        print_flush("❌ Video ID tidak ditemukan")
        return []

    print_flush(f"🎯 Video ID: {video_id}")
    print_flush(f"🔑 Menggunakan {len(COOKIES)} cookie untuk akses lebih banyak data...")
    
    # Inisialisasi database jika diperlukan
    db_manager = None
    geo_detector = None
    video_db_id = None
    
    if save_to_db and DB_AVAILABLE:
        db_manager = DatabaseManager()
        geo_detector = GeoLocationDetector()
        
        # Simpan video ke database
        video_data = {
            'video_id': video_id,
            'url': url,
            'platform': 'tiktok',
            'title': f"Video {video_id}",
            'author_username': 'unknown',
            'scraped_date': datetime.now()
        }
        video_db_id = db_manager.save_video(video_data)
        print_flush(f"💾 Video tersimpan dengan ID: {video_db_id}")
    
    comments = []
    cursor = 0
    retry_count = 0
    max_retries = 3
    page = 1
    saved_count = 0
    
    while len(comments) < max_comments:
        
        api_url = (
            f"https://www.tiktok.com/api/comment/list/"
            f"?aid=1988"
            f"&aweme_id={video_id}"
            f"&count=50"
            f"&cursor={cursor}"
        )
        
        try:
            time.sleep(random.uniform(2, 5))
            
            res = requests.get(
                api_url, 
                headers=HEADERS, 
                cookies=COOKIES,
                timeout=15
            )
            
            print_flush(f"📡 Halaman {page} | Status: {res.status_code} | Cursor: {cursor}")
            
            if res.status_code == 403:
                print_flush("❌ Akses ditolak! Cookie mungkin expired.")
                break
                
            if res.status_code == 429:
                print_flush("⏳ Rate limited. Menunggu 30 detik...")
                time.sleep(30)
                continue
                
            if res.status_code != 200:
                print_flush(f"⚠️ Request gagal: {res.status_code}")
                retry_count += 1
                if retry_count > max_retries:
                    break
                time.sleep(5)
                continue
            
            retry_count = 0
            
            try:
                data = res.json()
            except Exception as e:
                print_flush(f"⚠️ Gagal parsing JSON: {e}")
                break
            
            items = data.get("comments", [])
            
            if not items:
                print_flush("⛔ Tidak ada komentar lagi")
                break
            
            print_flush(f"📥 Mendapatkan {len(items)} komentar...")
            
            for c in items:
                create_time = c.get("create_time", 0)
                comment_text = c.get("text", "")
                user_data = c.get("user", {})
                
                # ========== DATA KOMENTAR LENGKAP ==========
                comment_data = {
                    "comment": comment_text,
                    "date": datetime.fromtimestamp(create_time).strftime("%Y-%m-%d") if create_time else "Unknown",
                    "likes": c.get("digg_count", 0),
                    "username": user_data.get("unique_id", user_data.get("nickname", "unknown")),
                    "display_name": user_data.get("nickname", ""),
                    "bio": user_data.get("signature", ""),
                    "is_reply": False,
                    "comment_id": c.get("cid", "")
                }
                comments.append(comment_data)
                
                # ========== SIMPAN KE DATABASE ==========
                if save_to_db and db_manager and video_db_id and geo_detector:
                    try:
                        # Analisis sentimen
                        sentiment, confidence = analyze_sentiment(comment_text, return_confidence=True)
                        
                        # ========== DETEKSI LOKASI DENGAN DATA LENGKAP ==========
                        location = geo_detector.detect_location_comprehensive(
                            username=comment_data['username'],
                            display_name=comment_data['display_name'],
                            bio=comment_data['bio'],
                            comment_text=comment_text
                        )
                        
                        # Data untuk database
                        db_comment_data = {
                            'video_id': video_db_id,
                            'comment_id': comment_data['comment_id'] or str(hash(comment_text))[:20],
                            'raw_text': comment_text,
                            'clean_text': comment_text.lower(),
                            'username': comment_data['username'],
                            'display_name': comment_data['display_name'],
                            'bio': comment_data['bio'],
                            'like_count': comment_data['likes'],
                            'comment_date': datetime.fromtimestamp(create_time) if create_time else datetime.now(),
                            'sentiment': sentiment,
                            'sentiment_score': confidence,
                            'province': location['province'],
                            'city': location['city'],
                            'island': location['island'],
                            'location_confidence': location['confidence'],
                            'detection_method': location['detection_method'],
                            'source': location['source']
                        }
                        
                        db_manager.save_comment(db_comment_data)
                        saved_count += 1
                        
                        # Progress setiap komentar untuk realtime
                        print_flush(f"  💾 [{saved_count}/{len(comments)}] {sentiment} - {comment_text[:50]}...")
                            
                    except Exception as e:
                        print_flush(f"⚠️ Gagal simpan ke DB: {e}")
                
                # Ambil balasan
                reply_count = c.get("reply_comment_total", 0)
                if reply_count > 0 and len(comments) < max_comments:
                    comment_id = c.get("cid", "")
                    if comment_id:
                        replies = get_comment_replies(comment_id, video_id, max_replies=5)
                        comments.extend(replies)
                        print_flush(f"  ↳ +{len(replies)} balasan")
            
            cursor = data.get("cursor", cursor + 50)
            has_more = data.get("has_more", False)
            page += 1
            
            print_flush(f"📊 Total terkumpul: {len(comments)} / {max_comments}")
            if save_to_db:
                print_flush(f"💾 Tersimpan di DB: {saved_count}")
            
            if not has_more:
                print_flush("🏁 Server menandakan tidak ada lagi komentar")
                break
            
            if len(comments) >= max_comments:
                break
            
        except requests.exceptions.RequestException as e:
            print_flush(f"⚠️ Error koneksi: {e}")
            time.sleep(10)
            continue
    
    print_flush(f"✅ Berhasil mengambil {len(comments)} komentar!")
    if save_to_db:
        print_flush(f"✅ {saved_count} komentar tersimpan di database")
    
    return comments[:max_comments]

# ===============================
# FUNGSI SCRAPE DAN SIMPAN KE DB
# ===============================
def scrape_and_save_to_db(video_url, max_comments=1000):
    """
    Scrape TikTok dan langsung simpan ke database
    """
    return scrape_tiktok_comments(video_url, max_comments, save_to_db=True)

# ===============================
# FUNGSI SCRAPING YOUTUBE
# ===============================
def _extract_youtube_id(url_or_id: str) -> str:
    """Extract YouTube video ID"""
    if "v=" in url_or_id:
        parts = url_or_id.split('v=')
        vid = parts[1].split('&')[0]
        return vid
    if "youtu.be/" in url_or_id:
        return url_or_id.split('youtu.be/')[1].split('?')[0]
    if "/shorts/" in url_or_id:
        return url_or_id.split('/shorts/')[1].split('?')[0]
    return url_or_id

def get_youtube_video_stats(video_id: str):
    """Get YouTube video statistics"""
    stats = {
        'platform': 'youtube',
        'video_title': None,
        'video_description': None,
        'video_author': None,
        'video_likes': None,
        'video_views': None,
        'video_shares': None,
        'video_saves': None,
        'video_comments_count': None,
        'video_publish_date': None,
        'video_thumbnail': None
    }
    
    try:
        import yt_dlp
        ydl_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': False, 'skip_download': True}
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            stats['video_title'] = info.get('title', '')
            stats['video_description'] = info.get('description', '')[:2000]
            stats['video_author'] = info.get('uploader', '')
            stats['video_likes'] = info.get('like_count')
            stats['video_views'] = info.get('view_count')
            stats['video_comments_count'] = info.get('comment_count')
            stats['video_thumbnail'] = info.get('thumbnail', '')
            
            upload_date = info.get('upload_date')
            if upload_date:
                stats['video_publish_date'] = datetime.strptime(upload_date, '%Y%m%d')
    except Exception as e:
        print_flush(f"⚠️ Error getting YouTube stats: {e}")
    
    return stats

def run_youtube_scraper(video: str, sentiment: bool, threshold: float, limit: int, lang: str):
    """Scrape YouTube comments"""
    video_id = _extract_youtube_id(video)
    print_flush(f"🎯 YouTube Video ID: {video_id}")
    
    video_stats = get_youtube_video_stats(video_id)
    comments = []
    
    try:
        from youtube_comment_downloader import YoutubeCommentDownloader
        downloader = YoutubeCommentDownloader()
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        count = 0
        for comment in downloader.get_comments_from_url(url):
            text = None
            if isinstance(comment, dict):
                for key in ('text', 'textDisplay', 'comment'):
                    if key in comment and comment[key]:
                        text = comment[key]
                        break
            if not text:
                text = str(comment)
            
            comments.append({'text': text})
            count += 1
            if limit > 0 and count >= limit:
                break
    except Exception as e:
        print_flush(f"⚠️ YouTube comment downloader failed: {e}")
    
    data = []
    for c in comments:
        raw = c.get('text') if isinstance(c, dict) else str(c)
        data.append({
            'text': raw,
            'clean_text': raw,
            'sentiment': None,
            'sentiment_score': None
        })
    
    return data, video_stats

# ===============================
# TESTING LANGSUNG
# ===============================
if __name__ == "__main__":
    import pandas as pd
    
    print_flush("="*60)
    print_flush("🕷️  TIKTOK SCRAPER DENGAN DATABASE")
    print_flush("="*60)
    
    test_url = input("\n📱 Masukkan URL TikTok: ").strip()
    
    try:
        max_komentar = int(input("📊 Maksimal komentar (default 500): ") or "500")
    except:
        max_komentar = 500
    
    save_db = input("💾 Simpan ke database? (y/n, default y): ").lower() or "y"
    save_db = save_db == 'y'
    
    print_flush("\n" + "="*60)
    hasil = scrape_tiktok_comments(test_url, max_comments=max_komentar, save_to_db=save_db)
    
    print_flush(f"\n📊 STATISTIK:")
    print_flush(f"Total komentar: {len(hasil)}")
    
    if save_db:
        print_flush("✅ Data tersimpan di database")
    
    print_flush(f"\n📝 Contoh 5 komentar pertama:")
    for i, c in enumerate(hasil[:5]):
        print_flush(f"{i+1}. {c.get('username', 'unknown')}: {c['comment'][:50]}... (❤️ {c.get('likes', 0)})")