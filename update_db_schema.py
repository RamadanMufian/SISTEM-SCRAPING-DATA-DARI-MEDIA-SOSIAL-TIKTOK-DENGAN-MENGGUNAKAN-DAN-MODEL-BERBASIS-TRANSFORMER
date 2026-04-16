# update_db_schema.py
"""
Script untuk menambahkan kolom baru ke tabel comments
"""

from database_config import DatabaseManager
from sqlalchemy import text

db = DatabaseManager()

print("="*60)
print("🔄 UPDATE STRUKTUR DATABASE")
print("="*60)

with db.engine.connect() as conn:
    # Cek kolom yang sudah ada
    result = conn.execute(text("SHOW COLUMNS FROM comments"))
    existing_columns = [row[0] for row in result]
    print(f"📋 Kolom yang sudah ada: {existing_columns}")
    
    # Tambah kolom display_name jika belum ada
    if 'display_name' not in existing_columns:
        try:
            conn.execute(text("ALTER TABLE comments ADD COLUMN display_name VARCHAR(200)"))
            print("✅ Kolom 'display_name' ditambahkan")
        except Exception as e:
            print(f"❌ Gagal tambah display_name: {e}")
    else:
        print("ℹ️ Kolom 'display_name' sudah ada")
    
    # Tambah kolom bio jika belum ada
    if 'bio' not in existing_columns:
        try:
            conn.execute(text("ALTER TABLE comments ADD COLUMN bio TEXT"))
            print("✅ Kolom 'bio' ditambahkan")
        except Exception as e:
            print(f"❌ Gagal tambah bio: {e}")
    else:
        print("ℹ️ Kolom 'bio' sudah ada")
    
    # Tambah kolom detection_source jika belum ada
    if 'detection_source' not in existing_columns:
        try:
            conn.execute(text("ALTER TABLE comments ADD COLUMN detection_source VARCHAR(50)"))
            print("✅ Kolom 'detection_source' ditambahkan")
        except Exception as e:
            print(f"❌ Gagal tambah detection_source: {e}")
    else:
        print("ℹ️ Kolom 'detection_source' sudah ada")
    
    # Commit perubahan
    conn.commit()
    
    # Verifikasi
    result = conn.execute(text("SHOW COLUMNS FROM comments"))
    updated_columns = [row[0] for row in result]
    print(f"\n📋 Kolom setelah update: {updated_columns}")
    
print("\n✅ Update struktur database selesai!")