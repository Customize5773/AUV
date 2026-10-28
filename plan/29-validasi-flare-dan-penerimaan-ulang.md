# 29 — Validasi geometri flare dan penerimaan ulang

28 Oktober 2026. Melanjutkan jeda pada [laporan 28](28-pengujian-keandalan-berjalan.md). Status pengujian lengkap masih berjalan; hasil sementara tidak menggantikan penerimaan laporan 27.

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

## Bukti

Artefak lokal berada di [`evidence/reliability-resumed/`](../ros2_ws/evidence/reliability-resumed/). Percobaan gagal sebelum perbaikan tetap tersedia di folder laporan 28 dan `blue1.json`; tidak dimasukkan sebagai run penerimaan berhasil.

- Build berhasil dan **112 tes unit lulus**, termasuk regresi marker dekat permukaan serta arah akustik hampir vertikal.
- **98/98 pemeriksaan label perturbasi** lulus pada frame simulator tersimpan. Ini bukan pengujian metrik posisi atau kolam nyata.
- Run pembanding `blue1-floor.json` lulus misi penuh: 225,760 s thrust–surface, 210,22720 poin, Square +20, penalti 0, galat XY maksimum 0,1373 m dan shutdown bersih. Build berikutnya hanya memperbaiki kata pada komentar source; kode eksekusi tetap sama. Matriks penerimaan source final dicatat terpisah.
- Enam run kualifikasi sebelum jeda lulus pada tiga jalur, nominal dan offset penempatan ±0,15 m/yaw ±0,10 rad. Offset diketahui estimator; seluruhnya seed 42 tanpa arus. Bukti tersebut historis dari laporan 28, bukan enam pengulangan baru pada sesi ini.

## Matriks penerimaan source final

Menunggu akhir pengujian varian blue drum dan pinger/pickup. Run memakai model gaya tujuh thruster serta estimator sensor virtual. Kelulusan misi dan referensi akurasi dilaporkan terpisah; batas referensi tetap XY 0,20 m, kedalaman 0,03 m dan heading 0,03 rad.
