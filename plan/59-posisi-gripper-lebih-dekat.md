# 59 — Gripper pickup lebih dekat ke badan AUV

Tanggal: 12 November 2026. Lingkup: posisi alat pickup pada simulasi extended. Bukan perubahan titik pelepasan payload awal atau kalibrasi mekanisme fisik.

## Evaluasi penempatan

Posisi lama titik tangkap adalah `(−0,20, 0, −0,45) m` terhadap pusat badan, sedangkan bagian bawah mesh/collision berada sekitar `z = −0,10 m`. Alat pickup tampak terpisah dari badan; titik tangkap berjarak 35 cm dari bawah hull.

Posisi akhir dipilih `(−0,20, 0, −0,40) m`: **naik 5 cm**, tanpa mengubah posisi horizontal. Atap naik dari `−0,42` menjadi `−0,37 m`. Dudukan kotak 16 × 16 mm menghubungkan atap ke badan, dari `z = −0,37` hingga `−0,09 m`; bertumpang tindih sedikit dengan hull dan atap agar tidak ada celah sambungan.

Batas reach diperiksa dari geometri simulator, bukan perkiraan visual:

- Bibir drum berada 32 cm di atas floor (base 2 cm dan dinding dengan puncak 32 cm).
- Pusat bola yang mengendap berada sekitar 4 cm di atas floor (base 2 cm + radius bola 2 cm).
- Hull mempunyai setengah tinggi 10 cm.

Untuk clearance hull 2 cm saat menjangkau bola, offset vertikal titik tangkap adalah `0,32 + 0,10 − 0,04 + 0,02 = 0,40 m`.

| Pilihan titik tangkap di bawah pusat | Clearance hull terhadap bibir saat bola terjangkau | Keputusan |
|---|---|---|
| 45 cm, lama | 7 cm | Bisa menjangkau, tetapi lebih jauh dari badan |
| 40 cm, baru | 2 cm | Dipakai, lebih dekat 5 cm dan masih punya clearance nominal |
| 18 cm | −20 cm | Ditolak; badan terlalu rendah terhadap bibir drum |

Angka clearance berlaku untuk posisi datar dan geometri simulator sekarang. Kemiringan, dimensi nyata dan toleransi fabrikasi belum tervalidasi. Kedekatan lebih jauh tidak boleh dicapai hanya dengan memendekkan alat tetap tanpa menghitung ulang kemampuan menjangkau dasar drum.

## Perubahan yang diselaraskan

`PICKUP_X` dan `PICKUP_Z` di generator arena menjadi sumber geometri statis bersama. Generator membuat collision/visual baru; controller memakai offset yang sama untuk alignment dan menyesuaikan target turun dari floor +49 cm menjadi floor +44 cm. Referee memakai offset baru dengan rotasi roll/pitch/yaw penuh dan envelope alat hingga dudukan.

Toleransi retensi **tetap 7,5 cm**; tes masih menolak offset bola 8 cm dan attachment yang hilang. Native physics tetap membuat joint hanya setelah kontak dengan bola teramati. Posisi baru mengikuti collision yang dibaca plugin; tidak menambahkan teleport atau mengubah syarat latch.

## Pembanding renderer Gazebo

Kedua gambar memakai pose/kamera sama. Gambar before menggunakan geometri lama pada salinan world untuk perbandingan; after memakai generator produksi baru.

| Sebelum | Sesudah |
|---|---|
| ![Gripper lama](../ros2_ws/evidence/gripper-close-20261112/before/gazebo-model.png) | ![Gripper dekat dengan dudukan](../ros2_ws/evidence/gripper-close-20261112/after/gazebo-model.png) |

## Verifikasi

Build lulus dan **180 tes unit lulus**. Tes baru memeriksa posisi gripper/dudukan, clearance drum dan target kedalaman controller; tes floor-envelope serta retensi disesuaikan terhadap geometri baru dengan batas keselamatan yang sama.

Bukti: [tes unit](../ros2_ws/evidence/gripper-close-20261112/unit-tests.log), [build](../ros2_ws/evidence/gripper-close-20261112/build.log). Penerimaan extended lengkap juga **lulus pada run pertama** setelah perubahan: layout alternatif, pinger drum 4, blue drum 3, urutan Y–B–R dan seed 91, dengan Gazebo GUI serta kedua POV.

| Pemeriksaan runtime | Hasil |
|---|---|
| Misi | DONE: acquisition → keluar penuh target zone → pickup bola sama → surface Square → stop |
| Skor | 290,78028, penalti 0 |
| Thrust–surface | 207,324 detik simulasi |
| Retensi fisika | 1.328 snapshot attachment konsisten sampai stop; tidak ada retention lost |
| Estimasi | Galat XY maksimum 0,120009 m, di bawah batas referensi 0,20 m |
| Penutupan | POV depan/bawah terverifikasi; thruster nol, kendaraan berhenti, shutdown bersih |

Bukti: [verification.json](../ros2_ws/evidence/gripper-close-20261112/verification.json), [run1.json](../ros2_ws/evidence/gripper-close-20261112/run1.json), [perhitungan dari SDF](../ros2_ws/evidence/gripper-close-20261112/placement.json). Checker/referee dan verifier bukti memakai syarat retensi serta identitas bola yang sama seperti laporan 58.

Ini penerimaan fungsional satu fixture, bukan benchmark peningkatan kecepatan. Runtime pada seluruh variasi arus/layout, mekanisme bergerak/retraksi, kekuatan dudukan, waterproofing serta fabrikasi fisik belum diuji. Collision, visual dan algoritme pickup sinkron, tetapi clearance nominal 2 cm bukan persetujuan toleransi mekanik kendaraan nyata.
