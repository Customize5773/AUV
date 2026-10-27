# 26 — ARENA dengan gaya tujuh thruster dan estimasi sensor

> Pembaruan lanjutan: kalibrasi DVL dan penerimaan penuh GUI/POV sudah diuji pada [laporan 27](27-kalibrasi-dvl-dan-penerimaan-gui.md). Angka dan keterbatasan headless di bawah tetap merupakan snapshot penerimaan awal.


28 Oktober 2026. Tujuan: memakai plant dan estimator kualifikasi pada ARENA, kemudian mengulang penerimaan blue drum dan pinger–pickup berdasarkan profil SAUVC 2027.2.1 yang sudah diaudit pada laporan 24.

## Implementasi

- `vehicle_model:=auto` memilih model dinamis pada kedua misi autonomous visual, kualifikasi dan ARENA. `vehicle_model:=ideal` tetap tersedia secara eksplisit sebagai pembanding historis. Manual tanpa autonomous tetap ideal secara default.
- SDF dinamis memakai gravitasi, plant gaya tujuh thruster, drag linear/kuadratik, buoyancy, inersia dan respons thruster. Plugin VelocityControl tidak dipasang pada AUV dinamis; tidak ada override kecepatan untuk menjaga lintasan.
- Propulsi memakai profil bersama HydroShips: empat horizontal dan tiga vertikal, allocator yang sama dengan kualifikasi. Kontrol aktif tetap surge/sway/heave/yaw; geometri tujuh thruster tidak berarti stabilisasi aktif enam sumbu sudah tersedia. Roll/pitch mendapat damping dan momen buoyancy dari plant.
- Estimator membaca tekanan, gyro/accel/magnetometer dan DVL virtual. XY awal ARENA berasal dari titik penempatan yang diketahui, dunia (34; 0,7); orientasi berasal dari sensor. Selanjutnya gerak terintegrasi dari sensor, bukan odometri ground truth.
- Controller, pose history untuk proyeksi kamera/pinger, guard dan pengendali propulsi membaca `/sauvc/state/odom`. Hanya referee dan harness penerimaan yang memakai `/sauvc/odom` sebagai pembanding independen.
- Referee menerbitkan `/sauvc/arena/status` untuk controller/guard dinamis. Isinya status tugas dan kegagalan tanpa koordinat ground truth. Hasil lengkap dan posisi bukti hanya tersedia di `/sauvc/arena/result` bagi pemeriksa/pencatat.
- Propulsi belum aktif pada preflight dengan perintah nol. State DIVE atau perintah manual nonzero mengaktifkan kendali; STOP/DONE/ABORT menonaktifkan seluruh kanal sampai restart. Referee menunggu thrust aktual sebelum menilai penyelaman, sehingga heave pasif saat preflight tidak dianggap misi.
- Awal timer ARENA dinamis memakai gaya aktual dari telemetri plant, ambang 0,05 N. Pemeriksaan stop memerlukan perintah nol dan gaya ketujuh thruster di bawah ambang, selain posisi kendaraan benar-benar stationary.
- Cruise/scan/drop/pickup alignment dinamis memakai kedalaman −0,30 m untuk memberi ruang pengereman dari permukaan; profil ideal historis tetap −0,12 m. Lift pickup berganti fase setelah mencapai kedalaman aman. Endpoint drop dan gripper tetap dihitung dari offset mekanik.

## Bukti dan kriteria

Artefak tersimpan lokal di [`evidence/arena-dynamics/`](../ros2_ws/evidence/arena-dynamics/); tidak otomatis ikut Git. Source native plant/profil gaya tidak dituning agar cocok lintasan. Unit test baru memeriksa plant ARENA, prior penempatan dan integrasi DVL pada heading 90°, aktivasi/disarm, serta pembedaan heave preflight dari attempt yang sudah mulai.

Penerimaan memerlukan misi DONE dari controller dan COMPLETE dari referee, pelintasan/flare/drop aktual, bonus Square, stop nyata, gaya nol dan shutdown bersih. Mode pinger juga memerlukan acquisition pada drum berpinger, seluruh badan keluar target zone, pickup dan retensi bola fisika yang sama sampai surface.

Node graph diperiksa untuk memastikan controller/estimator/propulsi/guard tidak berlangganan odometri ground truth atau hasil referee lengkap. Kontrak sensor dibatasi pada pengukuran/time/actuator timeout, dan semua paket gaya harus berisi tujuh kanal.

Galat estimator dibandingkan dengan ground truth hanya oleh harness. Ambang galat XY 0,20 m dari kualifikasi pendek tetap dilaporkan sebagai referensi, bukan diam-diam dilonggarkan untuk lintasan ARENA lebih panjang. Keberhasilan misi tidak berarti drift berada di bawah referensi tersebut. DVL masih dead reckoning tanpa koreksi posisi global; kalibrasi sensor/landmark fisik tetap diperlukan.

## Hasil penerimaan 28 Oktober

[verification.json](../ros2_ws/evidence/arena-dynamics/verification.json) mencatat `mission_acceptance_passed=true`.

| Misi dinamis | Status | Poin simulator | Thrust–surface | Galat XY maksimum | Galat kedalaman maksimum |
| --- | --- | ---: | ---: | ---: | ---: |
| Blue drum, nominal | Lulus | 209.62648 | 245.784 s | 0.2208 m | 0.0114 m |
| Pinger/pickup, varian 1 | Lulus | 290.26638 | 224.454 s | 0.1548 m | 0.0141 m |

Kedua misi mendapat Square +20, penalti 0, seluruh tujuh kanal gaya aktif selama misi dan mendekati nol pada akhir, serta shutdown bersih. Pinger/pickup memakai urutan Y-B-R, scene variant 1, blue drum 3 dan pinger drum 4. Bola yang sama tetap terikat pada akhir. Profil canonical tetap SHA-256 `83d37651452d3adfad91986053c5c6e59b6e40aa64de7223e7b517ecc30ec284`.

**103 tes unit lulus.** SDF blue drum dan pinger/pickup dinamis keduanya `Valid`. Karakterisasi fisik (`characterization.json`) lulus akselerasi terbatas, tracking kecepatan, pengereman reverse thrust, drag pasif, buoyancy tanpa daya dan tujuh thruster mati.

Empat injeksi gangguan lulus sebagai pengujian penghentian: `pressure_loss`, `dvl_loss`, `actuator_loss` dan `camera_loss`. Dalam run gangguan, ABORT adalah hasil yang diharapkan; perintah/gaya akhir nol, kendaraan stationary dan shutdown bersih. Kehilangan tekanan/DVL/aktuator diinjeksikan pada plant/sensor virtual, sedangkan camera_loss memutus penerimaan kamera controller; ini bukan pencabutan kamera fisik.

Regresi kualifikasi jalur 1 lulus setelah perubahan aktivasi propulsi bersama: start–surface 27,252 s, start–stop 32,488 s; tanpa konsumsi ground truth pada kendali. Tiga jalur tidak diulang seluruhnya pada sesi ini; bukti tiga jalur sebelumnya tetap pada laporan 24.

**Referensi akurasi:** blue drum menghasilkan galat XY maksimum 0,2208 m, melewati referensi kualifikasi pendek 0,20 m; pinger/pickup 0,1548 m. Nilai referensi tidak diubah. Pada JSON awal, `estimation_error.passed` adalah hasil pembanding kualifikasi itu, bukan kelulusan misi ARENA. Harness berikutnya memberi nama eksplisit `qualification_reference_passed`; ringkasan tetap menyatakan `all_arena_runs_meet_short_course_accuracy_reference=false`. Tidak ada klaim seluruh kriteria akurasi lulus.

Percobaan `blue-first.json` gagal saat heave pasif preflight dianggap premature surface; diperbaiki dengan menunggu thrust aktual dan diuji ulang. `blue-second.json` adalah run dinamis pembanding sebelum cruise diperjelas dan topic status dipisahkan; penerimaan final blue drum berada pada `blue-drum.json`.

Penerimaan ini **headless**. GUI/POV tidak diulang penuh dengan plant dinamis baru; konektivitas viewer sebelumnya tetap bukti tersendiri pada laporan 25. Waktu baru tidak dibandingkan sebagai peningkatan terhadap misi ideal lama, karena model dan kedalaman cruise berbeda.

## Batas model

Koefisien gaya/air adalah asumsi latihan, bukan kalibrasi PWM–thrust kendaraan. Sensor DVL/IMU/tekanan, akustik dan servo/latch tetap virtual. Referee tetap memberi konfirmasi tugas dari fisika simulator; konfirmasi ini belum diganti sensor kontak/payload hardware. Tidak ada bukti AUV, mixer Pixhawk, servo, hidrofon atau kolam nyata sudah tervalidasi.

## Menjalankan

```bash
cd /home/rasya/AUV/ros2_ws
bash tools/ros.sh build --symlink-install
# Blue drum, dinamika dan estimator sensor
bash tools/ros.sh launch sauvc_sim arena.launch.py edition:=2027 arena:=finals autonomous:=true vehicle_model:=dynamic
# Pinger, keluar target zone, pickup dan retensi
bash tools/ros.sh launch sauvc_sim arena.launch.py edition:=2027 arena:=finals autonomous:=true vehicle_model:=dynamic extended:=true
```

Jalankan satu mode setiap kali pada domain/partition yang sama. POV depan/bawah tetap menggunakan topic dan perintah pada [CARA-RUNNING.md](../ros2_ws/CARA-RUNNING.md).
