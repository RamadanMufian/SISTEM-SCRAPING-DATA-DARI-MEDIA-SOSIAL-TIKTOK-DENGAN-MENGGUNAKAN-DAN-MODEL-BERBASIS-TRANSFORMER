# 🚀 TikTok Sentiment & Geospatial Analysis Pro (V6.1)

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Framework-black?style=for-the-badge&logo=flask&logoColor=white)
![Transformers](https://img.shields.io/badge/Transformers-HuggingFace-yellow?style=for-the-badge&logo=huggingface&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-AI-red?style=for-the-badge&logo=pytorch&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-Scraping-green?style=for-the-badge&logo=selenium&logoColor=white)

Sistem analisis sentimen tingkat lanjut yang dirancang khusus untuk media sosial TikTok. Sistem ini menggabungkan **Deep Learning (Transformer)**, **Geospatial Intelligence**, dan **Viral Analytics** untuk memberikan wawasan mendalam tentang opini publik secara real-time.

---

## 🌟 Key Features

### 🧠 Advanced Sentiment Engine (V6.1)
Menggunakan pendekatan **Multi-Model Ensemble** yang dioptimalkan untuk bahasa gaul (slang) Indonesia:
- **IndoBERT Base P1**: Model bahasa Indonesia yang sangat akurat.
- **RoBERTa Sentiment**: Classifier khusus untuk sentimen.
- **Random Forest Validator**: Memvalidasi hasil AI dengan fitur ekstraksi teks manual.
- **Expert Hard Rules**: Menangani sarkasme dan kata-kata slang yang sering muncul di TikTok.

### 🗺️ Geospatial Detection
Mampu mendeteksi lokasi pengguna hingga level Provinsi dan Kota berdasarkan:
- Bio pengguna.
- Nama tampilan.
- Konteks teks komentar.
- Fokus khusus pada wilayah **Bengkulu** dengan Heatmap interaktif.

### 📈 Viral & Trend Analytics
- **Video Performance Index**: Menganalisis tingkat keviralitasan video.
- **Time Series charts**: Melihat perkembangan sentimen dari hari ke hari.
- **Word Clouds**: Mengidentifikasi kata kunci yang paling sering dibicarakan.
- **Top Highlights**: Menampilkan komentar paling berpengaruh (most liked) per kategori sentimen.

### 🏢 Enterprise Ready
- **Role-Based Access Control (RBAC)**: Sistem login admin yang aman.
- **Database Management**: Penyimpanan riwayat scraping dan analisis yang terstruktur.
- **Scraping Engine**: Mampu mengambil ribuan komentar dengan cepat dan aman.

---

## 🛠️ Tech Stack

- **Backend**: Python, Flask, SQLAlchemy
- **AI/ML**: PyTorch, HuggingFace Transformers (IndoBERT, RoBERTa), Scikit-learn
- **Data**: Pandas, NumPy
- **Scraping**: Selenium, Custom Scraper
- **Visualization**: Folium (Maps), Chart.js
- **Frontend**: HTML5, CSS3 (Premium UI), JavaScript

---

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/RamadanMufian/SISTEM-SCRAPING-DATA-DARI-MEDIA-SOSIAL-TIKTOK-DENGAN-MENGGUNAKAN-DAN-MODEL-BERBASIS-TRANSFORMER.git
   cd SISTEM-SCRAPING-DATA-DARI-MEDIA-SOSIAL-TIKTOK-DENGAN-MENGGUNAKAN-DAN-MODEL-BERBASIS-TRANSFORMER
   ```

2. **Create Virtual Environment & Install Dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   Buat file `.env` dan isi variabel berikut:
   ```env
   SECRET_KEY=your_secret_key_here
   DATABASE_URL=sqlite:///tiktok_db.sqlite3
   ```

4. **Initialize Database**
   ```bash
   python initialize_app.py
   ```

5. **Run the Application**
   ```bash
   python app.py
   ```
   Buka `http://localhost:5002` di browser Anda.

---

## 📖 Cara Penggunaan

1. **Login**: Masuk menggunakan akun admin.
2. **Scraper**: Masukkan link video TikTok yang ingin dianalisis.
3. **Analisis**: Tunggu sistem melakukan penarikan data dan klasifikasi AI.
4. **Dashboard**: Lihat grafik sentimen, heatmap geospasial, dan daftar komentar yang telah dianalisis.
5. **Heatmap Bengkulu**: Buka menu Heatmap untuk melihat persepsi publik khusus di wilayah Provinsi Bengkulu.

---

## 👤 Author
**Ramadan Mufian**
- GitHub: [@RamadanMufian](https://github.com/RamadanMufian)

---

## 📄 License
Project ini dilisensikan di bawah MIT License - lihat file [LICENSE](LICENSE) untuk detailnya.

---
*Dibuat dengan ❤️ untuk kemajuan analisis data di Indonesia.*