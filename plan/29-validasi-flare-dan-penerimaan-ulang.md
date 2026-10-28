# 29 — Validasi geometri flare dan penerimaan ulang

28–29 Oktober 2026. Melanjutkan jeda pada [laporan 28](28-pengujian-keandalan-berjalan.md). **Perbaikan diterima pada fixture yang diuji:** validasi flare, akustik hampir vertikal dan pemeriksa retensi diperbaiki; baseline dan pinger/pickup lulus ulang sampai surface–stop pada 29 Oktober.

Hasil berikutnya tersedia pada [laporan 30](30-pengujian-keandalan-berulang.md): matriks 18 kasus dan 120 tes unit. Angka serta fixture di bawah tetap merupakan bukti tahap ini, sebelum perbaikan integrasi DVL.

## Penyebab dan perbaikan

Peta controller pada percobaan gagal berisi blue flare dekat permukaan: misalnya lokal (10,675; 9,177; −0,149 m) dan (17,797; 7,479; +0,040 m), jauh dari flare latihan sesungguhnya di (16,5; 21; −1,6 m). Pemulihan pole biru tipis tidak membuktikan bahwa komponennya merupakan flare utuh: marker Square atau fragmen biru dapat lolos klasifikasi dan konfirmasi temporal. Peta statis kemudian menolak pengamatan baru yang berbeda lebih dari 0,75 m, sehingga target awal yang salah bertahan sampai timeout kontak.

Percobaan tambahan `blue1.json` hanya menolak kandidat yang tidak muat di bawah permukaan, tetapi masih gagal dengan target z = −0,512 m. Batas permukaan saja belum cukup.

`ArenaController.observe` sekarang memeriksa tinggi pusat pole terhadap dasar kolam yang dikonfigurasi. Flare biru/merah/kuning setinggi 0,8 m harus memiliki pusat sekitar 0,4 m di atas dasar, dengan toleransi 0,25 m. Kandidat yang tidak konsisten tidak masuk pending maupun peta landmark. Pole orange memakai geometri berbeda sehingga tidak menggunakan pemeriksaan ini. Edisi 2027 mengubah koordinat lokal V menjadi world X sebelum membaca profil kedalaman; edisi 2026 memakai profil lamanya.

Pemeriksaan memakai proyeksi kamera, pose hasil estimator dan prior bentuk dasar kolam; tidak memakai pose properti atau odometri ground truth. **Batas penting:** profil dasar tetap interpretasi geometri latihan, bukan hasil survei kolam nyata. Tinggi pole, kalibrasi kamera, attitude dan bathymetry perlu diukur sebelum menerapkan kriteria ini pada hardware. Deteksi label saja tetap tidak membuktikan jarak atau identitas objek.

Tidak ada perubahan pada gaya thruster, drag, noise sensor, batas kontak, timeout, konfirmasi jatuh bola, penilaian, watchdog atau toleransi pelintasan.

## Kasus tambahan: pinger hampir vertikal

Fixture baru pinger drum 1 (`a4-pinger1.json`) menemukan ABORT `stale_acoustics` pada alignment. Sebanyak 2.989 paket akustik diterima dengan kontrak valid. Pada t = 143,004 s, logger posisi fisika mencatat jarak horizontal sekitar 0,101 m dari sumber dan selisih kedalaman 1,551 m: komponen arah horizontal hanya sekitar 0,065, di bawah batas observabilitas 0,1 milik tracker. Ini analisis harness, bukan masukan posisi sumber ke controller.

Tracker sebelumnya mengembalikan None pada arah hampir vertikal meskipun paket valid dan segar, sehingga controller menganggap akustik sudah hilang. Sekarang pengamatan seperti itu mempertahankan target yang sudah tertriangulasi hanya jika posisi estimasi kendaraan berjarak <0,30 m dari target tersebut. Tidak ada ray baru atau bearing buatan yang ditambahkan. Tanpa target awal, paket invalid/duplikat, atau arah lemah jauh dari target, hasil tetap ditolak. Watchdog alignment 0,5 s tetap aktif ketika paket yang dapat diterima berhenti datang.

Tes regresi memeriksa retensi target lokal, tidak bertambahnya ray, penolakan frekuensi salah/duplikat, kasus jauh dan kasus tanpa triangulasi. Tes timeout akustik yang sudah ada tetap harus lulus. Perubahan ini hanya dipakai mode extended; tiga fixture blue drum yang selesai sebelumnya tidak menjalankan jalur akustik.

## Retensi pada badan yang miring

Run `a4-pinger1-final.json` kemudian berhasil drop, keluar target zone, pickup dan surface, tetapi gagal saat menunggu stop. Telemetri terakhir masih menyatakan `payload_attached=true`; pemeriksa retensi salah mengubah offset gripper hanya memakai yaw. Setelah disarm, roll/pitch badan berubah dan jarak terhadap titik gripper yang dihitung salah melewati 0,075 m, sehingga referee mengeluarkan PAYLOAD_RETENTION_LOST lalu premature_surface. Poin sementara yang sudah terhitung tidak membuat run gagal ini menjadi penerimaan berhasil.

Referee kini merotasi offset gripper (−0,20; 0; −0,45 m) memakai roll, pitch dan yaw dari pose fisika yang memang sudah dibacanya. Batas jarak tetap **0,075 m**, dan joint attachment tetap wajib. Tidak ada perubahan pada latch fisik, deteksi kontak atau cara controller mengambil bola. Tes memeriksa bola pada posisi gripper yang miring, penolakan deviasi 0,08 m meskipun attachment true, serta pencabutan kredit bila attachment false.

Pada 29 Oktober tidak ada proses simulasi lama yang tersisa. Run `a0-blue1-final` sebelumnya terputus sebelum menghasilkan JSON akhir; run itu tidak dihitung sebagai kegagalan misi alami atau keberhasilan. Pinger/pickup dan baseline diulang pada folder baru [`evidence/acceptance-retention-2027/`](../ros2_ws/evidence/acceptance-retention-2027/) agar bukti lama tetap utuh.

## Bukti

Artefak lokal berada di [`evidence/reliability-resumed/`](../ros2_ws/evidence/reliability-resumed/). Percobaan gagal sebelum perbaikan tetap tersedia di folder laporan 28 dan `blue1.json`; tidak dimasukkan sebagai run penerimaan berhasil.

- Build berhasil dan **113 tes unit lulus pada 29 Oktober**, termasuk regresi marker dekat permukaan, arah akustik hampir vertikal dan retensi dengan badan miring.
- **98/98 pemeriksaan label perturbasi** lulus pada frame simulator tersimpan. Ini bukan pengujian metrik posisi atau kolam nyata.
- Run pembanding `blue1-floor.json` lulus misi penuh: 225,760 s thrust–surface, 210,22720 poin, Square +20, penalti 0, galat XY maksimum 0,1373 m dan shutdown bersih. Build berikutnya hanya memperbaiki kata pada komentar source; kode eksekusi tetap sama. Matriks penerimaan source final dicatat terpisah.
- Enam run kualifikasi sebelum jeda lulus pada tiga jalur, nominal dan offset penempatan ±0,15 m/yaw ±0,10 rad. Offset diketahui estimator; seluruhnya seed 42 tanpa arus. Bukti tersebut historis dari laporan 28, bukan enam pengulangan baru pada sesi ini.

## Matriks penerimaan dan asal bukti

Ringkasan lokal: [verification.json](../ros2_ws/evidence/acceptance-retention-2027/verification.json). Lima fixture memiliki bukti lulus. Dua run diulang pada 29 Oktober; tiga varian blue drum memakai hasil 28 Oktober dengan hash controller dan detector yang sama. Perubahan akustik/retensi setelah ketiga run tersebut hanya memengaruhi jalur extended. Build, source dan instalasi pada dua run baru cocok, dengan SHA-256 tercatat di source.json. Percobaan gagal serta run terputus tetap dipertahankan terpisah.

| Fixture | Varian / urutan | Tanggal run | Thrust–surface | Poin simulator | Galat XY maksimum |
| --- | --- | --- | ---: | ---: | ---: |
| [Blue drum 1](../ros2_ws/evidence/acceptance-retention-2027/blue1.json) | 0 / B-R-Y | 29 Oktober | 225,752 s | 210,22744 | 0,1357 m |
| [Blue drum 2](../ros2_ws/evidence/reliability-resumed/a1-blue2-alt.json) | 1 / R-Y-B | 28 Oktober | 217,322 s | 210,48034 | 0,1018 m |
| [Blue drum 3](../ros2_ws/evidence/reliability-resumed/a2-blue3.json) | 0 / Y-B-R | 28 Oktober | 190,538 s | 211,28386 | 0,1352 m |
| [Blue drum 4](../ros2_ws/evidence/reliability-resumed/a3-blue4-alt.json) | 1 / R-B-Y | 28 Oktober | 188,128 s | 211,35616 | 0,1138 m |
| [Pinger drum 1, blue drum 4](../ros2_ws/evidence/acceptance-retention-2027/pinger1.json) | 0 / Y-R-B | 29 Oktober | 223,770 s | 290,28690 | 0,1849 m |

Seluruh run memakai gaya tujuh thruster dan estimator tekanan/IMU/magnetometer/DVL, berakhir DONE/COMPLETE, Square +20, penalti 0, perintah dan gaya nol, kendaraan stationary serta shutdown bersih. Ketujuh kanal benar-benar menghasilkan gaya selama misi. Pemeriksaan graph menunjukkan controller/estimator/propulsi/guard tidak mengonsumsi pose ground truth atau hasil referee lengkap. Pinger/pickup juga membuktikan acquisition, seluruh badan keluar target zone, pickup serta retensi bola yang sama sampai STOPPED; tidak ada PAYLOAD_RETENTION_LOST pada run penerimaan baru.

Kelulusan misi dan referensi akurasi dicatat terpisah dalam JSON. Semua lima run memenuhi batas referensi tetap: XY <0,20 m, kedalaman <0,03 m, heading <0,03 rad. Galat pinger baru 0,1849 m tetap di bawah referensi tetapi lebih besar daripada beberapa run sebelumnya; ini tidak membuktikan seluruh metrik estimator membaik. Waktu antarfixture memiliki lintasan/urutan berbeda dan tidak digunakan untuk menyimpulkan peningkatan kecepatan kendaraan.

Ini penerimaan **headless** pada fixture terbatas, seed sensor tetap dan tanpa arus. Angka lima fixture bukan probabilitas keandalan dari seluruh percobaan, karena percobaan gagal selama pengembangan tetap ada. GUI/POV dan empat injeksi gangguan masih menggunakan bukti historis [laporan 27](27-kalibrasi-dvl-dan-penerimaan-gui.md), tidak diulang pada sesi ini. Model aktif tetap empat sumbu surge/sway/heave/yaw dengan damping roll/pitch pasif. Kalibrasi kendaraan, PWM–thrust, geometri mixer, kamera, bathymetry, hidrofon dan mekanik nyata belum tervalidasi.
