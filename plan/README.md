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
| [Aplikasi mandiri HydroShips](07-hydroships.md) | Implementasi yang disetujui: Jetson–Pixhawk, dashboard, parameter, telemetri, dan pengujian SITL |
| [Validasi HydroShips langsung di Jetson](08-validasi-jetson-hydroships.md) | Pencocokan metrik host, startup, restart, pemulihan proses, dan integritas konfigurasi |
| [Platform autonomous ROS 2](09-platform-autonomous-ros2.md) | Editor misi, executor ROS 2, kontrak modul tugas, riwayat, dan pengujian software di Jetson |
| [Validasi Pixhawk fisik dan ROS 2](10-validasi-pixhawk-ros2.md) | Pembacaan ArduSub melalui USB, cadangan parameter, dan penerusan telemetri ke ROS 2 |
| [Simulasi arena SAUVC](12-simulasi-sauvc-ros2.md) | Workspace ROS 2/Gazebo terpisah, geometri kualifikasi/final dan bukti uji kamera/gerak |
| [Rencana kualifikasi autonomous](13-rencana-kualifikasi-autonomous.md) | Gate pergi/balik, U-turn, surface sesudah finish dan stop; menunggu konfirmasi |
| [Tinjauan rulebook terbaru dan rencana ARENA](14-tinjauan-rulebook-dan-rencana-arena.md) | Perbedaan aturan terbit/draf 2027, koreksi urutan misi dan penerimaan flare/payload; menunggu konfirmasi |

**Perkembangan berikutnya:** pengguna menyetujui aplikasi mandiri dengan BlueOS sebagai acuan, lalu meminta seluruh source digabung dalam Git AUV2027. Aplikasi tersedia di [`hydroships/`](../hydroships/README.md), port lokal **8081**. Laporan 07 menjadi acuan implementasi baru; catatan BlueOS di bawah merekam tahap sebelumnya.

**Koreksi inventaris:** sudah tersedia **3 kamera DWE**. Pembahasan 1–3 kamera adalah opsi penggunaan dari tiga unit tersebut, bukan rencana membeli kamera tambahan.

**Ketersediaan 12 Oktober 2026:** Pixhawk1 sudah tersedia melalui USB Jetson, memakai ArduSub 4.1.0. Pengguna mengonfirmasi catu daya hanya USB. Validasi baca telemetri/parameter dan relay ROS 2 dicatat di laporan 10; kamera belum divalidasi pada sesi ini. Catatan layanan BlueOS sebelumnya tersedia pada [laporan pelaksanaan](05-blueos-tanpa-periferal.md).

Arah awal platform adalah menjalankan/menyesuaikan **BlueOS pada Jetson**, kemudian berkembang menjadi aplikasi mandiri HydroShips. Pemeriksaan langsung mengidentifikasi Jetson Orin NX kelas 16 GB, Ubuntu 22.04.5, dan L4T 36.4.7. Akses Docker telah diberikan dan pengujian tanpa periferal berhasil dengan keterbatasan yang tercatat; ini belum validasi robot lengkap. Pixhawk1 teridentifikasi pada 12 Oktober 2026; model DWE, jumlah thruster, ESC, dan sensor kedalaman belum dikonfirmasi pada sesi ini.

Sumber aturan dan gambar arena tersedia dalam [riset SAUVC](../doc/README.md) dan [indeks gambar rulebook](../doc/sources/rulebook-images/README.md). Acuan teknis lomba yang ditelaah masih edisi 2026; perubahan aturan 2027 perlu ditinjau sebelum desain dibekukan.

Urutan kerja yang diusulkan: **identifikasi perangkat → BlueOS dan komunikasi → kamera → kendali dasar → navigasi → tugas tambahan → latihan terintegrasi**. Beberapa eksperimen persepsi dapat berjalan memakai rekaman saat hardware gerak belum siap.
