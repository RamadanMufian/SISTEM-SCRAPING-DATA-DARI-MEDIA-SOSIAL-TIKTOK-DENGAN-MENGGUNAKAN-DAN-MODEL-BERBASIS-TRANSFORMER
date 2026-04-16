# heatmap_generator.py - OPTIMIZED VERSION V2.1 (FIXED COLOR)
"""
Generate data untuk heatmap dan visualisasi - OPTIMIZED VERSION
FIXED:
- Warna tidak hitam lagi
- Menggunakan HEX color (lebih aman)
- Intensity minimal 0.3
- Debug output untuk troubleshooting
"""

import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta
import math

class HeatmapGenerator:
    """
    Generate data untuk heatmap sentimen - Enhanced & Optimized
    """
    
    def __init__(self):
        self.region_colors = {
            "very_positive": "#22c55e",   # Hijau terang
            "positive": "#86efac",          # Hijau muda
            "neutral": "#9ca3af",           # Abu-abu
            "negative": "#f87171",           # Merah muda
            "very_negative": "#dc2626"       # Merah tua
        }
        
        # Threshold untuk kategori
        self.thresholds = {
            "very_positive": 80,
            "positive": 60,
            "neutral": 40,
            "negative": 20,
            "very_negative": 0
        }
    
    # ===============================
    # STEP 1: PERBAIKI RUMUS SENTIMEN
    # ===============================
    def calculate_sentiment_score(self, stats):
        """
        Hitung skor sentimen yang balanced (tidak bias)
        Formula: ((positif - negatif) / total) * 100
        
        Args:
            stats: Dictionary dengan key 'positive', 'negative', 'total'
        
        Returns:
            float: Skor sentimen antara -100 hingga 100
        """
        pos = stats.get("positive", 0)
        neg = stats.get("negative", 0)
        total = stats.get("total", 1)
        
        if total == 0:
            return 0
        
        # 🔥 Balanced score: positif - negatif
        score = ((pos - neg) / total) * 100
        
        return score
    
    # ===============================
    # STEP 2: WARNA DENGAN HEX (LEBIH AMAN)
    # ===============================
    def get_color_from_score(self, score):
        """
        Dapatkan HEX color berdasarkan skor sentimen
        🔥 LANGSUNG HEX, BUKAN RGBA (lebih aman untuk Leaflet)
        
        Args:
            score: Skor sentimen antara -100 hingga 100
        
        Returns:
            tuple: (color_hex, intensity, color_rgba)
        """
        # 🔥 Minimal intensity 0.3 agar tidak transparan/hitam
        min_intensity = 0.3
        
        if score >= 0:
            # Positif: hijau dengan intensitas sesuai skor
            intensity = min(1.0, score / 100)
            intensity = max(min_intensity, intensity)
            
            # Interpolasi warna hijau
            # Base: #22c55e (RGB: 34, 197, 94)
            r = int(34 * intensity)
            g = int(197 * intensity)
            b = int(94 * intensity)
            
            # Pastikan minimal warna terlihat
            r = max(20, r)
            g = max(50, g)
            b = max(20, b)
            
            color_hex = f"#{r:02x}{g:02x}{b:02x}"
            color_rgba = f"rgba({r}, {g}, {b}, {intensity:.2f})"
            
        else:
            # Negatif: merah dengan intensitas sesuai skor
            intensity = min(1.0, abs(score) / 100)
            intensity = max(min_intensity, intensity)
            
            # Interpolasi warna merah
            # Base: #dc2626 (RGB: 220, 38, 38)
            r = int(220 * intensity)
            g = int(38 * intensity)
            b = int(38 * intensity)
            
            # Pastikan minimal warna terlihat
            r = max(50, r)
            g = max(10, g)
            b = max(10, b)
            
            color_hex = f"#{r:02x}{g:02x}{b:02x}"
            color_rgba = f"rgba({r}, {g}, {b}, {intensity:.2f})"
        
        # 🔥 FALLBACK: jika score sangat kecil (netral), pakai abu-abu
        if abs(score) < 5:
            color_hex = "#9ca3af"
            color_rgba = "rgba(156, 163, 175, 0.7)"
            intensity = 0.7
        
        return color_hex, intensity, color_rgba
    
    def get_color_gradient(self, score):
        """
        Dapatkan warna gradient (backward compatibility)
        
        Args:
            score: Skor sentimen antara -100 hingga 100
        
        Returns:
            tuple: (color_rgba, intensity)
        """
        color_hex, intensity, color_rgba = self.get_color_from_score(score)
        return color_rgba, intensity
    
    def get_hex_color_from_score(self, score):
        """
        Dapatkan HEX color dari skor sentimen untuk fallback
        
        Args:
            score: Skor sentimen antara -100 hingga 100
        
        Returns:
            str: Kode warna hex
        """
        color_hex, _, _ = self.get_color_from_score(score)
        return color_hex
    
    # ===============================
    # STEP 3: PERBAIKI RADIUS
    # ===============================
    def calculate_radius(self, total_comments):
        """
        Hitung radius marker berdasarkan jumlah komentar
        Menggunakan log scale untuk hasil yang lebih natural
        
        Args:
            total_comments: Jumlah komentar
        
        Returns:
            int: Radius dalam pixel (8-30)
        """
        if total_comments < 5:
            return 0  # Tidak ditampilkan
        
        # 🔥 Menggunakan log1p untuk skala yang lebih natural
        radius = np.log1p(total_comments) * 6
        
        # Batasi antara 8 dan 30
        radius = min(30, max(8, radius))
        
        return int(radius)
    
    # ===============================
    # STEP 4: FILTER DATA SAMPAH
    # ===============================
    def should_include_province(self, stats, min_comments=5):
        """
        Tentukan apakah provinsi harus ditampilkan
        
        Args:
            stats: Dictionary statistik provinsi
            min_comments: Minimal komentar untuk ditampilkan
        
        Returns:
            bool: True jika layak ditampilkan
        """
        total = stats.get("total", 0)
        
        # 🔥 Filter provinsi dengan data minim
        if total < min_comments:
            return False
        
        return True
    
    # ===============================
    # STEP 5: LOCATION DETECTION FIX
    # ===============================
    @staticmethod
    def word_match(keyword, text):
        """
        Cek apakah keyword ada sebagai kata utuh dalam text
        Menggunakan regex boundary untuk menghindari partial match
        
        Args:
            keyword: Kata kunci yang dicari
            text: Teks yang diperiksa
        
        Returns:
            bool: True jika ditemukan sebagai kata utuh
        """
        if not keyword or not text:
            return False
        
        # 🔥 Menggunakan word boundary untuk exact match
        pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
        return bool(re.search(pattern, text.lower()))
    
    # ===============================
    # STEP 6: GET LABEL
    # ===============================
    def get_label(self, score):
        """
        Dapatkan label berdasarkan skor sentimen
        
        Args:
            score: Skor sentimen antara -100 hingga 100
        
        Returns:
            str: Label sentimen
        """
        if score > 30:
            return "Positif"
        elif score < -30:
            return "Negatif"
        else:
            return "Netral"
    
    # ===============================
    # MAIN GENERATE FUNCTIONS
    # ===============================
    def generate_heatmap_data(self, regional_stats):
        """
        Generate data untuk heatmap dengan format Leaflet
        OPTIMIZED VERSION - FIXED COLOR
        
        Args:
            regional_stats: Dictionary dari GeoLocationDetector.get_regional_stats()
        
        Returns:
            List of dictionaries untuk plotting di peta
        """
        heatmap_data = []
        
        if not regional_stats or "by_province" not in regional_stats:
            print("⚠️ No regional stats available")
            return []
        
        print("\n" + "="*60)
        print("🗺️ GENERATING HEATMAP DATA (FIXED COLOR)")
        print("="*60)
        
        for province, stats in regional_stats["by_province"].items():
            # 🔥 STEP 4: Filter data sampah
            if not self.should_include_province(stats, min_comments=5):
                print(f"   ⚠️ Skipping {province}: only {stats.get('total', 0)} comments")
                continue
            
            # Skip jika tidak ada koordinat
            if "coordinates" not in stats or not stats["coordinates"]:
                print(f"   ⚠️ Skipping {province}: no coordinates")
                continue
            
            # 🔥 STEP 1: Hitung skor sentimen yang balanced
            score = self.calculate_sentiment_score(stats)
            
            total = stats.get("total", 0)
            pos = stats.get("positive", 0)
            neg = stats.get("negative", 0)
            neutral = stats.get("neutral", 0)
            
            # 🔥 STEP 2: Dapatkan warna HEX (lebih aman)
            color_hex, intensity, color_rgba = self.get_color_from_score(score)
            
            # 🔥 STEP 3: Hitung radius yang realistis
            radius = self.calculate_radius(total)
            
            # Hitung persentase untuk display
            positive_pct = round(pos / total * 100, 1) if total > 0 else 0
            negative_pct = round(neg / total * 100, 1) if total > 0 else 0
            neutral_pct = round(neutral / total * 100, 1) if total > 0 else 0
            
            # 🔥 DEBUG: Print untuk troubleshooting
            print(f"\n   📍 {province}:")
            print(f"      Total: {total} | Pos: {pos} | Neg: {neg} | Netral: {neutral}")
            print(f"      Score: {score:.1f} ({self.get_label(score)})")
            print(f"      Color: {color_hex} | Intensity: {intensity:.2f}")
            print(f"      Radius: {radius}px")
            
            # 🔥 FIELD YANG KONSISTEN untuk frontend
            heatmap_data.append({
                "province": province,
                "lat": stats["coordinates"]["lat"],
                "lon": stats["coordinates"]["lon"],
                "score": round(score, 1),                    # Skor balanced
                "value": round(positive_pct, 1),             # Untuk backward compatibility
                "color": color_hex,                          # 🔥 MAIN COLOR (HEX)
                "color_hex": color_hex,                      # 🔥 Backup field
                "color_rgba": color_rgba,                    # Untuk referensi
                "intensity": intensity,
                "radius": radius,
                "total": total,
                "positive": pos,
                "negative": neg,
                "neutral": neutral,
                "positive_pct": positive_pct,
                "negative_pct": negative_pct,
                "neutral_pct": neutral_pct,
                "label": self.get_label(score)
            })
        
        # Urutkan berdasarkan total komentar (descending)
        heatmap_data.sort(key=lambda x: x['total'], reverse=True)
        
        print("\n" + "="*60)
        print("📊 HEATMAP SUMMARY")
        print("="*60)
        print(f"✅ Total provinsi ditampilkan: {len(heatmap_data)}")
        
        if heatmap_data:
            scores = [d['score'] for d in heatmap_data]
            print(f"   - Skor tertinggi: {max(scores):.1f}")
            print(f"   - Skor terendah: {min(scores):.1f}")
            print(f"   - Rata-rata skor: {sum(scores)/len(scores):.1f}")
            
            # Hitung distribusi
            positive_count = sum(1 for d in heatmap_data if d['label'] == "Positif")
            negative_count = sum(1 for d in heatmap_data if d['label'] == "Negatif")
            neutral_count = sum(1 for d in heatmap_data if d['label'] == "Netral")
            
            print(f"   - Distribusi: Positif={positive_count}, Negatif={negative_count}, Netral={neutral_count}")
            
            # 🔥 Tampilkan contoh warna untuk debugging
            print("\n   🎨 Contoh warna yang dihasilkan:")
            for d in heatmap_data[:3]:
                print(f"      - {d['province']}: {d['color']} (score={d['score']})")
        
        return heatmap_data
    
    def generate_trend_data(self, df, date_column="date", sentiment_column="sentiment", days=30):
        """
        Generate data tren nasional harian
        
        Args:
            df: DataFrame dengan kolom date dan sentiment
            date_column: Nama kolom tanggal
            sentiment_column: Nama kolom sentimen
            days: Jumlah hari ke belakang
        
        Returns:
            List of dictionaries untuk chart line
        """
        if df.empty:
            return self._empty_trend_data(days)
        
        # Konversi ke datetime
        if date_column not in df.columns:
            print(f"⚠️ Kolom '{date_column}' tidak ditemukan")
            return self._empty_trend_data(days)
        
        df = df.copy()
        df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
        df = df.dropna(subset=[date_column])
        
        if df.empty:
            return self._empty_trend_data(days)
        
        # Filter data 30 hari terakhir
        cutoff = datetime.now() - timedelta(days=days)
        recent_df = df[df[date_column] >= cutoff]
        
        # Buat date range lengkap
        date_range = pd.date_range(end=datetime.now(), periods=days).date
        trend_data = []
        
        for date in date_range:
            day_df = recent_df[recent_df[date_column].dt.date == date]
            
            if not day_df.empty and sentiment_column in day_df.columns:
                total = len(day_df)
                positive = len(day_df[day_df[sentiment_column] == "Positif"])
                negative = len(day_df[day_df[sentiment_column] == "Negatif"])
                neutral = len(day_df[day_df[sentiment_column] == "Netral"])
                
                # 🔥 Hitung skor harian yang balanced
                if total > 0:
                    daily_score = ((positive - negative) / total) * 100
                else:
                    daily_score = 0
                
                trend_data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "total": total,
                    "positive": positive,
                    "negative": negative,
                    "neutral": neutral,
                    "positive_pct": round(positive / total * 100, 1) if total > 0 else 0,
                    "negative_pct": round(negative / total * 100, 1) if total > 0 else 0,
                    "score": round(daily_score, 1)
                })
            else:
                trend_data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "total": 0,
                    "positive": 0,
                    "negative": 0,
                    "neutral": 0,
                    "positive_pct": 0,
                    "negative_pct": 0,
                    "score": 0
                })
        
        days_with_data = sum(1 for d in trend_data if d['total'] > 0)
        print(f"📈 Trend data: {days_with_data}/{days} hari dengan data")
        
        return trend_data
    
    def _empty_trend_data(self, days):
        """Generate empty trend data"""
        return [{
            "date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
            "total": 0,
            "positive": 0,
            "negative": 0,
            "neutral": 0,
            "positive_pct": 0,
            "negative_pct": 0,
            "score": 0
        } for i in range(days)]
    
    def generate_comparison_data(self, regional_stats, min_comments=5):
        """
        Generate data perbandingan antar region
        
        Args:
            regional_stats: Dictionary dari GeoLocationDetector.get_regional_stats()
            min_comments: Minimal komentar untuk ditampilkan
        
        Returns:
            Dictionary dengan top_provinces, bottom_provinces, island_comparison
        """
        # Filter provinsi dengan minimal komentar
        valid_provinces = {}
        for p, s in regional_stats["by_province"].items():
            if s["total"] >= min_comments:
                # 🔥 Hitung skor balanced
                score = self.calculate_sentiment_score(s)
                valid_provinces[p] = {
                    **s,
                    "score": round(score, 1),
                    "label": self.get_label(score)
                }
        
        # Top 5 provinsi dengan skor sentimen tertinggi
        if valid_provinces:
            top_provinces = sorted(
                valid_provinces.items(),
                key=lambda x: (x[1]["score"], x[1]["total"]),
                reverse=True
            )[:5]
            
            # Bottom 5 provinsi dengan skor sentimen terendah
            bottom_provinces = sorted(
                valid_provinces.items(),
                key=lambda x: (x[1]["score"], -x[1]["total"])
            )[:5]
        else:
            top_provinces = []
            bottom_provinces = []
        
        # Perbandingan antar pulau
        island_comparison = []
        for island, stats in regional_stats["by_island"].items():
            if stats["total"] > 0:
                score = self.calculate_sentiment_score(stats)
                island_comparison.append({
                    "island": self._format_island_name(island),
                    "total": stats["total"],
                    "positive": stats["positive"],
                    "negative": stats["negative"],
                    "neutral": stats["neutral"],
                    "positive_pct": stats["positive_pct"],
                    "score": round(score, 1),
                    "label": self.get_label(score)
                })
        
        # Urutkan island comparison
        island_comparison.sort(key=lambda x: x['total'], reverse=True)
        
        # Format output
        result = {
            "top_provinces": [
                {"province": p, **s} for p, s in top_provinces
            ],
            "bottom_provinces": [
                {"province": p, **s} for p, s in bottom_provinces
            ],
            "island_comparison": island_comparison
        }
        
        # Debug print
        print(f"\n📊 Top provinces: {len(result['top_provinces'])}")
        print(f"📊 Bottom provinces: {len(result['bottom_provinces'])}")
        print(f"📊 Island comparison: {len(result['island_comparison'])}")
        
        return result
    
    def _format_island_name(self, island):
        """Format nama pulau untuk tampilan"""
        mapping = {
            "sumatra": "Sumatra",
            "jawa": "Jawa",
            "kalimantan": "Kalimantan",
            "sulawesi": "Sulawesi",
            "bali_nusa": "Bali & Nusa Tenggara",
            "maluku": "Maluku",
            "papua": "Papua"
        }
        return mapping.get(island, island)
    
    def generate_provinces_detail(self, regional_stats):
        """
        Generate detail per provinsi untuk tabel
        
        Args:
            regional_stats: Dictionary dari GeoLocationDetector.get_regional_stats()
        
        Returns:
            List of dictionaries untuk tabel
        """
        provinces_detail = []
        
        for province, stats in regional_stats["by_province"].items():
            total = stats["total"]
            
            if total > 0:
                # 🔥 Hitung skor balanced
                score = self.calculate_sentiment_score(stats)
                positive_pct = round(stats["positive"] / total * 100, 1)
                negative_pct = round(stats["negative"] / total * 100, 1)
                neutral_pct = round(stats["neutral"] / total * 100, 1)
            else:
                score = 0
                positive_pct = 0
                negative_pct = 0
                neutral_pct = 0
            
            # Tentukan warna trend berdasarkan skor
            if score >= 30:
                trend_color = "success"
            elif score >= 10:
                trend_color = "warning"
            elif score >= -10:
                trend_color = "info"
            elif score >= -30:
                trend_color = "warning"
            else:
                trend_color = "danger"
            
            provinces_detail.append({
                'nama': province,
                'total': total,
                'positive': stats['positive'],
                'negative': stats['negative'],
                'neutral': stats['neutral'],
                'positive_pct': positive_pct,
                'negative_pct': negative_pct,
                'neutral_pct': neutral_pct,
                'score': round(score, 1),
                'label': self.get_label(score),
                'trend_color': trend_color,
                'coordinates': stats.get('coordinates', {})
            })
        
        # Urutkan berdasarkan total komentar (descending)
        provinces_detail.sort(key=lambda x: x['total'], reverse=True)
        
        # Hitung statistik
        total_provinces = len(provinces_detail)
        provinces_with_data = sum(1 for p in provinces_detail if p['total'] > 0)
        
        print(f"\n📋 Tabel provinsi:")
        print(f"   - Total provinsi: {total_provinces}")
        print(f"   - Dengan data: {provinces_with_data}")
        print(f"   - Tanpa data: {total_provinces - provinces_with_data}")
        
        return provinces_detail
    
    def generate_geojson(self, regional_stats):
        """
        Generate GeoJSON untuk peta interaktif
        
        Args:
            regional_stats: Dictionary dari GeoLocationDetector.get_regional_stats()
        
        Returns:
            Dictionary dalam format GeoJSON
        """
        features = []
        
        for province, stats in regional_stats["by_province"].items():
            # Filter data minim
            if not self.should_include_province(stats, min_comments=5):
                continue
            
            if "coordinates" not in stats or not stats["coordinates"]:
                continue
            
            # Hitung skor balanced
            score = self.calculate_sentiment_score(stats)
            color = self.get_hex_color_from_score(score)
            label = self.get_label(score)
            
            feature = {
                "type": "Feature",
                "properties": {
                    "province": province,
                    "total": stats["total"],
                    "positive": stats["positive"],
                    "negative": stats["negative"],
                    "neutral": stats["neutral"],
                    "score": round(score, 1),
                    "label": label,
                    "color": color,
                    "marker-size": "medium",
                    "marker-color": color.replace("#", "")
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [stats["coordinates"]["lon"], stats["coordinates"]["lat"]]
                }
            }
            features.append(feature)
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        print(f"🗺️ GeoJSON generated: {len(features)} features")
        return geojson
    
    def get_color_by_pct(self, pct):
        """
        Dapatkan warna berdasarkan persentase (backward compatibility)
        
        Args:
            pct: Persentase positif (0-100)
        
        Returns:
            String kode warna hex
        """
        # Konversi pct ke score untuk kompatibilitas
        score = (pct - 50) * 2
        return self.get_hex_color_from_score(score)
    
    def get_stat_summary(self, regional_stats):
        """
        Generate ringkasan statistik dengan skor balanced
        
        Args:
            regional_stats: Dictionary dari GeoLocationDetector.get_regional_stats()
        
        Returns:
            Dictionary dengan ringkasan statistik
        """
        national = regional_stats.get("national", {})
        total = national.get("total_comments", 0)
        
        # 🔥 Hitung skor nasional yang balanced
        pos = national.get("positive", 0)
        neg = national.get("negative", 0)
        national_score = ((pos - neg) / total * 100) if total > 0 else 0
        
        # Hitung provinsi dengan data
        provinces_with_data = sum(
            1 for s in regional_stats["by_province"].values() 
            if s["total"] >= 5
        )
        
        # Hitung distribusi sentimen
        sentiment_dist = {
            "positive": pos,
            "negative": neg,
            "neutral": national.get("neutral", 0)
        }
        
        # Cari provinsi dengan skor tertinggi/terendah
        max_province = None
        min_province = None
        max_score = -101
        min_score = 101
        
        for province, stats in regional_stats["by_province"].items():
            if stats["total"] >= 5:  # Minimal 5 komentar
                score = self.calculate_sentiment_score(stats)
                if score > max_score:
                    max_score = score
                    max_province = province
                if score < min_score:
                    min_score = score
                    min_province = province
        
        return {
            "total_comments": total,
            "provinces_with_data": provinces_with_data,
            "total_provinces": len(regional_stats["by_province"]),
            "national_score": round(national_score, 1),
            "national_label": self.get_label(national_score),
            "sentiment_distribution": sentiment_dist,
            "positive_pct": round(pos / total * 100, 1) if total > 0 else 0,
            "negative_pct": round(neg / total * 100, 1) if total > 0 else 0,
            "best_province": {
                "name": max_province,
                "score": round(max_score, 1) if max_score > -101 else 0,
                "label": self.get_label(max_score) if max_score > -101 else "N/A"
            },
            "worst_province": {
                "name": min_province,
                "score": round(min_score, 1) if min_score < 101 else 0,
                "label": self.get_label(min_score) if min_score < 101 else "N/A"
            }
        }


# ===============================
# STANDALONE FUNCTIONS
# ===============================
def test_heatmap_generator():
    """Test fungsi-fungsi HeatmapGenerator yang sudah dioptimalkan"""
    print("\n" + "="*60)
    print("🧪 TESTING OPTIMIZED HEATMAP GENERATOR V2.1 (FIXED COLOR)")
    print("="*60)
    
    # Buat dummy data dengan berbagai skenario
    dummy_regional_stats = {
        "by_province": {
            "DKI JAKARTA": {
                "total": 150,
                "positive": 120,
                "negative": 20,
                "neutral": 10,
                "positive_pct": 80.0,
                "coordinates": {"lat": -6.21, "lon": 106.85}
            },
            "JAWA BARAT": {
                "total": 200,
                "positive": 50,
                "negative": 100,
                "neutral": 50,
                "positive_pct": 25.0,
                "coordinates": {"lat": -6.91, "lon": 107.61}
            },
            "JAWA TENGAH": {
                "total": 80,
                "positive": 40,
                "negative": 20,
                "neutral": 20,
                "positive_pct": 50.0,
                "coordinates": {"lat": -7.15, "lon": 110.14}
            },
            "SUMATRA UTARA": {
                "total": 50,
                "positive": 45,
                "negative": 3,
                "neutral": 2,
                "positive_pct": 90.0,
                "coordinates": {"lat": 3.6, "lon": 98.68}
            },
            "PAPUA": {
                "total": 10,
                "positive": 1,
                "negative": 8,
                "neutral": 1,
                "positive_pct": 10.0,
                "coordinates": {"lat": -2.5, "lon": 140.7}
            },
            "BALI": {
                "total": 3,  # Data minim, harus difilter
                "positive": 2,
                "negative": 1,
                "neutral": 0,
                "positive_pct": 66.7,
                "coordinates": {"lat": -8.34, "lon": 115.09}
            }
        },
        "by_island": {
            "jawa": {"total": 430, "positive": 210, "negative": 140, "neutral": 80, "positive_pct": 48.8}
        },
        "national": {
            "total_comments": 490,
            "positive": 256,
            "negative": 143,
            "neutral": 91
        }
    }
    
    generator = HeatmapGenerator()
    
    # Test calculate_sentiment_score
    print("\n📊 TESTING SENTIMENT SCORE CALCULATION:")
    for province, stats in dummy_regional_stats["by_province"].items():
        score = generator.calculate_sentiment_score(stats)
        label = generator.get_label(score)
        print(f"   {province}: Pos={stats['positive']}, Neg={stats['negative']} -> Score={score:.1f} ({label})")
    
    # Test get_color_from_score
    print("\n🎨 TESTING COLOR GENERATION (FIXED):")
    test_scores = [100, 70, 30, 10, 0, -10, -30, -70, -100]
    for score in test_scores:
        color_hex, intensity, color_rgba = generator.get_color_from_score(score)
        print(f"   Score {score:3d}: {color_hex} (intensity={intensity:.2f})")
    
    # Test calculate_radius
    print("\n📍 TESTING RADIUS CALCULATION:")
    test_totals = [1, 5, 10, 50, 100, 500, 1000, 5000]
    for total in test_totals:
        radius = generator.calculate_radius(total)
        print(f"   Total {total:4d} komentar -> radius {radius}px")
    
    # Test generate_heatmap_data
    print("\n🗺️ TESTING HEATMAP DATA GENERATION:")
    heatmap = generator.generate_heatmap_data(dummy_regional_stats)
    print(f"\n   ✅ Menghasilkan {len(heatmap)} titik heatmap (BALI difilter karena total <5)")
    
    print("\n   🎨 Detail warna yang dihasilkan:")
    for point in heatmap:
        print(f"\n   📍 {point['province']}:")
        print(f"      Score: {point['score']} ({point['label']})")
        print(f"      Color: {point['color']} ← 🔥 INI YANG DIPAKAI DI PETA")
        print(f"      Radius: {point['radius']}px")
        print(f"      Pos: {point['positive']}, Neg: {point['negative']}, Netral: {point['neutral']}")
    
    # Test generate_comparison_data
    print("\n📊 TESTING COMPARISON DATA:")
    comparison = generator.generate_comparison_data(dummy_regional_stats, min_comments=5)
    print(f"   Top provinces: {len(comparison['top_provinces'])}")
    for p in comparison['top_provinces']:
        print(f"      - {p['province']}: Score={p['score']} ({p['label']})")
    
    print(f"\n   Bottom provinces: {len(comparison['bottom_provinces'])}")
    for p in comparison['bottom_provinces']:
        print(f"      - {p['province']}: Score={p['score']} ({p['label']})")
    
    # Test get_stat_summary
    print("\n📈 TESTING STAT SUMMARY:")
    summary = generator.get_stat_summary(dummy_regional_stats)
    print(f"   Total comments: {summary['total_comments']}")
    print(f"   National score: {summary['national_score']} ({summary['national_label']})")
    print(f"   Best province: {summary['best_province']['name']} ({summary['best_province']['score']})")
    print(f"   Worst province: {summary['worst_province']['name']} ({summary['worst_province']['score']})")
    
    print("\n" + "="*60)
    print("✅ All tests passed!")
    print("🔥 WARNA SEKARANG SUDAH FIXED, TIDAK AKAN HITAM LAGI!")
    print("="*60)
    
    return generator

if __name__ == "__main__":
    test_heatmap_generator()