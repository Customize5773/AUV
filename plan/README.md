# Rencana Program — SAUVC 2027

Status: **draf pengantar untuk diskusi**, 1 Oktober 2026. Belum menjadi arsitektur final atau jadwal komitmen. Disusun dari percakapan dengan penanggung jawab Program.

Tujuan pekerjaan Program adalah mengintegrasikan Jetson, Pixhawk–ArduSub, dan kamera, kemudian membangun kemampuan robot menjalankan misi otonom secara bertahap. Fokus pertama: integrasi perangkat di meja dengan bukti pengujian yang dapat diulang.

| Dokumen | Isi |
| --- | --- |
| [Kondisi dan keputusan](01-kondisi-dan-keputusan.md) | Fakta dari pengguna, usulan, dan informasi yang belum diketahui |
| [Tahapan pekerjaan](02-tahapan-program.md) | Jobdesk, urutan kerja, ketergantungan, dan bukti selesai |
| [Opsi tiga kamera](03-opsi-kamera.md) | Alternatif penempatan dan cara memilih konfigurasi |
| [Pemeriksaan langsung Jetson](04-hasil-pemeriksaan-jetson.md) | Inventaris aktual, bukti perintah, status Docker, dan periferal |
| [Pelaksanaan BlueOS](05-blueos-tanpa-periferal.md) | Konfigurasi pengujian tanpa periferal dan status verifikasi |
| [Adaptasi BlueOS–Jetson](06-adaptasi-blueos-jetson.md) | Perapian antarmuka, suhu/platform, dan persistensi HydroShips |

**Koreksi inventaris:** sudah tersedia **3 kamera DWE**. Pembahasan 1–3 kamera adalah opsi penggunaan dari tiga unit tersebut, bukan rencana membeli kamera tambahan.

**Ketersediaan sesi saat ini:** pengguna mengonfirmasi hanya Jetson yang dapat diuji; kamera dan Pixhawk belum ada di tempat pengujian. Antarmuka dan layanan inti BlueOS 1.4.6 sudah berjalan pada `http://127.0.0.1:8080`; bukti dan batas kompatibilitas ada pada [laporan pelaksanaan](05-blueos-tanpa-periferal.md). Integrasi periferal menunggu perangkat tersedia.

Arah platform yang dipilih pengguna adalah menjalankan/menyesuaikan **BlueOS pada Jetson**. Pemeriksaan langsung mengidentifikasi Jetson Orin NX kelas 16 GB, Ubuntu 22.04.5, dan L4T 36.4.7. Akses Docker telah diberikan dan pengujian tanpa periferal berhasil dengan keterbatasan yang tercatat; ini belum validasi robot lengkap. Model Pixhawk dan DWE belum diketahui karena belum terdeteksi. Jumlah thruster, ESC, dan sensor kedalaman belum dikonfirmasi.

Sumber aturan dan gambar arena tersedia dalam [riset SAUVC](../doc/README.md) dan [indeks gambar rulebook](../doc/sources/rulebook-images/README.md). Acuan teknis lomba yang ditelaah masih edisi 2026; perubahan aturan 2027 perlu ditinjau sebelum desain dibekukan.

Urutan kerja yang diusulkan: **identifikasi perangkat → BlueOS dan komunikasi → kamera → kendali dasar → navigasi → tugas tambahan → latihan terintegrasi**. Beberapa eksperimen persepsi dapat berjalan memakai rekaman saat hardware gerak belum siap.
