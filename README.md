# AUV2027 — HydroShips

Panduan perintah kualifikasi, ARENA dan kedua POV: [Cara running simulator](ros2_ws/CARA-RUNNING.md).

Peta kode dan panduan Graphify: [Graphify untuk repo AUV](doc/GRAPHIFY.md).

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

**Profil default kini SAUVC 2027.2.1**, berdasarkan [rulebook resmi](https://sauvc.org/rulebook/) yang diperiksa 26 Oktober 2026. Kolam 50 × 25 m, tiga jalur kualifikasi, gate 2027, target zone, Surfacing Square, syarat reacquisition dan timer sudah dimigrasikan. Detail serta bukti penerimaan: [laporan 24](plan/24-migrasi-dan-uji-arena-2027.md). Fixture 2026 hanya untuk regresi eksplisit; hasil lama tetap berlabel edisi lamanya.

| Bagian | Status dan batas hasil |
| --- | --- |
| Geometri 2027 | Kolam, tiga jalur, gate menggantung, gate utama 1,5 × 1,5 m, mat 8 × 2 m dan Surfacing Square 2 × 2 m tersedia; posisi properti adalah pilihan latihan |
| Kualifikasi | Dive → pelintasan penuh → U-turn → kembali → surface → stop; dinamika tujuh thruster dan estimasi sensor virtual |
| Persepsi | Gate, flare, drum dan marker Surfacing Square dari kamera; tracking dan proyeksi metrik |
| ARENA blue drum | Navigation dahulu → flare sesuai urutan → drop blue drum → Surfacing Square → stop |
| ARENA pinger/pickup | TDOA virtual → drop red drum berpinger → seluruh badan keluar target zone → pickup bola yang sama → retensi sampai akhir |
| Penilaian 2027 | Timer sejak thrust, poin tugas, penalti kontak, bonus surface dan bonus Square; bonus inspeksi fisik tidak dimasukkan |
| Bukti pengujian terbaru | 121 tes unit; perbaikan DVL diuji pada empat kasus arus + satu nominal: 5/5 misi dan akurasi lulus, 2/5 penerimaan keseluruhan lulus; tiga kualifikasi arus masih gagal diam akhir |

**ARENA dan kualifikasi autonomous visual kini memakai model gaya tujuh thruster dan estimator sensor virtual secara default.** Ground truth digunakan oleh referee/pencatat; profil ideal tersedia sebagai pembanding eksplisit. [Laporan 26](plan/26-arena-dinamika-dan-estimasi-sensor.md) mencatat penerimaan awal dinamis; [laporan 27](plan/27-kalibrasi-dvl-dan-penerimaan-gui.md) memuat kalibrasi DVL dan dua misi penuh dengan Gazebo serta kedua POV. Pinger adalah model geometrik TDOA, servo pelepas memakai respons ideal, dan pickup memakai latch fixed setelah kontak. Hasil ini belum membuktikan performa AUV fisik atau ketahanan pada seluruh kondisi kolam.

[Laporan 31](plan/31-kalibrasi-dvl-dalam-arus.md) memperbaiki kalibrasi DVL dalam arus melalui penahan fisik virtual selama preflight dan konfirmasi penahan sebelum mempelajari bias. Penahan dilepas saat thrust pertama. Galat ARENA berarus turun dari 1,0594 menjadi 0,0651 m; ketiga kualifikasi berarus kini lulus akurasi. Ini prosedur penempatan tertahan, belum kalibrasi bebas hanyut. Station keeping dan prior posisi tidak diubah.

[Laporan 30](plan/30-pengujian-keandalan-berulang.md) mencatat matriks sebelum perbaikan penahan preflight: variasi seed sensor, prior posisi, cahaya 70% dan arus 0,02 m/s. Sembilan dari 12 kualifikasi dan lima dari enam ARENA memenuhi seluruh kriteria; semua 18 misi selesai dengan shutdown bersih. Estimator diperbaiki agar filter kecepatan kontrol tidak menambah lag posisi. Pada versi tersebut, empat kasus arus gagal: drift preflight ikut dipelajari sebagai bias DVL dan kendaraan bergerak setelah motor mati. Satu pengulangan tambahan prior posisi gagal akurasi pada 0,2010 m, sehingga total 14 dari 19 run diterima. Ini pengujian headless terbatas, belum bukti keandalan semua kondisi. Perbaikan flare/akustik/retensi sebelumnya tetap tercatat pada [laporan 29](plan/29-validasi-flare-dan-penerimaan-ulang.md).

## Menjalankan simulasi

Prasyarat dan pemasangan ada di [README workspace](ros2_ws/README.md). Gunakan wrapper workspace untuk memilih lingkungan ROS 2 Humble/Python 3.10 dan Gazebo Fortress yang sesuai.

```bash
cd /home/rasya/AUV/ros2_ws
bash tools/ros.sh build --symlink-install

# Kualifikasi autonomous; default memakai model dinamis dan estimasi sensor
bash tools/ros.sh launch sauvc_sim arena.launch.py edition:=2027 autonomous:=true

# ARENA: Navigation, flare dan blue drum
bash tools/ros.sh launch sauvc_sim arena.launch.py edition:=2027 arena:=finals autonomous:=true

# ARENA tambahan: pinger, drop, keluar target zone dan pickup
bash tools/ros.sh launch sauvc_sim arena.launch.py edition:=2027 arena:=finals autonomous:=true extended:=true
```

Jalankan satu mode setiap kali; hentikan mode sebelumnya sebelum membuka mode lain pada domain/partition yang sama. Tambahkan `headless:=true` untuk pengujian tanpa jendela. Simulasi terisolasi di `/home/rasya/AUV/ros2_ws` dan tidak menjalankan MAVLink atau output hardware.

## Laporan dan bukti

| Laporan | Isi |
| --- | --- |
| [15 — Kualifikasi autonomous](plan/15-hasil-kualifikasi-autonomous.md) | Alur misi, optimasi waktu dan jarak U-turn |
| [17 — Persepsi dan ARENA](plan/17-hasil-arena-autonomous.md) | Ketahanan deteksi, perbaikan gate dan misi blue drum |
| [18 — Dinamika dan estimasi sensor](plan/18-dinamika-dan-estimasi-sensor.md) | Model gaya, instrumen virtual dan pengujian gangguan |
| [19 — Penilaian dan rancangan servo](plan/19-penilaian-arena-dan-rancangan-servo.md) | Perhitungan skor, perbedaan interpretasi contoh aturan dan konsep dropper |
| [31 — Kalibrasi DVL dalam arus](plan/31-kalibrasi-dvl-dalam-arus.md) | Penahan preflight, konfirmasi kalibrasi dan akurasi lima run |
| [30 — Pengujian keandalan berulang](plan/30-pengujian-keandalan-berulang.md) | 18 run + satu pengulangan, 14 diterima; perbaikan integrasi DVL, batas prior dan kegagalan dalam arus |
| [29 — Validasi flare dan penerimaan ulang](plan/29-validasi-flare-dan-penerimaan-ulang.md) | Landmark, akustik hampir vertikal, retensi saat miring dan penerimaan lima fixture |
| [27 — Kalibrasi DVL dan GUI](plan/27-kalibrasi-dvl-dan-penerimaan-gui.md) | Koreksi bias preflight, penerimaan Gazebo + dua POV, dan batas akurasi |
| [26 — ARENA dinamis dan estimator](plan/26-arena-dinamika-dan-estimasi-sensor.md) | Model gaya bersama kualifikasi, isolasi ground truth dan penerimaan ulang |
| [24 — Migrasi dan uji 2027](plan/24-migrasi-dan-uji-arena-2027.md) | Profil default 2027, hasil runtime dan batas pembuktian |
| [20 — Pinger, pickup dan servo simulator](plan/20-pinger-pickup-dan-servo-simulator.md) | Mekanisme tambahan, dua fixture penerimaan dan batas model |

Log, trajectory, hasil referee dan ringkasan JSON berada secara lokal di `ros2_ws/evidence/`, yang diabaikan Git. Laporan menautkan artefak tersebut; artefak tidak otomatis tersedia pada clone baru. Percobaan gagal dipertahankan terpisah dari run penerimaan.

**Sinkronisasi 26 Oktober 2026:** `ros2_ws` dan HydroShips memakai satu profil tujuh thruster. Pemetaan output sudah dicocokkan dengan parameter Pixhawk; posisi/sudut dan matriks mixer fisik masih belum terverifikasi. Bukti terbaru tersedia pada [laporan 23](plan/23-sinkronisasi-7-thruster.md).

## Pekerjaan fisik yang tersisa

- Menentukan servo, driver/kanal dan catu daya; memfinalisasi mekanik, fabrikasi serta uji retensi/release basah.
- Mengkalibrasi thrust/PWM, baterai, massa, buoyancy, drag dan kemampuan putar kendaraan nyata.
- Mengkalibrasi kamera DWE, sensor kedalaman/IMU dan hidrofon; memverifikasi ketersediaan sensor lokalisasi fisik.
- Menguji kolam nyata, arus, air keruh, refleksi dan variasi susunan arena yang lebih luas.

Model OpenSCAD adalah rancangan awal, belum dirender atau diuji fabrikasi. Tidak ada klaim servo, pickup atau pinger fisik telah bekerja.

## Aplikasi onboard

Aplikasi dikembangkan di `hydroships/` dengan Git milik repositori AUV2027. Panduan pemasangan dan akses lokal **http://127.0.0.1:8081** tersedia pada [README aplikasi](hydroships/README.md). Profil eksperimen BlueOS sebelumnya menggunakan port 8080. Status simulator di atas tidak menyatakan aplikasi onboard sudah menjalankan misi tersebut pada AUV fisik.
