# 37 — Pengujian fault sensor dan aktuator setelah start

1 November 2026. Status: build dan 142 tes unit lulus; enam run runtime diterima (lima respons fault dan satu misi normal).

## Masalah dan perubahan

Fault native `imu_loss`, `pressure_loss`, `dvl_loss`, dan `actuator_loss` sebelumnya dipicu saat waktu simulasi melewati 12 detik. Preflight DVL kini dapat berlangsung sekitar 28 detik; akibatnya pengujian tersebut menguji kegagalan sebelum misi, bukan kehilangan sensor/aktuator saat bergerak.

Model native sekarang memulai penghitung saat perintah thruster nonnol pertama melepas penahan deployment. Keempat fault dipicu 12 detik sesudahnya. Watchdog aktuator sebenarnya tetap 0,5 detik wall-clock; batas stale sensor tidak diubah. Telemetry menambahkan `injected_fault`, terpisah dari payload sensor untuk navigasi.

Pemeriksa kualifikasi dan ARENA memverifikasi selang injeksi terhadap gaya thruster pertama >0,05 N pada rentang 11,9–12,1 detik (selisih pencuplikan antara perintah pertama dan gaya). Kualifikasi juga mewajibkan kalibrasi siap sebelum thrust dan 20 sampel telemetry terakhir bergaya nol untuk penerimaan fault dinamis. Tes unit menolak fault sebelum thrust, tanpa injeksi, atau jenis injeksi yang tidak cocok.

Percobaan awal gagal pada setup: kedua penguji mengirim `conditions_file:=` kosong saat `--conditions` tidak diberikan. ROS launch menolaknya sebelum simulator berjalan. Kini argumen tersebut dihilangkan sehingga launch memakai kondisi default. Bukti setup gagal dipertahankan di `evidence/post-start-faults-2027`; penerimaan ulang berada di `evidence/post-start-faults-rerun-2027`.

## Batas cakupan

Perubahan waktu berlaku untuk empat fault native di atas. Fault kamera, command, odometry, contact, clock dan controller_freeze masih memakai jadwal lama; matriks itu belum diperbaiki/diuji ulang pada tahap ini. Uji bridge yang terikat DIVE dari laporan 36 tetap bukti terpisah. Gangguan stale_sensors spontan historis belum diketahui penyebabnya. Pengujian ini headless dan belum merupakan bukti hardware.

## Hasil penerimaan akhir

| Pengujian | Injeksi sejak thrust pertama | Hasil |
|---|---|---|
| Kualifikasi: IMU hilang | 11,996 s | ABORT, gaya nol, shutdown bersih |
| Kualifikasi: tekanan hilang | 11,996 s | ABORT, gaya nol, shutdown bersih |
| Kualifikasi: DVL hilang | 12,006 s | ABORT, gaya nol, shutdown bersih |
| Kualifikasi: aktuator hilang | 12,004 s | ABORT, gaya nol, shutdown bersih |
| Kualifikasi normal | Tidak ada fault | Misi lengkap lulus; start–surface 27,644 s |
| ARENA: DVL hilang | 12,006 s | ABORT, gaya nol, shutdown bersih |

Semua run lulus bukti kalibrasi sebelum thrust dan pemisahan ground truth dari kontrol. Lima abort merupakan hasil yang diharapkan pada uji fault, bukan lima misi lengkap. Satu kegagalan setup sebelum perbaikan argumen kosong dipertahankan terpisah; tidak dihitung sebagai run runtime yang diterima.

Bukti gabungan: [verification.json](../ros2_ws/evidence/post-start-faults-rerun-2027/verification.json). Folder yang sama menyimpan manifest source termasuk library native, perintah, raw report, log build dan tes. Hash cocok saat verifikasi akhir. Unit test baru menolak penerimaan fault sebelum thrust/tanpa injeksi/jenis yang salah; runtime membuktikan empat jalur injeksi native dan regresi tanpa fault. Ini peningkatan validitas pengujian, bukan optimasi kecepatan kendaraan.
