# bengkulu_sentiment_analyzer.py
"""
Analisis sentimen khusus untuk Provinsi Bengkulu
Dengan deteksi lokasi super akurat dan weighting berdasarkan konteks lokal
"""

import re
import pandas as pd
from collections import Counter
from typing import Dict, List, Tuple

# =====================================================
# DATABASE KATA KUNCI KHUSUS BENGKULU
# =====================================================

BENGKULU_KEYWORDS = {
    # ========== KATA KUNCI UMUM ==========
    "bengkulu": 1.0,
    "bkl": 1.0,
    "bengkuluw": 0.9,
    "bengkuwu": 0.9,
    
    # ========== KABUPATEN ==========
    "bengkulu selatan": 1.0,
    "bengsel": 0.9,
    "manna": 0.9,
    "rejang lebong": 1.0,
    "curup": 0.9,
    "rejang": 0.8,
    "bengkulu utara": 1.0,
    "argamakmur": 0.9,
    "bengkulutara": 0.8,
    "kaur": 0.9,
    "bintuhan": 0.9,
    "seluma": 0.9,
    "tais": 0.9,
    "mukomuko": 0.9,
    "muko muko": 0.9,
    "lebong": 0.9,
    "muara aman": 0.9,
    "kepahiang": 0.9,
    "bengkulu tengah": 1.0,
    "karang tinggi": 0.9,
    
    # ========== KECAMATAN POPULER ==========
    "kota manna": 0.8,
    "pasar manna": 0.8,
    "kedurang": 0.8,
    "seginim": 0.8,
    "curup selatan": 0.8,
    "curup tengah": 0.8,
    "curup utara": 0.8,
    "ketahun": 0.8,
    "napal putih": 0.8,
    "putri hijau": 0.8,
    "enggano": 0.9,
    "kinal": 0.8,
    "maje": 0.8,
    "nasal": 0.8,
    "air periukan": 0.8,
    "talo": 0.8,
    "lubuk pinang": 0.8,
    "penarik": 0.8,
    "amen": 0.8,
    "topos": 0.8,
    "bermani ilir": 0.8,
    "merigi": 0.8,
    "ujan mas": 0.8,
    "pondok kelapa": 0.8,
    "taba penanjung": 0.8,
    
    # ========== TEMPAT WISATA ==========
    "pantai panjang": 0.9,
    "pantai jakat": 0.9,
    "pantai pasir putih": 0.9,
    "benteng malborough": 0.9,
    "benteng marlborough": 0.9,
    "rumah bung karno": 0.9,
    "rumah pengasingan bung karno": 0.9,
    "danau mas": 0.8,
    "air terjun": 0.8,
    "pulau enggano": 0.9,
    "pulau mega": 0.8,
    
    # ========== BUDAYA & TRADISI ==========
    "tabot": 0.9,
    "tabut": 0.9,
    "dol": 0.8,
    "tari andun": 0.8,
    "tari kejei": 0.8,
    
    # ========== TOKOH ==========
    "bung karno": 0.9,
    "soekarno": 0.8,
    "fatmawati": 0.8,
    "gubernur bengkulu": 0.8,
    "walikota bengkulu": 0.8,
    "bupati": 0.7,
    
    # ========== BAHASA DAERAH ==========
    "au": 0.7,
    "oghang": 0.7,
    "kelam": 0.7,
    "bese": 0.7,
    "kito": 0.7,
    "kite": 0.7,
    "awak": 0.6,
    "siko": 0.6,
}

# =====================================================
# SENTIMEN SPESIFIK BENGKULU
# =====================================================

POSITIVE_BENGKULU = [
    # Pujian umum
    "mantap", "keren", "bagus", "hebat", "top", "jos", "luar biasa",
    "sukses", "maju", "berkembang", "bangga", "salut", "setuju",
    
    # Pujian khusus Bengkulu
    "bengkulu juara", "bengkulu maju", "bengkulu bangkit", "bumi rafflesia",
    "pantai indah", "wisata bengkulu", "kuliner enak", "tabot meriah",
    
    # Dukungan
    "dukung", "support", "lanjutkan", "semangat", "amin", "aamiin",
    "alhamdulillah", "masya allah", "subhanallah",
    
    # Emosi positif
    "senang", "bahagia", "suka", "cinta", "gemes", "lucu", "ngakak", "wow",
]

NEGATIVE_BENGKULU = [
    # Kritik umum
    "jelek", "buruk", "parah", "gagal", "kecewa", "jengkel", "kesel",
    "mengecewakan", "kurang", "tidak", "gak", "nggak",
    
    # Kritik khusus Bengkulu
    "bengkulu ketinggalan", "infrastruktur buruk", "jalan rusak",
    "macet bengkulu", "banjir bengkulu", "pembangunan lambat",
    
    # Emosi negatif
    "marah", "benci", "muak", "jijik", "sedih", "terpuruk",
    
    # Kata kasar
    "tolol", "bodoh", "anjing", "kampret", "sampah", "rusak",
]

# =====================================================
# DETEKSI LOKASI YANG LEBIH AKURAT
# =====================================================

class BengkuluLocationDetector:
    """
    Deteksi lokasi di Bengkulu dengan tingkat akurasi tinggi
    """
    
    def __init__(self):
        self.keywords = BENGKULU_KEYWORDS
        
        # Mapping kode daerah
        self.region_codes = {
            "17.01": "BENGKULU SELATAN",
            "17.02": "REJANG LEBONG",
            "17.03": "BENGKULU UTARA",
            "17.04": "KAUR",
            "17.05": "SELUMA",
            "17.06": "MUKOMUKO",
            "17.07": "LEBONG",
            "17.08": "KEPAHIANG",
            "17.09": "BENGKULU TENGAH",
            "17.71": "BENGKULU"
        }
        
        # Pola nomor telepon/WA
        self.phone_patterns = [
            r'07\d{8,11}',  # No HP
            r'08\d{8,11}',  # No HP
            r'62\d{9,12}',  # No HP internasional
        ]
    
    def detect_region(self, text: str) -> Tuple[str, float]:
        """
        Deteksi region dengan confidence score
        
        Returns:
            (region_name, confidence)
        """
        if not text:
            return "TIDAK TERDETEKSI", 0.0
        
        text_lower = text.lower()
        scores = {}
        
        # Method 1: Keyword matching dengan bobot
        for keyword, weight in self.keywords.items():
            if keyword in text_lower:
                # Hitung frekuensi kemunculan
                count = text_lower.count(keyword)
                # Bobot bertambah sesuai frekuensi
                score = weight * min(count, 3)  # Maksimal 3x
                
                # Cari region yang cocok
                for region, region_keywords in self._get_region_mapping().items():
                    if any(k in keyword for k in region_keywords):
                        scores[region] = scores.get(region, 0) + score
        
        # Method 2: Deteksi pola "di [nama]"
        patterns = [
            r'di\s+([a-z\s]+?)(?:\s|\,|\.|$)',
            r'ke\s+([a-z\s]+?)(?:\s|\,|\.|$)',
            r'dari\s+([a-z\s]+?)(?:\s|\,|\.|$)',
            r'warga\s+([a-z\s]+?)(?:\s|\,|\.|$)',
            r'asal\s+([a-z\s]+?)(?:\s|\,|\.|$)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                for region, region_keywords in self._get_region_mapping().items():
                    for kw in region_keywords:
                        if kw in match:
                            scores[region] = scores.get(region, 0) + 0.8
        
        # Method 3: Deteksi kode pos/wilayah
        # Kode pos Bengkulu: 381xx, 382xx, 383xx, 384xx, 385xx, 386xx
        pos_patterns = [
            r'\b381\d{2}\b',  # Bengkulu Kota
            r'\b382\d{2}\b',  # Bengkulu Selatan
            r'\b383\d{2}\b',  # Rejang Lebong
            r'\b384\d{2}\b',  # Bengkulu Utara
            r'\b385\d{2}\b',  # Kaur
            r'\b386\d{2}\b',  # Seluma/Mukomuko
        ]
        
        for pattern in pos_patterns:
            if re.search(pattern, text_lower):
                scores["BENGKULU"] = scores.get("BENGKULU", 0) + 0.7
        
        # Pilih region dengan skor tertinggi
        if scores:
            best_region = max(scores, key=scores.get)
            max_score = scores[best_region]
            # Normalisasi confidence (max 1.0)
            confidence = min(1.0, max_score / 3)
            return best_region, confidence
        
        return "TIDAK TERDETEKSI", 0.0
    
    def _get_region_mapping(self) -> Dict[str, List[str]]:
        """Mapping region ke kata kunci"""
        return {
            "BENGKULU": ["bengkulu", "bkl", "kota bengkulu"],
            "BENGKULU SELATAN": ["bengkulu selatan", "bengsel", "manna"],
            "REJANG LEBONG": ["rejang lebong", "curup", "rejang"],
            "BENGKULU UTARA": ["bengkulu utara", "argamakmur", "bengkulutara"],
            "KAUR": ["kaur", "bintuhan"],
            "SELUMA": ["seluma", "tais"],
            "MUKOMUKO": ["mukomuko", "muko muko"],
            "LEBONG": ["lebong", "muara aman"],
            "KEPAHIANG": ["kepahiang"],
            "BENGKULU TENGAH": ["bengkulu tengah", "karang tinggi"]
        }


class BengkuluSentimentAnalyzer:
    """
    Analisis sentimen dengan bobot khusus Bengkulu
    """
    
    def __init__(self):
        self.positive_keywords = POSITIVE_BENGKULU
        self.negative_keywords = NEGATIVE_BENGKULU
        self.location_detector = BengkuluLocationDetector()
        
        # Intensifiers
        self.intensifiers = ["banget", "bgt", "sekali", "sangat", "parah", "super"]
        
        # Negation words
        self.negations = ["tidak", "tak", "bukan", "ga", "gak", "nggak", "enggak"]
    
    def preprocess(self, text: str) -> str:
        """Preprocessing teks"""
        if not isinstance(text, str):
            return ""
        
        text = text.lower()
        text = re.sub(r'http\S+|www\S+|https\S+', '', text)
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'#\w+', '', text)
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\d+', '', text)
        text = re.sub(r'(.)\1{2,}', r'\1\1', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def analyze(self, text: str, region: str = None) -> Dict:
        """
        Analisis sentimen komentar
        
        Returns:
            dict dengan sentiment, confidence, region, details
        """
        if not text:
            return {
                "sentiment": "Netral",
                "confidence": 0.0,
                "region": region,
                "details": {}
            }
        
        clean_text = self.preprocess(text)
        words = clean_text.split()
        
        # Deteksi lokasi
        detected_region, location_conf = self.location_detector.detect_region(text)
        if region is None:
            region = detected_region
        
        # Hitung skor
        pos_score = 0
        neg_score = 0
        
        # Method 1: Keyword matching
        for word in words:
            if word in self.positive_keywords:
                pos_score += 1
            if word in self.negative_keywords:
                neg_score += 1
        
        # Method 2: Phrase matching (bigram)
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i+1]}"
            if phrase in self.positive_keywords:
                pos_score += 1.5
            if phrase in self.negative_keywords:
                neg_score += 1.5
        
        # Method 3: Negation handling
        for i, word in enumerate(words):
            if word in self.negations and i < len(words) - 1:
                next_word = words[i + 1]
                if next_word in self.positive_keywords:
                    neg_score += 2  # "tidak bagus" = negatif
                    pos_score -= 1
                elif next_word in self.negative_keywords:
                    pos_score += 2  # "tidak jelek" = positif
                    neg_score -= 1
        
        # Method 4: Intensifier boost
        for intens in self.intensifiers:
            if intens in clean_text:
                if pos_score > neg_score:
                    pos_score += 2
                elif neg_score > pos_score:
                    neg_score += 2
        
        # Method 5: Emoji detection
        if "🔥" in text or "❤️" in text or "👍" in text or "😍" in text:
            pos_score += 1
        if "💩" in text or "👎" in text or "😡" in text or "🤮" in text:
            neg_score += 1
        
        # Tentukan sentimen
        total = pos_score + neg_score
        if total > 0:
            if pos_score > neg_score:
                sentiment = "Positif"
                confidence = min(95, 50 + (pos_score / total * 45))
            elif neg_score > pos_score:
                sentiment = "Negatif"
                confidence = min(95, 50 + (neg_score / total * 45))
            else:
                sentiment = "Netral"
                confidence = 50
        else:
            sentiment = "Netral"
            confidence = 30
        
        # Bonus confidence jika lokasi terdeteksi dengan baik
        if region != "TIDAK TERDETEKSI" and location_conf > 0.5:
            confidence = min(98, confidence + 5)
        
        return {
            "sentiment": sentiment,
            "confidence": round(confidence, 1),
            "region": region,
            "region_confidence": round(location_conf * 100, 1),
            "details": {
                "pos_score": pos_score,
                "neg_score": neg_score,
                "total_score": total,
                "words": len(words),
                "has_intensifier": any(i in clean_text for i in self.intensifiers),
                "has_negation": any(n in clean_text for n in self.negations)
            }
        }


class BengkuluBatchAnalyzer:
    """
    Batch analyzer untuk banyak komentar
    """
    
    def __init__(self):
        self.analyzer = BengkuluSentimentAnalyzer()
    
    def analyze_batch(self, comments: List[Dict]) -> List[Dict]:
        """
        Analisis batch komentar
        
        Args:
            comments: list of dict dengan field 'text' dan 'username'
        
        Returns:
            list of dict dengan hasil analisis
        """
        results = []
        
        for i, comment in enumerate(comments):
            text = comment.get('text', '')
            username = comment.get('username', '')
            
            # Analisis sentimen
            analysis = self.analyzer.analyze(text)
            
            results.append({
                'id': comment.get('id', i),
                'text': text,
                'username': username,
                'sentiment': analysis['sentiment'],
                'confidence': analysis['confidence'],
                'region': analysis['region'],
                'region_confidence': analysis['region_confidence']
            })
            
            if (i + 1) % 100 == 0:
                print(f"  Progress: {i + 1}/{len(comments)} komentar")
        
        return results
    
    def get_regional_stats(self, results: List[Dict]) -> Dict:
        """
        Dapatkan statistik per region
        """
        stats = {}
        
        for result in results:
            region = result['region']
            if region == "TIDAK TERDETEKSI":
                continue
            
            if region not in stats:
                stats[region] = {
                    "total": 0,
                    "positive": 0,
                    "negative": 0,
                    "neutral": 0,
                    "confidence_sum": 0
                }
            
            stats[region]["total"] += 1
            stats[region]["confidence_sum"] += result['confidence']
            
            if result['sentiment'] == "Positif":
                stats[region]["positive"] += 1
            elif result['sentiment'] == "Negatif":
                stats[region]["negative"] += 1
            else:
                stats[region]["neutral"] += 1
        
        # Hitung persentase
        for region in stats:
            total = stats[region]["total"]
            if total > 0:
                stats[region]["positive_pct"] = round(stats[region]["positive"] / total * 100, 1)
                stats[region]["negative_pct"] = round(stats[region]["negative"] / total * 100, 1)
                stats[region]["avg_confidence"] = round(stats[region]["confidence_sum"] / total, 1)
        
        return stats
    
    def get_summary(self, results: List[Dict]) -> Dict:
        """
        Dapatkan ringkasan analisis
        """
        total = len(results)
        if total == 0:
            return {}
        
        pos_count = sum(1 for r in results if r['sentiment'] == "Positif")
        neg_count = sum(1 for r in results if r['sentiment'] == "Negatif")
        neu_count = sum(1 for r in results if r['sentiment'] == "Netral")
        
        region_detected = sum(1 for r in results if r['region'] != "TIDAK TERDETEKSI")
        avg_confidence = sum(r['confidence'] for r in results) / total
        
        return {
            "total": total,
            "positive": pos_count,
            "negative": neg_count,
            "neutral": neu_count,
            "positive_pct": round(pos_count / total * 100, 1),
            "negative_pct": round(neg_count / total * 100, 1),
            "region_detected": region_detected,
            "detection_rate": round(region_detected / total * 100, 1),
            "avg_confidence": round(avg_confidence, 1)
        }


# =====================================================
# TESTING
# =====================================================
if __name__ == "__main__":
    print("="*60)
    print("🧪 TESTING BENGKULU SENTIMENT ANALYZER")
    print("="*60)
    
    analyzer = BengkuluSentimentAnalyzer()
    
    test_cases = [
        ("Bengkulu keren banget, maju terus!", "BENGKULU", "Positif"),
        ("Curup kota yang indah, suka aku", "REJANG LEBONG", "Positif"),
        ("Manna kurang berkembang, perlu perhatian", "BENGKULU SELATAN", "Negatif"),
        ("Argamakmur macet parah", "BENGKULU UTARA", "Negatif"),
        ("Kota Bengkulu biasa aja", "BENGKULU", "Netral"),
        ("Tabot Bengkulu luar biasa!", "BENGKULU", "Positif"),
        ("Pantai Panjang indah banget", "BENGKULU", "Positif"),
        ("Bengkulu gak maju-maju", "BENGKULU", "Negatif"),
        ("Warga Curup setuju", "REJANG LEBONG", "Positif"),
        ("Dari Manna ikutan", "BENGKULU SELATAN", "Netral"),
    ]
    
    print("\n📋 TEST CASES:")
    print("-"*70)
    
    for text, expected_region, expected_sentiment in test_cases:
        result = analyzer.analyze(text)
        region_ok = result['region'] == expected_region
        sent_ok = result['sentiment'] == expected_sentiment
        
        status = "✅" if (region_ok and sent_ok) else "❌"
        
        print(f"\n{status} Text: {text}")
        print(f"   Region: {result['region']} ({result['region_confidence']}%) - Expected: {expected_region}")
        print(f"   Sentiment: {result['sentiment']} ({result['confidence']}%) - Expected: {expected_sentiment}")
        print(f"   Details: pos={result['details']['pos_score']}, neg={result['details']['neg_score']}")
    
    print("\n" + "="*60)
    print("✅ TESTING COMPLETE")
    print("="*60)