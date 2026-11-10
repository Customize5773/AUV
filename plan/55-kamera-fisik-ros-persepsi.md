# 55 — Kamera fisik Jetson ke ROS/persepsi

Tanggal: 4 November 2026. Tujuan: membuktikan kamera USB bisa memasok gambar ke detektor ROS yang sudah digunakan simulator, mengukur latensi host dan memeriksa pengosongan deteksi saat kamera berhenti. Tidak ada adapter kendali atau koneksi Pixhawk yang dijalankan.

## Implementasi

[check_physical_camera.py](../ros2_ws/tools/check_physical_camera.py) adalah alat penerimaan terbatas, bukan layanan kamera produksi. OpenCV V4L2 membaca perangkat melalui alias stabil, menerbitkan RGB dengan QoS BEST_EFFORT depth 1 dan menjalankan node persepsi pada proses terpisah. Domain 187 dan localhost-only diwajibkan; topik gambar/hasil front dialihkan ke `/physical_test/`. Publikasi diberi jeda sekitar 0,1 detik setelah pembacaan, sehingga ini bukan benchmark laju maksimum kamera.

Setelah capture berhenti, alat menunggu tiga detik untuk memeriksa hasil stale tanpa deteksi, lalu menghentikan node dengan SIGINT. Proses gagal atau laporan `accepted: false` tidak dianggap lulus. Batas waktu luar diperlukan jika driver V4L2 macet.

Node tetap menggunakan kalibrasi simulator. CameraInfo uji dialihkan ke `/physical_test/unvalidated_camera_info`; geometri hasil deteksi **tidak tervalidasi untuk kendaraan nyata**. Uji hanya memakai satu kamera pada peran input front, bukan dua kamera fisik. Tidak ada target lomba berlabel dalam pengujian, sehingga hasil tidak membuktikan precision/recall gate, flare atau drum nyata.

## Pelaksanaan dan provenance

Jetson sempat tidak terjangkau melalui Ethernet maupun Wi-Fi. Wi-Fi `192.168.67.167` kembali merespons; identitas host key cocok dan autentikasi memakai kunci laptop yang sudah ada. Tidak mengubah konfigurasi jaringan.

Source `object_detection.py` Jetson berbeda dari laptop dan profil XML SHM belum tersedia pada path checkout Jetson. Agar tidak menimpa perubahan tersebut, modul yang diperlukan serta profil XML disalin ke direktori evidence terisolasi, lalu digunakan lewat PYTHONPATH khusus uji. [source-hashes.json](../ros2_ws/evidence/physical-camera-20261104/source-hashes.json) membedakan hash Jetson dan hash yang diuji. Ini **bukan deployment/sinkronisasi checkout Jetson**.

Percobaan awal gagal impor rclpy karena konfigurasi PYTHONPATH pada pemanggilan uji menimpa path ROS. Pemanggilan diperbaiki agar menambahkan path source ke path ROS yang sudah disource. Bukti kegagalan tetap disimpan sebagai `attempt1-environment-error.json`.

## Penerimaan

Run pertama selama 30 detik: 275 gambar dipublikasikan, 274 hasil diterima, tanpa kegagalan baca. Latensi host-after-read ke hasil p50 117,9 ms, p95 186,7 ms, maksimum 230,4 ms. Pemrosesan detektor p95 123,1 ms. Empat belas pesan stale diamati, termasuk setelah aliran dihentikan; proses persepsi exit 0. Satu gambar tidak menghasilkan hasil yang teramati; uji ini tidak mengisolasi penyebab kehilangan tersebut.

Run kedua selama 30 detik: 268 gambar dipublikasikan, 262 hasil diterima, tanpa kegagalan baca; p50 157,1 ms, p95 211,1 ms, maksimum 236,5 ms. Pemrosesan p95 128,7 ms; stale dan shutdown lulus, `accepted: true`. Enam gambar tidak menghasilkan hasil teramati; penyebab tidak diisolasi, sehingga pengujian ini belum membuktikan aliran tanpa kehilangan. Pemeriksaan akhir menunjukkan tidak ada pemilik kamera atau proses persepsi uji yang tertinggal ([cleanup.json](../ros2_ws/evidence/physical-camera-20261104/cleanup.json)).

Latensi tidak mencakup exposure, antrean kamera atau waktu sebelum `VideoCapture.read()` selesai. Profil penerimaan ini memeriksa aliran, validitas gambar, stale dan shutdown; belum menetapkan batas latensi untuk kontrol kendaraan.

Bukti run pertama: [verification1.json](../ros2_ws/evidence/physical-camera-20261104/verification1.json), [run1.json](../ros2_ws/evidence/physical-camera-20261104/run1.json). Hasil pengulangan akhir tersedia pada [verification.json](../ros2_ws/evidence/physical-camera-20261104/verification.json) dan [run.json](../ros2_ws/evidence/physical-camera-20261104/run.json).

Uji integrasi lokal dengan input sintetis dan node ROS/persepsi nyata lulus satu tes, mencakup penerimaan gambar, stale dan shutdown. Ini suite terpisah dari 178 tes unit simulator historis; tidak menjumlahkannya sebagai hasil regresi simulator baru. Log: [synthetic-test.log](../ros2_ws/evidence/physical-camera-20261104/synthetic-test.log). Kompilasi Python serta `git diff --check` juga lulus.

## Berikutnya

Kalibrasi intrinsics/distorsi dan pemasangan kamera, pengujian target lomba nyata berlabel, serta pengukuran antrean/exposure dan streaming lebih panjang. Belum ada bukti akurasi metrik atau kesiapan kontrol fisik dari uji ini. Prosedur pengulangan ada pada [panduan SSH](../CARA-OPERASI-SSH.md).
