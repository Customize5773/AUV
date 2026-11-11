# AUV2027 — HydroShips

**Alur aktif: [VS Code Remote SSH melalui Wi-Fi](CARA-OPERASI-SSH.md).** Migrasi GUI dan bukti pengujian: [laporan 53](plan/53-operasi-ssh-dan-arsip-gui.md).

Panduan perintah kualifikasi, ARENA dan kedua POV: [Cara running simulator](ros2_ws/CARA-RUNNING.md).

Peta kode dan panduan Graphify: [Graphify untuk repo AUV](doc/GRAPHIFY.md).

Repositori persiapan AUV tim HydroShips: operasi Jetson melalui VS Code Remote SSH, simulasi SAUVC dengan ROS 2/Gazebo, rancangan mekanik, serta laporan pengujian.

| Folder | Isi |
| --- | --- |
| `GUI-prototype/` pada Jetson | Arsip GUI lama; dihapus dari laptop sesuai konfirmasi pengguna, layanan dinonaktifkan |
| [tools/](CARA-OPERASI-SSH.md) | Operasi terminal: perangkat, telemetry pasif, uji kamera dan simulator systemd |
| [config/](config/propulsion.json) | Profil tujuh thruster bersama, mandiri dari GUI |
| [ros2_ws/](ros2_ws/README.md) | Workspace SAUVC terpisah: kualifikasi, ARENA, persepsi kamera dan misi autonomous |
| [mechanical/payload-servo/](mechanical/payload-servo/README.md) | Konsep parametrik pelepas payload dan gripper pickup berbasis servo |
| [plan/](plan/README.md) | Keputusan, rencana implementasi dan laporan bukti pengujian |
| [doc/](doc/README.md) | Riset SAUVC, referensi aturan dan arsip sumber |
| [deploy/blueos/](deploy/blueos/README.md) | Eksperimen adaptasi BlueOS resmi untuk Jetson |

## Status simulator

**Profil default kini SAUVC 2027.3.2**, berdasarkan [source resmi terkunci](doc/sources/rulebook-2027.3.2/README.md) dan audit perbedaan seluruh bagian terhadap 2027.2.1. Aturan tugas/skor/geometri tidak berubah; perubahan isi ada pada keanggotaan tim. Tiga kualifikasi dan dua misi ARENA lulus pada [laporan 41](plan/41-audit-dan-migrasi-rulebook-2027-3-2.md). Riwayat migrasi awal arena 2027 tetap pada laporan 24; fixture 2026 tersedia sebagai regresi eksplisit.

| Bagian | Status dan batas hasil |
| --- | --- |
| Geometri 2027 | Kolam, tiga jalur, gate menggantung, gate utama 1,5 × 1,5 m, mat 8 × 2 m dan Surfacing Square 2 × 2 m tersedia; posisi properti adalah pilihan latihan |
| Kualifikasi | Dive → pelintasan penuh → U-turn → kembali → surface → stop; dinamika tujuh thruster dan estimasi sensor virtual |
| Persepsi | Gate, flare, drum dan marker Surfacing Square dari kamera; tracking dan proyeksi metrik |
| ARENA blue drum | Navigation dahulu → flare sesuai urutan → drop blue drum → Surfacing Square → stop |
| ARENA pinger/pickup | TDOA virtual → drop red drum berpinger → seluruh badan keluar target zone → pickup bola yang sama → retensi sampai akhir |
| Penilaian 2027 | Timer sejak thrust, poin tugas, penalti kontak, bonus surface dan bonus Square; bonus inspeksi fisik tidak dimasukkan |
| Bukti pengujian terbaru | 178 tes unit simulator lulus; kualifikasi melalui terminal/systemd mencapai DONE dan shutdown bersih pada migrasi SSH (laporan 53) |

**ARENA dan kualifikasi autonomous visual kini memakai model gaya tujuh thruster dan estimator sensor virtual secara default.** Ground truth digunakan oleh referee/pencatat; profil ideal tersedia sebagai pembanding eksplisit. [Laporan 26](plan/26-arena-dinamika-dan-estimasi-sensor.md) mencatat penerimaan awal dinamis; [laporan 27](plan/27-kalibrasi-dvl-dan-penerimaan-gui.md) memuat kalibrasi DVL dan dua misi penuh dengan Gazebo serta kedua POV. Pinger adalah model geometrik TDOA, servo pelepas memakai respons ideal, dan pickup memakai latch fixed setelah kontak. Hasil ini belum membuktikan performa AUV fisik atau ketahanan pada seluruh kondisi kolam.

[Laporan 51](plan/51-regresi-pinger-dan-transport-jetson.md) memverifikasi dua run final ARENA pinger/pickup extended dengan profil SHM 16 MiB: retensi bola, skor dan shutdown bersih lulus. Satu kegagalan shutdown pada batch awal tetap dicatat. Transport sintetis lokal Jetson juga mereproduksi kehilangan default dan pulih ke 80/80 frame per aliran pada profil 16 MiB. Kamera exploreHD terdeteksi tetapi belum diuji streaming; backend HydroShips Jetson kemudian dipulihkan pada [laporan 52](plan/52-pemulihan-hydroships-jetson.md): unit memakai path repo aktif, venv Linux baru, API sehat dan bridge ROS ready; kendaraan tetap disconnected.

[Laporan 50](plan/50-akar-kehilangan-frame-shared-memory.md) berhasil mereproduksi kehilangan gambar besar pada ROS tanpa Gazebo: payload RGB 640×480 (900 KiB) melampaui segment shared memory 512 KiB. Perubahan kapasitas publisher ke 16 MiB mengembalikan 180/180 frame pada dua kamera; pembalikan ke 512 KiB mengembalikan kehilangan. Profil diterapkan khusus proses penerbit gambar, dengan resolusi dan watchdog tetap. Sebanyak 178 tes unit, tiga kualifikasi GUI, ARENA standar serta respons kehilangan kamera diterima. Regresi extended serta transport sintetis Jetson disusul pada laporan 51; driver kamera nyata belum divalidasi.

[Laporan 49](plan/49-diagnosis-transport-kamera.md) mempersempit anomali kamera terukur ke jalur setelah penerimaan native Gazebo, lalu menerapkan QoS gambar BEST_EFFORT dengan antrean satu frame. Gap frame segar persepsi depan pada tiga kualifikasi turun dari 1,20–1,50 s menjadi 0,50–0,71 s; tiga kualifikasi dan satu ARENA GUI final serta uji kehilangan kamera diterima. Sebanyak 177 tes unit lulus. Eksperimen asinkron tidak dipromosikan karena satu kegagalan shutdown; akar unik abort kamera historis masih terbuka.

[Laporan 48](plan/48-pemulihan-gate-hilang.md) mengoreksi skala yaw pencarian gate dinamis: nominal 0,18 rad/s sebelumnya mencapai 0,7 rad/s. Sebanyak 175 tes unit lulus; tiga GUI dan satu headless selesai, tetapi satu GUI abort stale_camera sehingga penerimaan masih parsial. Uji kehilangan kamera sengaja membuktikan abort dan gaya nol. Penyebab insiden gate_lost lama belum dinyatakan selesai.

[Laporan 47](plan/47-shutdown-pov-kamera.md) memperbaiki lifecycle POV melalui penampil Qt satu proses dan menutup GUI Gazebo sebelum server. Kualifikasi serta ARENA dinamis dengan dua POV lulus tanpa cleanup paksa; 174 tes unit lulus. Dua percobaan GUI sebelumnya gagal dan dipertahankan, termasuk satu `gate_lost` yang belum terselesaikan. Perintah POV terbaru ada di [panduan running](ros2_ws/CARA-RUNNING.md).

[Laporan 46](plan/46-penerimaan-kualifikasi-dan-regresi-pinger.md) menerima tiga kasus kualifikasi lanjutan (arus dengan hold dan dua prior), serta regresi ARENA pinger/pickup dinamis setelah isolasi bridge. Hold berarus 30 detik mencatat drift 0,50 cm dan emergency stop terverifikasi. Pinger mencatat thrust–surface 205,798 detik, skor simulator 290,82606 dan penalti 0. Sebanyak 170 tes unit lulus. Bukti 15 run jalur sebelumnya dan kelanjutan dipisahkan menurut snapshot source; motor-off dalam arus tetap dapat hanyut.

[Laporan 44](plan/44-konsistensi-kualifikasi-dan-preflight.md) melanjutkan konsistensi kualifikasi: 169 tes unit dan uji startup tertunda lulus. Batch pada source perbaikan menerima 15 run tiga jalur, lalu berhenti pada kasus arus yang gagal syarat stationary setelah motor-off; belum lulus 18/18. Pixhawk USB Jetson sudah menerima telemetri pada pemeriksaan pasif; tetap disarmed, [diagnosis CRITICAL dan verifikasi parameter](plan/45-diagnosis-pixhawk-usb-jetson.md) tersedia.

[Laporan 43](plan/43-isolasi-bridge-kamera-dan-sensor.md) menerapkan default bridge kamera terpisah. Jeda proses kamera 1 s dapat dilalui dengan sensor tetap segar; jeda kamera 3 s dan kehilangan bridge sensor tetap memicu abort. Dua kualifikasi (termasuk GUI/dua POV), ARENA blue drum penuh serta hold berarus 180 s lulus; drift hold 2,09 cm. Subscriber raw-image lambat tidak mereproduksi stale; penyebab insiden lama tetap belum terbukti. Detail shutdown parent/Qt dicatat dalam laporan.

[Laporan 42](plan/42-diagnosis-lokasi-stale-sensors.md) memvalidasi diagnosis produsen/native/ROS/estimator dengan dua pencatat independen. Umur sensor maksimum run nominal 73,37 ms terhadap batas 300 ms; drift hold 180 s 2,10 cm. Data lama tidak cukup untuk menentukan penyebab unik. Gazebo/probe shutdown bersih; grup viewer RQt masih memerlukan cleanup paksa yang dicatat.

[Laporan 41](plan/41-audit-dan-migrasi-rulebook-2027-3-2.md) menyelesaikan audit dan migrasi acuan 2027.3.2. Lima run headless diterima; diagnosis lokasi diteruskan pada laporan 42 dan isolasi transport pada laporan 43; penyebab historis, konsistensi dan optimasi vertikal rencana 40 masih terbuka.

[Laporan 39](plan/39-benchmark-dan-percepatan-uturn.md) mempercepat U-turn dinamis dengan permintaan yaw 0,7 rad/s. Tiga kandidat lulus pelintasan penuh dan mencatat start–surface 25,838–25,942 s, lebih cepat daripada baseline berpasangan. Rulebook resmi kini 2027.3.2 (30 Oktober); [pemeriksaan kualifikasi](doc/sources/rulebook-2027.3.2-check.md) pada tahap tersebut masih memakai fixture 2027.2.1; audit/migrasi berikutnya ada pada laporan 41.

[Laporan 38](plan/38-fault-runtime-setelah-gerak.md) mengikat fault kamera, command, odometry, contact, clock dan controller freeze ke awal gerak. Sembilan run diterima, termasuk kamera/command ARENA; batas pengaman tidak dilonggarkan.

[Laporan 37](plan/37-fault-setelah-start.md) memperbaiki waktu injeksi kehilangan IMU, tekanan, DVL dan aktuator menjadi 12 detik sesudah thrust mulai. Lima respons fault dan satu misi normal lulus; argumen kondisi kosong pada kedua penguji juga diperbaiki.

[Laporan 36](plan/36-investigasi-stale-sensors.md) menambahkan diagnostik jeda penerimaan dan umur paket sensor. Dua pengulangan bersih serta satu uji fault setelah DIVE lulus, tetapi penyebab gangguan spontan lama belum teridentifikasi.

[Laporan 35](plan/35-kualitas-kalibrasi-dvl-sebelum-start.md) menambahkan pemeriksaan kualitas bias DVL sebelum start. 139 tes unit lulus; 5/6 percobaan diterima. Tiga hold 180 detik yang diterima mencatat drift 2,10/2,07/1,86 cm; satu percobaan gagal karena stale_sensors. Kualifikasi nominal dan ARENA berarus lulus. Persiapan sampai thrust 26,76–28,31 detik simulasi. Gangguan sensor intermiten masih terbuka.

[Laporan 34](plan/34-uji-hold-panjang-dan-variasi-arus.md) menguji hold 180 detik pada arus konstan 0,02/0,05/0,10 m/s dengan arah berbeda antar-run. Dua dari tiga hold panjang lulus; satu gagal dengan drift 12,05 cm meski estimasi posisi tampak stabil. Regresi 30 detik lulus. Temuan menunjukkan batas bias DVL tersisa; hold jangka panjang belum andal. Pengendali tidak diubah dan ambang tidak dilonggarkan.

[Laporan 33](plan/33-sinkronisasi-kamera-dan-estimator.md) memperbaiki urutan kamera–sensor: observasi menunggu waktu estimator menyusul sebelum dikoreksi. Lima kasus prior, termasuk tiga pengulangan seed 91, menerima 13–19 koreksi dan mencatat galat maksimum 14,43–15,01 cm. Nominal dan hold berarus juga lulus; drift hold 2,36 cm dalam 30 detik. ARENA dan GUI tidak diuji ulang pada tahap ini.

[Laporan 32](plan/32-surface-hold-dan-koreksi-prior.md) menambahkan `surface_hold:=true` untuk menjaga estimasi posisi setelah surface dengan thruster aktif; default tetap motor-off. Empat hold berarus 0,02 m/s mencatat drift maksimum 2,01 cm dalam jendela 30 detik. Empat kasus prior kualifikasi lulus dengan galat maksimum 14,45–18,24 cm, memakai koreksi visual bersyarat terhadap gate yang disurvei; satu run tidak menerima koreksi. Inisialisasi sensor parsial dan penilaian hold ARENA juga diperbaiki. Ini penerimaan terbatas, bukan bukti semua kondisi atau kendaraan nyata.

[Laporan 31](plan/31-kalibrasi-dvl-dalam-arus.md) memperbaiki kalibrasi DVL dalam arus melalui penahan fisik virtual selama preflight dan konfirmasi penahan sebelum mempelajari bias. Penahan dilepas saat thrust pertama. Galat ARENA berarus turun dari 1,0594 menjadi 0,0651 m; ketiga kualifikasi berarus kini lulus akurasi. Ini prosedur penempatan tertahan, belum kalibrasi bebas hanyut. Pada tahap laporan 31, station keeping dan prior posisi belum diubah; kelanjutannya dicatat pada [laporan 32](plan/32-surface-hold-dan-koreksi-prior.md).

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
| [43 — Isolasi bridge kamera](plan/43-isolasi-bridge-kamera-dan-sensor.md) | 160 tes; enam eksperimen A/B/fault + empat penerimaan default, termasuk hold 180 s; guard tetap aktif |
| [42 — Diagnosis lokasi stale_sensors](plan/42-diagnosis-lokasi-stale-sensors.md) | 157 tes; 11 run matriks utama, empat lokasi fault terbedakan; sebab historis tetap tak teridentifikasi |
| [41 — Audit dan migrasi 2027.3.2](plan/41-audit-dan-migrasi-rulebook-2027-3-2.md) | 148 tes; tiga kualifikasi dan dua ARENA lulus, sumber dikunci dan delta diaudit |
| [40 — Rencana solusi berikutnya](plan/40-rencana-solusi-dan-validasi-berikutnya.md) | Tahap audit selesai; diagnosis, konsistensi dan optimasi lanjutan masih terbuka |
| [39 — Benchmark dan percepatan U-turn](plan/39-benchmark-dan-percepatan-uturn.md) | 147 tes; tiga pasangan lulus dan lebih cepat; fixture tetap 2027.2.1 |
| [38 — Fault runtime setelah gerak](plan/38-fault-runtime-setelah-gerak.md) | 146 tes; delapan respons fault dan satu misi normal lulus |
| [37 — Fault setelah start](plan/37-fault-setelah-start.md) | Empat fault native terikat start; lima respons fault dan satu kualifikasi normal lulus |
| [36 — Investigasi stale_sensors](plan/36-investigasi-stale-sensors.md) | Diagnostik, dua hold lulus, satu fault bridge saat misi aktif; gangguan historis masih terbuka |
| [35 — Kualitas kalibrasi DVL sebelum start](plan/35-kualitas-kalibrasi-dvl-sebelum-start.md) | Kesiapan berdasarkan ketidakpastian bias; 139 tes, 5/6 percobaan diterima |
| [34 — Hold panjang dan variasi arus](plan/34-uji-hold-panjang-dan-variasi-arus.md) | 134 tes unit; 3/4 run diterima, satu hold 180 detik gagal drift |
| [33 — Sinkronisasi kamera dan estimator](plan/33-sinkronisasi-kamera-dan-estimator.md) | 132 tes unit dan tujuh kualifikasi lulus; koreksi konsisten pada lima kasus prior |
| [32 — Surface hold dan koreksi prior](plan/32-surface-hold-dan-koreksi-prior.md) | Hold aktif opt-in, disarm saat fault, koreksi visual gate survei dan startup sensor parsial |
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

## Operasi onboard

Gunakan [panduan SSH](CARA-OPERASI-SSH.md). Laptop membuka `/home/aero/AUV` pada Jetson melalui `auv-wifi`; edit dan eksekusi berjalan di Jetson. GUI disimpan di `/home/aero/AUV/GUI-prototype` pada Jetson; folder GUI laptop telah dihapus sesuai konfirmasi pengguna. Integrasi kendali misi fisik belum tersedia; perintah simulasi tetap terisolasi dari hardware.

**Model AUV — 11 November 2026:** FBX SAUVC 2027 v1 sudah menjadi visual default simulator, dengan collision dan dinamika yang ada tetap dipakai. Build dan 179 tes lulus; kualifikasi serta ARENA dinamis dengan dua POV lulus pada penerimaan akhir. [Laporan 57 dan screenshot Gazebo](plan/57-model-auv-fbx-simulator.md).

**Regresi extended — 12 November 2026:** model AUV baru lulus satu run pinger/pickup extended, termasuk bola yang sama, retensi hingga stop, dua POV dan shutdown; skor 290,79888 tanpa penalti. 179 tes unit lulus kembali. Satu percobaan awal gagal karena viewer keluar. [Laporan 58](plan/58-regresi-pinger-model-auv.md).

**Gripper pickup — 12 November 2026:** titik tangkap dinaikkan 5 cm ke z −0,40 m, dengan dudukan tersambung ke badan. 180 tes dan satu penerimaan extended GUI/POV lulus. Clearance hull–rim nominal 2 cm masih memerlukan validasi fisik. [Evaluasi dan pembanding](plan/59-posisi-gripper-lebih-dekat.md).

**Evaluasi body — 12 November 2026:** penyederhanaan mesh sebelumnya terlalu agresif pada panel; revisi 816.288 segitiga memulihkan bentuk mendekati FBX penuh. 180 tes simulator, 2 tes konversi dan kualifikasi GUI/POV lulus. Collision dan parameter fisika masih pendekatan latihan. [Laporan 60](plan/60-evaluasi-body-dan-kualitas-mesh.md).

**Penerimaan body revisi — 12 November 2026:** ARENA extended GUI/POV lulus pada run pertama, termasuk pickup bola yang sama hingga stop; 290,77638 poin, penalti nol dan shutdown bersih. [Laporan 61](plan/61-penerimaan-extended-body-revisi.md).

**Collision sesuai visual — 12 November 2026:** hull box kini 51,8486 × 38,6876 × 20 cm, mengikuti batas mesh. Start-wall, prior estimator dan envelope referee disinkronkan; frame kamera tidak dihitung sebagai benda fisik. Build, 183 tes, dua kualifikasi (termasuk start miring) dan satu ARENA extended lulus; GUI/dua POV serta shutdown bersih terverifikasi pada run nominal dan extended. Gripper tidak berubah. Collision tetap AABB, parameter fisika belum terkalibrasi pada AUV nyata. [Laporan 62](plan/62-collision-sesuai-batas-visual.md).

**Regresi collision — 12 November 2026:** kualifikasi jalur 2 dengan arus 0,02 m/s dan prior meleset lulus; drift hold aktif 0,52 cm dalam sekitar 30 s dan emergency stop lulus. Satu ARENA selesai tetapi gagal shutdown; kedua penguji kini pause sebelum GUI exit. Kualifikasi dan ARENA GUI/dua POV sesudah perbaikan diterima dengan shutdown bersih; ARENA blue drum 2 mencatat 210,40156 poin tanpa penalti. 183 tes unit lulus. Semua percobaan tetap dicatat; belum jaminan keandalan semua kondisi atau validasi fisik. [Laporan 63](plan/63-regresi-collision-arus-dan-blue-drum.md).
