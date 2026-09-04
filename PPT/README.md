# Slide Presentasi Skripsi (HTML Deck)
**Universitas Gadjah Mada (UGM) • Departemen Ilmu Komputer dan Elektronika**

**Judul Skripsi:**  
*Aplikasi Visualisasi Data Gas While Drilling untuk Prediksi Tipe Hidrokarbon Menggunakan Algoritma Deterministik*  
*(Gas While Drilling Data Visualization Application for Hydrocarbon Type Prediction Using Deterministic Algorithms)*

**Penyusun:** Mohammad Azka Khairur Rahman (NIM: 23/511608/PA/21830)  
**Pembimbing:** Dr. Techn. Khabib Mustofa, S.Si., M.Kom.

---

## 🖥️ Cara Menjalankan Slide Presentasi

### Opsi 1: Menggunakan Python Server Launcher (Direkomendasikan)
Buka terminal dan jalankan:
```bash
py PPT/server.py
```
Aplikasi slide deck akan otomatis terbuka di browser pada URL `http://localhost:8060`.

### Opsi 2: Buka Langsung di Browser
Buka file `PPT/index.html` langsung di browser Anda (Chrome, Edge, Firefox, atau Safari).

---

## ⌨️ Kontrol Navigasi & Shortcut Presenter

| Tombol / Tombol Pintas | Aksi |
| :--- | :--- |
| `→` / `Space` / `PageDown` / `Enter` | Slide Berikutnya (*Next Slide*) |
| `←` / `PageUp` / `Backspace` | Slide Sebelumnya (*Previous Slide*) |
| `Home` | Kembali ke Slide Pertama (Cover) |
| `End` | Langsung ke Slide Terakhir (Penutup) |
| `F` | Toggle Layar Penuh (*Fullscreen Mode*) |
| `O` | Toggle *Slide Grid Overview* (Pilih slide secara visual) |
| `P` | Toggle *Presenter View* (Catatan pembicara + Stopwatch timer + Preview slide berikutnya) |
| `L` | Toggle *Laser Pointer Mode* (Titik laser merah interaktif mengikuti kursor mouse) |
| `B` atau `.` | Toggle *Blackout Screen* (Layar hitam saat sesi tanya jawab/diskusi) |
| `Print / Ctrl+P` | Cetak langsung ke PDF berkualitas tinggi (*High-Res Slides*) |

---

## 📑 Struktur Slide Presentasi (16 Slide)

1. **Slide 1: Cover / Judul Skripsi** (Logo UGM, Judul Indonesia & Inggris, Identitas Peneliti & Pembimbing)
2. **Slide 2: Agenda & Garis Besar Pembahasan** (7 Bagian Utama)
3. **Slide 3: Latar Belakang & Urgensi Penelitian** (Biaya eksplorasi tinggi, potensi GWD, keterbatasan wireline logging)
4. **Slide 4: Rumusan Masalah & Kesenjangan Penelitian** (Passive data plotters vs Black-box ML vs Regulasi SPE PRMS)
5. **Slide 5: Tujuan Penelitian** (4 Tujuan Utama: Engine, 21-Track UI, SOP & Audit Compliance, Latency & Usability)
6. **Slide 6: Manfaat Penelitian** (Dampak Industri Hulu Migas & Kontribusi Akademik)
7. **Slide 7: Tinjauan Pustaka & State-of-the-Art** (Tabel Perbandingan Komparatif Berbagai Platform)
8. **Slide 8: Metodologi Penelitian: 5-Phase SDLC** (Requirements, Architecture, Implementation, Verification, Release)
9. **Slide 9: Arsitektur Sistem & Aliran Data Modular** (Ingestion `parser.py`, Logic `engine.py`, UI `app.py`)
10. **Slide 10: Formulasi Matematis 16 Indikator Petrofisika** (Pixler, Haworth, GOW, WBS, Majority-Vote Classifier)
11. **Slide 11: Implementasi Antarmuka Multi-Track 21 Parameter** (Sticky Depth, Synchronized Crosshair, Facies Track)
12. **Slide 12: Fitur Unggulan 1: Column Configuration & Display Manager** (Show/Hide, Add Custom Column, Quick Tokens)
13. **Slide 13: Fitur Unggulan 2: Petrophysical Formula & Indicator Manager** (Formula Editor, Threshold Limits, Live Audit)
14. **Slide 14: Rencana Pengujian & Evaluasi Kinerja** (Unit Verification, Ground-Truth Matrix, Latency Target &lt;5s, Usability &gt;68)
15. **Slide 15: Jadwal & Timeline Penelitian** (Gantt Chart 8 Fase Juli s.d. November)
16. **Slide 16: Kesimpulan & Sesi Tanya Jawab (Q&A)** (Rekapitulasi Kontribusi & Penutup Diskusi)
