# Aktuasi rahang dan release terukur

19 November 2026. Melanjutkan gripper ringkas bergaya Newton pada [laporan 80](80-gripper-ringkas-bergaya-newton.md). Batang tetap 8 cm, di tengah body, tanpa slider; titik grip `(0, 0, −0,21) m`.

## Perubahan

Dua rahang kini link terpisah dengan sendi revolute sumbu X. Posisi awal tertutup dan bola tetap pada titik gripper. Command release membuka rahang melalui controller posisi Gazebo berbasis gaya; command grip menutupnya kembali. Batas latihan tiap rahang 0–0,35 rad, kecepatan 0,5 rad/s dan effort 0,04 Nm. Ini parameter simulator, bukan spesifikasi Newton atau kalibrasi servo nyata.

Release menunggu **posisi sendi yang diukur oleh physics** mencapai bukaan dengan galat kurang dari 0,015 rad pada kedua rahang. Timer servo lama tetap tersedia untuk kompatibilitas, tetapi selesainya timer saja tidak melepaskan bola. Limit latihan 0–20° per rahang dan command torsi maksimum 0,04 N·m; nilai ini belum dikalibrasi. `servo_angle_rad` tetap fase logis release lama, bukan sudut sendi aktual. Telemetri `/sauvc/arena/physics` menyediakan `jaw_ready`, `jaws_open`, `jaw_position_rad` dan `jaw_target_rad`.

![Rahang tertutup membawa bola](../ros2_ws/evidence/gripper-joints-20261119/preview/closed-loaded.png)

![Rahang terbuka saat bola dilepas](../ros2_ws/evidence/gripper-joints-20261119/preview/open.png)

[Video buka–lepas–tutup](../ros2_ws/evidence/gripper-joints-20261119/preview/jaw-motion.mp4) · [Rahang tertutup kembali tanpa bola](../ros2_ws/evidence/gripper-joints-20261119/preview/closed-empty.png). Render memakai world inspeksi dengan lampu tambahan, bukan perubahan cahaya misi. Frame dan posisi sendi direkam bersamaan; pengujian misi terpisah berjalan headless.

## Uji native

- Normal: command release pada 2,05 s, bola terlepas pada 2,85 s setelah kedua rahang terbuka. Command grip pada 4,40 s; posisi akhir ±0,00216 rad. Bola jatuh sekitar 1,725 m dengan gravitasi dan collision aktif.
- Macet: kedua limit sendi dikunci nol **hanya pada fixture fault**. Selama empat detik setelah release, timer servo telah selesai tetapi bola tetap attached dan tidak dinyatakan released. Salah satu sendi menyimpang sekitar 0,0133 rad akibat toleransi solver; ini tidak memenuhi bukaan dan tidak mengalahkan pengaman.
- Render normal mengulang hasil buka–lepas–tutup; 53 frame disimpan. Tidak ada pemindahan pose bola untuk memalsukan drop.

Probe awal gagal: ketika restraint preflight masih terpasang, sendi tetap nol. Pembanding tanpa anchor menunjukkan sendi bisa bergerak. Probe penerimaan kemudian melepas restraint lewat command thruster simulator yang sangat kecil sebelum release. Gain awal juga terlalu besar untuk inertia rahang dan menghasilkan osilasi sekitar 0,327 rad; gain P/D diubah menjadi 0,02/0,001 sehingga mencapai bukaan. Run diagnosis yang gagal tetap disimpan pada folder bukti, tidak dihitung sebagai penerimaan.

## Batas

Retensi bola masih memakai latch ideal; ini belum pembuktian genggaman berbasis gaya gesek, linkage/piston Newton, driver atau servo nyata. Batang pendek tetap **belum mendukung pickup dasar drum**, clearance mendatar −17 cm; extended tetap ditolak sebelum thrust. Tidak ada uji kendaraan fisik. Geometri dan performa produk Newton asli tidak diklaim.

## Bukti

[Probe native](../ros2_ws/evidence/gripper-joints-20261119/probe.py) · [normal](../ros2_ws/evidence/gripper-joints-20261119/accepted/verification.json) · [macet](../ros2_ws/evidence/gripper-joints-20261119/jam/verification.json) · [render](../ros2_ws/evidence/gripper-joints-20261119/preview/verification.json) · [202 tes unit](../ros2_ws/evidence/gripper-joints-20261119/unit-tests.log) · [build](../ros2_ws/evidence/gripper-joints-20261119/build.log).

## Regresi misi

Build dua paket selesai dan **202 tes unit lulus**. ARENA blue drum (seed 91, air 0,05/m) diterima: **210,14284 poin**, thrust–surface **228,572 s**, penalti nol. DONE, stationary, command/thrust akhir nol, akurasi estimator dan shutdown simulator lulus.

Parent batch awal berhenti dengan exit 143 ketika child ARENA masih berjalan. Run ARENA yang sama diteruskan sampai laporan akhir tersimpan; tidak diulang untuk mengganti hasil. Exit code child tidak dapat diambil ulang, sehingga ditandai `null` di ringkasan. Pemeriksaan shutdown di laporan misi tetap lulus; masalah terminasi parent belum didiagnosis.

Kualifikasi jalur 3 (offset 0,15 m, seed 42, air 0,10/m) juga diterima: gate kedua **22,994 s**, thrust–surface **25,578 s**, thrust–stop **30,542 s**. Exit 0, stationary, command/thrust akhir nol dan shutdown bersih. Kedua run memakai model gaya tujuh thruster dan estimator sensor; galat XY maksimum blue drum 6,35 cm dan kualifikasi 1,73 cm.

[Ringkasan verifikasi](../ros2_ws/evidence/gripper-joints-20261119/verification.json) · [ARENA](../ros2_ws/evidence/gripper-joints-20261119/blue/mission.json) · [kualifikasi](../ros2_ws/evidence/gripper-joints-20261119/qualification/mission.json) · [manifest source/aset](../ros2_ws/evidence/gripper-joints-20261119/source-sha256.json). Manifest 98 file diperiksa lagi setelah kedua run; source/aset tidak berubah selama penerimaan. Ini dua fixture terpilih, bukan pembuktian semua kondisi.

Pemeriksaan ulang bukti tersimpan:

```bash
cd /home/rasya/AUV/ros2_ws
bash tools/ros.sh python evidence/gripper-joints-20261119/verify.py
```
