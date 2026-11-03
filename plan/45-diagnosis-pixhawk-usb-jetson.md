# 45 — Diagnosis Pixhawk melalui USB Jetson

Tanggal: 3 November 2026. Tahap awal baca saja; dilanjutkan uji input netral terbatas saat disarmed atas permintaan pengguna. Tanpa arming atau perubahan parameter.

## Hasil

| Pemeriksaan | Hasil |
| --- | --- |
| USB Jetson | Pixhawk1 serial 230021000D51383236333932, `/dev/ttyACM0` |
| Propulsi | Seluruh 15 parameter profil cocok: FRAME_CONFIG=7, SERVO1–7_FUNCTION=33–39, arah motor +,+,−,+,−,+,−; SERVO8_FUNCTION=0 |
| Keamanan | Seluruh heartbeat dalam capture menunjukkan disarmed; semua pesan keluar adalah PARAM_REQUEST_READ (ID 20) |
| Input pilot | FS_PILOT_INPUT=2; FS_PILOT_TIMEOUT=3 detik |
| GCS | FS_GCS_ENABLE=2; SYSID_MYGCS=255; HydroShips port 8081 tidak aktif |
| Sensor utama | Gyro, accelerometer, magnetometer dan AHRS sehat pada SYS_STATUS |
| Tekanan/kedalaman | ABSOLUTE_PRESSURE enabled tetapi unhealthy; BARO1_DEVID=721674, BARO2/3_DEVID=0; SCALED_PRESSURE2 tidak diterima |
| Barometer pertama | 1013,934–1013,989 hPa pada capture lanjutan; bukan bukti kedalaman air |
| Heartbeat | system_status=5 (CRITICAL), custom_mode=19, base_mode=81 |

## Pembuktian dan pemulihan sementara

Setelah pengguna meminta perbaikan, uji terbatas mengirim 25 MANUAL_CONTROL netral (x=y=r=0, z=500, buttons=0) selama lima detik, dari system 255/component 190. Sebelum setiap pengiriman, heartbeat target system 1/component 1 harus segar dan disarmed. Tidak ada perintah arm, perubahan mode atau penulisan parameter.

Hasil terukur:

1. Sebelum input: tiga heartbeat CRITICAL (5).
2. Selama input netral: lima heartbeat STANDBY (3), tetap disarmed.
3. Input terakhir pada detik 8,864; heartbeat CRITICAL pertama sesudahnya pada detik 12,077 (selisih sekitar 3,21 detik), disertai STATUSTEXT `Lost manual control`.
4. Proses uji berhenti normal (exit 0) dan memulihkan pengaturan terminal serial.

Ini membuktikan kehilangan input pilot sebagai penyebab CRITICAL pada uji ini. Temuan sebelumnya berupa inferensi kini mempunyai pembanding langsung. Pemulihan STANDBY hanya berlangsung saat input segar tersedia; ini bukan perbaikan permanen atau bukti kesiapan misi. Tidak ada pengirim netral latar belakang yang ditinggalkan, karena itu akan menutupi hilangnya sumber kontrol sebenarnya.

STATUSTEXT juga merekam `MYGCS: 255, heartbeat lost`; uji sengaja tidak mengirim heartbeat GCS. Walaupun demikian, selama input pilot segar status STANDBY, sehingga peringatan GCS tersebut tidak mempertahankan CRITICAL pada kondisi disarmed yang diuji.

Kesehatan sensor kedalaman tetap masalah terpisah: status tekanan unhealthy tidak berubah menjadi bukti sensor siap hanya karena heartbeat menjadi STANDBY. Versi firmware terkini belum diminta ulang.

Bukti uji: [neutral-check.json](../ros2_ws/evidence/qualification-consistency-2027/jetson-usb-20261103/neutral-check.json), dengan assert pemeriksaan fase before/neutral/after, disarmed, timeout, pesan failsafe dan exit proses. Script di folder yang sama meminta kredensial interaktif; tidak ada kredensial disimpan.

## Tindakan berikutnya

Pertahankan failsafe. Untuk operasi berikutnya, jalur pilot/autonomy harus memiliki pemilik kontrol yang jelas, aliran setpoint dan heartbeat yang segar, serta penghentian saat sumber gagal. HydroShips saat ini hanya meneruskan telemetri dan belum menyediakan jalur kendali tersebut. Uji netral ini tidak menambahkan driver kendali produksi atau layanan otomatis.

Sensor kedalaman eksternal perlu diidentifikasi model serta koneksi fisiknya. Jika belum terpasang, ketiadaan data eksternal merupakan kekurangan perangkat, bukan alasan mengkalibrasi barometer internal sebagai depth. Jika sudah terpasang, periksa catu daya, bus dan deteksi sensor sebelum kalibrasi basah. Geometri mixer dan arah dorong fisik tetap belum terverifikasi oleh pembacaan parameter.

## Bukti

[Capture parameter dan status lanjutan](../ros2_ws/evidence/qualification-consistency-2027/jetson-usb-20261103/diagnosis-followup.json), [capture pertama](../ros2_ws/evidence/qualification-consistency-2027/jetson-usb-20261103/diagnosis.json), raw `diagnosis*.bin`, dan salinan source referensi berada pada folder bukti yang sama. Sebagian nama parameter lintas versi tidak dijawab; daftar `missing` disimpan dan tidak ditafsirkan sebagai nilai nol. Semua parameter profil propulsi berhasil diterima. Script pemeriksaan meminta password interaktif, tanpa menyimpannya.

Referensi resmi: [heartbeat ArduSub](https://github.com/ArduPilot/ardupilot/blob/f2af3c7e/ArduSub/GCS_Mavlink.cpp#L59), [flag failsafe](https://github.com/ArduPilot/ardupilot/blob/f2af3c7e/ArduSub/Sub.h#L242), [initialisasi pilot](https://github.com/ArduPilot/ardupilot/blob/f2af3c7e/ArduSub/Sub.cpp#L46), [timeout pilot](https://github.com/ArduPilot/ardupilot/blob/f2af3c7e/ArduSub/failsafe.cpp#L170), [status tekanan](https://github.com/ArduPilot/ardupilot/blob/f2af3c7e/ArduSub/GCS_Sub.cpp#L48), dan [definisi SYS_STATUS](https://mavlink.io/en/messages/common.html#SYS_STATUS).
