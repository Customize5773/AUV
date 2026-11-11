# 58 — Regresi pinger/pickup dengan model AUV baru

Tanggal laporan: 12 November 2026. Melanjutkan laporan 57 dengan visual FBX SAUVC 2027 v1. Nama direktori bukti `auv-mesh-extended-20261111` dipertahankan dari awal sesi.

## Cakupan

Model dinamis tujuh thruster, kendali berbasis estimator sensor, `extended=true`, layout alternatif `scene_variant=1`, blue drum 3, pinger drum 4, urutan flare Y–B–R dan seed 91. Kondisi tanpa arus, prior awal nol, skala pencahayaan 1. Menggunakan GUI Gazebo dan kedua POV. Acuan fixture simulator 2027.3.2.

Hash OBJ/MTL/metadata cocok dengan aset yang diterima pada laporan 57; tidak ada konversi ulang atau perubahan collision/dinamika/guard. Bukti: [asset-hashes.json](../ros2_ws/evidence/auv-mesh-extended-20261111/asset-hashes.json).

## Percobaan pertama

Run 1 ditolak: penampil POV keluar saat misi masih NAVIGATE, dengan pesan `POV viewer exited during mission`. Log kedua viewer tidak berisi traceback. Shutdown simulator bersih, tetapi misi belum selesai; run ini tidak dihitung sebagai keberhasilan.

Penyebab keluar viewer belum diketahui secara unik. Diagnostik checker ditambah agar kegagalan berikutnya menyertakan kode keluar setiap viewer; tidak mengubah syarat penerimaan, menghidupkan ulang viewer diam-diam, atau melonggarkan watchdog. Proses run 2 sudah dimulai sebelum tambahan diagnostik tersebut tersimpan, sehingga tidak diklaim memakai pesan baru.

Bukti percobaan gagal: [run1.json](../ros2_ws/evidence/auv-mesh-extended-20261111/run1.json), log simulator dan log POV pada direktori yang sama.

## Verifikasi penerimaan

Menggunakan checker dan referee yang sudah ada, ditambah verifier bukti terarah `verify.py` di direktori evidence. Verifier memeriksa batas akurasi melalui `check_reliability.metrics`, isolasi ground truth, kontrak sensor, kalibrasi DVL, tujuh thruster, POV, shutdown dan kondisi berhenti. Bukti extended harus menunjukkan:

- Payload pertama berada di drum pinger 4.
- Keluar seluruh badan dari target zone setelah acquisition, lalu kembali ke pickup.
- Acquisition dan retrieval mencatat ball_id `payload` yang sama.
- Event pickup mendahului surface dan stop; tidak ada `PAYLOAD_RETENTION_LOST`.
- Snapshot fisika dari sesudah grasp hingga stop mempertahankan attachment bola yang sama.
- Skor acquisition 50, reacquisition 60, Square 20 dan penalti nol.

Run 2 diterima oleh checker dan verifier:

| Pemeriksaan | Hasil |
|---|---|
| Misi | DONE, surface dan stop selesai |
| Skor simulator | 290,79888, penalti 0; acquisition 50, reacquisition 60, Square 20 |
| Thrust–surface | 206,704 detik waktu simulasi |
| Ball ID | `payload` yang sama pada acquisition dan retrieval |
| Retensi | 1.332 snapshot fisika setelah grasp hingga stop, attachment konsisten |
| Galat XY maksimum | 0,124858 m, di bawah batas referensi 0,20 m |
| Sensor/kendali | Estimator-only, kontrak sensor dan kalibrasi DVL lulus; tujuh thruster, gaya akhir nol |
| GUI/POV/shutdown | Kedua POV terverifikasi, shutdown bersih; tidak ada PID launch tercatat yang tersisa |

Seluruh **179 tes unit simulator lulus kembali**. Ini satu run extended yang diterima dari dua percobaan; run pertama gagal karena viewer keluar. Tidak menyatakan seluruh percobaan lulus atau akar keluarnya viewer telah diperbaiki. Penambahan diagnostik checker hanya memperjelas kode keluar pada kejadian berikutnya.

Bukti ringkas: [verification.json](../ros2_ws/evidence/auv-mesh-extended-20261111/verification.json), [verifier](../ros2_ws/evidence/auv-mesh-extended-20261111/verify.py), [tes unit](../ros2_ws/evidence/auv-mesh-extended-20261111/unit-tests.log), [cleanup](../ros2_ws/evidence/auv-mesh-extended-20261111/cleanup.json). Bukti mentah: [run2.json](../ros2_ws/evidence/auv-mesh-extended-20261111/run2.json).

## Batas

Ini pengujian simulator pada satu fixture extended; bukan bukti mekanisme pickup, hidrofon atau kendaraan nyata. Pengulangan ini belum mencakup arus dan seluruh variasi layout. Masalah viewer awal tetap terbuka meskipun pengulangan dapat berhasil.
