# 44 — Konsistensi kualifikasi dan waktu preflight

Tanggal pembaruan: 3 November 2026. Status: batch berhenti pada kasus arus setelah 15 kasus lulus.

## Temuan dan perbaikan

Batch pertama menerima 14 kasus, lalu berhenti pada jalur 3 seed 2026 karena `dvl_calibration_not_ready`. Sekitar 19 detik dari timeout 45 detik terpakai untuk startup renderer sebelum sensor tersedia. Kualitas DVL baru mencapai ambang mendekati deadline; jendela stabil dua detik belum selesai. Ini kegagalan preflight, bukan kejadian stale_sensors saat misi.

Runtime kualifikasi dan ARENA sekarang menghitung waktu kalibrasi dari health sensor valid pertama. Tanpa aliran sensor segar, batas 45 detik tetap berlaku; kalibrasi dengan data segar memiliki batas 45 detik sendiri dan batas absolut 90 detik sejak startup. Ambang kualitas DVL, jendela stabil, dan pengaman sensor aktif tidak dilonggarkan. Status terminal tidak terus ditambahkan ulang saat timeout.

169 tes unit lulus pada pemeriksaan ulang 3 November. Uji sengaja menunda server Gazebo 20 detik lulus pada jalur 3 seed 2026: pelintasan kedua 22,812 detik, surface 25,872 detik, stop 30,156 detik; galat posisi maksimum 3,51 cm, diagnosis `no_stale_sensor_event`, shutdown bersih. Waktu tersebut dihitung sejak thrust, bukan startup renderer. Satu uji ini belum menggantikan batch penuh.

## Penerimaan ulang

Batch baru terdiri atas lima seed pada masing-masing tiga jalur dan tiga kasus arus/prior. Source dibekukan selama batch. Hasil batch pertama tidak digabung menjadi penerimaan source baru. Status dan hasil aktual disimpan pada [summary.json](../ros2_ws/evidence/qualification-consistency-2027/corrected-batch/summary.json). Batch berhenti pada kegagalan pertama. Optimasi kecepatan berikutnya belum diterapkan.

Bukti sebelumnya dipertahankan pada `baseline-v2/`; uji startup tertunda berada pada `delayed-preflight/`, di bawah `ros2_ws/evidence/qualification-consistency-2027/`.

## Pixhawk pada Jetson

SSH ke `aero@192.168.2.2` berhasil setelah autentikasi dikonfirmasi pengguna. USB Pixhawk terdeteksi pada `/dev/ttyACM0` dengan alias `usb-ArduPilot_Pixhawk1_230021000D51383236333932-if00`. Port tidak memiliki pemilik saat pemeriksaan. Layanan HTTP HydroShips pada port 8081 tidak aktif.

Capture pasif sepuluh detik menerima 40.300 byte dan sepuluh heartbeat; kendaraan disarmed sepanjang sampel, ArduPilot tipe submarine, `system_status=5` (CRITICAL). Penyebab status tersebut belum ditetapkan. ATTITUDE dan tekanan internal diterima, tetapi SCALED_PRESSURE2 tidak terlihat dalam capture ini; sensor kedalaman eksternal belum terverifikasi. Tidak ada byte MAVLink yang dikirim, perubahan parameter, arming atau perintah motor. Parameter tujuh thruster belum dibaca ulang pada Jetson.

Bukti: [capture pasif](../ros2_ws/evidence/qualification-consistency-2027/jetson-usb-20261103/pixhawk-passive.json) dan raw `passive.bin`. Kegagalan autentikasi awal tetap disimpan dalam `access.json`. Kredensial tidak disimpan dalam artefak.

## Pekerjaan yang masih terbuka

Selesaikan batch penuh pada source perbaikan, regresi pinger/pickup setelah isolasi bridge, dan perbaikan shutdown viewer. Kalibrasi fisik thruster, mixer, sensor serta mekanik belum dilakukan; koneksi USB saja tidak memvalidasi kemampuan gerak AUV.

Diagnosis lanjutan: [laporan 45](45-diagnosis-pixhawk-usb-jetson.md). Parameter tujuh thruster sudah dibaca ulang dan cocok seluruhnya; sensor kedalaman serta penyebab CRITICAL dijelaskan dengan batas kepastian pada laporan tersebut.

Pembaruan hasil batch: seluruh 15 run tiga jalur lulus. Kasus ke-16 `q-current-91` menyelesaikan misi, tetapi gagal syarat `stationary` saat motor-off dalam arus. Batch berhenti; dua kasus prior belum dijalankan pada batch ini. Ini tidak dinyatakan sebagai penerimaan 18/18.
