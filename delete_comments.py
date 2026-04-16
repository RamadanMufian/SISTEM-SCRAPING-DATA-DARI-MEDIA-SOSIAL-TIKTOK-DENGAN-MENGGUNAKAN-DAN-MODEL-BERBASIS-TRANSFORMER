# delete_data.py
"""
Script untuk menghapus data komentar dari database
"""

from database_config import DatabaseManager
from sqlalchemy import text
import sys
import os

# Tambahkan path project
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def print_header(text):
    """Print header dengan format"""7
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

def get_database_stats(db):
    """Dapatkan statistik database"""
    with db.engine.connect() as conn:
        # Total videos
        result = conn.execute(text("SELECT COUNT(*) FROM videos"))
        videos = result.scalar()
        
        # Total comments
        result = conn.execute(text("SELECT COUNT(*) FROM comments"))
        comments = result.scalar()
        
        # Comments with province
        result = conn.execute(text("SELECT COUNT(*) FROM comments WHERE detected_province IS NOT NULL"))
        with_province = result.scalar()
        
        # Sentiment analysis
        result = conn.execute(text("SELECT COUNT(*) FROM sentiment_analysis"))
        sentiments = result.scalar()
        
        return {
            'videos': videos,
            'comments': comments,
            'with_province': with_province,
            'sentiments': sentiments
        }

def show_video_list(db):
    """Tampilkan daftar video"""
    print_header("📹 DAFTAR VIDEO")
    
    with db.engine.connect() as conn:
        result = conn.execute(text("""
            SELECT v.id, v.video_id, v.title, COUNT(c.id) as total_comments
            FROM videos v
            LEFT JOIN comments c ON v.id = c.video_id
            GROUP BY v.id
            ORDER BY v.id DESC
        """))
        
        videos = result.fetchall()
        
        if not videos:
            print_info("Tidak ada video di database")
            return
        
        print(f"\n{'ID':<5} {'Video ID':<20} {'Title':<30} {'Komentar':<10}")
        print("-"*70)
        for v in videos:
            title = v[2][:27] + '...' if v[2] and len(v[2]) > 30 else v[2] or '-'
            print(f"{v[0]:<5} {v[1]:<20} {title:<30} {v[3]:<10}")
        print("-"*70)

def delete_all_comments(db):
    """Hapus semua komentar"""
    print_header("⚠️ HAPUS SEMUA KOMENTAR")
    print_warning("Tindakan ini akan menghapus SEMUA komentar!")
    print_warning("Data tidak bisa dikembalikan!")
    
    # Tampilkan statistik sebelum hapus
    stats = get_database_stats(db)
    print(f"\n📊 Data yang akan dihapus:")
    print(f"   • Komentar: {stats['comments']}")
    print(f"   • Sentimen: {stats['sentiments']}")
    
    confirm = input("\nKetik 'DELETE' untuk konfirmasi: ").strip()
    if confirm == "DELETE":
        confirm2 = input("YAKIN? (y/n): ").strip().lower()
        if confirm2 == 'y':
            with db.engine.connect() as conn:
                # Hapus sentiment analysis dulu (foreign key)
                result = conn.execute(text("DELETE FROM sentiment_analysis"))
                sent_deleted = result.rowcount
                
                # Hapus comments
                result = conn.execute(text("DELETE FROM comments"))
                comm_deleted = result.rowcount
                
                conn.commit()
                
                print_success(f"{comm_deleted} komentar dihapus")
                print_success(f"{sent_deleted} data sentimen dihapus")
        else:
            print_info("Dibatalkan")
    else:
        print_info("Dibatalkan")

def delete_comments_by_video(db):
    """Hapus komentar berdasarkan video"""
    print_header("🗑️ HAPUS KOMENTAR PER VIDEO")
    
    # Tampilkan daftar video dulu
    show_video_list(db)
    
    try:
        video_id = int(input("\nMasukkan ID video: ").strip())
        
        # Cek video
        with db.engine.connect() as conn:
            result = conn.execute(text("SELECT id, video_id, title FROM videos WHERE id = :vid"), {"vid": video_id})
            video = result.first()
            
            if not video:
                print_error(f"Video dengan ID {video_id} tidak ditemukan")
                return
            
            print(f"\n📹 Video: {video[2] or video[1]}")
            
            # Hitung komentar
            result = conn.execute(text("SELECT COUNT(*) FROM comments WHERE video_id = :vid"), {"vid": video_id})
            count = result.scalar()
            
            if count == 0:
                print_info("Tidak ada komentar untuk video ini")
                return
            
            print(f"📊 Akan menghapus {count} komentar")
            
            confirm = input("\nLanjutkan? (y/n): ").strip().lower()
            if confirm == 'y':
                # Hapus sentiment analysis
                result = conn.execute(text("""
                    DELETE FROM sentiment_analysis 
                    WHERE comment_id IN (SELECT id FROM comments WHERE video_id = :vid)
                """), {"vid": video_id})
                sent_deleted = result.rowcount
                
                # Hapus comments
                result = conn.execute(text("DELETE FROM comments WHERE video_id = :vid"), {"vid": video_id})
                comm_deleted = result.rowcount
                
                conn.commit()
                
                print_success(f"{comm_deleted} komentar dihapus")
                print_success(f"{sent_deleted} data sentimen dihapus")
                
                # Tanya apakah video juga mau dihapus
                delete_video = input("\nHapus juga data videonya? (y/n): ").strip().lower()
                if delete_video == 'y':
                    result = conn.execute(text("DELETE FROM videos WHERE id = :vid"), {"vid": video_id})
                    conn.commit()
                    print_success("Video dihapus")
            else:
                print_info("Dibatalkan")
                
    except ValueError:
        print_error("ID tidak valid")

def delete_comments_by_province(db):
    """Hapus komentar berdasarkan provinsi"""
    print_header("🗑️ HAPUS KOMENTAR PER PROVINSI")
    
    with db.engine.connect() as conn:
        # Tampilkan provinsi yang ada
        result = conn.execute(text("""
            SELECT detected_province, COUNT(*) 
            FROM comments 
            WHERE detected_province IS NOT NULL
            GROUP BY detected_province
            ORDER BY COUNT(*) DESC
        """))
        
        provinces = result.fetchall()
        
        if not provinces:
            print_info("Tidak ada komentar dengan provinsi")
            return
        
        print("\n📋 PROVINSI YANG ADA:")
        for prov, count in provinces:
            print(f"   • {prov}: {count} komentar")
        
        province = input("\nMasukkan nama provinsi: ").strip().upper()
        
        # Cek apakah provinsi ada
        result = conn.execute(text("SELECT COUNT(*) FROM comments WHERE detected_province = :prov"), {"prov": province})
        count = result.scalar()
        
        if count == 0:
            print_error(f"Tidak ada komentar dari provinsi {province}")
            return
        
        print(f"\n📊 Akan menghapus {count} komentar dari {province}")
        
        confirm = input("\nLanjutkan? (y/n): ").strip().lower()
        if confirm == 'y':
            # Hapus sentiment analysis
            result = conn.execute(text("""
                DELETE FROM sentiment_analysis 
                WHERE comment_id IN (SELECT id FROM comments WHERE detected_province = :prov)
            """), {"prov": province})
            sent_deleted = result.rowcount
            
            # Hapus comments
            result = conn.execute(text("DELETE FROM comments WHERE detected_province = :prov"), {"prov": province})
            comm_deleted = result.rowcount
            
            conn.commit()
            
            print_success(f"{comm_deleted} komentar dihapus")
            print_success(f"{sent_deleted} data sentimen dihapus")
        else:
            print_info("Dibatalkan")

def delete_old_comments(db):
    """Hapus komentar lama"""
    print_header("🗑️ HAPUS KOMENTAR LAMA")
    
    try:
        days = int(input("Hapus komentar lebih dari berapa hari? (default 30): ").strip() or "30")
        
        with db.engine.connect() as conn:
            # Hitung komentar yang akan dihapus
            result = conn.execute(text("""
                SELECT COUNT(*) FROM comments 
                WHERE comment_date < DATE_SUB(NOW(), INTERVAL :days DAY)
            """), {"days": days})
            count = result.scalar()
            
            if count == 0:
                print_info(f"Tidak ada komentar lebih dari {days} hari")
                return
            
            print(f"📊 Akan menghapus {count} komentar yang lebih dari {days} hari")
            
            confirm = input("\nLanjutkan? (y/n): ").strip().lower()
            if confirm == 'y':
                # Hapus sentiment analysis
                result = conn.execute(text("""
                    DELETE FROM sentiment_analysis 
                    WHERE comment_id IN (
                        SELECT id FROM comments 
                        WHERE comment_date < DATE_SUB(NOW(), INTERVAL :days DAY)
                    )
                """), {"days": days})
                sent_deleted = result.rowcount
                
                # Hapus comments
                result = conn.execute(text("""
                    DELETE FROM comments 
                    WHERE comment_date < DATE_SUB(NOW(), INTERVAL :days DAY)
                """), {"days": days})
                comm_deleted = result.rowcount
                
                conn.commit()
                
                print_success(f"{comm_deleted} komentar lama dihapus")
                print_success(f"{sent_deleted} data sentimen dihapus")
            else:
                print_info("Dibatalkan")
                
    except ValueError:
        print_error("Input tidak valid")

def reset_database(db):
    """Reset database - hapus semua data"""
    print_header("⚠️ RESET DATABASE - HAPUS SEMUA DATA")
    print_warning("⚠️⚠️⚠️ PERINGATAN EKSTREM ⚠️⚠️⚠️")
    print_warning("Tindakan ini akan menghapus SEMUA data dari SEMUA tabel!")
    print_warning("Data tidak bisa dikembalikan!")
    print_warning("Termasuk: videos, comments, sentiment_analysis, dll.")
    
    stats = get_database_stats(db)
    print(f"\n📊 Data yang akan dihapus:")
    print(f"   • Videos: {stats['videos']}")
    print(f"   • Comments: {stats['comments']}")
    print(f"   • Sentimen: {stats['sentiments']}")
    
    confirm1 = input("\nKetik 'RESET DATABASE' untuk konfirmasi: ").strip()
    if confirm1 == "RESET DATABASE":
        confirm2 = input("YAKIN 100%? (ketik 'YES'): ").strip()
        if confirm2 == "YES":
            confirm3 = input("TERAKHIR KALI: Lanjutkan reset? (y/n): ").strip().lower()
            if confirm3 == 'y':
                with db.engine.connect() as conn:
                    # Matikan foreign key check
                    conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
                    
                    # Hapus semua data
                    tables = ['sentiment_analysis', 'comments', 'viral_predictions', 
                              'regional_stats', 'daily_trends', 'videos']
                    
                    for table in tables:
                        try:
                            result = conn.execute(text(f"DELETE FROM {table}"))
                            deleted = result.rowcount
                            if deleted > 0:
                                print(f"   ✅ {table}: {deleted} baris dihapus")
                        except Exception as e:
                            print(f"   ⚠️ {table}: {e}")
                    
                    # Aktifkan foreign key check
                    conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
                    conn.commit()
                
                print_success("\nSEMUA DATA BERHASIL DIHAPUS!")
            else:
                print_info("Dibatalkan")
        else:
            print_info("Dibatalkan")
    else:
        print_info("Dibatalkan")

def show_statistics(db):
    """Tampilkan statistik database"""
    print_header("📊 STATISTIK DATABASE")
    
    stats = get_database_stats(db)
    
    print(f"\n📹 Videos: {stats['videos']}")
    print(f"💬 Comments: {stats['comments']}")
    print(f"📍 Comments with province: {stats['with_province']}")
    print(f"📊 Sentiment analysis: {stats['sentiments']}")
    
    # Distribusi sentimen
    if stats['sentiments'] > 0:
        with db.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT sentiment, COUNT(*) 
                FROM sentiment_analysis 
                GROUP BY sentiment
            """))
            print("\n📊 Distribusi sentimen:")
            for row in result:
                print(f"   • {row[0]}: {row[1]}")

def main():
    """Menu utama"""
    print_header("🗑️ TOOLS HAPUS DATA DATABASE")
    
    # Inisialisasi database
    try:
        db = DatabaseManager()
    except Exception as e:
        print_error(f"Gagal konek ke database: {e}")
        return
    
    while True:
        print("\n" + "="*60)
        print("📋 MENU UTAMA")
        print("="*60)
        print("1. Lihat statistik database")
        print("2. Lihat daftar video")
        print("3. Hapus SEMUA komentar")
        print("4. Hapus komentar berdasarkan video")
        print("5. Hapus komentar berdasarkan provinsi")
        print("6. Hapus komentar lama (>X hari)")
        print("7. RESET DATABASE (hapus semua data)")
        print("0. Keluar")
        print("="*60)
        
        choice = input("\nPilih menu (0-7): ").strip()
        
        if choice == "0":
            print_info("Keluar dari program")
            break
        elif choice == "1":
            show_statistics(db)
        elif choice == "2":
            show_video_list(db)
        elif choice == "3":
            delete_all_comments(db)
        elif choice == "4":
            delete_comments_by_video(db)
        elif choice == "5":
            delete_comments_by_province(db)
        elif choice == "6":
            delete_old_comments(db)
        elif choice == "7":
            reset_database(db)
        else:
            print_error("Pilihan tidak valid")
        
        input("\nTekan Enter untuk melanjutkan...")

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