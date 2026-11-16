# 71 — Demonstrasi dan konsistensi revisi optik

Tanggal: **16 November 2026**. Cakupan: simulator; tidak mengirim perintah ke AUV/Pixhawk nyata.

## Permintaan dan batas

Membuka Gazebo bersama POV depan/bawah, menyimpan rekaman kamera dan mengulang misi pada revisi laporan 70. Tidak mengubah kecepatan, pengaman, dinamika atau detektor. Bukti berlaku pada matriks terpilih, bukan seluruh kondisi kolam.

## Demonstrasi

Kualifikasi jalur 3, seed 42, offset lateral 0,15 m, atenuasi sintetis 0,10/m: pemeriksa misi lulus, pelintasan resmi 24,392 detik; start–surface 27,492 detik; start–stop 32,318 detik.

ARENA extended, seed 42, varian 1, urutan Y–B–R, blue drum 3, pinger drum 4, atenuasi 0,05/m: pemeriksa misi lulus; thrust–surface 207,762 detik; skor simulator 290,76714 poin, penalti 0. Retensi bola, keluar target zone, pickup dan Surfacing Square diperiksa oleh checker.

Kedua checker memverifikasi jendela Gazebo/POV dan shutdown bersih. Pengguna kemudian mengonfirmasi bahwa jendela Gazebo dan kedua POV sudah terlihat melalui jawaban sesi ini. Video hanya merekam topik kamera, tanpa desktop. Bagian awal mencakup startup/preflight.

- [Video kualifikasi](../ros2_ws/evidence/demo-consistency-20261116/demo-qualification/pov.mp4): DIVE sekitar 00:32, U-turn 00:50, surface 01:00.
- [Video ARENA](../ros2_ws/evidence/demo-consistency-20261116/demo-arena/pov.mp4): flare pertama 01:39, drop 04:19, pickup 04:48, surface 06:30.
- Timestamp bab lengkap tersedia pada `pov.json` di masing-masing direktori video. Waktu video memakai wall time dan dapat berbeda dari waktu simulasi.

**Batas kamera:** startup menampilkan placeholder sekitar 4 detik. Pada video kualifikasi, POV bawah menampilkan placeholder stale pada 00:40,6–00:42,4 dan 00:45,8–00:46,6, kemudian pulih. Kualifikasi memakai kamera depan sehingga tetap lulus. Cuplikan ARENA setelah startup tidak menunjukkan placeholder hitam pada pemeriksaan frame. Pemeriksaan ini memakai proporsi piksel gelap pada video, bukan pengukuran timestamp sensor; tidak membuktikan akar masalah ataupun bahwa semua jeda kamera telah hilang. Data ada di `camera-review.json` masing-masing demo.

## Pengulangan — selesai

Matriks 15 run: dua demo GUI, sembilan kualifikasi 0,10/m (tiga seed × tiga jalur), satu kualifikasi arus/hold, satu prior posisi dan dua ARENA tambahan. Seluruh run serial. Manifest source dicek sebelum setiap run; hasil gagal tetap disimpan.

[Ringkasan dan matriks](../ros2_ws/evidence/demo-consistency-20261116/summary.json) · [Runner](../ros2_ws/evidence/demo-consistency-20261116/run.py)

**15/15 run diterima**, seluruhnya `DONE` dan shutdown bersih; tidak ada grup POV yang memerlukan cleanup paksa. Manifest 98 file source cocok sebelum setiap run dan pada pemeriksaan akhir.

| Kelompok | Hasil |
|---|---|
| Demo GUI kualifikasi + ARENA | 2/2 diterima; pengguna mengonfirmasi jendela terlihat |
| Kualifikasi 3 jalur × seed 7/42/91 | 9/9 diterima; start–surface 26,102–27,408 detik |
| Kualifikasi arus/hold + prior posisi | 2/2 diterima |
| ARENA tambahan extended + blue drum | 2/2 diterima |

Sembilan kualifikasi reguler: finish resmi 22,972–24,280 detik, start–stop 30,842–32,624 detik; galat XY maksimum 3,413 cm. Jalur 2 memakai yaw awal 0,08 rad, jalur 3 offset lateral 0,15 m. Ketiganya memakai atenuasi 0,10/m; ini parameter sintetis, bukan NTU.

Kasus arus `[0, 0.02, 0]` m/s: hold diminta 30 detik, teramati 29,988 detik, drift XY maksimum 5,46 mm dan perubahan kedalaman 6,15 mm. Hold memakai gaya aktif; abort uji menonaktifkan hold dan mengembalikan thruster ke nol. Kasus prior `[0.1, -0.1]` m dengan offset lateral 0,15 m dan yaw 0,1 rad lulus; galat XY maksimum 14,765 cm. Satu kasus ini tidak membuktikan seluruh rentang prior.

ARENA tambahan: extended seed 7 mencapai 290,75628 poin dalam 208,124 detik; blue drum seed 91 mencapai 210,15448 poin dalam 228,184 detik. Penalti masing-masing nol. Dengan demo, ada tiga run ARENA pada batch ini; dua extended dan satu blue drum.

**Catatan log penutupan:** setiap run mencatat satu `stale_sensors` sesudah `DONE` dan checker mencatat world dipause sebelum shutdown. Urutan ini konsisten dengan produsen sensor berhenti saat penutupan; bukan abort misi pada batch ini. Tidak ada klaim bahwa log sepenuhnya tanpa ERROR atau bahwa penyebab historis stale telah ditentukan.

[Verifikasi akhir](../ros2_ws/evidence/demo-consistency-20261116/verification.json) membedakan `mission_suite_passed: true` dari `uninterrupted_dual_pov: false`. Dengan demikian, angka 15/15 tidak berarti kedua kamera bebas jeda.

Tahap ini tidak mengubah source produksi; 195 tes unit terakhir tetap merujuk laporan 70 dan tidak diulang untuk perubahan dokumentasi/evidence ini. Belum ada validasi fisik atau jaminan keandalan di seluruh kondisi kolam.
