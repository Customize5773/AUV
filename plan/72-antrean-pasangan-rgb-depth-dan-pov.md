# 72 — Antrean pasangan RGB–depth dan jeda POV

16 November 2026. Menindaklanjuti jeda kamera bawah pada demo laporan 71. Seluruh pekerjaan dibatasi pada simulator dan uji DDS software; tidak mengakses atau menguji kendaraan fisik.

## Diagnosis

Kualifikasi dinamis jalur 3, seed 42, offset lateral 0,15 m dan atenuasi sintetis 0,10/m diulang dengan GUI, kedua POV, perekam serta observer metadata RGB/depth/raw/persepsi. Sebelum perubahan, misi tetap lulus, tetapi observer merekam satu status stale kamera bawah sesudah gambar pertama masuk. Sela keluaran bawah maksimum **1,112 detik**. Dalam sela tersebut observer masih menerima **10 pasangan RGB–depth dengan timestamp sama**. RGB/depth datang dengan sela maksimum sekitar 0,135 detik; pemrosesan deteksi bawah sekitar 31 ms. Ini mempersempit titik kehilangan ke jalur penerimaan/pencocokan optik, bukan bukti sensor Gazebo berhenti.

Filter memakai empat subscriber masukan dengan antrean satu frame. RGB dan depth tiba sebagai pesan terpisah; ketika RGB berikutnya menggantikan RGB sebelumnya sebelum depth pasangan diproses, timestamp yang cocok hilang. Cache pencocokan tiga capture tidak dapat memulihkan pesan yang telah dibuang oleh antrean DDS.

Uji DDS terkontrol pada domain terpisah mengirim RGB stamp 1, RGB stamp 2, lalu depth stamp 1 sebelum executor membaca antrean. Dengan depth 1 tidak ada keluaran; dengan depth 3, keluaran stamp 1 muncul. Uji ini mereproduksi mekanisme kehilangan pasangan. Ini tidak membuktikan semua kejadian stale historis memiliki penyebab yang sama.

## Perubahan terbatas

`water_optics.py` memakai antrean **tiga frame hanya pada masukan privat RGB/depth**, sesuai batas tiga capture `FramePairs`. Keluaran publik tetap BEST_EFFORT/depth 1. Timestamp harus cocok tepat, output tetap memakai stamp sumber, cache tetap terbatas dan tidak memutar ulang capture lama. Efek warna, resolusi, FPS sensor, detektor, pengaman dan kontrol kendaraan tidak diubah.

Hanya dua file produksi/tes berbeda dari manifest laporan 71: modul optik dan tes kontrak QoS-nya. Source lengkap dibekukan pada [manifest](../ros2_ws/evidence/camera-pairing-20261116/source-sha256.json).

## Pengulangan GUI

**195 tes pytest lulus.** Pengujian unittest 139 kasus adalah bagian dari suite yang sama, bukan tambahan 139 tes unik.

| Run setelah perbaikan | Sela raw depan maksimum | Sela raw bawah maksimum | Stale setelah gambar pertama sampai DONE | Misi/shutdown |
|---|---:|---:|---|---|
| 1 | 0,381 s | 0,363 s | 0 / 0 | Lulus / bersih |
| 2 | 0,594 s | 0,470 s | 0 / 0 | Lulus / bersih |
| 3 | 0,452 s | 0,420 s | 0 / 0 | Lulus / bersih |

Ketiganya memakai fixture yang sama untuk mengulang pengaruh penjadwalan runtime, bukan tiga layout baru. Observer menghitung fresh=False per kamera sesudah pesan pertama yang fresh hingga DONE. Pemeriksaan video DIVE–DONE menemukan nol placeholder hitam pada kedua POV; analisis piksel ini bersifat heuristik dan dicocokkan dengan metadata fresh. Startup dan penutupan dinilai terpisah.

[Analisis kamera](../ros2_ws/evidence/camera-pairing-20261116/camera-analysis.json) · [Reproduksi DDS depth 1](../ros2_ws/evidence/camera-pairing-20261116/burst-before.json) · [DDS depth 3](../ros2_ws/evidence/camera-pairing-20261116/burst-after.json).

Rekaman baru: [run 1](../ros2_ws/evidence/camera-pairing-20261116/after-1/pov.mp4), [run 2](../ros2_ws/evidence/camera-pairing-20261116/after-2/pov.mp4), [run 3](../ros2_ws/evidence/camera-pairing-20261116/after-3/pov.mp4). Rekaman lama tetap disimpan dan tidak diubah menjadi hasil sehat.

## Penerimaan akhir — selesai

**195 tes lulus** dengan `bash tools/ros.sh python -m pytest src/sauvc_sim/test -q` (16,99 detik). Empat misi lengkap dan satu respons fault diterima; semuanya shutdown bersih, tanpa cleanup paksa grup POV.

| Pengujian | Hasil |
|---|---|
| Reproduksi sebelum perubahan | Misi lulus; satu stale bawah sesudah gambar pertama, sela raw bawah maksimum 1,112 s |
| GUI sesudah perubahan 1 | Lulus, tanpa stale setelah gambar pertama; sela bawah maksimum 0,363 s |
| GUI sesudah perubahan 2 | Lulus, tanpa stale setelah gambar pertama; sela bawah maksimum 0,470 s |
| GUI sesudah perubahan 3 | Lulus, tanpa stale setelah gambar pertama; sela bawah maksimum 0,420 s |
| Kehilangan depth selektif | Lulus respons fault; RGB depan 30/bawah 29 pesan, depth/output keduanya nol setelah grace 0,5 s |
| ARENA extended 0,05/m | Lulus; 290,7468 poin, thrust–surface 208,440 s, penalti nol |

Tiga kualifikasi memakai GUI dan kedua POV, kondisi sama seperti reproduksi. Masing-masing mencapai surface dalam 27,804 / 27,150 / 27,744 detik dari thrust. Video DIVE sampai DONE tidak mengandung placeholder hitam pada pemeriksaan piksel; metadata persepsi juga tidak mencatat stale setelah gambar pertama hingga DONE. Pemeriksaan video adalah heuristik pendukung, bukan pengganti timestamp/metadata. Startup sebelum gambar pertama dan penutupan setelah DONE tidak dianggap misi aktif.

Kehilangan depth: ABORT `stale_camera` sekitar **2,402 s wall** setelah injeksi, command/gaya akhir nol, kendaraan stationary dan shutdown bersih. Checker misi sengaja keluar 1 karena misi terputus; verifier fault keluar 0 karena respons aman sesuai harapan. Antrean tidak memutar ulang gambar lama untuk menyembunyikan fault.

ARENA extended tetap membuktikan flare Y–B–R, drop ke drum pinger, keluar zona, pickup bola yang sama, retensi hingga surface dan Surfacing Square. Galat XY maksimum 12,470 cm; command/gaya akhir nol dan stationary.

Manifest 98 file cocok pada pemeriksaan akhir. Dibanding revisi batch 15 run laporan 71, hanya `water_optics.py` dan `test_water_optics.py` berubah. Tidak ada perubahan detektor, controller, threshold stale, model gaya atau mixer.

[Verifikasi akhir](../ros2_ws/evidence/camera-pairing-20261116/verification.json) · [Analisis kamera](../ros2_ws/evidence/camera-pairing-20261116/camera-analysis.json) · [Burst DDS sebelum](../ros2_ws/evidence/camera-pairing-20261116/burst-before.json) / [sesudah](../ros2_ws/evidence/camera-pairing-20261116/burst-after.json).

Ulangi verifier dari `ros2_ws`: `bash tools/ros.sh python evidence/camera-pairing-20261116/verify.py`. Verifier mengharuskan source tetap cocok dengan manifest.

## Batas

Perbaikan menutup mekanisme kehilangan pasangan yang direproduksi. Tiga pengulangan tidak menjamin bebas stale pada semua beban komputer, layout atau kondisi kolam. Batch 15/15 laporan 71 tetap bukti revisi sebelum perubahan ini. Tidak ada klaim optimasi waktu kendaraan atau validasi fisik baru.
