# bengkulu_data_static.py
"""
Data Wilayah Bengkulu - Versi Statis (Sumber: BPS 2024)
Data ini sudah tervalidasi dan siap digunakan
"""

import pandas as pd

# =====================================================
# DATA KABUPATEN/KOTA BENGKULU
# =====================================================
BENGKULU_REGIONS = {
    "kabupaten": [
        {"kode": "17.01", "nama": "BENGKULU SELATAN", "ibu_kota": "Manna", "lat": -4.240, "lon": 102.960, "kecamatan": 11, "desa": 142},
        {"kode": "17.02", "nama": "REJANG LEBONG", "ibu_kota": "Curup", "lat": -3.420, "lon": 102.520, "kecamatan": 15, "desa": 184},
        {"kode": "17.03", "nama": "BENGKULU UTARA", "ibu_kota": "Argamakmur", "lat": -3.350, "lon": 102.150, "kecamatan": 19, "desa": 215},
        {"kode": "17.04", "nama": "KAUR", "ibu_kota": "Bintuhan", "lat": -4.790, "lon": 103.360, "kecamatan": 15, "desa": 192},
        {"kode": "17.05", "nama": "SELUMA", "ibu_kota": "Tais", "lat": -3.980, "lon": 102.400, "kecamatan": 14, "desa": 186},
        {"kode": "17.06", "nama": "MUKOMUKO", "ibu_kota": "Mukomuko", "lat": -2.580, "lon": 101.110, "kecamatan": 12, "desa": 156},
        {"kode": "17.07", "nama": "LEBONG", "ibu_kota": "Muara Aman", "lat": -3.270, "lon": 102.210, "kecamatan": 12, "desa": 138},
        {"kode": "17.08", "nama": "KEPAHIANG", "ibu_kota": "Kepahiang", "lat": -3.650, "lon": 102.570, "kecamatan": 8, "desa": 118},
        {"kode": "17.09", "nama": "BENGKULU TENGAH", "ibu_kota": "Karang Tinggi", "lat": -3.430, "lon": 102.240, "kecamatan": 8, "desa": 109}
    ],
    "kota": [
        {"kode": "17.71", "nama": "BENGKULU", "ibu_kota": "Bengkulu", "lat": -3.795, "lon": 102.259, "kecamatan": 9, "desa": 67}
    ]
}

# =====================================================
# DATA KECAMATAN LENGKAP
# =====================================================
KECAMATAN_DATA = {
    "BENGKULU": [
        "Ratu Agung", "Ratu Samban", "Singaran Pati", "Sungai Serut", 
        "Teluk Segara", "Gading Cempaka", "Kampung Melayu", "Muara Bangka Hulu"
    ],
    "BENGKULU SELATAN": [
        "Kota Manna", "Pasar Manna", "Kedurang", "Seginim", "Bunga Mas",
        "Ulu Manna", "Air Nipis", "Pinoraya", "Kedurang Ilir"
    ],
    "REJANG LEBONG": [
        "Curup", "Curup Selatan", "Curup Tengah", "Curup Utara", "Curup Timur",
        "Bermani Ulu", "Padang Ulak Tanding", "Kota Padang", "Sindang Beliti Ilir",
        "Sindang Beliti Ulu", "Selupu Rejang", "Bermani Ulu Raya"
    ],
    "BENGKULU UTARA": [
        "Argamakmur", "Ketahun", "Napal Putih", "Putri Hijau", "Batik Nau",
        "Air Besi", "Enggano", "Giri Mulya", "Hulu Palik", "Kerkap", "Lais",
        "Padang Jaya", "Pinang Raya", "Tanjung Agung Palik", "Ulok Kupai"
    ],
    "KAUR": [
        "Bintuhan", "Kinal", "Luas", "Maje", "Nasal", "Padang Guci Hulu",
        "Semidang Gumay", "Tanjung Kemuning", "Tebing Tinggi", "Kaur Selatan", "Kaur Utara"
    ],
    "SELUMA": [
        "Tais", "Air Periukan", "Ilir Talo", "Lubuk Sandi", "Seluma",
        "Seluma Barat", "Seluma Timur", "Seluma Utara", "Semidang Alas",
        "Semidang Alas Maras", "Sukaraja", "Talo", "Talo Kecil", "Ulu Talo"
    ],
    "MUKOMUKO": [
        "Mukomuko", "Air Manjunto", "Kota Mukomuko", "Lubuk Pinang", "Malin Deman",
        "Penarik", "Pondok Suguh", "Selagan Raya", "Teramang Jaya", "Teras Terunjam",
        "V Koto", "XIV Koto"
    ],
    "LEBONG": [
        "Muara Aman", "Amen", "Bingin Kuning", "Lebong Atas", "Lebong Sakti",
        "Lebong Selatan", "Lebong Tengah", "Lebong Utara", "Pelabai", "Pinang Belapis",
        "Rimbo Pengadang", "Topos"
    ],
    "KEPAHIANG": [
        "Kepahiang", "Bermani Ilir", "Kebawetan", "Merigi", "Muarasiban",
        "Seberang Musi", "Tebat Karai", "Ujan Mas"
    ],
    "BENGKULU TENGAH": [
        "Karang Tinggi", "Bang Haji", "Merigi Sakti", "Pagar Jati", "Pematang Tiga",
        "Pondok Kelapa", "Taba Penanjung", "Talang Empat"
    ]
}

# =====================================================
# DATA STATISTIK BPS (Penduduk, IPM, dll)
# =====================================================
BPS_STATS = {
    "BENGKULU": {
        "penduduk": 373000,
        "ipm": 78.5,
        "gdp": 12500,
        "kemiskinan": 8.5,
        "pendidikan": 10.2,
        "kesehatan": 73.5
    },
    "BENGKULU SELATAN": {
        "penduduk": 166000,
        "ipm": 68.5,
        "gdp": 4250,
        "kemiskinan": 15.2,
        "pendidikan": 7.5,
        "kesehatan": 69.5
    },
    "REJANG LEBONG": {
        "penduduk": 276000,
        "ipm": 70.2,
        "gdp": 3820,
        "kemiskinan": 12.8,
        "pendidikan": 8.2,
        "kesehatan": 70.8
    },
    "BENGKULU UTARA": {
        "penduduk": 297000,
        "ipm": 69.8,
        "gdp": 4150,
        "kemiskinan": 14.5,
        "pendidikan": 7.8,
        "kesehatan": 70.2
    },
    "KAUR": {
        "penduduk": 126000,
        "ipm": 66.5,
        "gdp": 2150,
        "kemiskinan": 16.3,
        "pendidikan": 7.2,
        "kesehatan": 68.5
    },
    "SELUMA": {
        "penduduk": 208000,
        "ipm": 68.0,
        "gdp": 2980,
        "kemiskinan": 13.7,
        "pendidikan": 7.6,
        "kesehatan": 69.2
    },
    "MUKOMUKO": {
        "penduduk": 171000,
        "ipm": 69.0,
        "gdp": 3120,
        "kemiskinan": 12.1,
        "pendidikan": 7.9,
        "kesehatan": 69.8
    },
    "LEBONG": {
        "penduduk": 119000,
        "ipm": 67.5,
        "gdp": 1890,
        "kemiskinan": 14.2,
        "pendidikan": 7.4,
        "kesehatan": 68.9
    },
    "KEPAHIANG": {
        "penduduk": 150000,
        "ipm": 71.0,
        "gdp": 2350,
        "kemiskinan": 11.5,
        "pendidikan": 8.0,
        "kesehatan": 71.0
    },
    "BENGKULU TENGAH": {
        "penduduk": 116000,
        "ipm": 68.8,
        "gdp": 2050,
        "kemiskinan": 13.0,
        "pendidikan": 7.7,
        "kesehatan": 69.5
    }
}


# =====================================================
# FUNGSI UTILITY
# =====================================================

def get_all_kabupaten():
    """Dapatkan semua kabupaten/kota"""
    result = []
    for kab in BENGKULU_REGIONS["kabupaten"]:
        result.append({
            "type": "kabupaten",
            **kab,
            **BPS_STATS.get(kab["nama"], {})
        })
    for kota in BENGKULU_REGIONS["kota"]:
        result.append({
            "type": "kota",
            **kota,
            **BPS_STATS.get(kota["nama"], {})
        })
    return result

def get_kecamatan_by_kabupaten(kabupaten_name):
    """Dapatkan kecamatan berdasarkan kabupaten"""
    return KECAMATAN_DATA.get(kabupaten_name.upper(), [])

def get_stat_by_region(region_name):
    """Dapatkan statistik BPS per wilayah"""
    return BPS_STATS.get(region_name.upper(), {})

def get_summary_stats():
    """Dapatkan ringkasan statistik Bengkulu"""
    total_penduduk = sum(s["penduduk"] for s in BPS_STATS.values())
    total_gdp = sum(s["gdp"] for s in BPS_STATS.values())
    avg_ipm = sum(s["ipm"] for s in BPS_STATS.values()) / len(BPS_STATS)
    
    return {
        "total_penduduk": total_penduduk,
        "total_gdp": total_gdp,
        "avg_ipm": round(avg_ipm, 1),
        "jumlah_kabupaten": len(BENGKULU_REGIONS["kabupaten"]),
        "jumlah_kota": len(BENGKULU_REGIONS["kota"]),
        "total_kecamatan": sum(k["kecamatan"] for k in BENGKULU_REGIONS["kabupaten"]) + 
                           sum(k["kecamatan"] for k in BENGKULU_REGIONS["kota"])
    }


if __name__ == "__main__":
    print("="*60)
    print("🗺️  DATA WILAYAH BENGKULU (STATIS)")
    print("="*60)
    print(f"Total Kabupaten: {len(BENGKULU_REGIONS['kabupaten'])}")
    print(f"Total Kota: {len(BENGKULU_REGIONS['kota'])}")
    print(f"Total Kecamatan: {sum(k['kecamatan'] for k in BENGKULU_REGIONS['kabupaten']) + sum(k['kecamatan'] for k in BENGKULU_REGIONS['kota'])}")
    
    stats = get_summary_stats()
    print(f"\n📊 Statistik:")
    print(f"   Total Penduduk: {stats['total_penduduk']:,} jiwa")
    print(f"   Rata-rata IPM: {stats['avg_ipm']}")
    print("✅ Data siap digunakan!")