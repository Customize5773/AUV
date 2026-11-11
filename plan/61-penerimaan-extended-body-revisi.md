# 61 — Penerimaan extended dengan body revisi

Tanggal: 12 November 2026. Melengkapi batas pengujian laporan 60: ARENA extended belum diulang setelah mesh diperbaiki dari 230.463 menjadi 816.288 segitiga.

## Ruang lingkup

Mesh dan material aktif diverifikasi hash-nya cocok dengan laporan 60. Gripper memakai revisi laporan 59, yaitu titik tangkap `(−0,20, 0, −0,40) m` dengan dudukan terhubung. Tidak ada perubahan kode produksi, guard, collision atau parameter gerak pada tahap ini.

Skenario: dinamis tujuh thruster, `extended=true`, layout alternatif 1, blue drum 3, pinger drum 4, urutan Y–B–R, seed 91, tanpa arus dan prior awal nol. Gazebo GUI dan kedua POV dibuka. Kondisi disimpan pada [conditions.json](../ros2_ws/evidence/body-extended-20261112/conditions.json).

Verifier bukti yang sama dengan laporan 59 memeriksa kelulusan checker, akurasi referensi, isolasi ground truth, kalibrasi DVL, gaya akhir nol, kondisi berhenti dan shutdown. Untuk extended, bukti harus menunjukkan acquisition pada drum pinger 4, seluruh badan keluar target zone, pickup bola yang sama, attachment konsisten hingga stop, serta bonus reacquisition dan Square tanpa penalti.

Bukti source/aset: [asset-hashes.json](../ros2_ws/evidence/body-extended-20261112/asset-hashes.json), [source-hashes.json](../ros2_ws/evidence/body-extended-20261112/source-hashes.json).

## Hasil

**Run pertama diterima** oleh checker dan verifier bukti, dengan seluruh syarat berikut:

| Pemeriksaan | Hasil |
|---|---|
| Misi | DONE, surface Square dan stop selesai |
| Skor | 290,77638 poin, penalti 0 |
| Thrust–surface | 207,454 detik simulasi |
| Payload | Acquisition di drum pinger 4, keluar penuh zona, kemudian pickup ball_id `payload` yang sama |
| Retensi | 1.325 snapshot attachment konsisten dari sesudah grasp hingga stop; tanpa retention lost |
| Estimasi | Galat XY maksimum 0,116119 m, di bawah batas referensi 0,20 m |
| Kendali/sensor | Isolasi ground truth, kontrak sensor, DVL dan tujuh thruster lulus; gaya akhir nol dan stationary |
| Tampilan/penutupan | Kedua POV terverifikasi; shutdown bersih, PID launch tercatat tidak tersisa |

Bukti akhir: [verification.json](../ros2_ws/evidence/body-extended-20261112/verification.json), [run1.json](../ros2_ws/evidence/body-extended-20261112/run1.json), [verifier](../ros2_ws/evidence/body-extended-20261112/verify.py), [cleanup](../ros2_ws/evidence/body-extended-20261112/cleanup.json). Tidak ada perubahan source produksi atau percobaan ulang untuk memperoleh hasil ini.

Gabungan laporan 60 dan 61 membuktikan revisi body serta gripper saat ini bekerja pada satu kualifikasi GUI/POV dan satu ARENA extended GUI/POV. Ini penerimaan fungsional, bukan benchmark peningkatan kecepatan atau bukti konsistensi banyak pengulangan.

## Batas

Penerimaan satu fixture tidak membuktikan keandalan seluruh kondisi arus/layout atau performa AUV nyata. Tes 180 simulator dan 2 konversi dari laporan 60 merupakan bukti terpisah; suite tersebut tidak dijalankan ulang pada tahap ini karena tidak ada perubahan source produksi.

Collision masih lebih panjang sekitar 4,08 cm di masing-masing ujung X daripada visual. Penyamaan collision, envelope referee, start-wall dan pemeriksaan pelintasan tetap pekerjaan terpisah. Massa, inertia, drag, buoyancy serta posisi gaya thruster juga belum dikalibrasi terhadap kendaraan fisik. Belum ada benchmark FPS/VRAM panjang.
