# Pemeriksaan Pixhawk dan rencana 7 thruster

Tanggal: **26 Oktober 2026, Asia/Jakarta**. Pengguna menetapkan target kendaraan **7 thruster** dan meminta pemeriksaan Pixhawk yang terhubung ke laptop. Pemeriksaan dilakukan langsung lewat USB secara baca saja; tidak ada arming, motor test, perubahan mode/parameter, reboot atau flashing firmware.

## Hasil perangkat saat ini

| Bagian | Hasil live |
| --- | --- |
| Perangkat | Pixhawk1, dikonfirmasi descriptor USB dan STATUSTEXT |
| Port | `/dev/ttyACM0`; alias `usb-ArduPilot_Pixhawk1_230021000D51383236333932-if00` |
| Firmware | `ArduSub V4.1.0 (f2af3c7e)`; AUTOPILOT_VERSION cocok |
| Frame | STATUSTEXT **`Frame: CUSTOM_7T`**, `FRAME_CONFIG=7` |
| Target MAVLink | System 1, component 1 |
| Status | MANUAL; seluruh heartbeat yang diamati **disarmed** |
| Parameter | **893/893**, pembacaan lengkap dan backup disimpan |
| Output yang dilaporkan | `RCOut: PWM:1-12`; `BRD_PWM_COUNT=4` |
| Rentang motor | `MOT_PWM_MIN=1100`, `MOT_PWM_MAX=1900`; trim SERVO1–7 1500 |
| Telemetri output | SERVO1–7 melaporkan 1500 µs saat disarmed; ini bukan pengukuran listrik pin atau bukti ESC/motor terpasang |

## Pemetaan output dari parameter

Penamaan fungsi mengikuti [enum SRV_Channel upstream pada commit firmware yang dilaporkan](https://github.com/ArduPilot/ardupilot/blob/f2af3c7e/libraries/SRV_Channel/SRV_Channel.h). Firmware ini melaporkan frame custom; kesamaan metadata git tidak membuktikan seluruh binary identik dengan upstream.

| Output | SERVOx_FUNCTION | Fungsi | MOT_x_DIRECTION |
| --- | --- | --- | --- |
| 1 | 33 | Motor 1 | +1 |
| 2 | 34 | Motor 2 | +1 |
| 3 | 35 | Motor 3 | −1 |
| 4 | 36 | Motor 4 | +1 |
| 5 | 37 | Motor 5 | −1 |
| 6 | 38 | Motor 6 | +1 |
| 7 | 39 | Motor 7 | −1 |
| 8 | 0 | Disabled | Tidak digunakan untuk menentukan susunan |
| 9 | 82 | Motor 9 | Bukan konfirmasi kanal servo payload |
| 10 | 83 | Motor 10 | Bukan konfirmasi kanal servo payload |
| 11 | 186 | ID fungsi tercatat; kegunaan fisik belum dikonfirmasi | — |
| 12 | 0 | Disabled | — |

Dengan demikian **SERVO7 pada board yang diperiksa sekarang adalah Motor7**, bukan kanal gripper. Jangan membawa pemetaan proyek/konfigurasi lama enam thruster ke kendaraan ini. Nilai ±1 adalah pembalik perintah motor; tidak memberi informasi posisi thruster, arah sumbu fisik atau jenis propeller tanpa pemeriksaan mekanik.

Dokumentasi [frame ArduSub](https://ardupilot.org/sub/docs/sub-frames.html) menampilkan preset 3/4/5/6/8 motor, bukan preset generik tujuh motor. Angka **7 pada FRAME_CONFIG berarti Custom**, bukan jumlah motor. Bukti yang lebih spesifik pada board ini adalah label `CUSTOM_7T`, tujuh fungsi Motor1–7 dan keluaran netralnya. Koefisien mixer tetap perlu diverifikasi.

## Konfirmasi susunan dari konfigurator

**26 Oktober 2026:** pengguna meneruskan keterangan teman yang mengonfigurasi Pixhawk: **4 horizontal + 3 vertikal**, dengan **T1–T4 horizontal** dan **T5–T7 vertikal**. Teman tersebut menyebut arah/mixing berasal dari kombinasi konfigurasi 8 thruster dan 5 thruster sebelumnya. Ini konfirmasi rancangan dari konfigurator, belum hasil pengukuran arah thrust atau pengujian gerak motor.

| Kelompok | Motor | Output menurut pembacaan USB sebelumnya |
| --- | --- | --- |
| Horizontal | T1, T2, T3, T4 | SERVO1, SERVO2, SERVO3, SERVO4 |
| Vertikal | T5, T6, T7 | SERVO5, SERVO6, SERVO7 |

Pembagian horizontal/vertikal kini diketahui. Pernyataan “arah sama” belum menetapkan posisi depan/belakang/kiri/kanan, sudut horizontal, tanda gaya positif, maupun koefisien roll/pitch/yaw/heave/surge/sway setiap motor. Tidak diasumsikan otomatis ±45° atau seluruh 6-DoF hanya dari jumlah motor.

Acuan berikutnya adalah blok source `CUSTOM_7T`/pemanggilan `add_motor_raw_6dof`, patch mixer atau tabel koefisien yang benar-benar digunakan saat build, disertai gambar posisi serta arah tiap thruster. Acuan itu diperlukan agar model simulator dan firmware menggunakan pemetaan yang sama. Parameter arah motor hasil readback tetap snapshot tersendiri dan bukan pengganti matriks mixer.

## Yang belum dapat dipastikan

- Posisi dan orientasi fisik rinci tujuh thruster serta kesesuaian kabel/konektor. Pembagian T1–T4 horizontal dan T5–T7 vertikal sudah dikonfirmasi konfigurator di atas.
- Matriks custom yang benar-benar dikompilasi ke firmware. Source `/home/rasya/ardupilot` yang ditemukan memiliki HEAD `96f98857f7fc` dan placeholder custom, bukan source yang melaporkan `CUSTOM_7T`; tidak dipakai untuk mengklaim koefisien board saat ini.
- Kesesuaian tanda mixer dan MOT_x_DIRECTION dengan pemasangan nyata serta seluruh kemampuan gerak/6-DoF.
- Ketersediaan ESC, baterai dan supply aktuator. SYS_STATUS melaporkan sekitar 0,72 V pada monitor baterai; data itu tidak dianggap bukti kondisi baterai propulsi atau kalibrasi monitor daya.
- SCALED_PRESSURE internal diterima; tidak ada SCALED_PRESSURE2 pada interval ini, sehingga sensor kedalaman eksternal belum terverifikasi.
- Model servo/catu daya/driver/kanal payload tetap belum dikonfirmasi. Output 9/10 tidak otomatis dianggap gripper karena fungsi live-nya Motor9/Motor10.

## Implikasi proyek dan bukti

Konfigurasi firmware sudah menunjukkan **custom tujuh thruster**, tetapi pengujian ini tidak membuktikan gerak tujuh motor atau kesesuaian mixer dengan rangka. Model dinamis kualifikasi di `ros2_ws` masih enam thruster; rencana hardware tujuh thruster belum diterapkan pada model tersebut. Penyesuaian simulator memerlukan geometri serta koefisien mixer yang dikonfirmasi.

Artefak lokal pada `hydroships/evidence/pixhawk-2026-10-26/`: `readback.json`, backup `readback.params`, `probe-readonly.py` dan `summary.json` dengan checksum. Folder evidence diabaikan Git. Script hanya mengirim PARAM_REQUEST_LIST, PARAM_REQUEST_READ bila diperlukan, dan MAV_CMD_REQUEST_MESSAGE untuk meminta informasi. Port ditutup setelah pemeriksaan.

Pemeriksaan ini memperbarui snapshot [laporan 10](10-validasi-pixhawk-ros2.md) yang saat itu melaporkan BLUEROV1. Tidak ada parameter board yang ditulis pada sesi ini.
