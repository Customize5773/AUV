# Optimasi awal kualifikasi dinamis

19 November 2026. Fokus: mengurangi waktu kualifikasi dengan model gaya tujuh thruster, estimator sensor dan gripper pendek tetap. Tidak menguji kendaraan fisik.

## Perubahan

Controller kualifikasi dinamis edisi 2027 mulai mencari/mendekati gate ketika estimasi kedalaman mencapai **−0,25 m**, sambil terus mengatur kedalaman menuju **−0,60 m** selama transit. Sebelumnya kendaraan menunggu kedalaman kerja tercapai sebelum pendekatan dimulai.

Batas kecepatan dan gaya, clearance U-turn 0,6 m, pelintasan penuh, timer, referee, sensor dan batas stale tetap sama. Profil ideal serta edisi 2026 mempertahankan transisi sebelumnya. Angka −0,25 m adalah parameter latihan untuk model ini, bukan ketentuan kedalaman dari rulebook atau kalibrasi AUV nyata.

Perubahan produksi hanya pada transisi DIVE di `qualification.py`, ditambah satu tes perilaku: belum maju sebelum ambang, kedalaman tetap dikendalikan saat mulai maju, dan profil lama mempertahankan perilakunya. **198 tes simulator lulus.** Ini perubahan Python; plugin C++ tidak diubah atau dibangun ulang pada sesi ini.

## Perbandingan kondisi identik

Tiga run baseline diselesaikan sebelum source diubah, lalu tiga run sesudah perubahan. Semuanya jalur 1, seed 7, prior nol, arus nol, atenuasi 0/m, speed scale 8, dinamis dan tanpa GUI. Setiap run memiliki world/launch baru. Kondisi identik tidak menjadikan penjadwalan kamera/DDS deterministik.

| Metrik simulasi | Median sebelum | Median sesudah | Berkurang |
|---|---:|---:|---:|
| Thrust → gate kedua | 23,678 s | **21,802 s** | **1,876 s** |
| Thrust → surface | 26,772 s | **24,896 s** | **1,876 s** |
| Thrust → stop | 32,280 s | **29,554 s** | **2,726 s** |

![Perbandingan tiga run per revisi](../ros2_ws/evidence/qualification-start-20261119/comparison.png)

Ketiga baseline dan ketiga run baru lulus. Rentang waktu gate baseline **22,756–23,682 s**; sesudah perubahan **21,062–22,028 s**. Durasi state DIVE sebelum pendekatan sekitar 2,950 s pada baseline dan 1,248–1,256 s sesudah perubahan. Ini menunjukkan jeda yang dipangkas, bukan bukti waktu seluruh misi deterministik atau tercepat di lomba.

## Uji tambahan pada controller baru

| Fixture | Gate kedua | Surface | Stop | Hasil |
|---|---:|---:|---:|---|
| Jalur 2, seed 42, prior ±10 cm, offset 15 cm, yaw 0,1 rad | 21,046 s | 24,174 s | 28,764 s | Lulus |
| Jalur 3, seed 42, atenuasi 0,10/m, offset 15 cm | 22,138 s | 25,232 s | 29,686 s | Lulus |

**Lima run pada controller baru diterima**, mencakup tiga jalur. Seluruh delapan run sesi ini (tiga baseline + lima baru) DONE, stationary, command/gaya akhir nol dan shutdown bersih; pemeriksa akurasi serta navigasi sensor juga lulus. Tidak ada batas kelulusan yang dilonggarkan. Manifest baseline identik antar-run; manifest baru identik antar-run dan cocok dengan source saat verifikasi. Perbedaan kedua manifest tepat file controller dan tesnya. Manifest tambahan meliputi 98 source/binary/aset.

## Batas dan aturan

Halaman resmi diperiksa 19 November: versi yang ditampilkan tetap **2027.3.2**, diperbarui 30 Oktober. Kualifikasi tetap menuntut dua pelintasan seluruh badan dengan U-turn; waktu resmi berhenti pada pelintasan kedua. Surface/stop merupakan metrik tambahan proyek. [Rulebook resmi](https://sauvc.org/rulebook/#qualification) · [catatan pemeriksaan halaman](../ros2_ws/evidence/qualification-start-20261119/rulebook-check.json). Pemeriksaan ini tidak mengklaim perbandingan seluruh commit repo resmi pada 19 November.

Pengulangan nominal tiga kali per revisi merupakan sampel kecil. Arus, seluruh kondisi persepsi, GUI dan hardware belum diulang untuk perubahan ini. ARENA tidak memakai transisi controller kualifikasi yang diubah; bukti ARENA tetap run 18 November, bukan run baru sesi ini. Pickup pendek tetap terbuka sesuai [laporan 77](77-diagnosis-pickup-dengan-titik-mesh-asli.md).

## Bukti

[Verifikasi gabungan](../ros2_ws/evidence/qualification-start-20261119/verification.json) · [skrip pemeriksa](../ros2_ws/evidence/qualification-start-20261119/verify.py) · [source/aset hash](../ros2_ws/evidence/qualification-start-20261119/source-sha256.json) · [log 198 tes](../ros2_ws/evidence/qualification-start-20261119/unit-tests.log).

```bash
cd /home/rasya/AUV/ros2_ws
bash tools/ros.sh python evidence/qualification-start-20261119/verify.py
```

Perintah memeriksa bukti tersimpan terhadap source saat ini, tanpa menjalankan hardware. Manifest laporan 75/76 merujuk controller sebelum optimasi ini dan dapat menolak source baru; gunakan verifikasi laporan ini untuk revisi aktif.
