 INSTALASI DEPENDENCIES     
 Buat Virtual Environment
 # Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

 KONFIGURASI DATABASE
 Buat Database
 -- Login ke MySQL
mysql -u root -p

-- Buat database
CREATE DATABASE tiktok_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Cek database
SHOW DATABASES;

# Jalankan Python shell
python

# Inisialisasi database
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
...     print("Database berhasil dibuat!")
...
>>> exit()



 Setup Cookie untuk Scraping TikTok
 Buka TikTok.com di Chrome/Firefox

Login dengan akun Anda

Install ekstensi "Get cookies.txt" dari Chrome Web Store

Klik ekstensi → Export → Simpan sebagai cookies.txt di folder project