# Pixhawk fisik dan relay telemetri ROS 2 — 12 Oktober 2026

Pixhawk asli kini tersedia pada Jetson. Pengguna mengonfirmasi catu daya **hanya USB Jetson**, belum menggunakan baterai/power module dalam pengujian ini. HydroShips awalnya belum membuka koneksi kendaraan; port serial yang terdeteksi kemudian dihubungkan melalui API aplikasi yang sudah ada.

## Perangkat dan data yang teramati

| Pemeriksaan | Hasil |
| --- | --- |
| USB | Pixhawk1 pada `/dev/ttyACM0`, alias stabil `/dev/serial/by-id/usb-ArduPilot_Pixhawk1_230021000D51383236333932-if00` |
| Firmware | ArduSub 4.1.0; STATUSTEXT melaporkan `ArduSub V4.1.0 (f2af3c7e)` |
| Target MAVLink | System 1, component 1, autopilot 3, vehicle type 12 |
| Kondisi saat validasi | MANUAL, disarmed |
| Frame yang dilaporkan | `BLUEROV1`; ini konfigurasi firmware, belum validasi susunan thruster fisik |
| Parameter | **893 / 893**, pembacaan lengkap |
| Telemetri diterima | Roll, pitch, yaw, heading, voltage, current, battery_remaining, altitude |
| Tekanan eksternal | Belum ada data `SCALED_PRESSURE2` pada snapshot; keberadaan/kalibrasi sensor belum terbukti |
| Identitas UID MAVLink | Dilaporkan `0`; tidak dianggap identitas unik. USB memiliki serial yang dipakai untuk pemilihan perangkat |

Tegangan yang teramati sekitar 0,7 V adalah laporan mentah autopilot. Dalam kondisi hanya USB, angka ini dan persentase baterai tidak membuktikan baterai utama terpasang atau monitor daya sudah terkalibrasi. `VFR_HUD.alt` tetap altitude, bukan kedalaman terhadap permukaan air.

## Perubahan aplikasi

Telemetri kini diteruskan oleh worker MAVLink yang sama ke topic **`/auv2027/vehicle/state`**, `std_msgs/msg/String` JSON, sekitar 2 Hz. ROS 2 tidak membuka port USB kedua. Sumber serial/demo/UDP, sesi, usia heartbeat, dan status stale tetap tersedia agar modul autonomous dapat membedakan data yang layak digunakan.

Relay menambahkan usia antrean ke usia data, menandai data kedaluwarsa, dan meneruskan field kosong saat koneksi diputus. Subscriber tetap harus menerapkan timeout lokal bila seluruh proses publisher berhenti. Halaman **Autonomous** mendapat panel Telemetri kendaraan: identitas, mode/armed, parameter, orientasi, tegangan, tekanan eksternal, dan status penerusan ke ROS.

Semua perubahan berada dalam Git AUV2027. API kendali gerak tidak ditambahkan. Rencana misi dan driver tugas masih berlabel software test; tersambungnya telemetri belum menjadi izin menjalankan misi fisik.

## Hasil pengujian

- **15 tes backend lulus**, termasuk lifecycle misi yang sudah ada, penerimaan telemetri oleh subscriber `rclpy` terpisah melalui DDS, propagasi disconnect, dan pengujian usia/stale dengan clock terkontrol. Tes integrasi memakai domain 78 dan sumber demo terisolasi.
- **Perangkat fisik diamati selama 60,7 detik**: serial connected sepanjang sampel, sesi tetap, heartbeat <3 detik, orientasi baru, penghitung pesan meningkat, tetap disarmed, dan parameter lengkap. Tidak ada kejadian penulisan parameter pada interval pengujian.
- **Subscriber ROS 2 independen pada domain 0 menerima enam frame live dari sumber serial**, dengan data orientasi baru dan penghitung MAVLink yang meningkat. Ini memverifikasi alur USB Pixhawk → HydroShips → ROS 2, bukan sekadar penemuan nama topic.
- Layanan HydroShips diperbarui dan dimulai ulang sekali. Port perangkat yang sama dibuka kembali; seluruh 893 parameter diunduh ulang dan cocok dengan cadangan sebelum pembaruan. Ini pengujian restart layanan/reopen serial, **bukan** cabut-pasang USB fisik atau reboot Jetson.
- Browser Autonomous diuji pada 1280/1440/1920 piksel dengan Pixhawk asli: ArduSub 4.1.0, 893 parameter, disarmed, dan relay aktif ditampilkan. Tidak ada error JavaScript, overflow horizontal, atau permintaan mutasi dari pemeriksaan halaman.
- Pemeriksaan baca saja pada enam halaman lama lulus, termasuk ekspor parameter, perbandingan cadangan, dialog parameter yang dibatalkan, dan unduhan log. Tidak ada mutasi API atau respons HTTP gagal.
- Skenario editor/eksekusi/abort/restart Autonomous serta perpindahan status kendaraan juga lulus pada layanan uji port 8083/domain 77. Layanan uji dihentikan setelah pemeriksaan.

Cadangan sebelum/sesudah pengamatan dibandingkan pada baris data parameter; keduanya identik. SHA-256 baris data: `e4aeff7f95d5c9ea447c3ac97f38037b0d60647cbe4f837b28a9f19a17ca660f`. Pengecekan interval menggunakan cache parameter API; pencocokan sebelum/sesudah restart di atas memakai unduhan baru dari Pixhawk.

## Bukti dan cara mengulang

Artefak lokal di `hydroships/evidence/pixhawk/` (tidak masuk Git):

- `pre-update.params`: cadangan sebelum pembaruan layanan.
- `pixhawk-before.params`, `pixhawk-after.params`, `hardware.json`: pengamatan 60 detik.
- `ros-vehicle.json`: hasil subscriber DDS terpisah.
- `deployed.json`: status setelah layanan diperbarui.
- `browser/`: hasil pemeriksaan browser dan screenshot dengan sumber perangkat fisik.

Dari `hydroships/`, setelah serial terhubung dan daftar parameter lengkap:

```bash
env -u PYTHONPATH .venv/bin/python scripts/check-pixhawk.py --seconds 60
source /opt/ros/humble/setup.bash
ROS_DOMAIN_ID=0 /usr/bin/python3 scripts/check-ros-vehicle.py --source serial --output evidence/pixhawk/ros-vehicle.json
env -u PYTHONPATH .venv/bin/python scripts/check-browser.py --read-only --desktop-only --output evidence/pixhawk/browser
```

Kontrak payload dan aturan freshness: [README ROS 2](../hydroships/ros2_ws/README.md#telemetri-pixhawk-ke-ros-2).

## Batas dan langkah berikutnya

Belum dilakukan arming, ganti mode, gerak thruster, perubahan parameter, flashing firmware, kalibrasi, validasi kedalaman, atau pemasangan kamera. Langkah berikutnya adalah mengidentifikasi sensor kedalaman/kamera yang tersedia dan menyiapkan modul tugas pertama untuk membaca data melalui kontrak ROS 2 ini. Pengujian kontrol kendaraan memerlukan pemetaan aktuator dan kondisi perangkat yang jelas; belum dijalankan dalam sesi ini.
