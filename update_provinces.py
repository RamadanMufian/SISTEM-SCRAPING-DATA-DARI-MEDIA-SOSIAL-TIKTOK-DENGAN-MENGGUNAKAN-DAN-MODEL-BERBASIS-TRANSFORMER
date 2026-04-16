# update_provinces.py
"""
Script untuk update provinsi yang sudah ada di database
Menggunakan geo_sentiment.py yang sudah ditingkatkan
"""

from database import DatabaseManager
from geo_sentiment import GeoLocationDetector
from models_db import Comment  # Import model Comment dari models_db
import sys

def print_header(text):
    """Print header dengan format"""
    print("\n" + "="*60)
    print(f"📌 {text}")
    print("="*60)

def print_success(text):
    """Print success message"""
    print(f"✅ {text}")

def print_error(text):
    """Print error message"""
    print(f"❌ {text}")

def print_warning(text):
    """Print warning message"""
    print(f"⚠️ {text}")

def print_info(text):
    """Print info message"""
    print(f"ℹ️ {text}")

def main():
    """Main function untuk update provinsi"""
    print_header("🔄 UPDATE PROVINSI DATABASE")
    
    # Inisialisasi database manager dan detector
    db = DatabaseManager()
    detector = GeoLocationDetector()
    
    # Ambil komentar yang belum punya provinsi
    comments = db.session.query(Comment).filter(
        Comment.detected_province.is_(None)
    ).all()
    
    print_info(f"Total komentar tanpa provinsi: {len(comments)}")
    
    if not comments:
        print_success("Semua komentar sudah memiliki provinsi!")
        return
    
    updated = 0
    failed = 0
    
    print("\n🔍 MENDETEKSI PROVINSI...")
    print("-" * 50)
    
    for i, comment in enumerate(comments, 1):
        try:
            # Deteksi lokasi dari teks komentar
            result = detector.detect_from_comment_text(comment.raw_text)
            
            if result['province']:
                # Update komentar
                comment.detected_province = result['province']
                comment.detected_city = result.get('city')
                comment.detected_island = result.get('island', 'Sumatra' if result['province'] in [
                    'ACEH', 'SUMATERA UTARA', 'SUMATERA BARAT', 'RIAU', 'JAMBI',
                    'SUMATERA SELATAN', 'BENGKULU', 'LAMPUNG', 'KEP. BANGKA BELITUNG', 'KEP. RIAU'
                ] else None)
                comment.location_confidence = result['confidence']
                comment.detection_method = result['method']
                comment.detection_source = 'comment'
                
                updated += 1
                
                # Progress setiap 10 komentar
                if i % 10 == 0:
                    print(f"  Progress: {i}/{len(comments)} - Updated: {updated}")
                
                # Print detail setiap 50 komentar
                if i % 50 == 0:
                    print(f"  ✅ ID {comment.id}: {comment.raw_text[:50]}... -> {result['province']}")
            else:
                failed += 1
                
        except Exception as e:
            print_error(f"Error pada komentar ID {comment.id}: {e}")
            failed += 1
            continue
        
        # Commit setiap 100 komentar
        if i % 100 == 0:
            db.session.commit()
            print(f"  💾 Commit {i} komentar")
    
    # Commit terakhir
    db.session.commit()
    
    print("\n" + "="*60)
    print("📊 HASIL UPDATE")
    print("="*60)
    print(f"✅ Berhasil update: {updated} komentar")
    print(f"❌ Gagal: {failed} komentar")
    print(f"📊 Total diproses: {len(comments)} komentar")
    
    # Tampilkan statistik provinsi setelah update
    print("\n📋 STATISTIK PROVINSI SETELAH UPDATE:")
    with db.engine.connect() as conn:
        from sqlalchemy import text
        result = conn.execute(text("""
            SELECT detected_province, COUNT(*) 
            FROM comments 
            WHERE detected_province IS NOT NULL
            GROUP BY detected_province
            ORDER BY COUNT(*) DESC
        """))
        
        provinces = result.fetchall()
        if provinces:
            for prov, count in provinces[:10]:
                print(f"   • {prov}: {count} komentar")
        else:
            print("   ⚠️ Belum ada provinsi terdeteksi")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Program dihentikan oleh user")
        sys.exit(0)
    except Exception as e:
        print_error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)