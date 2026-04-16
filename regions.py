# regions.py
"""
Database wilayah Indonesia untuk geolocation
Sumber: Kemendagri RI
"""

INDONESIAN_REGIONS = {
    "pulau": {
        "sumatra": ["ACEH", "SUMATERA UTARA", "SUMATERA BARAT", "RIAU", "JAMBI", 
                   "SUMATERA SELATAN", "BENGKULU", "LAMPUNG", "KEP. BANGKA BELITUNG", 
                   "KEP. RIAU"],
        "jawa": ["DKI JAKARTA", "JAWA BARAT", "JAWA TENGAH", "DI YOGYAKARTA", 
                "JAWA TIMUR", "BANTEN"],
        "kalimantan": ["KALIMANTAN BARAT", "KALIMANTAN TENGAH", "KALIMANTAN SELATAN", 
                      "KALIMANTAN TIMUR", "KALIMANTAN UTARA"],
        "sulawesi": ["SULAWESI UTARA", "SULAWESI TENGAH", "SULAWESI SELATAN", 
                    "SULAWESI TENGGARA", "GORONTALO", "SULAWESI BARAT"],
        "bali_nusa": ["BALI", "NUSA TENGGARA BARAT", "NUSA TENGGARA TIMUR"],
        "maluku": ["MALUKU", "MALUKU UTARA"],
        "papua": ["PAPUA", "PAPUA BARAT", "PAPUA TENGAH", "PAPUA PEGUNUNGAN", 
                 "PAPUA SELATAN", "PAPUA BARAT DAYA"]
    },
    
    "provinsi": {
        "11": {"nama": "ACEH", "ibu_kota": "Banda Aceh", "lat": 5.55, "lon": 95.32},
        "12": {"nama": "SUMATERA UTARA", "ibu_kota": "Medan", "lat": 3.58, "lon": 98.67},
        "13": {"nama": "SUMATERA BARAT", "ibu_kota": "Padang", "lat": -0.95, "lon": 100.35},
        "14": {"nama": "RIAU", "ibu_kota": "Pekanbaru", "lat": 0.53, "lon": 101.45},
        "15": {"nama": "JAMBI", "ibu_kota": "Jambi", "lat": -1.59, "lon": 103.61},
        "16": {"nama": "SUMATERA SELATAN", "ibu_kota": "Palembang", "lat": -2.99, "lon": 104.76},
        "17": {"nama": "BENGKULU", "ibu_kota": "Bengkulu", "lat": -3.80, "lon": 102.26},
        "18": {"nama": "LAMPUNG", "ibu_kota": "Bandar Lampung", "lat": -5.45, "lon": 105.27},
        "19": {"nama": "KEP. BANGKA BELITUNG", "ibu_kota": "Pangkal Pinang", "lat": -2.13, "lon": 106.11},
        "21": {"nama": "KEP. RIAU", "ibu_kota": "Tanjung Pinang", "lat": 0.92, "lon": 104.45},
        "31": {"nama": "DKI JAKARTA", "ibu_kota": "Jakarta", "lat": -6.21, "lon": 106.85},
        "32": {"nama": "JAWA BARAT", "ibu_kota": "Bandung", "lat": -6.91, "lon": 107.61},
        "33": {"nama": "JAWA TENGAH", "ibu_kota": "Semarang", "lat": -7.01, "lon": 110.44},
        "34": {"nama": "DI YOGYAKARTA", "ibu_kota": "Yogyakarta", "lat": -7.80, "lon": 110.36},
        "35": {"nama": "JAWA TIMUR", "ibu_kota": "Surabaya", "lat": -7.26, "lon": 112.75},
        "36": {"nama": "BANTEN", "ibu_kota": "Serang", "lat": -6.12, "lon": 106.15},
        "51": {"nama": "BALI", "ibu_kota": "Denpasar", "lat": -8.65, "lon": 115.22},
        "52": {"nama": "NUSA TENGGARA BARAT", "ibu_kota": "Mataram", "lat": -8.58, "lon": 116.12},
        "53": {"nama": "NUSA TENGGARA TIMUR", "ibu_kota": "Kupang", "lat": -10.18, "lon": 123.58},
        "61": {"nama": "KALIMANTAN BARAT", "ibu_kota": "Pontianak", "lat": -0.02, "lon": 109.34},
        "62": {"nama": "KALIMANTAN TENGAH", "ibu_kota": "Palangka Raya", "lat": -2.21, "lon": 113.92},
        "63": {"nama": "KALIMANTAN SELATAN", "ibu_kota": "Banjarmasin", "lat": -3.32, "lon": 114.59},
        "64": {"nama": "KALIMANTAN TIMUR", "ibu_kota": "Samarinda", "lat": -0.50, "lon": 117.15},
        "65": {"nama": "KALIMANTAN UTARA", "ibu_kota": "Tanjung Selor", "lat": 2.84, "lon": 117.37},
        "71": {"nama": "SULAWESI UTARA", "ibu_kota": "Manado", "lat": 1.49, "lon": 124.84},
        "72": {"nama": "SULAWESI TENGAH", "ibu_kota": "Palu", "lat": -0.90, "lon": 119.86},
        "73": {"nama": "SULAWESI SELATAN", "ibu_kota": "Makassar", "lat": -5.15, "lon": 119.43},
        "74": {"nama": "SULAWESI TENGGARA", "ibu_kota": "Kendari", "lat": -3.99, "lon": 122.51},
        "75": {"nama": "GORONTALO", "ibu_kota": "Gorontalo", "lat": 0.54, "lon": 123.06},
        "76": {"nama": "SULAWESI BARAT", "ibu_kota": "Mamuju", "lat": -2.68, "lon": 118.89},
        "81": {"nama": "MALUKU", "ibu_kota": "Ambon", "lat": -3.65, "lon": 128.19},
        "82": {"nama": "MALUKU UTARA", "ibu_kota": "Sofifi", "lat": 0.72, "lon": 127.57},
        "91": {"nama": "PAPUA", "ibu_kota": "Jayapura", "lat": -2.53, "lon": 140.72},
        "92": {"nama": "PAPUA BARAT", "ibu_kota": "Manokwari", "lat": -0.86, "lon": 134.06},
        "93": {"nama": "PAPUA TENGAH", "ibu_kota": "Nabire", "lat": -3.37, "lon": 135.50},
        "94": {"nama": "PAPUA PEGUNUNGAN", "ibu_kota": "Wamena", "lat": -4.10, "lon": 138.95},
        "95": {"nama": "PAPUA SELATAN", "ibu_kota": "Merauke", "lat": -8.50, "lon": 140.40},
        "96": {"nama": "PAPUA BARAT DAYA", "ibu_kota": "Sorong", "lat": -0.86, "lon": 131.25}
    },
    
    "kota_besar": [
        {"nama": "Jakarta", "provinsi": "DKI JAKARTA", "lat": -6.21, "lon": 106.85, "penduduk": 10562000},
        {"nama": "Surabaya", "provinsi": "JAWA TIMUR", "lat": -7.26, "lon": 112.75, "penduduk": 2985000},
        {"nama": "Bandung", "provinsi": "JAWA BARAT", "lat": -6.91, "lon": 107.61, "penduduk": 2475000},
        {"nama": "Medan", "provinsi": "SUMATERA UTARA", "lat": 3.58, "lon": 98.67, "penduduk": 2210000},
        {"nama": "Semarang", "provinsi": "JAWA TENGAH", "lat": -7.01, "lon": 110.44, "penduduk": 1680000},
        {"nama": "Makassar", "provinsi": "SULAWESI SELATAN", "lat": -5.15, "lon": 119.43, "penduduk": 1475000},
        {"nama": "Palembang", "provinsi": "SUMATERA SELATAN", "lat": -2.99, "lon": 104.76, "penduduk": 1660000},
        {"nama": "Batam", "provinsi": "KEP. RIAU", "lat": 1.13, "lon": 104.05, "penduduk": 1200000},
        {"nama": "Pekanbaru", "provinsi": "RIAU", "lat": 0.53, "lon": 101.45, "penduduk": 1090000},
        {"nama": "Denpasar", "provinsi": "BALI", "lat": -8.65, "lon": 115.22, "penduduk": 897000}
    ]
}

# Database kata kunci lokasi
LOCATION_KEYWORDS = {
    "aceh": "ACEH", "medan": "SUMATERA UTARA", "padang": "SUMATERA BARAT",
    "pekanbaru": "RIAU", "jambi": "JAMBI", "palembang": "SUMATERA SELATAN",
    "bengkulu": "BENGKULU", "lampung": "LAMPUNG", "pangkal pinang": "KEP. BANGKA BELITUNG",
    "tanjung pinang": "KEP. RIAU", "jakarta": "DKI JAKARTA", "bandung": "JAWA BARAT",
    "semarang": "JAWA TENGAH", "yogyakarta": "DI YOGYAKARTA", "surabaya": "JAWA TIMUR",
    "serang": "BANTEN", "denpasar": "BALI", "mataram": "NUSA TENGGARA BARAT",
    "kupang": "NUSA TENGGARA TIMUR", "pontianak": "KALIMANTAN BARAT",
    "palangkaraya": "KALIMANTAN TENGAH", "banjarmasin": "KALIMANTAN SELATAN",
    "samarinda": "KALIMANTAN TIMUR", "tanjung selor": "KALIMANTAN UTARA",
    "manado": "SULAWESI UTARA", "palu": "SULAWESI TENGAH", "makassar": "SULAWESI SELATAN",
    "kendari": "SULAWESI TENGGARA", "gorontalo": "GORONTALO", "mamuju": "SULAWESI BARAT",
    "ambon": "MALUKU", "ternate": "MALUKU UTARA", "jayapura": "PAPUA",
    "manokwari": "PAPUA BARAT", "nabire": "PAPUA TENGAH", "wamena": "PAPUA PEGUNUNGAN",
    "merauke": "PAPUA SELATAN", "sorong": "PAPUA BARAT DAYA"
}

def get_province_from_city(city_name):
    """Dapatkan provinsi dari nama kota"""
    city_lower = city_name.lower().strip()
    
    for code, prov in INDONESIAN_REGIONS["provinsi"].items():
        if prov["ibu_kota"].lower() in city_lower:
            return prov["nama"]
    
    for city in INDONESIAN_REGIONS["kota_besar"]:
        if city["nama"].lower() in city_lower:
            return city["provinsi"]
    
    return None

def get_island_from_province(province_name):
    """Dapatkan pulau dari nama provinsi"""
    province_upper = province_name.upper()
    
    for island, provinces in INDONESIAN_REGIONS["pulau"].items():
        if province_upper in [p.upper() for p in provinces]:
            island_names = {
                "sumatra": "Sumatra",
                "jawa": "Jawa",
                "kalimantan": "Kalimantan",
                "sulawesi": "Sulawesi",
                "bali_nusa": "Bali & Nusa Tenggara",
                "maluku": "Maluku",
                "papua": "Papua"
            }
            return island_names.get(island, island)
    
    return "Lainnya"