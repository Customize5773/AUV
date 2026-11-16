# 69 — Pemeriksaan rulebook dan perbaikan halo biru ARENA

16 November 2026, Asia/Jakarta. Melanjutkan kegagalan pendekatan flare ARENA 0,05/m pada laporan 68.

## Rulebook

[Halaman resmi](https://sauvc.org/rulebook/) masih menyatakan **2027.3.2**, diperbarui **30 Oktober 2026**. Perbandingan `master` repo resmi dengan commit arsip menghasilkan `identical`, nol commit/file berubah. Tidak ada migrasi aturan simulator pada tahap ini. [Bukti pemeriksaan 16 November](../doc/sources/rulebook-check-20261116.json). Pemeriksaan ini mencakup halaman/source resmi tersebut, bukan pengumuman kanal privat.

## Diagnosis dari capture baru

Run headless dengan kondisi yang sama kembali gagal `mission_or_state_timeout`. Observer terpisah merekam metadata deteksi, gambar, estimasi pose dan ground truth untuk diagnosis. Controller tidak mendapat ground truth atau posisi fixture dari observer.

Rekaman menunjukkan penguat deteksi tiang biru tipis menghasilkan kandidat palsu di tepi objek merah/oranye. Piksel latar air di satu sisi objek memiliki blue-score lebih tinggi dibanding objek berwarna di sisi lainnya. Perbandingan dengan rata-rata kiri/kanan menganggapnya sebagai puncak biru, walaupun sisi yang lain masih latar biasa.

Pada 12 frame awal, flare biru sebenarnya berada di luar field of view, tetapi sisi orange flare diberi kandidat biru. Kandidat biru yang kemudian memenuhi filter proyeksi berada sekitar **3,65 m** dari posisi flare sebenarnya. Target yang keliru terkunci; pengaman loncatan map kemudian menolak observasi yang sebenarnya benar karena selisihnya lebih dari 0,75 m. AUV sempat menyentuh flare merah saat mencoba mencapai target biru yang keliru.

Capture lebih akhir memperlihatkan flare biru asli satu piksel: bbox detektor sesuai proyeksi observer dan estimasi posisinya sudah dekat posisi sebenarnya. Ini mempersempit penyebab ke kandidat palsu awal, bukan kebutuhan menaikkan toleransi map atau membuka akses ground truth bagi navigasi. [Capture baseline](../ros2_ws/evidence/arena-water-20261116/diagnosis/capture.json), [kandidat proyeksi](../ros2_ws/evidence/arena-water-20261116/diagnosis/blue-candidates.json), [frame dengan halo](../ros2_ws/evidence/arena-water-20261116/diagnosis/blue-00.png), [flare asli](../ros2_ws/evidence/arena-water-20261116/diagnosis/late/blue-00.png).

## Perubahan kecil pada detektor

[object_detection.py](../ros2_ws/src/sauvc_sim/sauvc_sim/object_detection.py) sekarang mensyaratkan blue-score lebih tinggi dari **kedua** tetangga horizontal, bukan rata-ratanya:

`contrast = min(center − left, center − right)`

Offset empat piksel, threshold kontras, mask warna ketat, syarat bentuk, tracking, proyeksi, outlier gate 0,75 m, kontrol, kecepatan, geometri dan referee tetap. Input detektor tetap RGB saja. Koreksi ditujukan pada jalur pemulihan flare biru tipis/desaturasi; gambar raw/POV tidak diubah.

Tes baru memasang objek merah/oranye/kuning/hijau/abu pada latar air berwarna, memastikan sisinya tidak menjadi flare biru palsu, lalu menambahkan tiang biru satu piksel yang terlalu desaturasi untuk mask ketat dan memastikan tetap terdeteksi.

## Bukti uji

- **194 tes unit lulus** dan build package selesai.
- **94 pemeriksaan perturbasi** pada frame simulator tersimpan lulus, termasuk blur, perubahan cahaya/noise dan occlusion yang dicakup penguji lama. Ini pemeriksaan label, bukan bukti akurasi metrik seluruh kondisi.
- Replay **12 frame halo** menghapus kandidat palsu; **tiga frame flare asli satu piksel** mempertahankan bbox-nya. [Replay kontras](../ros2_ws/evidence/arena-water-20261116/diagnosis/contrast-replay.json), [perturbasi](../ros2_ws/evidence/arena-water-20261116/perturbations.json).
- Pada penerimaan pertama, kandidat biru terkonfirmasi dengan posisi metrik sekitar **0,17 m** dari fixture, dibanding kandidat awal baseline sekitar 3,65 m. Ini perbandingan satu observasi per run oleh observer, bukan klaim semua galat posisi turun dengan rasio tersebut.

**Ketiga penerimaan headless lulus**, semuanya DONE, tiga flare jatuh sesuai urutan, penalti 0, bonus Square +20, kendaraan berhenti dengan command/gaya nol, shutdown bersih dan semua PID launch berakhir.

| Kasus | Kondisi | Poin | Thrust–surface | Galat XY maksimum |
|---|---|---:|---:|---:|
| Extended yang sebelumnya gagal | 0,05/m, seed 42, layout 1, Y–B–R, pinger drum 4 | 290,76456 | 207,848 s | 13,72 cm |
| Blue drum | 0,05/m, seed 7, layout 0, B–R–Y, blue drum 1 | 210,15790 | 228,070 s | 5,92 cm |
| Extended regresi ringan | 0,025/m, seed 91, layout 1, Y–B–R, pinger drum 4 | 290,74242 | 208,586 s | 13,89 cm |

Kedua extended juga membuktikan drop ke drum berpinger, seluruh badan keluar target zone, pickup dan retensi bola yang sama sampai akhir. Kasus blue drum membuktikan drop ke drum biru. Perbedaan fixture/urutan berarti waktu antarrun ini tidak dipakai untuk mengklaim percepatan kendaraan.

Source dan aset dibekukan pada [manifest](../ros2_ws/evidence/arena-water-20261116/acceptance/source-sha256.json). Verifier membuktikan bahwa dibanding source laporan 68, hanya `object_detection.py` dan tesnya yang berubah. [Summary runner](../ros2_ws/evidence/arena-water-20261116/acceptance/runner.json), [verifikasi lengkap](../ros2_ws/evidence/arena-water-20261116/acceptance/verification.json), [log verifier](../ros2_ws/evidence/arena-water-20261116/acceptance/verifier.log). Baseline yang gagal tetap disimpan; hasil ini bukan penghapusan kegagalan historis.

Dengan bukti tersebut, kegagalan pendekatan flare ARENA 0,05/m **terselesaikan pada fixture yang diuji**. Ini tiga run terpilih, bukan matriks keandalan lengkap.

## Batas dan penggunaan

Default tetap air jernih; profil ringan `water-light.json` tetap 0,025/m. Nilai 0,05/m adalah kondisi latihan sintetis, bukan hasil pengukuran kekeruhan kolam SAUVC atau NTU. Penerimaan terpilih belum membuktikan seluruh layout/cahaya/arus dan belum menjadi benchmark Jetson. GUI/POV tidak diulang pada tahap ini; pengujian headless tetap merender kedua kamera.

Kualifikasi 0,10/m dari laporan 68 belum diperbaiki atau diuji ulang. Tidak ada tuning kecepatan baru, perubahan model gaya atau pengujian AUV fisik. [Cara running dan POV](../ros2_ws/CARA-RUNNING.md).

Untuk memeriksa ulang bukti lokal pada source yang sama, dari `ros2_ws`:

```bash
bash tools/ros.sh python evidence/arena-water-20261116/acceptance/verify.py
```

Seluruh command, kondisi JSON, capture dan runner serial tersedia di direktori bukti. Pilih output baru saat mengulang pengujian agar hasil sebelumnya tetap utuh.

Kelanjutan: [laporan 70](70-kualifikasi-optik-010-dan-median-warna.md) menyelesaikan kasus kualifikasi 0,10/m pada tiga jalur terpilih; kegagalan yang tercatat di sini tetap menjadi bukti historis.
