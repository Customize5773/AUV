# AUV2027 — HydroShips

Repositori persiapan AUV tim HydroShips: aplikasi onboard Jetson–Pixhawk, simulasi SAUVC dengan ROS 2/Gazebo, rancangan mekanik, serta laporan pengujian.

| Folder | Isi |
| --- | --- |
| [hydroships/](hydroships/README.md) | Aplikasi onboard: dashboard, telemetri, parameter, monitor sistem dan log |
| [ros2_ws/](ros2_ws/README.md) | Workspace SAUVC terpisah: kualifikasi, ARENA, persepsi kamera dan misi autonomous |
| [mechanical/payload-servo/](mechanical/payload-servo/README.md) | Konsep parametrik pelepas payload dan gripper pickup berbasis servo |
| [plan/](plan/README.md) | Keputusan, rencana implementasi dan laporan bukti pengujian |
| [doc/](doc/README.md) | Riset SAUVC, referensi aturan dan arsip sumber |
| [deploy/blueos/](deploy/blueos/README.md) | Eksperimen adaptasi BlueOS resmi untuk Jetson |

## Status simulator

Ringkasan berdasarkan bukti penerimaan **25 Oktober 2026**. Acuan implementasi adalah [rulebook SAUVC 2026 v6.1.0](https://sauvc.org/rulebook/); status dan perbedaan aturan dibahas pada [tinjauan rulebook](plan/14-tinjauan-rulebook-dan-rencana-arena.md). Detail yang tidak ditentukan aturan, seperti koordinat fixture dan ketebalan konstruksi, dipilih sebagai asumsi latihan.

| Bagian | Status dan batas hasil |
| --- | --- |
| Kualifikasi autonomous | Dive → lewat gate seluruh badan → U-turn → lewat kembali → surface → stop; empat skenario terbaru lulus |
| Dinamika kualifikasi | Gaya enam thruster, drag, buoyancy, inersia dan pengereman; kontrol memakai estimasi tekanan, IMU/magnetometer dan DVL virtual |
| U-turn lebih dekat | Jarak tambahan setelah pelintasan terestimasi 0,6 m; empat run terbaru mencatat start–surface 27,458–30,116 s |
| Persepsi kamera | Deteksi gate, flare dan drum, tracking antarframe serta proyeksi metrik; pengujian kamera dan perturbasi gambar tersedia |
| ARENA blue drum | Navigation, tiga flare sesuai urutan, drop ke blue drum, surface dan stop telah dibuktikan pada simulator |
| ARENA tambahan | Pinger virtual → drop ke red drum berpinger → gate tambahan → pickup bola yang sama → retensi sampai surface → stop; dua fixture lulus |
| Bukti bola/payload | Collision dan posisi bola aktual diperiksa oleh referee terpisah; perintah release/close saja tidak dianggap berhasil |
| Penilaian dan abort | Rincian poin tugas, bonus, penalti dan retensi; aturan abort latihan tetap lebih ketat daripada rulebook |
| Penerimaan terbaru | 84 tes unit, dua misi tambahan, uji mekanisme dan regresi blue drum lulus; run penerimaan menutup bersih |

**ARENA masih memakai gerak ideal dan odometri ground truth.** Model gaya dan estimator sensor digunakan pada kualifikasi. Pinger adalah model geometrik TDOA, servo pelepas memakai respons ideal, dan pickup memakai latch fixed setelah kontak. Hasil ini belum membuktikan performa AUV fisik atau ketahanan pada seluruh kondisi kolam.

## Menjalankan simulasi

Prasyarat dan pemasangan ada di [README workspace](ros2_ws/README.md). Gunakan wrapper workspace untuk memilih lingkungan ROS 2 Humble/Python 3.10 dan Gazebo Fortress yang sesuai.

```bash
cd /home/rasya/AUV/ros2_ws
bash tools/ros.sh build --symlink-install

# Kualifikasi autonomous; default memakai model dinamis dan estimasi sensor
bash tools/ros.sh launch sauvc_sim arena.launch.py autonomous:=true

# ARENA: Navigation, flare dan blue drum
bash tools/ros.sh launch sauvc_sim arena.launch.py arena:=finals autonomous:=true

# ARENA tambahan: pinger, drop, pelintasan gate tambahan dan pickup
bash tools/ros.sh launch sauvc_sim arena.launch.py arena:=finals autonomous:=true extended:=true
```

Jalankan satu mode setiap kali; hentikan mode sebelumnya sebelum membuka mode lain pada domain/partition yang sama. Tambahkan `headless:=true` untuk pengujian tanpa jendela. Simulasi terisolasi di `/home/rasya/AUV/ros2_ws` dan tidak menjalankan MAVLink atau output hardware.

## Laporan dan bukti

| Laporan | Isi |
| --- | --- |
| [15 — Kualifikasi autonomous](plan/15-hasil-kualifikasi-autonomous.md) | Alur misi, optimasi waktu dan jarak U-turn |
| [17 — Persepsi dan ARENA](plan/17-hasil-arena-autonomous.md) | Ketahanan deteksi, perbaikan gate dan misi blue drum |
| [18 — Dinamika dan estimasi sensor](plan/18-dinamika-dan-estimasi-sensor.md) | Model gaya, instrumen virtual dan pengujian gangguan |
| [19 — Penilaian dan rancangan servo](plan/19-penilaian-arena-dan-rancangan-servo.md) | Perhitungan skor, perbedaan interpretasi contoh aturan dan konsep dropper |
| [20 — Pinger, pickup dan servo simulator](plan/20-pinger-pickup-dan-servo-simulator.md) | Mekanisme tambahan, dua fixture penerimaan dan batas model |

Log, trajectory, hasil referee dan ringkasan JSON berada secara lokal di `ros2_ws/evidence/`, yang diabaikan Git. Laporan menautkan artefak tersebut; artefak tidak otomatis tersedia pada clone baru. Percobaan gagal dipertahankan terpisah dari run penerimaan.

## Pekerjaan fisik yang tersisa

- Menentukan servo, driver/kanal dan catu daya; memfinalisasi mekanik, fabrikasi serta uji retensi/release basah.
- Mengkalibrasi thrust/PWM, baterai, massa, buoyancy, drag dan kemampuan putar kendaraan nyata.
- Mengkalibrasi kamera DWE, sensor kedalaman/IMU dan hidrofon; memverifikasi ketersediaan sensor lokalisasi fisik.
- Menguji kolam nyata, arus, air keruh, refleksi dan variasi susunan arena yang lebih luas.

Model OpenSCAD adalah rancangan awal, belum dirender atau diuji fabrikasi. Tidak ada klaim servo, pickup atau pinger fisik telah bekerja.

## Aplikasi onboard

Aplikasi dikembangkan di `hydroships/` dengan Git milik repositori AUV2027. Panduan pemasangan dan akses lokal **http://127.0.0.1:8081** tersedia pada [README aplikasi](hydroships/README.md). Profil eksperimen BlueOS sebelumnya menggunakan port 8080. Status simulator di atas tidak menyatakan aplikasi onboard sudah menjalankan misi tersebut pada AUV fisik.
