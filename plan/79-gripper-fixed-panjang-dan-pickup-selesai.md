# Gripper fixed 30 cm di bawah hull dan penerimaan pickup

19 November 2026. Pengguna mengizinkan titik grip diperpanjang setelah diagnosis gripper pendek. **Gripper tetap di tengah dan tanpa slider**, dengan titik grip `(0, 0, −0,40) m`, yaitu 30 cm di bawah hull. Pekerjaan ini hanya pada simulator.

## Hasil

Build selesai, **200 tes lulus**, serta penerimaan extended, blue drum dan kualifikasi diterima. Pickup yang sebelumnya ditolak kini berhasil pada fixture extended: drop ke red drum berpinger, seluruh badan keluar target zone, kembali mengambil bola yang sama, lalu mempertahankannya hingga surface–stop.

| Fixture 2027 dinamis | Hasil |
|---|---|
| Extended, varian 1, blue drum 3, pinger drum 4, Y–B–R, seed 42, air 0,05/m, Gazebo/dua POV | **290,8026 poin**, thrust–surface **206,580 s**, penalti nol, retensi sampai stop; galat XY maksimum 9,64 cm |
| Blue drum, seed 91, air 0,05/m | **210,15928 poin**, thrust–surface **228,024 s**, penalti nol; galat XY maksimum 6,88 cm |
| Kualifikasi jalur 3, offset 0,15 m, seed 42, air 0,10/m | Gate kedua **22,234 s**, thrust–surface **24,818 s**, thrust–stop **29,272 s**; galat XY maksimum 1,79 cm |

Ketiganya DONE, stationary, command/gaya akhir nol, akurasi estimator memenuhi pemeriksa, dan shutdown bersih. Gazebo serta kedua POV extended terverifikasi; encoder rekaman keluar 0 dan viewer tidak membutuhkan cleanup paksa.

![Render awal gripper tetap panjang dengan bola terpasang](../ros2_ws/evidence/gripper-fixed-040-20261119/initial.png)

Gambar berasal dari spectator Gazebo. Lampu inspeksi hanya ditambahkan pada world capture. Pada **110 snapshot awal**, bola berada pada titik grip yang sama, attachment pemuatan aktif, payload belum dilepas. Selisih maksimum tercatat 0 m pada resolusi telemetri.

## Perubahan yang diperlukan

- Titik grip berubah dari z −0,18 menjadi **−0,40 m**; dudukan rigid kini tersambung dari atap jari sampai hull. Joint tetap `fixed`; tidak ada joint prismatic atau mekanisme memanjang.
- Spawn bola, drop/pickup alignment dan retensi memakai titik grip yang sama. Bukaan collision jari tetap 42 mm untuk bola 40 mm. Clearance nominal hull terhadap bibir drum +2 cm, menjadi sekitar **1,8 cm** pada pendekatan kontak.
- Envelope bersama mencakup alat tetap dan bola yang dibawa. Transform tool yang berulang pada referee ARENA dihapus karena sudah tercakup dalam envelope bersama. Batas floor/gate tidak dilonggarkan.
- Jadwal kedalaman profil legacy 2026 juga memakai kedalaman dangkal di dekat tepi kolam agar alat panjang tidak diarahkan ke lantai; runtime legacy tidak termasuk penerimaan tahap ini.
- Kualifikasi 2027 memakai target kedalaman kerja **−0,50 m**. Pendekatan tetap mulai setelah estimasi kedalaman −0,25 m sambil melanjutkan penyelaman. Pada posisi mendatar di kedalaman kerja, batas bawah alat/bola konservatif −0,92 m, sehingga berada di dalam bukaan gate −1…0 m.

Regresi kualifikasi pertama pada target lama −0,60 m **gagal `outside_gate_opening`** karena alat baru terlalu dalam. Run tersebut tetap disimpan. Setelah target kerja diperbaiki, pengulangan lulus. Tes baru memeriksa envelope alat di bukaan gate dan command kedalaman, termasuk mode ideal/dinamis; pengaman geometri tak terjangkau tetap diuji dengan konfigurasi negatif.

Dua ARENA dijalankan sebelum penyesuaian kedalaman kualifikasi terakhir. Manifest sebelum/sesudah menunjukkan perubahan lanjutan tepat pada `qualification.py` dan tesnya; geometri, controller ARENA, referee, plugin serta aset yang dipakai ARENA cocok dengan revisi sekarang. Penyesuaian tersebut tidak mengubah ARENA. Manifest akhir mencakup **98 source/binary/aset**.

## Bukti retensi dan batas mekanisme

Setelah release terdapat fase payload bebas, kemudian **1.340 snapshot** payload terpasang kembali. Jarak maksimum bola terhadap titik grip native **4,71 cm**, di bawah toleransi **7,5 cm** yang tetap. Referee memberi acquisition 50, reacquisition 60 dan mencatat keluar zona sebelum pengambilan kembali, dengan ID bola `payload` yang sama.

Mekanisme pickup simulator adalah **joint latch ideal yang hanya dibuat setelah collision dengan bola**, bukan model jari menutup dan mempertahankan bola melalui gaya gesek. Sampel telemetri 20 Hz tidak menangkap flag kontak singkat pada run ini (`pickup_contact_frames_observed = 0`); karena itu tidak ada klaim kontak langsung terekam pada frame tersebut. Bukti runtime adalah attachment/gerak bola, retensi dan skor, bersama syarat kontak pada pembentukan latch di plugin. Kamera/rekaman tidak menggantikan pemeriksa fisika.

Servo pelepas masih respons ideal latihan. Torsi, waterproofing, fabrikasi, massa/dimensi serta mekanik AUV nyata belum divalidasi. Kedalaman transit legacy 2026 juga disesuaikan untuk alat panjang pada bagian kolam dangkal. Profil penerimaan ini 2027; runtime profil legacy 2026 dan seluruh kondisi lingkungan tidak diuji pada tahap ini. Pengujian fisik tetap dikecualikan.

## Bukti dan cara menjalankan

- [Verifikasi gabungan](../ros2_ws/evidence/gripper-fixed-040-20261119/verification.json) · [skrip pemeriksa bukti](../ros2_ws/evidence/gripper-fixed-040-20261119/verify.py) · [manifest akhir](../ros2_ws/evidence/gripper-fixed-040-20261119/source-sha256.json).
- [Extended](../ros2_ws/evidence/gripper-fixed-040-20261119/extended-1/mission.json) · [video dua POV](../ros2_ws/evidence/gripper-fixed-040-20261119/extended-1/pov.mp4) · [blue drum](../ros2_ws/evidence/gripper-fixed-040-20261119/blue/mission.json) · [kualifikasi final](../ros2_ws/evidence/gripper-fixed-040-20261119/qualification-2/mission.json).
- [Kualifikasi gagal sebelum koreksi kedalaman](../ros2_ws/evidence/gripper-fixed-040-20261119/qualification/mission.json) · [manifest sebelum koreksi](../ros2_ws/evidence/gripper-fixed-040-20261119/before-depth-source-sha256.json).
- [200 tes](../ros2_ws/evidence/gripper-fixed-040-20261119/unit-tests-depth.log) · [build](../ros2_ws/evidence/gripper-fixed-040-20261119/build.log) · [panduan launch dan POV](../ros2_ws/CARA-RUNNING.md).

```bash
cd /home/rasya/AUV/ros2_ws
bash tools/ros.sh python evidence/gripper-fixed-040-20261119/verify.py
```

Perintah ini memeriksa bukti tersimpan, termasuk hash source dan ruang lingkup perubahan antar-run. Tidak mengaktifkan hardware.
