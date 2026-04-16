"""
Scraping data wilayah BPS untuk Provinsi Bengkulu
Sumber: sig.bps.go.id
"""

import requests
import pandas as pd
import time
from typing import List, Dict

def fetch_wilayah(level: int, kode: str = None) -> List[Dict]:
    """
    Fetch data wilayah dari API BPS
    
    Args:
        level: 1=Provinsi, 2=Kabupaten/Kota, 3=Kecamatan, 4=Desa/Kelurahan
        kode: Kode wilayah parent (untuk level > 1)
    
    Returns:
        List of wilayah
    """
    base_url = "https://sig.bps.go.id/rest-bridging/getwilayah"
    
    params = {"level": level}
    if kode:
        params["kode"] = kode
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                return data
            else:
                print(f"⚠️ Unexpected response format for level {level}: {type(data)}")
                return []
        else:
            print(f"⚠️ Error {response.status_code} for level {level}")
            return []
            
    except Exception as e:
        print(f"❌ Error fetching level {level}: {e}")
        return []

def scrape_bengkulu_regions():
    """
    Scrape seluruh wilayah Provinsi Bengkulu
    """
    print("="*60)
    print("🗺️  SCRAPING WILAYAH PROVINSI BENGKULU")
    print("="*60)
    
    # Kode Provinsi Bengkulu
    PROVINSI_KODE = "17"
    PROVINSI_NAMA = "BENGKULU"
    
    data_all = []
    
    # Step 1: Ambil data kabupaten/kota (level 2)
    print("\n📊 Mengambil data Kabupaten/Kota...")
    kab_list = fetch_wilayah(level=2, kode=PROVINSI_KODE)
    
    if not kab_list:
        print("❌ Gagal mengambil data kabupaten/kota!")
        return None
    
    print(f"✅ Ditemukan {len(kab_list)} Kabupaten/Kota")
    
    # Step 2: Loop setiap kabupaten
    for i, kab in enumerate(kab_list, 1):
        kode_kab = kab.get('kode', '')
        nama_kab = kab.get('nama', '')
        
        print(f"\n  [{i}/{len(kab_list)}] {nama_kab} (Kode: {kode_kab})")
        
        # Ambil kecamatan (level 3)
        kec_list = fetch_wilayah(level=3, kode=kode_kab)
        
        if not kec_list:
            print(f"    ⚠️ Tidak ada data kecamatan untuk {nama_kab}")
            continue
        
        print(f"    📍 {len(kec_list)} kecamatan ditemukan")
        
        # Loop setiap kecamatan
        for kec in kec_list:
            kode_kec = kec.get('kode', '')
            nama_kec = kec.get('nama', '')
            
            # Ambil desa/kelurahan (level 4)
            desa_list = fetch_wilayah(level=4, kode=kode_kec)
            
            if desa_list:
                for desa in desa_list:
                    data_all.append({
                        "provinsi": PROVINSI_NAMA,
                        "kabupaten": nama_kab,
                        "kecamatan": nama_kec,
                        "desa_kelurahan": desa.get('nama', ''),
                        "kode_desa": desa.get('kode', '')
                    })
                print(f"      - {nama_kec}: {len(desa_list)} desa/kelurahan")
            else:
                print(f"      - {nama_kec}: Tidak ada data desa")
            
            # Delay kecil untuk menghindari rate limit
            time.sleep(0.1)
    
    return data_all

def get_kabupaten_list():
    """Ambil daftar kabupaten Bengkulu"""
    kab_list = fetch_wilayah(level=2, kode="17")
    
    if kab_list:
        df = pd.DataFrame(kab_list)
        df = df[['kode', 'nama']]
        df.columns = ['kode_kabupaten', 'nama_kabupaten']
        return df
    return None

def get_kecamatan_by_kabupaten(kode_kabupaten):
    """Ambil daftar kecamatan berdasarkan kode kabupaten"""
    kec_list = fetch_wilayah(level=3, kode=kode_kabupaten)
    
    if kec_list:
        df = pd.DataFrame(kec_list)
        df = df[['kode', 'nama']]
        df.columns = ['kode_kecamatan', 'nama_kecamatan']
        df['kode_kabupaten'] = kode_kabupaten
        return df
    return None

def get_desa_by_kecamatan(kode_kecamatan):
    """Ambil daftar desa/kelurahan berdasarkan kode kecamatan"""
    desa_list = fetch_wilayah(level=4, kode=kode_kecamatan)
    
    if desa_list:
        df = pd.DataFrame(desa_list)
        df = df[['kode', 'nama']]
        df.columns = ['kode_desa', 'nama_desa']
        df['kode_kecamatan'] = kode_kecamatan
        return df
    return None

def save_to_excel(data, filename="bengkulu_wilayah.xlsx"):
    """Simpan data ke file Excel"""
    if not data:
        print("⚠️ Tidak ada data untuk disimpan")
        return
    
    df = pd.DataFrame(data)
    
    # Simpan ke Excel dengan multiple sheets
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # Sheet 1: Semua data
        df.to_excel(writer, sheet_name='Semua Wilayah', index=False)
        
        # Sheet 2: Statistik per kabupaten
        stats = df.groupby('kabupaten').agg({
            'kecamatan': 'nunique',
            'desa_kelurahan': 'count'
        }).reset_index()
        stats.columns = ['Kabupaten', 'Jumlah Kecamatan', 'Jumlah Desa/Kelurahan']
        stats.to_excel(writer, sheet_name='Statistik Kabupaten', index=False)
        
        # Sheet 3: Daftar kabupaten
        kab_list = df[['kabupaten']].drop_duplicates().reset_index(drop=True)
        kab_list.to_excel(writer, sheet_name='Daftar Kabupaten', index=False)
    
    print(f"✅ Data disimpan ke {filename}")
    return df

def print_summary(df):
    """Print ringkasan data"""
    if df is None or df.empty:
        print("❌ Tidak ada data")
        return
    
    print("\n" + "="*60)
    print("📊 RINGKASAN DATA WILAYAH BENGKULU")
    print("="*60)
    
    # Hitung statistik
    total_kab = df['kabupaten'].nunique()
    total_kec = df['kecamatan'].nunique()
    total_desa = len(df)
    
    print(f"\n📍 Total Kabupaten/Kota: {total_kab}")
    print(f"📍 Total Kecamatan: {total_kec}")
    print(f"📍 Total Desa/Kelurahan: {total_desa}")
    
    print("\n📋 DAFTAR KABUPATEN/KOTA:")
    for kab in sorted(df['kabupaten'].unique()):
        kec_count = df[df['kabupaten'] == kab]['kecamatan'].nunique()
        desa_count = len(df[df['kabupaten'] == kab])
        print(f"   • {kab}: {kec_count} kecamatan, {desa_count} desa")
    
    print("\n📋 CONTOH 10 DATA TERAKHIR:")
    print(df.tail(10).to_string(index=False))


def main():
    """Fungsi utama"""
    print("\n" + "="*60)
    print("🗺️  SCRAPER DATA WILAYAH BPS - BENGKULU")
    print("="*60)
    
    # Scrape data
    data = scrape_bengkulu_regions()
    
    if data:
        # Save to Excel
        df = save_to_excel(data, "bengkulu_wilayah.xlsx")
        
        # Print summary
        print_summary(df)
        
        # Optional: Export ke CSV juga
        df.to_csv("bengkulu_wilayah.csv", index=False)
        print("\n✅ Juga disimpan ke bengkulu_wilayah.csv")
        
    else:
        print("❌ Gagal mengambil data")

if __name__ == "__main__":
    main()