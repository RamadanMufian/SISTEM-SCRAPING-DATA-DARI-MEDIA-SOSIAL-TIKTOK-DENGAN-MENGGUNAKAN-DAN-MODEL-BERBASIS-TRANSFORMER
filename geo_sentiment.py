# geo_sentiment.py - AGGRESSIVE VERSION FOR SUMATRA
"""
Geolocation detection untuk komentar media sosial
DENGAN FOKUS KHUSUS SUMATRA & BENGKULU
"""

import re
import pandas as pd
from regions import LOCATION_KEYWORDS, get_province_from_city, get_island_from_province, INDONESIAN_REGIONS

class GeoLocationDetector:
    """
    Deteksi lokasi dari berbagai sumber dengan FOKUS SUMATRA
    """
    
    def __init__(self):
        self.location_keywords = LOCATION_KEYWORDS
        self.province_data = INDONESIAN_REGIONS["provinsi"]
        self.cities_data = INDONESIAN_REGIONS["kota_besar"]
        self.stats = {
            "total_detected": 0,
            "by_source": {},
            "by_confidence": {}
        }
        
        # ========== DATABASE KHUSUS SUMATRA ==========
        self.sumatra_provinces = {
            # ACEH
            'aceh': 'ACEH', 'banda aceh': 'ACEH', 'aceh besar': 'ACEH', 'serambi mekkah': 'ACEH',
            'lhong': 'ACEH', 'sigli': 'ACEH', 'takengon': 'ACEH', 'langsa': 'ACEH', 'lhokseumawe': 'ACEH',
            'sabang': 'ACEH', 'subulussalam': 'ACEH', 'gayo': 'ACEH', 'meulaboh': 'ACEH',
            
            # SUMATERA UTARA
            'medan': 'SUMATERA UTARA', 'sumut': 'SUMATERA UTARA', 'tanah deli': 'SUMATERA UTARA',
            'binjai': 'SUMATERA UTARA', 'pematang siantar': 'SUMATERA UTARA', 'tanjung balai': 'SUMATERA UTARA',
            'tebing tinggi': 'SUMATERA UTARA', 'sibolga': 'SUMATERA UTARA', 'padang sidempuan': 'SUMATERA UTARA',
            'danau toba': 'SUMATERA UTARA', 'parapat': 'SUMATERA UTARA', 'berastagi': 'SUMATERA UTARA',
            'karo': 'SUMATERA UTARA', 'simalungun': 'SUMATERA UTARA', 'tapanuli': 'SUMATERA UTARA',
            'mandailing': 'SUMATERA UTARA', 'batak': 'SUMATERA UTARA', 'horas': 'SUMATERA UTARA',
            
            # SUMATERA BARAT
            'padang': 'SUMATERA BARAT', 'sumbar': 'SUMATERA BARAT', 'ranah minang': 'SUMATERA BARAT',
            'bukittinggi': 'SUMATERA BARAT', 'payakumbuh': 'SUMATERA BARAT', 'pariaman': 'SUMATERA BARAT',
            'sawahlunto': 'SUMATERA BARAT', 'solok': 'SUMATERA BARAT', 'padang panjang': 'SUMATERA BARAT',
            'minangkabau': 'SUMATERA BARAT', 'minang': 'SUMATERA BARAT', 'urang awak': 'SUMATERA BARAT',
            'pasaman': 'SUMATERA BARAT', 'agamo': 'SUMATERA BARAT', 'tanah datar': 'SUMATERA BARAT',
            
            # RIAU
            'pekanbaru': 'RIAU', 'riau': 'RIAU', 'pku': 'RIAU', 'bengkalis': 'RIAU', 'dumai': 'RIAU',
            'siak': 'RIAU', 'kampar': 'RIAU', 'pelalawan': 'RIAU', 'rokan': 'RIAU', 'kepulauan meranti': 'RIAU',
            'indragiri': 'RIAU', 'kuansing': 'RIAU', 'melayu': 'RIAU', 'lanang': 'RIAU',
            
            # JAMBI
            'jambi': 'JAMBI', 'batanghari': 'JAMBI', 'sungai penuh': 'JAMBI', 'kerinci': 'JAMBI',
            'bungo': 'JAMBI', 'tebo': 'JAMBI', 'muaro jambi': 'JAMBI', 'sarolangun': 'JAMBI',
            'merangin': 'JAMBI', 'tanjung jabung': 'JAMBI',
            
            # SUMATERA SELATAN
            'palembang': 'SUMATERA SELATAN', 'sumsel': 'SUMATERA SELATAN', 'bumi sriwijaya': 'SUMATERA SELATAN',
            'lubuklinggau': 'SUMATERA SELATAN', 'prabumulih': 'SUMATERA SELATAN', 'pagardewa': 'SUMATERA SELATAN',
            'ogan': 'SUMATERA SELATAN', 'musi': 'SUMATERA SELATAN', 'sriwijaya': 'SUMATERA SELATAN',
            'emerald': 'SUMATERA SELATAN', 'banyuasin': 'SUMATERA SELATAN',
            
            # ========== BENGKULU (FOKUS UTAMA) ==========
            'bengkulu': 'BENGKULU', 'bkl': 'BENGKULU', 'bengkuluw': 'BENGKULU', 'bengkuwu': 'BENGKULU',
            'provinsi bengkulu': 'BENGKULU', 'kota bengkulu': 'BENGKULU', 'bungo': 'BENGKULU',
            'bengkoelen': 'BENGKULU', 'benkoelen': 'BENGKULU', 'bengkoe': 'BENGKULU',
            
            # Kabupaten di Bengkulu
            'rejang lebong': 'BENGKULU', 'rejang': 'BENGKULU', 'curup': 'BENGKULU', 'lebong': 'BENGKULU',
            'kepahiang': 'BENGKULU', 'kepahiang': 'BENGKULU', 'seluma': 'BENGKULU', 'tais': 'BENGKULU',
            'muko muko': 'BENGKULU', 'mukomuko': 'BENGKULU', 'kaur': 'BENGKULU', 'bintuhan': 'BENGKULU',
            'bengkulu utara': 'BENGKULU', 'bengkulu selatan': 'BENGKULU', 'bengkulu tengah': 'BENGKULU',
            
            # Destinasi di Bengkulu
            'pantai panjang': 'BENGKULU', 'pantai jakat': 'BENGKULU', 'pantai pasir putih': 'BENGKULU',
            'danau mas': 'BENGKULU', 'air terjun': 'BENGKULU', 'benteng malborough': 'BENGKULU',
            'benteng marlborough': 'BENGKULU', 'rumah pengasingan bung karno': 'BENGKULU',
            'bung karno': 'BENGKULU', 'soekarno': 'BENGKULU',
            
            # LAMPUNG
            'lampung': 'LAMPUNG', 'bandar lampung': 'LAMPUNG', 'bdl': 'LAMPUNG', 'lampung barat': 'LAMPUNG',
            'lampung timur': 'LAMPUNG', 'lampung tengah': 'LAMPUNG', 'lampung utara': 'LAMPUNG',
            'lampung selatan': 'LAMPUNG', 'metro': 'LAMPUNG', 'kalianda': 'LAMPUNG', 'liwa': 'LAMPUNG',
            
            # KEP. BANGKA BELITUNG
            'pangkal pinang': 'KEP. BANGKA BELITUNG', 'babel': 'KEP. BANGKA BELITUNG',
            'bangka': 'KEP. BANGKA BELITUNG', 'belitung': 'KEP. BANGKA BELITUNG', 'sungailiat': 'KEP. BANGKA BELITUNG',
            'toboali': 'KEP. BANGKA BELITUNG', 'mentok': 'KEP. BANGKA BELITUNG', 'tanjung pandan': 'KEP. BANGKA BELITUNG',
            
            # KEP. RIAU
            'tanjung pinang': 'KEP. RIAU', 'kepri': 'KEP. RIAU', 'batam': 'KEP. RIAU', 'bintan': 'KEP. RIAU',
            'karimun': 'KEP. RIAU', 'lingga': 'KEP. RIAU', 'natuna': 'KEP. RIAU', 'anambas': 'KEP. RIAU',
        }
        
        # ========== VARIASI PENULISAN (UNTUK KASUS TYPO) ==========
        self.typo_variations = {
            'bengkulu': ['bengkulu', 'bengklu', 'bengkuwu', 'bengkoelo', 'bengkoe', 'bengkul', 'bngklu'],
            'medan': ['medan', 'mdn', 'meda', 'medann'],
            'padang': ['padang', 'pdg', 'padang', 'padank'],
            'pekanbaru': ['pekanbaru', 'pku', 'pekan baru', 'pekanbaro'],
            'palembang': ['palembang', 'plg', 'palem bang', 'palembang'],
            'lampung': ['lampung', 'lampong', 'lampunk', 'lmpung'],
            'aceh': ['aceh', 'ace', 'acehh', 'atjeh'],
        }
        
        # ========== KATA KUNCI KOMENTAR UNTUK SUMATRA ==========
        self.sumatra_comment_patterns = [
            # Pola dengan kata kunci provinsi
            (r'(?:di|ke|dari|warga|asal|orang)\s+(?:sumatera|sumatra)\s+(?:utara|barat|selatan|tengah)', 0.75),
            (r'(?:di|ke|dari|warga|asal|orang)\s+(?:provinsi\s+)?(?:bengkulu|aceh|riau|jambi|lampung)', 0.8),
            
            # Pola dengan nama kota
            (r'(?:di|ke|dari|warga|asal|orang)\s+(?:kota\s+)?(?:medan|padang|pekanbaru|palembang|bengkulu|bandar lampung)', 0.75),
            
            # Pola dengan kode kota
            (r'\b(?:mdn|pku|plg|bkl|pdg|bdl)\b', 0.7),
            
            # Pola dengan hashtag
            (r'#(?:bengkulu|medan|padang|pekanbaru|palembang|lampung|aceh|riau|jambi)', 0.85),
            
            # Pola dengan emoji lokasi
            (r'📍\s*(?:bengkulu|medan|padang|pekanbaru|palembang)', 0.9),
        ]
        
        # ========== KATA KUNCI KHUSUS BENGKULU ==========
        self.bengkulu_keywords = {
            # Nama daerah
            'bengkulu': 'BENGKULU', 'bkl': 'BENGKULU', 'bengkuluw': 'BENGKULU', 'bungo': 'BENGKULU',
            
            # Kabupaten/Kota
            'rejang lebong': 'BENGKULU', 'curup': 'BENGKULU', 'kepahiang': 'BENGKULU',
            'seluma': 'BENGKULU', 'muko muko': 'BENGKULU', 'mukomuko': 'BENGKULU', 'kaur': 'BENGKULU',
            'bengkulu utara': 'BENGKULU', 'bengkulu selatan': 'BENGKULU', 'bengkulu tengah': 'BENGKULU',
            
            # Tempat wisata
            'pantai panjang': 'BENGKULU', 'pantai jakat': 'BENGKULU', 'benteng malborough': 'BENGKULU',
            'benteng marlborough': 'BENGKULU', 'rumah bung karno': 'BENGKULU', 'danau mas': 'BENGKULU',
            
            # Tokoh
            'bung karno': 'BENGKULU', 'soekarno': 'BENGKULU', 'fatmawati': 'BENGKULU',
            
            # Budaya
            'tabot': 'BENGKULU', 'tabut': 'BENGKULU', 'dol': 'BENGKULU', 'tari andun': 'BENGKULU',
            
            # Bahasa daerah
            'au': 'BENGKULU', 'oghang': 'BENGKULU', 'kelam': 'BENGKULU', 'bese': 'BENGKULU',
            'kito': 'BENGKULU', 'kite': 'BENGKULU',
        }
        
        # Gabungkan semua database
        self.location_keywords.update(self.sumatra_provinces)
        self.location_keywords.update(self.bengkulu_keywords)
        
        # Database kode kota umum
        self.city_codes = {
            # Sumatra
            'mdn': 'SUMATERA UTARA', 'medan': 'SUMATERA UTARA',
            'pdg': 'SUMATERA BARAT', 'padang': 'SUMATERA BARAT',
            'pku': 'RIAU', 'pekanbaru': 'RIAU',
            'plg': 'SUMATERA SELATAN', 'palembang': 'SUMATERA SELATAN',
            'bkl': 'BENGKULU', 'bengkulu': 'BENGKULU',
            'lampung': 'LAMPUNG', 'bdl': 'LAMPUNG',
            'aceh': 'ACEH', 'bna': 'ACEH',
            'jambi': 'JAMBI',
            'pangkal pinang': 'KEP. BANGKA BELITUNG',
            'tanjung pinang': 'KEP. RIAU', 'batam': 'KEP. RIAU',
        }
        
        # Kata kunci untuk deteksi dari topik
        self.topic_keywords = {
            'banjir jakarta': 'DKI JAKARTA',
            'macet bandung': 'JAWA BARAT',
            'gunung merapi': 'DI YOGYAKARTA',
            'bromo': 'JAWA TIMUR',
            'raja ampat': 'PAPUA BARAT DAYA',
            'labuan bajo': 'NUSA TENGGARA TIMUR',
            'danau toba': 'SUMATERA UTARA',
            'kawah ijén': 'JAWA TIMUR',
            'bali': 'BALI',
            'komodo': 'NUSA TENGGARA TIMUR',
            'borobudur': 'JAWA TENGAH',
            'prambanan': 'DI YOGYAKARTA',
            
            # Topik Sumatra
            'gempa bengkulu': 'BENGKULU',
            'bencana bengkulu': 'BENGKULU',
            'pembangunan bengkulu': 'BENGKULU',
            'wisata bengkulu': 'BENGKULU',
            'pantai panjang bengkulu': 'BENGKULU',
            'benteng malborough': 'BENGKULU',
            'rumah bung karno': 'BENGKULU',
            'tabot bengkulu': 'BENGKULU',
        }
    
    def get_province_from_code(self, code):
        """Dapatkan provinsi dari kode kota"""
        return self.city_codes.get(code.lower())
    
    def detect_from_username(self, username):
        """Layer 1: Deteksi dari username - FOKUS SUMATRA"""
        result = {"province": None, "city": None, "confidence": 0, "method": None}
        
        if not username:
            return result
        
        username_lower = username.lower()
        
        # Prioritas untuk kode Sumatra
        sumatra_codes = ['mdn', 'pku', 'plg', 'bkl', 'pdg', 'bna', 'jmb', 'lmp', 'batam']
        for code in sumatra_codes:
            if code in username_lower:
                province = self.get_province_from_code(code)
                if province:
                    result["province"] = province
                    result["confidence"] = 0.75
                    result["method"] = f"sumatra_code_{code}"
                    return result
        
        # Pola 1: kode_kota diikuti angka
        match = re.search(r'([a-z]{2,5})[0-9_]+', username_lower)
        if match:
            code = match.group(1)
            province = self.get_province_from_code(code)
            if province:
                result["province"] = province
                result["confidence"] = 0.7
                result["method"] = "username_code_number"
                return result
        
        # Pola 2: _kode_kota_ (user_jkt, budi_sby)
        match = re.search(r'_([a-z]{2,5})_?', username_lower)
        if match:
            code = match.group(1)
            province = self.get_province_from_code(code)
            if province:
                result["province"] = province
                result["confidence"] = 0.7
                result["method"] = "username_underscore"
                return result
        
        # Pola 3: nama kota langsung di username
        sumatra_cities = ['bengkulu', 'medan', 'padang', 'pekanbaru', 'palembang', 'lampung', 'aceh']
        for city in sumatra_cities:
            if city in username_lower:
                province = self.get_province_from_code(city)
                if province:
                    result["province"] = province
                    result["confidence"] = 0.7
                    result["method"] = f"username_city_{city}"
                    return result
        
        return result
    
    def detect_from_display_name(self, display_name):
        """Layer 2: Deteksi dari display name - FOKUS SUMATRA"""
        result = {"province": None, "city": None, "confidence": 0, "method": None}
        
        if not display_name:
            return result
        
        text = display_name.lower()
        
        # Pola 1: Nama (Kota)
        match = re.search(r'\(([^)]+)\)', text)
        if match:
            city_candidate = match.group(1).strip()
            province = get_province_from_city(city_candidate)
            if province:
                result["province"] = province
                result["city"] = city_candidate
                result["confidence"] = 0.85
                result["method"] = "display_name_parentheses"
                return result
        
        # Pola 2: "Warga [Kota]", "Dari [Kota]", "Asal [Kota]"
        patterns = [
            (r'warga\s+([a-z\s]+)', 0.8),
            (r'dari\s+([a-z\s]+)', 0.8),
            (r'asal\s+([a-z\s]+)', 0.8),
            (r'📍\s*([a-z\s]+)', 0.85),
            (r'🏠\s*([a-z\s]+)', 0.85),
            (r'🌍\s*([a-z\s]+)', 0.8),
        ]
        
        for pattern, confidence in patterns:
            match = re.search(pattern, text)
            if match:
                city_candidate = match.group(1).strip()
                province = get_province_from_city(city_candidate)
                if province:
                    result["province"] = province
                    result["city"] = city_candidate
                    result["confidence"] = confidence
                    result["method"] = "display_name_pattern"
                    return result
        
        return result
    
    def detect_from_bio(self, bio):
        """Layer 3: Deteksi dari bio profil - FOKUS SUMATRA"""
        result = {"province": None, "city": None, "confidence": 0, "method": None}
        
        if not bio:
            return result
        
        text = bio.lower()
        
        # Pola 1: Format dengan separator
        separators = ['|', '-', '•', '/', '\\', ',', ';']
        for sep in separators:
            if sep in text:
                parts = [p.strip() for p in text.split(sep)]
                for part in parts[:3]:
                    clean_part = re.sub(r'[^\w\s]', '', part).strip()
                    if len(clean_part) > 2:
                        province = get_province_from_city(clean_part)
                        if province:
                            result["province"] = province
                            result["city"] = clean_part
                            result["confidence"] = 0.9
                            result["method"] = "bio_separator"
                            return result
        
        # Pola 2: Kata kunci lokasi
        location_keywords = [
            ('based in', 0.85), ('living in', 0.85), ('tinggal di', 0.85),
            ('📍', 0.9), ('🏠', 0.9), ('🌍', 0.85), ('from', 0.8),
        ]
        
        for keyword, confidence in location_keywords:
            if keyword in text:
                after_keyword = text.split(keyword)[-1].strip()
                words = after_keyword.split()
                if words:
                    city_candidate = words[0].strip('.,;!?')
                    province = get_province_from_city(city_candidate)
                    if province:
                        result["province"] = province
                        result["city"] = city_candidate
                        result["confidence"] = confidence
                        result["method"] = f"bio_{keyword.replace(' ', '_')}"
                        return result
        
        return result
    
    def detect_from_topic(self, text):
        """Deteksi lokasi dari topik yang dibahas"""
        result = {"province": None, "city": None, "confidence": 0, "method": None}
        
        if not text:
            return result
        
        text_lower = text.lower()
        
        for topic, province in self.topic_keywords.items():
            if topic in text_lower:
                result["province"] = province
                result["confidence"] = 0.7
                result["method"] = "topic_keyword"
                return result
        
        return result
    
    def detect_from_comment_text(self, text):
        """
        Layer 4: Deteksi dari teks komentar - AGGRESSIVE FOR SUMATRA
        """
        result = {"province": None, "city": None, "confidence": 0, "method": None}
        
        if not text:
            return result
        
        text_lower = text.lower()
        
        # ========== METHOD 1: PRIORITAS UNTUK BENGKULU ==========
        for keyword, province in self.bengkulu_keywords.items():
            if keyword in text_lower:
                result["province"] = province
                result["island"] = "Sumatra"
                result["confidence"] = 0.9
                result["method"] = f"bengkulu_keyword_{keyword}"
                print(f"   📍 [BENGKULU] Found '{keyword}' -> {province}")
                return result
        
        # ========== METHOD 2: Cek semua kata kunci Sumatra ==========
        for keyword, province in self.sumatra_provinces.items():
            if keyword in text_lower:
                result["province"] = province
                result["island"] = "Sumatra"
                result["confidence"] = 0.85
                result["method"] = f"sumatra_keyword_{keyword}"
                print(f"   📍 [SUMATRA] Found '{keyword}' -> {province}")
                return result
        
        # ========== METHOD 3: Cek pola komentar khusus Sumatra ==========
        for pattern, confidence in self.sumatra_comment_patterns:
            match = re.search(pattern, text_lower)
            if match:
                # Ekstrak provinsi dari match
                matched_text = match.group(0)
                for keyword, province in self.sumatra_provinces.items():
                    if keyword in matched_text:
                        result["province"] = province
                        result["island"] = "Sumatra"
                        result["confidence"] = confidence
                        result["method"] = f"pattern_{pattern[:20]}"
                        print(f"   📍 [PATTERN] Found '{matched_text}' -> {province}")
                        return result
        
        # ========== METHOD 4: Cek pola "di [kota]" ==========
        city_patterns = [
            (r'di\s+([a-z\s]+?)(?:\s|\,|\.|$)', 0.7),
            (r'ke\s+([a-z\s]+?)(?:\s|\,|\.|$)', 0.7),
            (r'dari\s+([a-z\s]+?)(?:\s|\,|\.|$)', 0.7),
            (r'warga\s+([a-z\s]+?)(?:\s|\,|\.|$)', 0.75),
            (r'asal\s+([a-z\s]+?)(?:\s|\,|\.|$)', 0.7),
            (r'📍\s*([a-z\s]+?)(?:\s|\,|\.|$)', 0.85),
        ]
        
        for pattern, confidence in city_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                city = match.strip()
                # Cek apakah kota itu adalah nama provinsi Sumatra
                for keyword, province in self.sumatra_provinces.items():
                    if keyword in city or city in keyword:
                        result["province"] = province
                        result["island"] = "Sumatra"
                        result["city"] = city
                        result["confidence"] = confidence
                        result["method"] = f"city_pattern_{pattern[:10]}"
                        print(f"   📍 [CITY] Found '{city}' -> {province}")
                        return result
        
        # ========== METHOD 5: Cek nama provinsi lengkap ==========
        for province in self.province_data.values():
            prov_name = province["nama"].lower()
            if prov_name in text_lower and prov_name in ['aceh', 'sumatera utara', 'sumatera barat', 'riau', 'jambi', 'sumatera selatan', 'bengkulu', 'lampung']:
                result["province"] = province["nama"]
                result["island"] = "Sumatra"
                result["confidence"] = 0.8
                result["method"] = "province_name"
                print(f"   📍 [PROVINCE] Found '{province['nama']}' in text")
                return result
        
        # ========== METHOD 6: Cek variasi typo untuk Bengkulu ==========
        for correct, variations in self.typo_variations.items():
            for var in variations:
                if var in text_lower:
                    province = self.get_province_from_code(correct)
                    if province:
                        result["province"] = province
                        result["island"] = "Sumatra"
                        result["confidence"] = 0.75
                        result["method"] = f"typo_{correct}_{var}"
                        print(f"   📍 [TYPO] Found '{var}' -> {province}")
                        return result
        
        # ========== METHOD 7: Deteksi dari topik ==========
        topic_result = self.detect_from_topic(text)
        if topic_result["province"]:
            return topic_result
        
        return result
    
    def detect_location_comprehensive(self, username="", display_name="", bio="", comment_text=""):
        """Deteksi lokasi dari semua sumber dengan prioritas"""
        result = {
            "province": None,
            "city": None,
            "island": None,
            "confidence": 0,
            "detection_method": None,
            "source": None
        }
        
        # Layer 1: Deteksi dari username
        if username:
            user_result = self.detect_from_username(username)
            if user_result["province"] and user_result["confidence"] > result["confidence"]:
                result.update({
                    "province": user_result["province"],
                    "city": user_result.get("city"),
                    "confidence": user_result["confidence"],
                    "detection_method": user_result["method"],
                    "source": "username"
                })
        
        # Layer 2: Deteksi dari display name
        if display_name and result["confidence"] < 0.8:
            display_result = self.detect_from_display_name(display_name)
            if display_result["province"] and display_result["confidence"] > result["confidence"]:
                result.update({
                    "province": display_result["province"],
                    "city": display_result.get("city"),
                    "confidence": display_result["confidence"],
                    "detection_method": display_result["method"],
                    "source": "display_name"
                })
        
        # Layer 3: Deteksi dari bio
        if bio and result["confidence"] < 0.7:
            bio_result = self.detect_from_bio(bio)
            if bio_result["province"] and bio_result["confidence"] > result["confidence"]:
                result.update({
                    "province": bio_result["province"],
                    "city": bio_result.get("city"),
                    "confidence": bio_result["confidence"],
                    "detection_method": bio_result["method"],
                    "source": "bio"
                })
        
        # Layer 4: Deteksi dari teks komentar (PALING AGRESIF)
        if comment_text and result["confidence"] < 0.6:
            comment_result = self.detect_from_comment_text(comment_text)
            if comment_result["province"] and comment_result["confidence"] > result["confidence"]:
                result.update({
                    "province": comment_result["province"],
                    "city": comment_result.get("city"),
                    "island": comment_result.get("island"),
                    "confidence": comment_result["confidence"],
                    "detection_method": comment_result["method"],
                    "source": "comment"
                })
        
        # Hitung pulau jika ada provinsi
        if result["province"] and not result["island"]:
            result["island"] = get_island_from_province(result["province"])
        
        # Update statistik
        if result["province"]:
            self.stats["total_detected"] += 1
            if result["source"]:
                self.stats["by_source"][result["source"]] = self.stats["by_source"].get(result["source"], 0) + 1
        
        return result
    
    # ... (method batch_detect, get_regional_stats, dll tetap sama) ...
    
    # ========== METHOD BATCH_DETECT ==========
    def batch_detect(self, df, username_col="username", display_name_col="display_name", 
                    bio_col="bio", text_col="comment"):
        """
        Deteksi lokasi untuk seluruh dataframe dengan semua sumber
        """
        results = []
        
        # Reset stats
        self.stats = {
            "total_detected": 0,
            "by_source": {},
            "by_confidence": {}
        }
        
        print(f"\n🔍 MENDETEKSI LOKASI UNTUK {len(df)} KOMENTAR")
        print("-" * 50)
        
        new_columns = ['province', 'city', 'island', 'confidence', 'detection_method', 'detection_source', 'source']
        
        for idx, row in df.iterrows():
            location = self.detect_location_comprehensive(
                username=row.get(username_col, ""),
                display_name=row.get(display_name_col, ""),
                bio=row.get(bio_col, ""),
                comment_text=row.get(text_col, "")
            )
            results.append(location)
            
            if (idx + 1) % 50 == 0:
                print(f"  Progress: {idx + 1}/{len(df)} komentar")
        
        df_result = pd.DataFrame(results)
        
        cols_to_remove = [col for col in new_columns if col in df.columns]
        if cols_to_remove:
            df = df.drop(columns=cols_to_remove)
            print(f"[INFO] Menghapus kolom duplikat: {cols_to_remove}")
        
        df = pd.concat([df, df_result], axis=1)
        
        if 'province' in df.columns:
            detected_count = len(df[df['province'].notna()])
            total_count = len(df)
            detected_pct = (detected_count / total_count * 100) if total_count > 0 else 0
            detected_pct = round(detected_pct, 1)
        else:
            detected_count = 0
            total_count = len(df)
            detected_pct = 0
        
        print(f"\n📍 LOKASI DETEKSI SUMMARY")
        print("=" * 50)
        print(f"📊 Total komentar: {total_count}")
        print(f"✅ Terdeteksi: {detected_count} ({detected_pct:.1f}%)")
        print(f"❌ Tidak terdeteksi: {total_count - detected_count} ({100 - detected_pct:.1f}%)")
        
        if detected_count > 0 and 'source' in df.columns:
            print("\n📊 SUMBER DETEKSI:")
            source_counts = df['source'].value_counts()
            for source, count in source_counts.items():
                source_pct = (count / detected_count * 100) if detected_count > 0 else 0
                source_pct = round(source_pct, 1)
                print(f"   • {source}: {count} ({source_pct:.1f}%)")
        
        return df
    
    def get_regional_stats(self, df, sentiment_column="sentiment"):
        """Dapatkan statistik sentimen per region"""
        stats = {
            "by_province": {},
            "by_island": {},
            "by_city": {},
            "national": {
                "total_comments": len(df),
                "positive": 0,
                "negative": 0,
                "neutral": 0
            }
        }
        
        if sentiment_column in df.columns:
            stats["national"]["positive"] = len(df[df[sentiment_column] == "Positif"])
            stats["national"]["negative"] = len(df[df[sentiment_column] == "Negatif"])
            stats["national"]["neutral"] = len(df[df[sentiment_column] == "Netral"])
        
        if "province" in df.columns:
            prov_df = df[df["province"].notna() & (df["province"] != "Tidak Diketahui")]
            all_provinces = prov_df["province"].unique()
            
            print(f"\n📍 Statistik per Provinsi:")
            print(f"   - Menemukan {len(all_provinces)} provinsi dengan data")
            
            for province in all_provinces:
                prov_data = prov_df[prov_df["province"] == province]
                
                if sentiment_column in prov_data.columns:
                    positive = len(prov_data[prov_data[sentiment_column] == "Positif"])
                    negative = len(prov_data[prov_data[sentiment_column] == "Negatif"])
                    neutral = len(prov_data[prov_data[sentiment_column] == "Netral"])
                    total = len(prov_data)
                    positive_pct = round(positive / total * 100, 1) if total > 0 else 0
                else:
                    positive = negative = neutral = 0
                    positive_pct = 0
                    total = len(prov_data)
                
                stats["by_province"][province] = {
                    "total": total,
                    "positive": positive,
                    "negative": negative,
                    "neutral": neutral,
                    "positive_pct": positive_pct,
                    "coordinates": self._get_province_coordinates(province)
                }
        
        if "island" in df.columns:
            island_df = df[df["island"].notna()]
            all_islands = island_df["island"].unique()
            
            for island in all_islands:
                island_data = island_df[island_df["island"] == island]
                
                if sentiment_column in island_data.columns:
                    positive = len(island_data[island_data[sentiment_column] == "Positif"])
                    negative = len(island_data[island_data[sentiment_column] == "Negatif"])
                    neutral = len(island_data[island_data[sentiment_column] == "Netral"])
                    total = len(island_data)
                    positive_pct = round(positive / total * 100, 1) if total > 0 else 0
                else:
                    positive = negative = neutral = 0
                    positive_pct = 0
                    total = len(island_data)
                
                stats["by_island"][island] = {
                    "total": total,
                    "positive": positive,
                    "negative": negative,
                    "neutral": neutral,
                    "positive_pct": positive_pct
                }
        
        return stats
    
    def _get_province_coordinates(self, province_name):
        """Dapatkan koordinat untuk plotting di peta"""
        if not province_name:
            return None
            
        for code, prov in self.province_data.items():
            if prov["nama"] == province_name:
                return {"lat": prov["lat"], "lon": prov["lon"]}
        
        return {"lat": -2.5, "lon": 118.0}
    
    get_province_coordinates = _get_province_coordinates
    
    def get_detection_stats(self):
        """Dapatkan statistik deteksi"""
        return self.stats
    
    def reset_stats(self):
        """Reset statistik deteksi"""
        self.stats = {
            "total_detected": 0,
            "by_source": {},
            "by_confidence": {}
        }