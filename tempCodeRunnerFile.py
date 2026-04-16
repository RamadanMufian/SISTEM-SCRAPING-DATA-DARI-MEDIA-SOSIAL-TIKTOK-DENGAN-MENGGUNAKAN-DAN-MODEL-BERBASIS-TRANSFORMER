from flask import Flask, render_template, request, jsonify, session
from scraper import scrape_tiktok_comments
from sentiment import analyze_sentiment, analyze_batch
from collections import Counter
import pandas as pd
import re
import json
import os
import time
from datetime import timedelta, datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from viral_analyzer import ViralAnalyzer
from database_config import DatabaseManager
from geo_sentiment import GeoLocationDetector
from scraper import scrape_and_save_to_db
from bengkulu_geodata import BengkuluHeatmapGenerator
from geo_sentiment import GeoLocationDetector
from database import DatabaseManager
from models_db import Comment, SentimentAnalysis

# Inisialisasi database manager dan geo detector
db_manager = DatabaseManager()
geo_detector = GeoLocationDetector()

# Cek ketersediaan models_db
try:
    from models_db import Comment, SentimentAnalysis, Video
    MODELS_AVAILABLE = True
    print("✅ Models_db tersedia")
except ImportError:
    print("⚠️ Module models_db tidak ditemukan, beberapa fitur database tidak akan berfungsi")
    MODELS_AVAILABLE = False

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-this'
app.permanent_session_lifetime = timedelta(days=1)

# =========================
# PREPROCESSING FUNCTION
# =========================
def preprocess_text(text):
    """Bersihkan teks untuk analisis"""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\d+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# =========================
# SENTIMENT DISTRIBUTION
# =========================
def get_sentiment_distribution(df):
    """Hitung distribusi sentimen"""
    total = len(df)
    if total == 0:
        return {"Positif": 0, "Negatif": 0, "Netral": 0}
    
    sentiment_counts = df["sentiment"].value_counts()
    return {
        "Positif": int(sentiment_counts.get("Positif", 0)),
        "Negatif": int(sentiment_counts.get("Negatif", 0)),
        "Netral": int(sentiment_counts.get("Netral", 0))
    }

# =========================
# TREND ANALYSIS
# =========================
def analyze_trends(df):
    """Analisis trend berdasarkan tanggal"""
    if df.empty or "date" not in df.columns:
        return {
            "labels": [],
            "positif": [],
            "negatif": [],
            "netral": []
        }
    
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    
    if df.empty:
        return {
            "labels": [],
            "positif": [],
            "negatif": [],
            "netral": []
        }
    
    df["date_only"] = df["date"].dt.date
    
    # Sentimen per hari
    trend_sentiment = (
        df.groupby(["date_only", "sentiment"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    
    # Pastikan semua kolom ada
    for col in ["Positif", "Negatif", "Netral"]:
        if col not in trend_sentiment.columns:
            trend_sentiment[col] = 0
    
    # Urutkan berdasarkan tanggal
    trend_sentiment = trend_sentiment.sort_values("date_only")
    
    return {
        "labels": trend_sentiment["date_only"].astype(str).tolist(),
        "positif": trend_sentiment["Positif"].tolist(),
        "negatif": trend_sentiment["Negatif"].tolist(),
        "netral": trend_sentiment["Netral"].tolist(),
    }

# =========================
# WORD CLOUD DATA
# =========================
def get_top_words(df, n=30):
    """Ambil kata-kata paling sering muncul"""
    if df.empty or "clean_text" not in df.columns:
        return []
    
    all_words = " ".join(df["clean_text"].fillna("")).split()
    if not all_words:
        return []
    
    word_freq = Counter(all_words)
    
    # Filter stop words sederhana
    stop_words = {'yang', 'dan', 'di', 'ini', 'itu', 'dengan', 'untuk', 'tidak', 
                  'akan', 'pada', 'karena', 'juga', 'ke', 'saya', 'dia', 'mereka', 
                  'kita', 'kami', 'yah', 'ya', 'eh', 'oh', 'ah', 'dong', 'sih',
                  'kok', 'loh', 'deh', 'tau', 'aja', 'doang', 'yg', 'udah', 'sudah',
                  'bisa', 'ada', 'aku', 'kamu', 'orang', 'video', 'tiktok', 'pak',
                  'bapak', 'bpk'}
    
    filtered_words = [(word, count) for word, count in word_freq.most_common(100) 
                     if word not in stop_words and len(word) > 2]
    
    return filtered_words[:n]

# =========================
# PARALLEL SENTIMENT ANALYSIS
# =========================
def analyze_sentiments_parallel(comments, max_workers=3):
    """Analisis sentimen secara paralel untuk kecepatan"""
    data = []
    
    if not comments:
        return data
    
    # Siapkan teks untuk analisis
    texts = [c.get("comment", "") for c in comments]
    
    # Analisis dalam batch
    start_time = time.time()
    processed = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit semua tugas
        future_to_comment = {
            executor.submit(analyze_sentiment, text, True): (i, comment) 
            for i, (text, comment) in enumerate(zip(texts, comments))
        }
        
        # Kumpulkan hasil
        for future in as_completed(future_to_comment):
            i, comment = future_to_comment[future]
            try:
                result = future.result(timeout=5)
                
                if isinstance(result, tuple) and len(result) == 2:
                    sentiment, confidence = result
                else:
                    sentiment = result
                    confidence = 50.0
                
                # Bersihkan teks untuk word cloud
                clean_text = preprocess_text(comment.get("comment", ""))
                
                # Deteksi lokasi komprehensif
                location = geo_detector.detect_location_comprehensive(
                    username=comment.get("username", ""),
                    display_name=comment.get("display_name", ""),
                    bio=comment.get("bio", ""),
                    comment_text=comment.get("comment", "")
                )
                
                data.append({
                    "comment": comment.get("comment", ""),
                    "clean_text": clean_text,
                    "sentiment": sentiment,
                    "confidence": confidence,
                    "date": comment.get("date", "Unknown"),
                    "username": comment.get("username", "unknown"),
                    "display_name": comment.get("display_name", ""),
                    "bio": comment.get("bio", ""),
                    "likes": comment.get("likes", 0),
                    "province": location.get('province'),
                    "city": location.get('city'),
                    "island": location.get('island'),
                    "location_confidence": location.get('confidence', 0),
                    "detection_method": location.get('detection_method'),
                    "detection_source": location.get('source')
                })
                
                processed += 1
                if processed % 50 == 0:
                    print(f"  Progress analisis: {processed}/{len(comments)}")
                    
            except Exception as e:
                print(f"Error analyzing comment {i}: {e}")
                # Fallback
                data.append({
                    "comment": comment.get("comment", ""),
                    "clean_text": preprocess_text(comment.get("comment", "")),
                    "sentiment": "Netral",
                    "confidence": 0,
                    "date": comment.get("date", "Unknown"),
                    "username": comment.get("username", "unknown"),
                    "display_name": comment.get("display_name", ""),
                    "bio": comment.get("bio", ""),
                    "likes": comment.get("likes", 0),
                    "province": None,
                    "city": None,
                    "island": None,
                    "location_confidence": 0,
                    "detection_method": None,
                    "detection_source": None
                })
    
    elapsed = time.time() - start_time
    print(f"✅ Analisis {len(comments)} komentar selesai dalam {elapsed:.2f} detik")
    
    return data

# =========================
# MAIN PIPELINE - DENGAN PENYIMPANAN KE DATABASE
# =========================
def run_full_pipeline(link, max_comments=1000, save_to_db=True):
    """
    Jalankan pipeline lengkap dengan model hybrid RoBERTa + Rule-based
    dan SIMPAN KE DATABASE
    """
    print(f"🚀 Memulai pipeline untuk: {link}")
    print(f"📊 Target komentar: {max_comments}")
    print(f"💾 Simpan ke database: {save_to_db}")
    
    # 1️⃣ SCRAPING
    start_scrape = time.time()
    comments = scrape_tiktok_comments(link, max_comments=max_comments)
    scrape_time = time.time() - start_scrape
    
    if not comments:
        print("❌ Tidak ada komentar ditemukan")
        return None
    
    print(f"✅ Scraping selesai: {len(comments)} komentar dalam {scrape_time:.2f} detik")
    
    # 2️⃣ SIMPAN VIDEO KE DATABASE (jika diaktifkan)
    video_db_id = None
    if save_to_db and MODELS_AVAILABLE:
        try:
            # Extract video ID dari URL
            import re
            video_id_match = re.search(r'/video/(\d+)', link)
            video_id = video_id_match.group(1) if video_id_match else f"video_{int(time.time())}"
            
            # Data video
            video_data = {
                'video_id': video_id,
                'url': link,
                'platform': 'tiktok',
                'title': f"Video {video_id}",
                'author_username': 'unknown',
                'views_count': 0,
                'likes_count': 0,
                'comments_count': len(comments),
                'scraped_date': datetime.now()
            }
            
            video_db_id = db_manager.save_video(video_data)
            print(f"💾 Video tersimpan dengan ID: {video_db_id}")
        except Exception as e:
            print(f"⚠️ Gagal simpan video: {e}")
    
    # 3️⃣ SENTIMENT ANALYSIS (PARALLEL)
    start_sentiment = time.time()
    data = analyze_sentiments_parallel(comments)
    sentiment_time = time.time() - start_sentiment
    
    if not data:
        print("❌ Tidak ada data sentimen")
        return None
    
    df = pd.DataFrame(data)
    
    # 4️⃣ SIMPAN KOMENTAR KE DATABASE
    saved_count = 0
    if save_to_db and video_db_id and MODELS_AVAILABLE:
        for i, comment_data in enumerate(data):
            try:
                db_comment_data = {
                    'video_id': video_db_id,
                    'comment_id': f"cmt_{int(time.time())}_{i}",
                    'raw_text': comment_data['comment'],
                    'clean_text': comment_data['clean_text'],
                    'username': comment_data['username'],
                    'display_name': comment_data.get('display_name', ''),
                    'bio': comment_data.get('bio', ''),
                    'like_count': comment_data['likes'],
                    'comment_date': datetime.now(),
                    'sentiment': comment_data['sentiment'],
                    'sentiment_score': comment_data['confidence'],
                    'province': comment_data.get('province'),
                    'city': comment_data.get('city'),
                    'island': comment_data.get('island'),
                    'location_confidence': comment_data.get('location_confidence', 0),
                    'detection_method': comment_data.get('detection_method'),
                    'detection_source': comment_data.get('detection_source')
                }
                db_manager.save_comment(db_comment_data)
                saved_count += 1
                
                if (i + 1) % 50 == 0:
                    print(f"  💾 Tersimpan: {i+1}/{len(data)} komentar")
                    
            except Exception as e:
                print(f"⚠️ Gagal simpan komentar {i}: {e}")
        
        print(f"✅ {saved_count} komentar tersimpan di database")
    
    # 5️⃣ ANALISIS
    sentiment_dist = get_sentiment_distribution(df)
    total = len(df)
    
    # Persentase untuk summary
    summary = {
        "Positif": round((sentiment_dist["Positif"] / total * 100), 1) if total > 0 else 0,
        "Negatif": round((sentiment_dist["Negatif"] / total * 100), 1) if total > 0 else 0,
        "Netral": round((sentiment_dist["Netral"] / total * 100), 1) if total > 0 else 0,
    }
    
    # 6️⃣ TREND
    trend_chart = analyze_trends(df)
    
    # 7️⃣ TOP WORDS
    top_words = get_top_words(df)
    
    # 8️⃣ STATISTIK TAMBAHAN
    stats = {
        "total_likes": int(df["likes"].sum()) if "likes" in df.columns else 0,
        "avg_likes": round(df["likes"].mean(), 1) if total > 0 and "likes" in df.columns else 0,
        "unique_users": int(df["username"].nunique()) if "username" in df.columns else 0,
        "avg_confidence": round(df["confidence"].mean(), 1) if total > 0 and "confidence" in df.columns else 0,
        "locations_detected": int(df["province"].notna().sum()) if "province" in df.columns else 0,
        "detection_rate": round(df["province"].notna().sum() / total * 100, 1) if total > 0 and "province" in df.columns else 0,
        "processing_time": {
            "scraping": round(scrape_time, 2),
            "sentiment": round(sentiment_time, 2),
            "total": round(scrape_time + sentiment_time, 2)
        },
        "saved_to_db": saved_count
    }
    
    print(f"✅ Pipeline selesai. Total: {total} komentar")
    print(f"📊 Stats: {stats}")
    
    # 9️⃣ HIGHLIGHT KOMENTAR
    highlights = {}
    for sentiment in ["Positif", "Negatif", "Netral"]:
        sentiment_df = df[df["sentiment"] == sentiment]
        if not sentiment_df.empty:
            top = sentiment_df.nlargest(3, "confidence")[["comment", "username", "confidence"]].to_dict("records")
            highlights[sentiment] = top
        else:
            highlights[sentiment] = []
    
    return {
        "results": data,
        "sentiment_dist": sentiment_dist,
        "summary": summary,
        "trend_chart": trend_chart,
        "top_words": top_words,
        "total": total,
        "stats": stats,
        "highlights": highlights,
        "video_db_id": video_db_id,
        "saved_to_db": saved_count
    }

# =========================
# ROUTES
# =========================
@app.route("/", methods=["GET", "POST"])
def index():
    """Halaman utama dengan dukungan max_comments dari form"""
    
    # Ambil total komentar di database untuk ditampilkan
    total_comments_in_db = 0
    if MODELS_AVAILABLE:
        try:
            from models_db import Comment
            total_comments_in_db = db_manager.session.query(Comment).count()
        except Exception as e:
            print(f"⚠️ Gagal ambil total komentar: {e}")
    
    if request.method == "POST":
        link = request.form.get("link", "").strip()
        
        # AMBIL NILAI MAX_COMMENTS DARI FORM, DEFAULT 1000
        try:
            max_comments = int(request.form.get("max_comments", 1000))
            # Batasi antara 100 - 5000
            max_comments = max(100, min(5000, max_comments))
        except ValueError:
            max_comments = 1000
        
        if not link:
            return render_template("index.html", error="Masukkan URL TikTok", total_comments_in_db=total_comments_in_db)
        
        try:
            print(f"🔍 Menganalisis: {link}")
            print(f"🎯 Target komentar: {max_comments}")
            
            # Jalankan pipeline DENGAN SAVE TO DB = TRUE
            result = run_full_pipeline(link, max_comments=max_comments, save_to_db=True)
            
            if result:
                print(f"✅ Render template dengan {len(result['results'])} komentar")
                print(f"💾 Tersimpan di DB: {result.get('saved_to_db', 0)} komentar")
                
                return render_template(
                    "index.html",
                    results=result["results"],
                    sentiment_dist=result["sentiment_dist"],
                    summary=result["summary"],
                    trend_chart=result["trend_chart"],
                    top_words=result["top_words"],
                    total=result["total"],
                    stats=result["stats"],
                    highlights=result["highlights"],
                    max_comments=max_comments,
                    saved_to_db=result.get("saved_to_db", 0),
                    total_comments_in_db=total_comments_in_db + result.get("saved_to_db", 0),
                    success=True
                )
            else:
                print("❌ Result None")
                return render_template("index.html", error="Gagal mengambil komentar", total_comments_in_db=total_comments_in_db)
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return render_template("index.html", error=f"Terjadi kesalahan: {str(e)}", total_comments_in_db=total_comments_in_db)
    
    return render_template("index.html", total_comments_in_db=total_comments_in_db)

# app.py - Tambahkan di bagian routes

# Import generator Bengkulu
from bengkulu_geodata import BengkuluHeatmapGenerator
from database import DatabaseManager
from models_db import Comment, SentimentAnalysis
import pandas as pd

@app.route("/bengkulu-heatmap")
def bengkulu_heatmap():
    """Halaman heatmap khusus Provinsi Bengkulu"""
    print("="*60)
    print("🗺️  BENGKULU HEATMAP")
    print("="*60)
    
    generator = BengkuluHeatmapGenerator()
    db = DatabaseManager()
    
    # Ambil komentar yang terdeteksi di Bengkulu
    comments = db.session.query(Comment).filter(
        Comment.detected_province == 'BENGKULU'
    ).all()
    
    print(f"📊 Total komentar Bengkulu: {len(comments)}")
    
    # ========== DETEKSI SENTIMEN PER KABUPATEN ==========
    # Inisialisasi data sentimen per kabupaten
    sentiment_by_region = {}
    for region in generator.get_all_regions():
        sentiment_by_region[region["nama"]] = {
            "positive": 0,
            "negative": 0,
            "neutral": 0,
            "total": 0,
            "positive_pct": 0
        }
    
    # Keyword mapping untuk deteksi kabupaten
    region_keywords = {
        "BENGKULU": ["bengkulu", "kota bengkulu", "bkl"],
        "BENGKULU SELATAN": ["bengkulu selatan", "manna", "bengsel"],
        "BENGKULU UTARA": ["bengkulu utara", "argamakmur", "bengkulutara"],
        "BENGKULU TENGAH": ["bengkulu tengah", "karang tinggi"],
        "REJANG LEBONG": ["rejang lebong", "curup", "rejang"],
        "KAUR": ["kaur", "bintuhan"],
        "SELUMA": ["seluma", "tais"],
        "MUKOMUKO": ["mukomuko", "muko muko"],
        "LEBONG": ["lebong", "muara aman"],
        "KEPAHIANG": ["kepahiang"]
    }
    
    # Proses setiap komentar
    for comment in comments:
        # Ambil sentimen
        sentiment = "Netral"
        if comment.sentiment:
            sentiment = comment.sentiment.sentiment
        
        # Deteksi region dari teks komentar
        text = (comment.raw_text or "").lower()
        detected_region = None
        
        for region, keywords in region_keywords.items():
            for kw in keywords:
                if kw in text:
                    detected_region = region
                    break
            if detected_region:
                break
        
        if detected_region and detected_region in sentiment_by_region:
            if sentiment == "Positif":
                sentiment_by_region[detected_region]["positive"] += 1
            elif sentiment == "Negatif":
                sentiment_by_region[detected_region]["negative"] += 1
            else:
                sentiment_by_region[detected_region]["neutral"] += 1
            sentiment_by_region[detected_region]["total"] += 1
    
    # Hitung persentase per region
    for region in sentiment_by_region:
        total = sentiment_by_region[region]["total"]
        if total > 0:
            sentiment_by_region[region]["positive_pct"] = round(
                sentiment_by_region[region]["positive"] / total * 100, 1
            )
    
    # Generate heatmap data
    heatmap_data = generator.generate_heatmap_data(sentiment_by_region)
    stats = generator.get_statistics_summary(heatmap_data)
    
    # Hitung total sentimen nasional untuk pie chart
    total_positive = sum(s["positive"] for s in sentiment_by_region.values())
    total_negative = sum(s["negative"] for s in sentiment_by_region.values())
    total_neutral = sum(s["neutral"] for s in sentiment_by_region.values())
    
    print(f"✅ Heatmap generated: {len(heatmap_data)} regions")
    print(f"   Positif: {total_positive}, Negatif: {total_negative}, Netral: {total_neutral}")
    
    return render_template(
        "bengkulu_heatmap.html",
        heatmap_data=heatmap_data,
        stats=stats,
        total_comments=len(comments),
        national_sentiment={
            "positive": total_positive,
            "negative": total_negative,
            "neutral": total_neutral
        }
    )
    
    return render_template(
        "bengkulu_heatmap.html",
        heatmap_data=heatmap_data,
        stats=stats,
        total_comments=total_comments,
        national_sentiment=national_sentiment
    )
    
@app.route("/scrape-to-db", methods=["GET", "POST"])
def scrape_to_db():
    """Halaman scraping langsung ke database"""
    
    # Ambil total komentar di database
    total_comments_in_db = 0
    if MODELS_AVAILABLE:
        try:
            from models_db import Comment
            total_comments_in_db = db_manager.session.query(Comment).count()
        except Exception as e:
            print(f"⚠️ Gagal ambil total komentar: {e}")
    
    if request.method == "POST":
        video_url = request.form.get("link", "").strip()
        max_comments = int(request.form.get("max_comments", 500))
        
        if not video_url:
            return render_template("scrape_to_db.html", error="URL tidak boleh kosong", total_comments_in_db=total_comments_in_db)
        
        try:
            # Gunakan pipeline yang sama dengan save_to_db=True
            result = run_full_pipeline(video_url, max_comments=max_comments, save_to_db=True)
            
            if result:
                return render_template("scrape_to_db.html", 
                                      success=True, 
                                      video_id=result.get('video_db_id'),
                                      total=result.get('saved_to_db', 0),
                                      total_comments_in_db=total_comments_in_db + result.get('saved_to_db', 0))
            else:
                return render_template("scrape_to_db.html", error="Gagal scraping", total_comments_in_db=total_comments_in_db)
                
        except Exception as e:
            return render_template("scrape_to_db.html", error=str(e), total_comments_in_db=total_comments_in_db)
    
    return render_template("scrape_to_db.html", total_comments_in_db=total_comments_in_db)

@app.route("/sentiment-heatmap")
def sentiment_heatmap():
    """Halaman heatmap sentimen Indonesia - TANPA DUMMY"""
    from geo_sentiment import GeoLocationDetector
    from heatmap_generator import HeatmapGenerator
    import pandas as pd
    from datetime import datetime
    
    detector = GeoLocationDetector()
    generator = HeatmapGenerator()
    
    if not MODELS_AVAILABLE:
        print("[WARN] Models tidak tersedia")
        return render_template(
            "sentiment_heatmap.html",
            total_comments=0,
            active_regions=0,
            national_stats={"positive_pct": 0, "negative_pct": 0},
            heatmap_data=[],
            trend_data=[],
            island_comparison=[],
            top_provinces=[],
            bottom_provinces=[],
            provinces_detail=[],
            summary={},
            data_source="Database Tidak Terhubung"
        )
    
    try:
        from models_db import Comment, SentimentAnalysis
        
        # Ambil SEMUA komentar
        comments = db_manager.session.query(Comment).all()
        
        print(f"[DB] Total komentar di database: {len(comments)}")
        
        if not comments or len(comments) == 0:
            print("[INFO] Database kosong")
            return render_template(
                "sentiment_heatmap.html",
                total_comments=0,
                active_regions=0,
                national_stats={"positive_pct": 0, "negative_pct": 0},
                heatmap_data=[],
                trend_data=[],
                island_comparison=[],
                top_provinces=[],
                bottom_provinces=[],
                provinces_detail=[],
                summary={},
                data_source="Database Kosong"
            )
        
        # Konversi ke dataframe
        data_list = []
        for c in comments:
            sentiment = "Netral"
            if hasattr(c, 'sentiment') and c.sentiment:
                sentiment = c.sentiment.sentiment
            
            data_list.append({
                'comment': c.raw_text or '',
                'username': c.username or '',
                'sentiment': sentiment,
                'date': c.comment_date or datetime.now(),
                'province': c.detected_province,
                'city': c.detected_city,
                'island': c.detected_island,
                'detection_method': getattr(c, 'detection_method', None),
                'detection_source': getattr(c, 'detection_source', None),
                'location_confidence': getattr(c, 'location_confidence', 0)
            })
        
        df = pd.DataFrame(data_list)
        
        # Hitung statistik awal
        total_comments = len(df)
        detected_initial = df['province'].notna().sum()
        detection_rate_initial = (detected_initial / total_comments * 100) if total_comments > 0 else 0
        
        print(f"[DATA] Dataframe: {total_comments} baris")
        print(f"[LOC] Provinsi terdeteksi awal: {detected_initial} ({detection_rate_initial:.1f}%)")
        
        # Deteksi ulang untuk yang belum punya provinsi
        if detected_initial < total_comments * 0.1:
            print("[INFO] Mendeteksi ulang lokasi...")
            
            undetected_mask = df['province'].isna()
            undetected_df = df[undetected_mask].copy()
            
            if not undetected_df.empty:
                print(f"   - {len(undetected_df)} komentar akan dideteksi ulang")
                
                try:
                    detected_df = detector.batch_detect(
                        undetected_df,
                        username_col='username',
                        display_name_col='display_name' if 'display_name' in df.columns else None,
                        bio_col='bio' if 'bio' in df.columns else None,
                        text_col='comment'
                    )
                    
                    # ========== PERBAIKAN: UPDATE DENGAN AMAN ==========
                    # Pastikan index yang akan diupdate sama
                    undetected_indices = df[undetected_mask].index
                    detected_indices = detected_df.index
                    
                    if len(undetected_indices) == len(detected_indices):
                        # Update dengan values
                        df.loc[undetected_indices, 'province'] = detected_df['province'].values
                        df.loc[undetected_indices, 'city'] = detected_df['city'].values
                        df.loc[undetected_indices, 'island'] = detected_df['island'].values
                        
                        if 'confidence' in detected_df.columns:
                            df.loc[undetected_indices, 'location_confidence'] = detected_df['confidence'].values
                        if 'detection_method' in detected_df.columns:
                            df.loc[undetected_indices, 'detection_method'] = detected_df['detection_method'].values
                        if 'source' in detected_df.columns:
                            df.loc[undetected_indices, 'detection_source'] = detected_df['source'].values
                    else:
                        print(f"[WARN] Size mismatch, using manual update")
                        # Update manual per baris
                        for i, idx in enumerate(undetected_indices):
                            if i < len(detected_df):
                                df.at[idx, 'province'] = detected_df.iloc[i]['province']
                                df.at[idx, 'city'] = detected_df.iloc[i]['city']
                                df.at[idx, 'island'] = detected_df.iloc[i]['island']
                                if 'confidence' in detected_df.columns:
                                    df.at[idx, 'location_confidence'] = detected_df.iloc[i]['confidence']
                                if 'detection_method' in detected_df.columns:
                                    df.at[idx, 'detection_method'] = detected_df.iloc[i]['detection_method']
                                if 'source' in detected_df.columns:
                                    df.at[idx, 'detection_source'] = detected_df.iloc[i]['source']
                    
                    detected_final = df['province'].notna().sum()
                    print(f"[OK] Setelah deteksi ulang: {detected_final} provinsi terdeteksi ({detected_final/total_comments*100:.1f}%)")
                    
                except Exception as e:
                    print(f"[ERR] Error saat deteksi ulang: {e}")
                    import traceback
                    traceback.print_exc()
        
        # Isi nilai kosong
        df['province'] = df['province'].fillna('Tidak Diketahui')
        df['island'] = df['island'].fillna('Lainnya')
        df['city'] = df['city'].fillna('')
        df['sentiment'] = df['sentiment'].fillna('Netral')
        
        # Hitung statistik regional
        df_with_province = df[df['province'] != 'Tidak Diketahui'].copy()
        
        if len(df_with_province) == 0:
            print("[WARN] Tidak ada data dengan provinsi")
            return render_template(
                "sentiment_heatmap.html",
                total_comments=total_comments,
                active_regions=0,
                national_stats={"positive_pct": 0, "negative_pct": 0},
                heatmap_data=[],
                trend_data=[],
                island_comparison=[],
                top_provinces=[],
                bottom_provinces=[],
                provinces_detail=[],
                summary={"Positif": 0, "Negatif": 0, "Netral": 0},
                data_source=f"{total_comments} komentar (0 dengan lokasi)"
            )
        
        # Hitung statistik regional
        regional_stats = detector.get_regional_stats(df_with_province)
        
        # Generate data untuk visualisasi
        heatmap_data = generator.generate_heatmap_data(regional_stats)
        trend_data = generator.generate_trend_data(df)
        comparison = generator.generate_comparison_data(regional_stats, min_comments=1)
        provinces_detail = generator.generate_provinces_detail(regional_stats)
        
        # Statistik nasional
        national = regional_stats["national"]
        total = national["total_comments"]
        positive = national["positive"]
        negative = national["negative"]
        neutral = national["neutral"]
        
        positive_pct = (positive / total * 100) if total > 0 else 0
        negative_pct = (negative / total * 100) if total > 0 else 0
        neutral_pct = (neutral / total * 100) if total > 0 else 0
        
        summary = {
            "Positif": round(positive_pct, 1),
            "Negatif": round(negative_pct, 1),
            "Netral": round(neutral_pct, 1)
        }
        
        print(f"[OK] FINAL: {len(provinces_detail)} provinsi ditampilkan")
        print(f"[OK] Total komentar dengan provinsi: {total}")
        print(f"[OK] Positif: {summary['Positif']}%, Negatif: {summary['Negatif']}%, Netral: {summary['Netral']}%")
        
        return render_template(
            "sentiment_heatmap.html",
            total_comments=total,
            active_regions=len(regional_stats["by_province"]),
            national_stats={
                "positive": positive,
                "negative": negative,
                "neutral": neutral,
                "positive_pct": positive_pct,
                "negative_pct": negative_pct
            },
            heatmap_data=heatmap_data,
            trend_data=trend_data,
            island_comparison=comparison["island_comparison"],
            top_provinces=comparison["top_provinces"],
            bottom_provinces=comparison["bottom_provinces"],
            provinces_detail=provinces_detail,
            summary=summary,
            data_source=f"{total} komentar dari {len(provinces_detail)} provinsi"
        )
        
    except Exception as e:
        print(f"[ERR] Error di heatmap: {e}")
        import traceback
        traceback.print_exc()
        
        return render_template(
            "sentiment_heatmap.html",
            total_comments=0,
            active_regions=0,
            national_stats={"positive_pct": 0, "negative_pct": 0},
            heatmap_data=[],
            trend_data=[],
            island_comparison=[],
            top_provinces=[],
            bottom_provinces=[],
            provinces_detail=[],
            summary={},
            data_source=f"Error: {str(e)[:50]}"
        )
        
        # Konversi ke dataframe
        data_list = []
        for c in comments:
            # Ambil sentimen
            sentiment = "Netral"
            if hasattr(c, 'sentiment') and c.sentiment:
                sentiment = c.sentiment.sentiment
            
            data_list.append({
                'comment': c.raw_text or '',
                'username': c.username or '',
                'sentiment': sentiment,
                'date': c.comment_date or datetime.now(),
                'province': c.detected_province,
                'city': c.detected_city,
                'island': c.detected_island,
                'detection_method': getattr(c, 'detection_method', None),
                'detection_source': getattr(c, 'detection_source', None),
                'location_confidence': getattr(c, 'location_confidence', 0)
            })
        
        df = pd.DataFrame(data_list)
        
        # Hitung statistik awal
        total_comments = len(df)
        detected_initial = df['province'].notna().sum()
        detection_rate_initial = (detected_initial / total_comments * 100) if total_comments > 0 else 0
        
        print(f"📊 Dataframe: {total_comments} baris")
        print(f"📍 Provinsi terdeteksi awal: {detected_initial} ({detection_rate_initial:.1f}%)")
        
        # Deteksi ulang untuk yang belum punya provinsi
        if detected_initial < total_comments * 0.1:  # Kurang dari 10%
            print("🔍 Mendeteksi ulang lokasi untuk data yang belum terdeteksi...")
            
            # Filter data yang belum punya provinsi
            undetected_mask = df['province'].isna()
            undetected_df = df[undetected_mask].copy()
            
            if not undetected_df.empty:
                print(f"   - {len(undetected_df)} komentar akan dideteksi ulang")
                
                # Deteksi ulang
                detected_df = detector.batch_detect(
                    undetected_df,
                    username_col='username',
                    display_name_col='display_name' if 'display_name' in df.columns else None,
                    bio_col='bio' if 'bio' in df.columns else None,
                    text_col='comment'
                )
                
                # Update dataframe original
                df.loc[undetected_mask, 'province'] = detected_df['province'].values
                df.loc[undetected_mask, 'city'] = detected_df['city'].values
                df.loc[undetected_mask, 'island'] = detected_df['island'].values
                df.loc[undetected_mask, 'location_confidence'] = detected_df['confidence'].values
                df.loc[undetected_mask, 'detection_method'] = detected_df['detection_method'].values
                df.loc[undetected_mask, 'detection_source'] = detected_df['source'].values
                
                # Hitung ulang setelah deteksi
                detected_final = df['province'].notna().sum()
                print(f"✅ Setelah deteksi ulang: {detected_final} provinsi terdeteksi ({detected_final/total_comments*100:.1f}%)")
        
        # Isi nilai kosong
        df['province'] = df['province'].fillna('Tidak Diketahui')
        df['island'] = df['island'].fillna('Lainnya')
        df['city'] = df['city'].fillna('')
        df['sentiment'] = df['sentiment'].fillna('Netral')
        
        # Hitung statistik regional (hanya untuk provinsi yang terdeteksi)
        df_with_province = df[df['province'] != 'Tidak Diketahui'].copy()
        
        if len(df_with_province) == 0:
            print("⚠️ Tidak ada data dengan provinsi yang terdeteksi")
            return render_template(
                "sentiment_heatmap.html",
                total_comments=total_comments,
                active_regions=0,
                national_stats={"positive_pct": 0, "negative_pct": 0},
                heatmap_data=[],
                trend_data=[],
                island_comparison=[],
                top_provinces=[],
                bottom_provinces=[],
                provinces_detail=[],
                summary={"Positif": 0, "Negatif": 0, "Netral": 0},
                data_source=f"{total_comments} komentar (0 dengan lokasi)"
            )
        
        # Hitung statistik regional
        regional_stats = detector.get_regional_stats(df_with_province)
        
        # Generate data untuk visualisasi
        heatmap_data = generator.generate_heatmap_data(regional_stats)
        trend_data = generator.generate_trend_data(df)
        comparison = generator.generate_comparison_data(regional_stats, min_comments=1)
        provinces_detail = generator.generate_provinces_detail(regional_stats)
        
        # Statistik nasional
        national = regional_stats["national"]
        total = national["total_comments"]
        positive = national["positive"]
        negative = national["negative"]
        neutral = national["neutral"]
        
        positive_pct = (positive / total * 100) if total > 0 else 0
        negative_pct = (negative / total * 100) if total > 0 else 0
        neutral_pct = (neutral / total * 100) if total > 0 else 0
        
        summary = {
            "Positif": round(positive_pct, 1),
            "Negatif": round(negative_pct, 1),
            "Netral": round(neutral_pct, 1)
        }
        
        print(f"✅ FINAL: {len(provinces_detail)} provinsi ditampilkan")
        print(f"📊 Total komentar dengan provinsi: {total}")
        print(f"📊 Positif: {summary['Positif']}%, Negatif: {summary['Negatif']}%, Netral: {summary['Netral']}%")
        
        return render_template(
            "sentiment_heatmap.html",
            total_comments=total,
            active_regions=len(regional_stats["by_province"]),
            national_stats={
                "positive": positive,
                "negative": negative,
                "neutral": neutral,
                "positive_pct": positive_pct,
                "negative_pct": negative_pct
            },
            heatmap_data=heatmap_data,
            trend_data=trend_data,
            island_comparison=comparison["island_comparison"],
            top_provinces=comparison["top_provinces"],
            bottom_provinces=comparison["bottom_provinces"],
            provinces_detail=provinces_detail,
            summary=summary,
            data_source=f"{total} komentar dari {len(provinces_detail)} provinsi"
        )
        
    except Exception as e:
        print(f"❌ Error di heatmap: {e}")
        import traceback
        traceback.print_exc()
        
        return render_template(
            "sentiment_heatmap.html",
            total_comments=0,
            active_regions=0,
            national_stats={"positive_pct": 0, "negative_pct": 0},
            heatmap_data=[],
            trend_data=[],
            island_comparison=[],
            top_provinces=[],
            bottom_provinces=[],
            provinces_detail=[],
            summary={},
            data_source=f"Error: {str(e)[:50]}"
        )

@app.route("/viral-dashboard")
def viral_dashboard():
    db = DatabaseManager()
    analyzer = ViralAnalyzer(db)
    
    # Ambil data
    viral_topics = db.get_viral_topics()
    predictions = db.get_viral_predictions()
    alerts = db.get_alerts()
    
    return render_template(
        "viral_dashboard.html",
        viral_topics=viral_topics,
        predictions=predictions,
        alerts=alerts
    )

@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    """API endpoint untuk analisis"""
    data = request.get_json()
    link = data.get("link", "").strip()
    
    try:
        max_comments = int(data.get("max_comments", 1000))
        max_comments = max(100, min(5000, max_comments))
    except (ValueError, TypeError):
        max_comments = 1000
    
    if not link:
        return jsonify({"error": "URL diperlukan"}), 400
    
    try:
        result = run_full_pipeline(link, max_comments=max_comments, save_to_db=True)
        if result:
            return jsonify(result)
        else:
            return jsonify({"error": "Gagal menganalisis"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/status")
def status():
    """Cek status server"""
    # Hitung total komentar di database
    total_db = 0
    if MODELS_AVAILABLE:
        try:
            from models_db import Comment
            total_db = db_manager.session.query(Comment).count()
        except:
            pass
    
    return jsonify({
        "status": "running",
        "version": "3.2",
        "features": [
            "scraping with cookie", 
            "hybrid sentiment (RoBERTa + rule-based)",
            "parallel processing",
            "trend analysis",
            "confidence scoring",
            "custom max comments (100-5000)",
            "auto-save to database",
            "multi-layer location detection",
            "enhanced heatmap visualization"
        ],
        "model": "w11wo/indonesian-roberta-base-sentiment-classifier",
        "default_max_comments": 1000,
        "database": {
            "connected": MODELS_AVAILABLE,
            "total_comments": total_db
        }
    })

if __name__ == "__main__":
    print("="*70)
    print("🚀 TIKTOK SENTIMENT ANALYSIS SERVER v3.2")
    print("="*70)
    print("📊 Model: Indonesian RoBERTa + Rule-based Hybrid")
    print("⚡ Fitur: Parallel processing, Confidence scoring")
    print("💾 Auto-save to database: ENABLED")
    print("📍 Multi-layer location detection: ENABLED")
    print("🎯 Default Max Comments: 1000")
    print("📊 Heatmap: Menampilkan SEMUA provinsi dengan data")
    print("="*70)
    print("🌐 Server running at http://localhost:5000")
    print("="*70)
    
    # Nonaktifkan reloader untuk menghindari error di Windows
    app.run(debug=True, use_reloader=False, host="0.0.0.0", port=5000)