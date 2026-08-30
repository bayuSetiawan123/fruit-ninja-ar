# 🍉 Fruit Ninja AR

**Fruit Ninja AR** adalah game berbasis **Augmented Reality (AR)** yang dikembangkan menggunakan Python. Pemain dapat memotong buah yang muncul melalui kamera dengan gerakan tangan, serta menghindari bom agar mendapatkan skor setinggi mungkin.

## 🎮 Fitur

* 🍎 Pemotongan buah menggunakan gerakan tangan
* 💣 Bom sebagai obstacle
* 🏆 Sistem high score
* 🔊 Background music dan sound effect
* 🍌 Berbagai jenis buah
* ✂️ Animasi buah ketika berhasil dipotong
* 📸 Penyimpanan snapshot gameplay
* 🎯 Sistem perhitungan skor

## 🛠️ Teknologi

* **Python**
* **OpenCV**
* **MediaPipe**
* **Pygame**
* **NumPy**

## 📂 Struktur Project

```text
fruit-ninja-ar/
├── assets/
│   ├── apel.png
│   ├── pisang.png
│   ├── jeruk.png
│   ├── kiwi.png
│   ├── lemon.png
│   ├── nanas.png
│   ├── stroberi.png
│   ├── bomb.png
│   └── audio/
│
├── snapshots/
│   └── gameplay screenshots
│
├── main.py
├── backup.py
├── highscore.txt
├── requirements.txt
├── .gitignore
└── README.md
```

## 🚀 Instalasi

Clone repository:

```bash
git clone https://github.com/bayuSetiawan123/fruit-ninja-ar.git
```

Masuk ke folder project:

```bash
cd fruit-ninja-ar
```

Buat virtual environment:

```bash
python -m venv venv
```

Aktifkan virtual environment di Windows:

```powershell
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## ▶️ Menjalankan Game

Setelah semua dependencies ter-install, jalankan:

```bash
python main.py
```

Pastikan kamera/webcam tersedia karena game menggunakan kamera untuk fitur Augmented Reality.

## 📸 Screenshots

Beberapa hasil gameplay tersedia di folder [`snapshots`](snapshots/).

## 🎓 Project Information

Project ini dibuat sebagai tugas mata kuliah **Virtual dan Augmented Reality**.

## 👨‍💻 Author

**Bayu Setiawan**

GitHub: [@bayuSetiawan123](https://github.com/bayuSetiawan123)
