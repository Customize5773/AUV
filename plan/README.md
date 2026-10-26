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
| [Rencana kualifikasi autonomous](13-rencana-kualifikasi-autonomous.md) | Gate pergi/balik, U-turn, surface sesudah finish dan stop; selesai pada model latihan ideal |
| [Tinjauan rulebook terbaru dan rencana ARENA](14-tinjauan-rulebook-dan-rencana-arena.md) | Perbedaan aturan terbit/draf 2027, koreksi urutan misi dan penerimaan flare/payload; implementasi dilanjutkan pada laporan 17 |
| [Hasil kualifikasi autonomous](15-hasil-kualifikasi-autonomous.md) | Implementasi controller visual/odometri, pemeriksa independen, pengawas dan bukti pengujian |
| [Hasil deteksi kamera](16-hasil-deteksi-kamera.md) | Gate, flare berwarna dan blue/red drum dari citra, topic persepsi, uji frame simulator dan batas hasil |
| [Hasil ARENA autonomous](17-hasil-arena-autonomous.md) | Ketahanan persepsi, tracking, proyeksi kamera, misi visual, bola flare dinamis, payload masuk blue drum dan pemeriksa independen |
| [Dinamika dan estimasi sensor](18-dinamika-dan-estimasi-sensor.md) | Kualifikasi dengan gaya enam thruster, drag/buoyancy, AHRS/tekanan/DVL, pemisahan ground truth dan bukti uji fisika/sensor |

**Perkembangan berikutnya:** pengguna menyetujui aplikasi mandiri dengan BlueOS sebagai acuan, lalu meminta seluruh source digabung dalam Git AUV2027. Aplikasi tersedia di [`hydroships/`](../hydroships/README.md), port lokal **8081**. Laporan 07 menjadi acuan implementasi baru; catatan BlueOS di bawah merekam tahap sebelumnya.

**Koreksi inventaris:** sudah tersedia **3 kamera DWE**. Pembahasan 1–3 kamera adalah opsi penggunaan dari tiga unit tersebut, bukan rencana membeli kamera tambahan.

**Ketersediaan 12 Oktober 2026:** Pixhawk1 sudah tersedia melalui USB Jetson, memakai ArduSub 4.1.0. Pengguna mengonfirmasi catu daya hanya USB. Validasi baca telemetri/parameter dan relay ROS 2 dicatat di laporan 10; kamera belum divalidasi pada sesi ini. Catatan layanan BlueOS sebelumnya tersedia pada [laporan pelaksanaan](05-blueos-tanpa-periferal.md).

Arah awal platform adalah menjalankan/menyesuaikan **BlueOS pada Jetson**, kemudian berkembang menjadi aplikasi mandiri HydroShips. Pemeriksaan langsung mengidentifikasi Jetson Orin NX kelas 16 GB, Ubuntu 22.04.5, dan L4T 36.4.7. Akses Docker telah diberikan dan pengujian tanpa periferal berhasil dengan keterbatasan yang tercatat; ini belum validasi robot lengkap. Pixhawk1 teridentifikasi pada 12 Oktober 2026; model DWE, jumlah thruster, ESC, dan sensor kedalaman belum dikonfirmasi pada sesi ini.

Sumber aturan dan gambar arena tersedia dalam [riset SAUVC](../doc/README.md) dan [indeks gambar rulebook](../doc/sources/rulebook-images/README.md). Acuan aktif adalah edisi 2027.2.1; laporan 21 dan 24 mencatat perubahan serta migrasi simulator.

Urutan kerja yang diusulkan: **identifikasi perangkat → BlueOS dan komunikasi → kamera → kendali dasar → navigasi → tugas tambahan → latihan terintegrasi**. Beberapa eksperimen persepsi dapat berjalan memakai rekaman saat hardware gerak belum siap.

[19 — Penilaian ARENA dan rancangan servo payload](19-penilaian-arena-dan-rancangan-servo.md): ledger skor, bukti fisika bola dan rancangan mekanik awal; tanpa aktivasi hardware.

[20 — Pinger, pickup dan servo simulator](20-pinger-pickup-dan-servo-simulator.md): mode ARENA tambahan, TDOA hidrofon virtual, pickup berbasis kontak dan retensi bola; mekanisme hardware masih rancangan.

[21 — Pembaruan rulebook 2027.2.1](21-update-rulebook-2027.md): publikasi resmi 26 Oktober, perubahan geometri/reacquisition/square/timer dan kebutuhan migrasi; simulator tetap baseline 2026 sampai implementasi diuji ulang.

[22 — Pixhawk dan rencana 7 thruster](22-pixhawk-konfigurasi-7-thruster.md): pembacaan USB langsung, CUSTOM_7T, backup parameter dan pemetaan output; geometri serta koefisien mixer masih perlu dikonfirmasi, tanpa motor test.

[23 — Sinkronisasi 7 thruster](23-sinkronisasi-7-thruster.md): profil bersama 4 horizontal + 3 vertikal, allocator/plant tujuh kanal, panel HydroShips dan relay ROS; asumsi geometri tetap terpisah dari mixer hardware yang belum terverifikasi.

[24 — Migrasi dan uji arena 2027](24-migrasi-dan-uji-arena-2027.md): profil default 2027.2.1, geometri baru, target-zone exit, Surfacing Square dan penerimaan runtime.
