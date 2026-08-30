# 🍉 Fruit Ninja AR

**Fruit Ninja AR** adalah game berbasis **Augmented Reality (AR)** yang dikembangkan menggunakan Python. Game ini mengadaptasi konsep permainan Fruit Ninja dengan mekanisme interaksi yang unik, yaitu menggunakan **gerakan hidung pemain untuk memotong buah** yang muncul melalui kamera.

Posisi hidung pemain dideteksi secara real-time menggunakan **MediaPipe**, kemudian koordinatnya digunakan sebagai titik interaksi dengan objek buah. Ketika posisi hidung mengenai buah, sistem mendeteksi adanya interaksi dan buah akan terpotong sehingga pemain mendapatkan skor.

## 🎮 Fitur

* 👃 **Nose Tracking** — mendeteksi posisi hidung pemain secara real-time
* 🍎 **Fruit Cutting** — memotong buah dengan menggerakkan hidung
* 💣 **Bomb Obstacle** — bom yang harus dihindari
* 🏆 **High Score** — menyimpan skor tertinggi
* 🔊 **Background Music & Sound Effects**
* 🍌 **Multiple Fruits** — berbagai jenis buah
* ✂️ **Fruit Splitting** — buah terbelah ketika berhasil dipotong
* 📸 **Gameplay Snapshots**

## 👃 Mengapa Menggunakan Hidung?

Penggunaan hidung sebagai kontrol merupakan bagian dari konsep interaksi unik dalam game ini. Dibandingkan menggunakan mouse, keyboard, atau tangan, hidung dipilih sebagai **titik interaksi yang langsung berasal dari posisi wajah pemain**.

Dengan bantuan teknologi **face tracking**, pergerakan wajah dapat diterjemahkan menjadi input permainan secara real-time. Hal ini membuat pemain dapat berinteraksi dengan objek virtual hanya dengan menggerakkan kepala dan hidung di depan kamera.

Mekanisme ini juga menjadi eksperimen sederhana mengenai bagaimana **computer vision dapat digunakan sebagai metode human-computer interaction (HCI)** dalam sebuah permainan berbasis AR.

## 🧠 Cara Kerja

Secara sederhana, sistem bekerja melalui beberapa tahap:

```text
📷 Camera
   ↓
👤 Face Detection / Tracking
   ↓
👃 Nose Landmark Detection
   ↓
📍 Nose Position
   ↓
💥 Collision Detection
   ↓
🍎 Fruit Hit
   ↓
✂️ Fruit Cut + Score
```

Kamera menangkap wajah pemain secara real-time. **MediaPipe** digunakan untuk mendeteksi landmark wajah, termasuk posisi hidung. Posisi tersebut kemudian dipetakan ke koordinat permainan.

Ketika koordinat hidung berinteraksi dengan area buah, sistem menganggap buah terkena dan menjalankan efek pemotongan serta menambahkan skor pemain.

## 🛠️ Teknologi

| Teknologi     | Penggunaan                               |
| ------------- | ---------------------------------------- |
| **Python**    | Bahasa pemrograman utama                 |
| **OpenCV**    | Pengolahan kamera dan computer vision    |
| **MediaPipe** | Face tracking dan deteksi landmark wajah |
| **NumPy**     | Pengolahan data dan koordinat            |
| **Pygame**    | Game engine, rendering, audio, dan input |

## 📂 Struktur Project

```text
fruit-ninja-ar/
├── assets/
│   ├── apel.png
│   ├── apel_emas.png
│   ├── apel_half1.png
│   ├── apel_half2.png
│   ├── bomb.png
│   ├── jeruk.png
│   ├── kiwi.png
│   ├── lemon.png
│   ├── nanas.png
│   ├── pisang.png
│   ├── stroberi.png
│   └── audio files
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

Aktifkan virtual environment pada Windows:

```powershell
venv\Scripts\activate
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

## ▶️ Menjalankan Game

Jalankan program dengan:

```powershell
python main.py
```

Pastikan komputer memiliki **webcam/kamera** karena kamera digunakan untuk mendeteksi wajah dan posisi hidung pemain.

## 🎯 Cara Bermain

1. Jalankan game.
2. Izinkan akses kamera jika diminta.
3. Posisikan wajah di depan kamera.
4. Gerakkan hidung ke arah buah yang muncul.
5. Sentuhkan posisi hidung dengan buah untuk memotongnya.
6. Hindari bom.
7. Kumpulkan skor sebanyak mungkin.
8. Coba kalahkan high score.

## 📸 Screenshots

Beberapa hasil gameplay tersedia pada folder [`snapshots`](snapshots/).

## 🎓 Project Information

Project ini dibuat sebagai tugas mata kuliah **Virtual dan Augmented Reality**.

Project ini merupakan implementasi sederhana yang menggabungkan **computer vision, face tracking, dan game development** untuk menghasilkan bentuk interaksi manusia dengan objek virtual secara real-time.

## 👨‍💻 Author

**Bayu Setiawan**

GitHub: [@bayuSetiawan123](https://github.com/bayuSetiawan123)
