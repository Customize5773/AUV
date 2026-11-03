# 46 — Penerimaan kualifikasi dan regresi pinger

Tanggal: 3 November 2026. Status: tiga kasus kualifikasi lanjutan dan satu regresi ARENA pinger diterima.

## Ruang lingkup

Melanjutkan laporan 44 tanpa mengubah controller, estimator, model gaya, thruster atau batas pengaman. Lima belas run tiga jalur pada `corrected-batch/` diterima. Kasus arus motor-off menyelesaikan misi tetapi gagal stationary; hasil gagal dipertahankan. Menjaga posisi dalam arus memerlukan thruster aktif, sehingga kasus penggantinya dinamai eksplisit `q-current-hold-91` dengan `--surface-hold`.

Ini perubahan skenario penerimaan, bukan klaim bahwa kendaraan tidak hanyut saat motor-off. Profil default tetap motor-off. Hasil 15 run dan kelanjutan dicatat sebagai dua tahap dengan hash source berbeda pada pemeriksa matriks/tes; tidak diklaim satu batch source identik 18/18.

## Pemeriksa dan tes

Metrik hold mewajibkan `hold_verification.passed`, `abort_disarmed` dan `abort_thrusters_zero`, selain stationary, zero_command, akurasi, serta shutdown bersih. Uji tanpa hold tetap harus memenuhi `thrusters_zero`. Tes menolak hold gagal dan kegagalan emergency stop; 170 tes unit simulator lulus.

## Hasil yang tersedia

- Kasus arus lateral 0,02 m/s seed 91: misi dan hold lulus. Window 29,988 detik, drift maksimum 0,00500 m, perubahan kedalaman 0,00697 m. Emergency stop disarmed dan gaya thruster nol terbukti; diagnosis tidak menemukan stale sensor; checker dan kedua probe exit 0, shutdown bersih.
- Prior jalur 2 seed 42 lulus: galat XY maksimum 0,14528 m, start–surface 28,254 detik. Prior jalur 3 seed 91 lulus: galat XY maksimum 0,14764 m, start–surface 26,538 detik. Kedua checker dan probe exit 0, tanpa stale sensor pada window diagnosis, shutdown bersih.
- ARENA pinger/pickup dinamis seed 91, layout alternatif, blue drum 3, pinger drum 4, urutan Y-B-R: **lulus**. Thrust–surface 205,798 detik; skor simulator 290,82606; bonus Square +20; penalti 0. Galat posisi maksimum 0,14905 m. `physical_retention`, `extended_proof`, `surfacing_square_verified`, kontrol sensor-only dan tujuh thruster semuanya benar. Event kontak flare, payload masuk drum, full exit target zone, pickup, surface dan stopped tercatat. Perintah/gaya akhir nol, stationary benar, checker/probe exit 0, shutdown Gazebo tanpa pemaksaan.

Log pinger mencatat `stale_sensors` sesudah DONE pada tahap physics dijeda sebelum shutdown. Diagnosis window misi aktif mengklasifikasikan `no_stale_sensor_event`; ini tidak diklaim sebagai log tanpa ERROR sama sekali. Penyebab historis stale spontan tetap belum ditetapkan secara unik.

Bukti: [kelanjutan kualifikasi](../ros2_ws/evidence/qualification-consistency-2027/remaining-challenges/summary.json) dan [hasil hold](../ros2_ws/evidence/qualification-consistency-2027/remaining-challenges/q-current-hold-91.json). Hasil lama: [15 penerimaan dan kegagalan motor-off](../ros2_ws/evidence/qualification-consistency-2027/corrected-batch/summary.json).

## Batas

Seluruh hasil merupakan simulator. Pengendali Pixhawk produksi, sensor kedalaman dan mekanik belum divalidasi; tidak ada perintah hardware pada tahap ini. Optimasi kecepatan tambahan dan shutdown viewer belum dikerjakan pada tahap ini.

Ringkasan penerimaan kualifikasi dengan assert bukti, hash laporan dan perbedaan source antartahap: [resumed-verification.json](../ros2_ws/evidence/qualification-consistency-2027/resumed-verification.json). Seluruh file runtime/native/controller identik antara 15 run sebelumnya dan tiga kasus kelanjutan; hanya pemeriksa matriks dan tesnya berubah.

Bukti regresi: [pinger summary](../ros2_ws/evidence/qualification-consistency-2027/pinger-regression/summary.json), [laporan lengkap](../ros2_ws/evidence/qualification-consistency-2027/pinger-regression/a-pinger-91.json). Verifier memeriksa event, retensi, skor, emergency stop hold, hash source dan exit proses; satu regresi pinger bukan bukti keandalan semua kondisi.
