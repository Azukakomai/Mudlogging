/**
 * UGM Skripsi Slide Deck Interactive Engine
 * Author: Mohammad Azka Khairur Rahman
 */

let currentSlideIndex = 0;
let totalSlides = 0;
let isLaserActive = false;
let presentationStartTime = null;
let timerInterval = null;

// Speaker notes dictionary for each slide
const SPEAKER_NOTES = {
  1: `Selamat pagi/siang Bapak/Ibu Dewan Penguji dan Pembimbing. 
Perkenalkan saya Mohammad Azka Khairur Rahman. 
Hari ini saya akan mempresentasikan proposal/seminar hasil skripsi saya dengan judul: 
"Aplikasi Visualisasi Data Gas While Drilling untuk Prediksi Tipe Hidrokarbon Menggunakan Algoritma Deterministik" di bawah bimbingan Dr. Techn. Khabib Mustofa.`,

  2: `Berikut adalah garis besar presentasi hari ini yang terbagi dalam 7 agenda utama:
1. Latar Belakang & Rumusan Masalah
2. Tujuan & Manfaat Penelitian
3. Tinjauan Pustaka & Research Gap
4. Metodologi SDLC 5-Phase
5. Arsitektur Sistem & Formulasi Matematis
6. Implementasi Antarmuka 21-Track
7. Rencana Evaluasi, Timeline & Gantt Chart.`,

  3: `Latar Belakang:
- Operasi pemboran eksplorasi minyak & gas bumi berbiaya sangat tinggi (puluhan juta USD).
- Gas While Drilling (GWD) merupakan data kromatografi pertama ($C_1 - C_5$) yang keluar saat batuan dihancurkan oleh mata bor.
- Masalah utama: GWD selama ini hanya dijadikan log pemantauan sekunder. Keputusan fluida ditunda sampai Wireline Logging pasca pemboran yang memakan waktu rig standby berhari-hari dan biaya ratusan ribu USD.`,

  4: `Problem Statement & Research Gap:
- Software komersial (Techlog, Geolog, WellCAD, LogPlot) sebagian besar adalah passive data plotters. Tidak memiliki otomasi klasifikasi fluida multi-rasio.
- Machine learning black-box ditolak pada sertifikasi cadangan resmi karena melanggar SPE PRMS Chapter 4 (wajib auditable dan deterministik).
- Kebutuhan: Dibutuhkan platform open-source berbasis web yang deterministik, traceable 100%, dan instan (< 5 detik).`,

  5: `Tujuan Penelitian:
1. Membangun engine Python untuk 16+ indikator rasio gas (Pixler, Haworth, GOW, WBS, GOR) dan majority-vote classification.
2. Membangun UI visualisasi interaktif 21-track yang dilengkapi Column Manager dan Formula Manager.
3. Membuktikan kepatuhan penuh terhadap SOP industri (SPE, AAPG, SPE PRMS, API RP 31A).
4. Mengoptimalkan throughput pipeline < 5.0 detik dan skor usability > 68/100.`,

  6: `Manfaat Penelitian:
- Industri: Early fluid intelligence, menghemat jutaan dolar biaya rig standby, menghilangkan ketergantungan lisensi software mahal ($20k-$50k/tahun).
- Akademik: Demokratisasi akses perangkat lunak petrofisika bagi mahasiswa dan peneliti, serta media pedagogi interaktif di bidang geosains dan komputasi.`,

  7: `Tinjauan Pustaka & State of the Art:
- Membandingkan Commercial Workstation, Drafting Tools, Open-Source Plotters, Machine Learning, dan Proposisi Skripsi ini.
- Skripsi ini mengisi gap: menyediakan automated forecasting multi-rasio yang deterministik, open-source, dan berantarmuka modern.`,

  8: `Metodologi Penelitian: 5-Phase SDLC
1. System Requirements: Analisis kebutuhan wellsite geologist & petrophysicist.
2. Architectural Design: Decoupled 3-layer architecture.
3. Software Implementation: Ingestion, Engine, Evaluation, & UI.
4. System Verification: Unit test mathematical tensor & ground-truth validation.
5. Release & Packaging: Pinned requirements.txt & open-source repository.`,

  9: `Arsitektur Sistem:
- 3 Lapisan Modular: Ingestion Layer (parser.py), Deterministic Logic Layer (engine.py), Reactive UI Layer (app.py).
- Seluruh pemrosesan berjalan in-memory menggunakan vectorized NumPy/Pandas untuk mencegah disk I/O bottleneck.`,

  10: `Formulasi Matematis:
- Rasio Pixler (R1-R5), Haworth Show Ratios (Wh, Bh, Ch), Dryness, Carbon Index.
- Composite indicators: GOW, GOW_noTG, WBS, GOR.
- Majority-Vote Decision Logic yang mengintegrasikan 8 parameter sekaligus untuk menentukan Gas, Oil, atau Water.`,

  11: `Implementasi Antarmuka 21-Track:
- Sticky Measured Depth (MD) column di kiri.
- 21 kolom grafik continuous independen.
- Synchronized crosshair cursor: hovering pada satu kedalaman memunculkan garis dan tooltip sinkron di seluruh 21 track.
- Quick KPI performance summary bar di bagian atas.`,

  12: `Fitur Unggulan: Column Configuration Manager
- Fleksibilitas tinggi bagi petrofisis untuk mengaktifkan/menonaktifkan track tertentu.
- Kemampuan menambahkan custom column dengan formula matematis buatan sendiri dan quick variable tokens.`,

  13: `Fitur Unggulan: Petrophysical Formula Manager
- Pengguna dapat mengedit formula rasio gas secara langsung.
- Mengatur batas ambang klasifikasi (Gas, Oil, Water).
- Live calculation preview yang memvalidasi hasil kalkulasi terhadap baris data sumur aktif secara instan.`,

  14: `Rencana Pengujian & Evaluasi:
1. Mathematical Verification: Zero drift pada unit test.
2. Empirical Ground-Truth: Evaluasi Accuracy, Precision, Recall, Macro-F1 terhadap data Wireline Formation Tester (RFT/MDT).
3. Latency Benchmark: Target < 5.0s (Hasil aktual: ~12.96 ms untuk 3000m).
4. Usability Testing: Kuesioner 10 item dengan target S_bar > 68/100.`,

  15: `Timeline & Gantt Chart:
- 8 fase terencana dari Juli hingga November: Literature Review, Schema Definition, Architecture, Parsing, Algorithm, UI, Testing, hingga Writing & Submission.`,

  16: `Kesimpulan & Penutup:
- Sistem ini berhasil merealisasikan visualisasi multi-track 21 parameter dan klasifikasi hidrokarbon deterministik berbasis web yang cepat, auditable, dan sesuai SOP industri.
- Terima kasih atas perhatian Bapak/Ibu Dewan Penguji. Saya siap menerima masukan, saran, dan pertanyaan.`
};

document.addEventListener('DOMContentLoaded', () => {
  const slides = document.querySelectorAll('.slide-canvas');
  totalSlides = slides.length;
  
  // Scale canvas to fit viewport
  resizeSlideScale();
  window.addEventListener('resize', resizeSlideScale);

  // Show first slide
  showSlide(0);

  // Build overview grid
  buildOverviewGrid();

  // Keyboard navigation
  setupKeyboardShortcuts();

  // Laser pointer tracking
  setupLaserPointer();

  // Start presentation timer
  startTimer();
});

/**
 * Responsive Scaling to maintain exact 16:9 aspect ratio without distortion
 */
function resizeSlideScale() {
  const container = document.getElementById('presentationStage');
  if (!container) return;

  const w = window.innerWidth;
  const h = window.innerHeight;
  const targetW = 1280;
  const targetH = 720;

  const scaleX = (w * 0.96) / targetW;
  const scaleY = (h * 0.94) / targetH;
  const scale = Math.min(scaleX, scaleY);

  document.querySelectorAll('.slide-canvas').forEach(slide => {
    slide.style.transform = `scale(${scale})`;
  });
}

/**
 * Display a specific slide by index (0-based)
 */
function showSlide(index) {
  const slides = document.querySelectorAll('.slide-canvas');
  if (index < 0 || index >= slides.length) return;

  slides.forEach((s, idx) => {
    s.classList.remove('active');
    if (idx === index) {
      s.classList.add('active');
    }
  });

  currentSlideIndex = index;
  updateNavigationUI();
  updatePresenterNotes();
}

function nextSlide() {
  if (currentSlideIndex < totalSlides - 1) {
    showSlide(currentSlideIndex + 1);
  }
}

function prevSlide() {
  if (currentSlideIndex > 0) {
    showSlide(currentSlideIndex - 1);
  }
}

/**
 * Update UI Elements (Counters, Progress Bar)
 */
function updateNavigationUI() {
  const counterEl = document.getElementById('slideCounterBadge');
  if (counterEl) {
    counterEl.innerText = `${currentSlideIndex + 1} / ${totalSlides}`;
  }

  const progressBar = document.getElementById('deckProgressBar');
  if (progressBar && totalSlides > 1) {
    const pct = ((currentSlideIndex) / (totalSlides - 1)) * 100;
    progressBar.style.width = `${pct}%`;
  }
}

/**
 * Keyboard Navigation & Hotkeys
 */
function setupKeyboardShortcuts() {
  window.addEventListener('keydown', (e) => {
    // Ignore if typing in an input
    if (['input', 'textarea', 'select'].includes(e.target.tagName.toLowerCase())) return;

    switch (e.key) {
      case 'ArrowRight':
      case 'ArrowDown':
      case ' ':
      case 'PageDown':
      case 'Enter':
        e.preventDefault();
        nextSlide();
        break;

      case 'ArrowLeft':
      case 'ArrowUp':
      case 'PageUp':
      case 'Backspace':
        e.preventDefault();
        prevSlide();
        break;

      case 'Home':
        e.preventDefault();
        showSlide(0);
        break;

      case 'End':
        e.preventDefault();
        showSlide(totalSlides - 1);
        break;

      case 'f':
      case 'F':
        toggleFullscreen();
        break;

      case 'o':
      case 'O':
        toggleOverviewModal();
        break;

      case 'p':
      case 'P':
        togglePresenterModal();
        break;

      case 'l':
      case 'L':
        toggleLaserPointer();
        break;

      case 'b':
      case 'B':
      case '.':
        toggleBlackout();
        break;

      case 'Escape':
        closeAllModals();
        break;
    }
  });
}

/**
 * Fullscreen Controller
 */
function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen().catch(err => {});
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen();
    }
  }
}

/**
 * Slide Overview Grid (Press 'O')
 */
function buildOverviewGrid() {
  const container = document.getElementById('overviewGridMount');
  if (!container) return;
  container.innerHTML = '';

  const slides = document.querySelectorAll('.slide-canvas');
  slides.forEach((slide, idx) => {
    const titleEl = slide.querySelector('.slide-title-text');
    const catEl = slide.querySelector('.slide-category-tag');
    const title = titleEl ? titleEl.innerText : (idx === 0 ? 'Judul Skripsi' : `Slide ${idx + 1}`);
    const cat = catEl ? catEl.innerText : 'UGM Skripsi';

    const card = document.createElement('div');
    card.className = `overview-card ${idx === currentSlideIndex ? 'current' : ''}`;
    card.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <span style="font-size: 0.68rem; color: var(--accent-cyan); font-weight: 700;">#${idx + 1}</span>
        <span style="font-size: 0.65rem; color: var(--text-muted);">${cat}</span>
      </div>
      <strong style="font-size: 0.84rem; color: #fff; line-height: 1.3;">${title}</strong>
    `;
    card.onclick = () => {
      showSlide(idx);
      toggleOverviewModal();
    };
    container.appendChild(card);
  });
}

function toggleOverviewModal() {
  const m = document.getElementById('overviewModal');
  if (m) {
    m.classList.toggle('active');
    if (m.classList.contains('active')) {
      buildOverviewGrid();
    }
  }
}

/**
 * Presenter Mode (Press 'P')
 */
function togglePresenterModal() {
  const m = document.getElementById('presenterModal');
  if (m) {
    m.classList.toggle('active');
    if (m.classList.contains('active')) {
      updatePresenterNotes();
    }
  }
}

function updatePresenterNotes() {
  const notesText = SPEAKER_NOTES[currentSlideIndex + 1] || 'No speaker notes for this slide.';
  const notesEl = document.getElementById('presenterNotesText');
  if (notesEl) {
    notesEl.innerText = notesText;
  }

  const presSlideTitle = document.getElementById('presenterCurrentSlideTitle');
  if (presSlideTitle) {
    const slides = document.querySelectorAll('.slide-canvas');
    const title = slides[currentSlideIndex]?.querySelector('.slide-title-text')?.innerText || `Slide ${currentSlideIndex + 1}`;
    presSlideTitle.innerText = `${currentSlideIndex + 1}. ${title}`;
  }

  const nextSlideTitle = document.getElementById('presenterNextSlideTitle');
  if (nextSlideTitle) {
    if (currentSlideIndex < totalSlides - 1) {
      const slides = document.querySelectorAll('.slide-canvas');
      const nextTitle = slides[currentSlideIndex + 1]?.querySelector('.slide-title-text')?.innerText || `Slide ${currentSlideIndex + 2}`;
      nextSlideTitle.innerText = `Next: ${nextTitle}`;
    } else {
      nextSlideTitle.innerText = `Next: [End of Presentation]`;
    }
  }
}

/**
 * Presentation Timer
 */
function startTimer() {
  presentationStartTime = Date.now();
  if (timerInterval) clearInterval(timerInterval);

  timerInterval = setInterval(() => {
    const elapsed = Math.floor((Date.now() - presentationStartTime) / 1000);
    const mins = String(Math.floor(elapsed / 60)).padStart(2, '0');
    const secs = String(elapsed % 60).padStart(2, '0');
    
    const timerEl = document.getElementById('presenterTimerDisplay');
    if (timerEl) {
      timerEl.innerText = `${mins}:${secs}`;
    }

    const clockEl = document.getElementById('presenterClockDisplay');
    if (clockEl) {
      const now = new Date();
      clockEl.innerText = now.toLocaleTimeString();
    }
  }, 1000);
}

function resetTimer() {
  presentationStartTime = Date.now();
}

/**
 * Laser Pointer Controller (Press 'L')
 */
function toggleLaserPointer() {
  isLaserActive = !isLaserActive;
  const laser = document.getElementById('laserPointer');
  if (laser) {
    laser.style.display = isLaserActive ? 'block' : 'none';
  }
}

function setupLaserPointer() {
  const laser = document.getElementById('laserPointer');
  window.addEventListener('mousemove', (e) => {
    if (isLaserActive && laser) {
      laser.style.left = `${e.clientX}px`;
      laser.style.top = `${e.clientY}px`;
    }
  });
}

/**
 * Blackout Screen Controller (Press 'B')
 */
function toggleBlackout() {
  const screen = document.getElementById('blackoutScreen');
  if (screen) {
    screen.classList.toggle('active');
  }
}

function closeAllModals() {
  const overview = document.getElementById('overviewModal');
  if (overview) overview.classList.remove('active');

  const presenter = document.getElementById('presenterModal');
  if (presenter) presenter.classList.remove('active');

  const blackout = document.getElementById('blackoutScreen');
  if (blackout) blackout.classList.remove('active');
}

/**
 * Print Presentation to PDF
 */
function printSlideDeck() {
  window.print();
}
