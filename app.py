from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from scraper import scrape_tiktok_comments
from sentiment import analyze_sentiment, analyze_batch
from collections import Counter
import pandas as pd
import re
import json
import os
import time
import hashlib
import functools
from datetime import timedelta, datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from viral_analyzer import ViralAnalyzer
from geo_sentiment import GeoLocationDetector
from scraper import scrape_and_save_to_db
from bengkulu_geodata import BengkuluHeatmapGenerator
from heatmap_generator import HeatmapGenerator
from database import DatabaseManager
from models_db import Comment, SentimentAnalysis, User, Video, DailyTrend, RegionalStat

load_dotenv()

# Inisialisasi database manager dan geo detector
db_manager = DatabaseManager()
geo_detector = GeoLocationDetector()

# Cek ketersediaan models_db
MODELS_AVAILABLE = True
try:
    print("✅ Models_db tersedia dan terintegrasi")
except Exception as e:
    print(f"⚠️ Error inisialisasi: {e}")
    MODELS_AVAILABLE = False

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'tiktok-sentimen-analysis-secret-key-2024')
app.permanent_session_lifetime = timedelta(days=1)

# =============================================
# HELPER: PASSWORD HASHING
# =============================================
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(plain: str, hashed: str) -> bool:
    return hash_password(plain) == hashed

# =============================================
# DECORATOR: LOGIN REQUIRED
# =============================================
def login_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Silakan login terlebih dahulu.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

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
    default_result = {"labels": [], "positif": [], "negatif": [], "netral": []}
    
    if df.empty or "date" not in df.columns:
        return default_result
    
    try:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])
        if df.empty: return default_result
        
        df["date_only"] = df["date"].dt.date
        trend_sentiment = df.groupby(["date_only", "sentiment"]).size().unstack(fill_value=0).reset_index()
        
        for col in ["Positif", "Negatif", "Netral"]:
            if col not in trend_sentiment.columns: trend_sentiment[col] = 0
        
        trend_sentiment = trend_sentiment.sort_values("date_only")
        labels = [str(d) for d in trend_sentiment["date_only"].tolist()]
        
        return {
            "labels": labels,
            "positif": trend_sentiment["Positif"].tolist(),
            "negatif": trend_sentiment["Negatif"].tolist(),
            "netral": trend_sentiment["Netral"].tolist(),
        }
    except Exception as e:
        print(f"⚠️ Error dalam analyze_trends: {e}")
        return default_result

# =========================
# WORD CLOUD DATA
# =========================
def get_top_words(df, n=30):
    if df.empty or "clean_text" not in df.columns: return []
    all_words = " ".join(df["clean_text"].fillna("")).split()
    if not all_words: return []
    
    word_freq = Counter(all_words)
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
    data = []
    if not comments: return data
    
    texts = [c.get("comment", "") for c in comments]
    start_time = time.time()
    processed = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_comment = {
            executor.submit(analyze_sentiment, text, True): (i, comment) 
            for i, (text, comment) in enumerate(zip(texts, comments))
        }
        
        for future in as_completed(future_to_comment):
            i, comment = future_to_comment[future]
            try:
                result = future.result(timeout=5)
                sentiment, confidence = result if isinstance(result, tuple) else (result, 50.0)
                
                clean_text = preprocess_text(comment.get("comment", ""))
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
            except Exception as e:
                print(f"Error analyzing comment {i}: {e}")
                data.append({
                    "comment": comment.get("comment", ""),
                    "clean_text": preprocess_text(comment.get("comment", "")),
                    "sentiment": "Netral", "confidence": 0, "date": comment.get("date", "Unknown"),
                    "username": comment.get("username", "unknown"), "display_name": comment.get("display_name", ""),
                    "bio": comment.get("bio", ""), "likes": comment.get("likes", 0),
                    "province": None, "city": None, "island": None, "location_confidence": 0,
                    "detection_method": None, "detection_source": None
                })
    
    print(f"✅ Analisis {len(comments)} komentar selesai dalam {time.time() - start_time:.2f} detik")
    return data

# =========================
# MAIN PIPELINE
# =========================
def run_full_pipeline(link, max_comments=1000, save_to_db=True):
    print(f"🚀 Memulai pipeline untuk: {link}")
    comments = scrape_tiktok_comments(link, max_comments=max_comments)
    if not comments: return None
    
    video_db_id = None
    if save_to_db and MODELS_AVAILABLE:
        try:
            video_id_match = re.search(r'/video/(\d+)', link)
            video_id = video_id_match.group(1) if video_id_match else f"video_{int(time.time())}"
            video_data = {
                'video_id': video_id, 'url': link, 'platform': 'tiktok',
                'title': f"Video {video_id}", 'author_username': 'unknown',
                'views_count': 0, 'likes_count': 0, 'comments_count': len(comments),
                'scraped_date': datetime.now()
            }
            video_db_id = db_manager.save_video(video_data)
        except Exception as e: print(f"⚠️ Gagal simpan video: {e}")
    
    data = analyze_sentiments_parallel(comments)
    if not data: return None
    df = pd.DataFrame(data)
    
    saved_count = 0
    if save_to_db and video_db_id and MODELS_AVAILABLE:
        for i, comment_data in enumerate(data):
            try:
                db_comment_data = {
                    'video_id': video_db_id, 'comment_id': f"cmt_{int(time.time())}_{i}",
                    'raw_text': comment_data['comment'], 'clean_text': comment_data['clean_text'],
                    'username': comment_data['username'], 'display_name': comment_data.get('display_name', ''),
                    'bio': comment_data.get('bio', ''), 'like_count': comment_data['likes'],
                    'comment_date': datetime.now(), 'sentiment': comment_data['sentiment'],
                    'sentiment_score': comment_data['confidence'], 'province': comment_data.get('province'),
                    'city': comment_data.get('city'), 'island': comment_data.get('island'),
                    'location_confidence': comment_data.get('location_confidence', 0),
                    'detection_method': comment_data.get('detection_method'),
                    'detection_source': comment_data.get('detection_source')
                }
                db_manager.save_comment(db_comment_data)
                saved_count += 1
            except Exception as e: print(f"⚠️ Gagal simpan komentar {i}: {e}")
    
    sentiment_dist = get_sentiment_distribution(df)
    total = len(df)
    summary = {k: round((v / total * 100), 1) if total > 0 else 0 for k, v in sentiment_dist.items()}
    
    highlights = {}
    for sentiment in ["Positif", "Negatif", "Netral"]:
        sentiment_df = df[df["sentiment"] == sentiment]
        highlights[sentiment] = sentiment_df.nlargest(3, "confidence")[["comment", "username", "confidence"]].to_dict("records") if not sentiment_df.empty else []
    
    return {
        "results": data, "sentiment_dist": sentiment_dist, "summary": summary,
        "trend_chart": analyze_trends(df), "top_words": get_top_words(df),
        "total": total, "highlights": highlights, "video_db_id": video_db_id,
        "tiktok_video_id": video_id,
        "saved_to_db": saved_count, "stats": {"total_likes": int(df["likes"].sum()) if "likes" in df.columns else 0}
    }

# =============================================
# AUTH ROUTES
# =============================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session: return redirect(url_for('index'))
    error = None
    if request.method == 'POST':
        username_input = request.form.get('username', '').strip()
        password_input = request.form.get('password', '')
        user = db_manager.session.query(User).filter((User.username == username_input) | (User.email == username_input)).first()
        if user and check_password(password_input, user.password_hash):
            if not user.is_active: error = 'Akun Anda tidak aktif.'
            else:
                session.permanent = bool(request.form.get('remember'))
                session['user_id'] = user.id
                session['username'] = user.username
                session['full_name'] = user.full_name or user.username
                session['role'] = user.role
                user.last_login = datetime.now()
                db_manager.session.commit()
                flash(f'Selamat datang, {session["full_name"]}!', 'success')
                return redirect(request.args.get('next', '/'))
        else: error = 'Username atau kata sandi salah.'
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session: return redirect(url_for('index'))
    
    error = None
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        if password != request.form.get('confirm_password', ''): error = 'Konfirmasi kata sandi tidak cocok.'
        elif len(password) < 8: error = 'Kata sandi minimal 8 karakter.'
        else:
            try:
                new_user = User(username=username, email=email, full_name=full_name,
                                password_hash=hash_password(password), role='admin', is_active=True)
                db_manager.session.add(new_user)
                db_manager.session.commit()
                flash('Akun administrator berhasil dibuat! Silakan login.', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                db_manager.session.rollback()
                error = 'Gagal membuat akun. Username atau email mungkin sudah terdaftar.'
    return render_template('register.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    flash('Berhasil keluar sistem.', 'success')
    return redirect(url_for('login'))

# =============================================
# MAIN ROUTES (LOGIN REQUIRED)
# =============================================

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    total_comments_in_db = db_manager.session.query(Comment).count() if MODELS_AVAILABLE else 0
    bengkulu_comments_count = db_manager.session.query(Comment).filter(Comment.detected_province == 'BENGKULU').count() if MODELS_AVAILABLE else 0
    
    if request.method == "POST":
        link = request.form.get("link", "").strip()
        max_comments = max(100, min(5000, int(request.form.get("max_comments", 1000))))
        if not link: return render_template("index.html", error="Masukkan URL TikTok", total_comments_in_db=total_comments_in_db, bengkulu_comments_count=bengkulu_comments_count)
        
        result = run_full_pipeline(link, max_comments=max_comments, save_to_db=True)
        if result:
            return render_template("index.html", results=result["results"], sentiment_dist=result["sentiment_dist"],
                                  summary=result["summary"], trend_labels=result["trend_chart"]["labels"] or ["Hari Ini"],
                                  trend_positif=result["trend_chart"]["positif"] or [result["sentiment_dist"]["Positif"]],
                                  trend_negatif=result["trend_chart"]["negatif"] or [result["sentiment_dist"]["Negatif"]],
                                  trend_netral=result["trend_chart"]["netral"] or [result["sentiment_dist"]["Netral"]],
                                  top_words=result["top_words"], total=result["total"], stats=result["stats"],
                                  highlights=result["highlights"], max_comments=max_comments, saved_to_db=result["saved_to_db"],
                                  total_comments_in_db=total_comments_in_db + result["saved_to_db"], 
                                  bengkulu_comments_count=bengkulu_comments_count, success=True)
        return render_template("index.html", error="Gagal mengambil komentar", total_comments_in_db=total_comments_in_db, bengkulu_comments_count=bengkulu_comments_count)
    
    return render_template("index.html", total_comments_in_db=total_comments_in_db, bengkulu_comments_count=bengkulu_comments_count, active_page='home')

@app.route("/bengkulu-heatmap")
@login_required
def bengkulu_heatmap():
    from bengkulu_geodata import BengkuluHeatmapGenerator
    generator = BengkuluHeatmapGenerator()
    comments = db_manager.session.query(Comment).filter(Comment.detected_province == 'BENGKULU').all()
    
    sentiment_by_region = {r["nama"]: {"positive": 0, "negative": 0, "neutral": 0, "total": 0, "positive_pct": 0} for r in generator.get_all_regions()}
    region_keywords = {"BENGKULU": ["bengkulu", "kota bengkulu"], "BENGKULU SELATAN": ["manna"], "BENGKULU UTARA": ["argamakmur"], "BENGKULU TENGAH": ["karang tinggi"], "REJANG LEBONG": ["curup"], "KAUR": ["bintuhan"], "SELUMA": ["tais"], "MUKOMUKO": ["mukomuko"], "LEBONG": ["muara aman"], "KEPAHIANG": ["kepahiang"]}
    
    for c in comments:
        text = (c.raw_text or "").lower()
        sent = c.sentiment.sentiment if c.sentiment else "Netral"
        for reg, kws in region_keywords.items():
            if any(kw in text for kw in kws):
                sentiment_by_region[reg][sent.lower().replace("positif", "positive").replace("negatif", "negative").replace("netral", "neutral")] += 1
                sentiment_by_region[reg]["total"] += 1
                break
    
    for r in sentiment_by_region:
        if sentiment_by_region[r]["total"] > 0: sentiment_by_region[r]["positive_pct"] = round(sentiment_by_region[r]["positive"] / sentiment_by_region[r]["total"] * 100, 1)
    
    total_comments_in_db = db_manager.session.query(Comment).count()
    # Hitung sentimen nasional untuk chart donut di template
    pos = db_manager.session.query(Comment).join(SentimentAnalysis).filter(SentimentAnalysis.sentiment == 'Positif').count()
    neg = db_manager.session.query(Comment).join(SentimentAnalysis).filter(SentimentAnalysis.sentiment == 'Negatif').count()
    neu = db_manager.session.query(Comment).join(SentimentAnalysis).filter(SentimentAnalysis.sentiment == 'Netral').count()
    
    national_sentiment = {
        "positive": pos,
        "negative": neg,
        "neutral": neu
    }

    return render_template("bengkulu_heatmap.html", 
                           heatmap_data=generator.generate_heatmap_data(sentiment_by_region), 
                           stats=generator.get_statistics_summary(generator.generate_heatmap_data(sentiment_by_region)), 
                           total_comments=len(comments), 
                           total_comments_in_db=total_comments_in_db,
                           bengkulu_comments_count=len(comments),
                           national_sentiment=national_sentiment,
                           active_page='bengkulu',
                           now=datetime.now())

@app.route("/status")
def status():
    return jsonify({"status": "running", "database": {"connected": True, "name": "tiktok_db1", "count": db_manager.session.query(Comment).count()}})

# =============================================
# ADDITIONAL FEATURES ROUTES
# =============================================

@app.route("/sentiment-heatmap")
@login_required
def sentiment_heatmap():
    generator = HeatmapGenerator()
    
    # Query all comments that have locations
    # For performance in large DB, you might want to limit this or use RegionalStat table
    comments = db_manager.session.query(Comment).all()
    
    data_list = []
    for c in comments:
        if c.detected_province and c.sentiment:
            data_list.append({
                "province": c.detected_province,
                "city": c.detected_city,
                "island": c.detected_island,
                "sentiment": c.sentiment.sentiment
            })
    
    df = pd.DataFrame(data_list)
    regional_stats = geo_detector.get_regional_stats(df)
    
    heatmap_data = generator.generate_heatmap_data(regional_stats)
    stats = generator.get_stat_summary(regional_stats)
    comparison = generator.generate_comparison_data(regional_stats)
    provinces_detail = generator.generate_provinces_detail(regional_stats)
    
    # Generate trend data (requires full comment objects with dates)
    df_trend = pd.DataFrame([{
        "date": c.comment_date,
        "sentiment": c.sentiment.sentiment if c.sentiment else "Netral"
    } for c in comments if c.comment_date])
    trend_data = generator.generate_trend_data(df_trend)
    
    total_comments_in_db = len(comments)
    bengkulu_comments_count = db_manager.session.query(Comment).filter(Comment.detected_province == 'BENGKULU').count()
    
    return render_template(
        "sentiment_heatmap.html", 
        heatmap_data=heatmap_data,
        national_stats=stats,
        total_comments=stats['total_comments'],
        active_regions=stats['provinces_with_data'],
        trend_data=trend_data,
        island_comparison=comparison,
        provinces_detail=provinces_detail,
        total_comments_in_db=total_comments_in_db,
        bengkulu_comments_count=bengkulu_comments_count,
        active_page='heatmap'
    )

@app.route("/scrape-to-db", methods=["GET", "POST"])
@login_required
def scrape_to_db():
    total_comments_in_db = db_manager.session.query(Comment).count()
    bengkulu_count = db_manager.session.query(Comment).filter(Comment.detected_province == 'BENGKULU').count()
    videos = db_manager.session.query(Video).order_by(Video.scraped_date.desc()).limit(10).all()
    
    if request.method == "POST":
        link = request.form.get("link", "").strip()
        max_comments = max(100, min(2000, int(request.form.get("max_comments", 500))))
        
        if not link:
            return render_template("scrape_to_db.html", error="Masukkan URL TikTok", 
                                   total_comments_in_db=total_comments_in_db, bengkulu_count=bengkulu_count, videos=videos)
        
        result = run_full_pipeline(link, max_comments=max_comments, save_to_db=True)
        
        if result:
            # Refresh data after scrape
            total_comments_in_db = db_manager.session.query(Comment).count()
            videos = db_manager.session.query(Video).order_by(Video.scraped_date.desc()).limit(10).all()
            
            return render_template("scrape_to_db.html", 
                                   success=True, 
                                   total=result["saved_to_db"],
                                   video_id=result["tiktok_video_id"],
                                   total_comments_in_db=total_comments_in_db,
                                   bengkulu_comments_count=bengkulu_count,
                                   bengkulu_count=bengkulu_count, # Compatibility
                                   videos=videos,
                                   active_page='scrape')
        
        return render_template("scrape_to_db.html", error="Gagal mengambil komentar", 
                               total_comments_in_db=total_comments_in_db, 
                               bengkulu_comments_count=bengkulu_count,
                               bengkulu_count=bengkulu_count, # Compatibility
                               videos=videos)

    return render_template("scrape_to_db.html", 
                           total_comments_in_db=total_comments_in_db, 
                           bengkulu_comments_count=bengkulu_count, 
                           bengkulu_count=bengkulu_count, # Compatibility
                           videos=videos,
                           active_page='scrape')

@app.route("/video-analysis/<video_id>")
@login_required
def video_analysis(video_id):
    video = db_manager.session.query(Video).filter(Video.video_id == video_id).first()
    if not video:
        flash("Video tidak ditemukan.", "error")
        return redirect(url_for('scrape_to_db'))
    
    comments_query = video.comments
    total = len(comments_query)
    
    total_comments_in_db = db_manager.session.query(Comment).count()
    bengkulu_comments_count = db_manager.session.query(Comment).filter(Comment.detected_province == 'BENGKULU').count()
    
    if total == 0:
        return render_template("video_analysis.html", video=video, comments=[], total_comments=0, 
                               total_comments_in_db=total_comments_in_db, bengkulu_comments_count=bengkulu_comments_count)
    
    # Process comments for visualization
    data = []
    sentiment_dist = {"Positif": 0, "Negatif": 0, "Netral": 0}
    location_stats = {}
    
    for c in comments_query:
        sent = c.sentiment.sentiment if c.sentiment else "Netral"
        sentiment_dist[sent] += 1
        
        if c.detected_province:
            location_stats[c.detected_province] = location_stats.get(c.detected_province, 0) + 1
            
        data.append({
            "text": c.raw_text,
            "username": c.username,
            "sentiment": sent,
            "confidence": c.sentiment.sentiment_score if c.sentiment else 0,
            "province": c.detected_province or "Luar Sumatra",
            "date": c.comment_date.strftime('%Y-%m-%d %H:%M') if c.comment_date else "Unknown",
            "likes": c.like_count
        })
    
    # Sort data for top comments (most liked)
    top_comments = sorted(data, key=lambda x: x['likes'], reverse=True)[:5]
    
    df = pd.DataFrame(data)
    positive_pct = round((sentiment_dist["Positif"] / total * 100), 1)
    negative_pct = round((sentiment_dist["Negatif"] / total * 100), 1)
    neutral_pct = round((sentiment_dist["Netral"] / total * 100), 1)
    
    # Chart data structure
    trend_data = analyze_trends(df)
    chart_data = {
        "sentiment": {
            "labels": ["Positif", "Negatif", "Netral"],
            "values": [sentiment_dist["Positif"], sentiment_dist["Negatif"], sentiment_dist["Netral"]],
            "colors": ["#2e7d32", "#c62828", "#9ca3af"]
        },
        "trend": {
            "dates": trend_data["labels"],
            "positif": trend_data["positif"],
            "negatif": trend_data["negatif"],
            "netral": trend_data["netral"]
        }
    }
    
    # Map video properties to match template expectations
    video_legacy = {
        "title": video.title or "Video TikTok",
        "video_id": video.video_id,
        "author": video.author_username or "Unknown",
        "url": video.url or "#",
        "views": video.views_count or 0,
        "likes": video.likes_count or 0,
        "total_comments": total,
        "scraped_date": video.scraped_date
    }
    
    return render_template("video_analysis.html", 
                           video=video_legacy, 
                           comments=data, 
                           total_comments=total,
                           sentiment_stats=sentiment_dist,
                           location_stats=location_stats,
                           positive_pct=positive_pct,
                           negative_pct=negative_pct,
                           neutral_pct=neutral_pct,
                           chart_data=chart_data,
                           top_comments=top_comments,
                           total_comments_in_db=total_comments_in_db,
                           bengkulu_comments_count=bengkulu_comments_count,
                           active_page='scrape')

@app.route("/about")
@login_required
def about():
    total_comments_in_db = db_manager.session.query(Comment).count()
    bengkulu_comments_count = db_manager.session.query(Comment).filter(Comment.detected_province == 'BENGKULU').count()
    return render_template("about.html", 
                           total_comments_in_db=total_comments_in_db, 
                           bengkulu_comments_count=bengkulu_comments_count, 
                           active_page='about')

@app.route("/how-to-use")
@login_required
def how_to_use():
    return "Halaman Panduan - Dalam Pengembangan"

@app.route("/faq")
@login_required
def faq():
    return "Halaman FAQ - Dalam Pengembangan"

@app.route("/privacy")
@login_required
def privacy():
    return "Halaman Privasi - Dalam Pengembangan"

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False, host="0.0.0.0", port=5002)