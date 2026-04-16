# test_bps_api.py
"""
Test koneksi ke API BPS
"""

import requests

def test_api():
    """Test berbagai endpoint API BPS"""
    
    print("="*60)
    print("🔍 TEST API BPS")
    print("="*60)
    
    # Test endpoint provinsi (level 1)
    print("\n1. TEST ENDPOINT PROVINSI...")
    url = "https://sig.bps.go.id/rest-bridging/getwilayah?level=1"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Berhasil! Ditemukan {len(data)} provinsi")
            
            # Cari Bengkulu
            for prov in data:
                if 'BENGKULU' in prov.get('nama', '').upper():
                    print(f"   📍 Provinsi Bengkulu: kode={prov.get('kode')}, nama={prov.get('nama')}")
        else:
            print(f"   ❌ Gagal: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test endpoint kabupaten Bengkulu (level 2)
    print("\n2. TEST ENDPOINT KABUPATEN BENGKULU...")
    url = "https://sig.bps.go.id/rest-bridging/getwilayah?level=2&kode=17"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Berhasil! Ditemukan {len(data)} kabupaten/kota di Bengkulu")
            
            for kab in data[:5]:  # Tampilkan 5 pertama
                print(f"      - {kab.get('nama')} (kode: {kab.get('kode')})")
        else:
            print(f"   ❌ Gagal: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "="*60)
    print("✅ TEST SELESAI")
    print("="*60)

if __name__ == "__main__":
    test_api()