# Kondisi awal dan keputusan

Tanggal: 1 Oktober 2026. Label **disepakati** berarti dinyatakan pengguna; label **usulan** belum merupakan keputusan bersama.

| Topik | Status | Catatan |
| --- | --- | --- |
| Tanggung jawab | Disepakati | Pengguna menangani seluruh bagian Program, kurang lebih sendiri |
| Bekal | Dinyatakan pengguna | Familiar dengan bahasa/perangkat pemrograman, Linux, OpenCV, ROS/ROS 2, dan mikrokontroler yang dibahas; tingkat kedalaman tiap bidang belum dinilai |
| Robot | Diketahui | Masih tahap frame/body |
| Jetson | Diperiksa langsung | Orin NX kelas 16 GB menurut device tree/RAM; Ubuntu 22.04.5, L4T 36.4.7; lihat [hasil pemeriksaan](04-hasil-pemeriksaan-jetson.md) |
| Pixhawk | Diketahui dari pengguna | Sudah dimiliki; belum terdeteksi melalui USB, model dan firmware aktual belum diketahui |
| Autopilot | Arah yang dinyatakan | ArduSub; versi dan kondisi instalasi belum diperiksa |
| BlueOS | Pilihan pengguna | Menjalankan atau menyesuaikan BlueOS agar bekerja pada Jetson |
| Kamera | Diketahui | Tersedia 3 unit DWE; model, antarmuka, dan spesifikasi belum diketahui |
| Pemakaian kamera | Terbuka | Pilih fungsi, posisi, jumlah terpasang, serta pemrosesan bersamaan atau bergantian |
| Thruster, ESC, kedalaman | Belum diketahui | Ketersediaan, tipe, jumlah, pemasangan, dan arah belum dikonfirmasi |
| Akses perangkat | Dikonfirmasi pengguna dan pemeriksaan | Saat ini hanya Jetson tersedia; kamera dan Pixhawk belum ada di tempat pengujian. Akses Docker sesi ditolak izin; sudo memerlukan kata sandi |
| Jadwal | Belum diketahui | Jam kerja mingguan, tenggat demonstrasi, dan akses kolam |

## Arah teknis yang diusulkan

- Pixhawk–ArduSub menjalankan kendali gerak dasar sesuai konfigurasi kendaraan yang nanti dipastikan.
- Jetson menjalankan pengolahan kamera dan program misi. Antarmuka perintah ke autopilot dipilih setelah versi firmware dan mode yang tersedia diverifikasi.
- BlueOS menjadi platform pengelolaan dan integrasi onboard. Program misi dikembangkan sebagai layanan yang dapat diuji tersendiri; bentuk extension atau layanan terpisah belum diputuskan.
- Pilihan ROS 2, bahasa tiap modul, algoritma visi, dan metode estimasi posisi belum dibekukan.

Dokumentasi BlueOS menyediakan jalur instalasi manual pada sistem dasar yang sudah terpasang; image siap pakai yang didokumentasikan berfokus pada Raspberry Pi. Ini memberi jalur eksperimen untuk Jetson, bukan jaminan kompatibilitas model tertentu. [Instalasi resmi](https://blueos.cloud/docs/stable/usage/installation/), diperiksa 1 Oktober 2026.

## Data pertama yang perlu dikumpulkan

1. Identifikasi Jetson/OS/RAM/penyimpanan sudah dicatat; cocokkan carrier fisik sebelum pekerjaan khusus board. Label minor JetPack belum dipastikan; gunakan L4T dan versi paket hasil pemeriksaan.
2. Model Pixhawk, firmware dan versi, port yang tersedia, serta cadangan parameter bila sudah dikonfigurasi.
3. Model tiap DWE, konektor, identitas perangkat, format video, dan kebutuhan daya.
4. Rancangan posisi kamera, ruang pandang bebas, sambungan ke enclosure, serta rencana thruster/aktuator.
5. Waktu akses perangkat dan target demonstrasi pertama.

Model periferal yang belum diketahui tidak menghambat penulisan kebutuhan atau eksperimen pada rekaman. Identitas Jetson kini tersedia untuk persiapan instalasi; driver kamera dan performa tiga kamera tetap menunggu pemeriksaan unit dan uji integrasi.
