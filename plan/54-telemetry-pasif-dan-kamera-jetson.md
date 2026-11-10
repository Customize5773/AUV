# 54 — Telemetry pasif dan capture kamera Jetson

Tanggal: 4 November 2026. Pemeriksaan langsung Jetson `192.168.2.2`, mengikuti alur terminal SSH yang aktif. GUI telah diarsipkan; unit `hydroships.service` tidak ditemukan/inactive, sehingga pemulihan historis pada laporan 52 bukan status layanan aktif sekarang. Unit tersebut tidak dihidupkan kembali.

## Hasil

| Pemeriksaan | Bukti |
|---|---|
| Pixhawk USB | Alias serial stabil tersedia, perangkat tidak sedang dimiliki proses lain sebelum capture |
| Telemetry 12 detik | Exit 0; 12 heartbeat, 120 ATTITUDE, 24 SYS_STATUS, 24 SERVO_OUTPUT_RAW |
| Heartbeat terakhir | Disarmed, system_status 5 (CRITICAL), custom_mode 19; umur sekitar 0,994 detik |
| Output terakhir | Kanal servo 1–7 masing-masing 1500 µs, kanal 8 nol; bukan bukti thrust atau arah motor |
| Tekanan | SCALED_PRESSURE 24 pesan; SCALED_PRESSURE2 tidak diterima. Flag tekanan enabled tetapi unhealthy |
| Kamera exploreHD | Capture 60 frame selesai sebelum timeout, exit 0; MJPEG 640×480 dengan konfigurasi 30 fps |
| Kestabilan kamera | Log menunjukkan satu dropped buffer; estimasi laju sesaat 21,48–25,69 fps, bukan benchmark berkelanjutan |

Telemetry dan capture dijalankan bersamaan memakai perintah yang sudah tersedia di `tools/auv.sh`. Pembaca MAVLink hanya menerima; tidak mengirim heartbeat, parameter request/write, arm, mode atau kontrol. Capture kamera dibuang ke `/dev/null`, tidak ada gambar tersimpan untuk menilai kualitas atau deteksi.

Bukti lengkap: [capture.json](../ros2_ws/evidence/jetson-passive-20261104/capture.json) dan [verification.json](../ros2_ws/evidence/jetson-passive-20261104/verification.json).

## Implikasi dan berikutnya

Koneksi USB telemetry dan capture V4L2 fisik sudah terbukti pada uji singkat ini. Ini tidak memvalidasi mixer tujuh thruster, kalibrasi kedalaman atau navigasi nyata. Status CRITICAL tetap dicatat, bukan ditutupi dengan input netral latar belakang. Diagnosis historis kehilangan input pilot ada pada laporan 45; capture sekarang juga merekam `MYGCS: 255, heartbeat lost`, tetapi tidak mengisolasi ulang penyebab CRITICAL.

Tahap berikutnya: jalur kamera fisik → ROS/persepsi dengan pengukuran umur frame dan pengujian lebih panjang; identifikasi sensor kedalaman eksternal sebelum estimator fisik. Misi simulator tetap terpisah dari port serial Pixhawk. Pengendalian fisik belum dihubungkan.

## Pemeriksaan lokal tambahan

`python3 -m pytest tools/test_ssh_ops.py -q`: **3 lulus, 1 gagal**. Kegagalan `test_profile_is_shared_without_gui_dependency` memerlukan symlink `GUI-prototype/backend/hydroships/propulsion.json` yang tidak tersedia pada kondisi arsip sekarang. Ini tidak menggagalkan capture Jetson di atas, tetapi suite lokal belum bersih. Tidak mengubah arsip GUI atau kontrak tes pada tahap ini karena migrasi tersebut merupakan perubahan workspace yang sedang berlangsung.
