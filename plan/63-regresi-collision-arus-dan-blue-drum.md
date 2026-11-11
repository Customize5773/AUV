# 63 — Regresi collision: arus/prior dan blue drum

Tanggal: 12 November 2026. Kelanjutan laporan 62, untuk menutup celah penerimaan pada kualifikasi berarus dan ARENA standar setelah collision disesuaikan dengan visual.

## Ruang lingkup

Mesh, controller, collision, guard dan toleransi penerimaan tidak berubah; hash-nya cocok dengan laporan 62. Urutan teardown pada kedua penguji diubah setelah ditemukan kegagalan shutdown, seperti dijelaskan di bawah. Pengujian memakai model gaya tujuh thruster dan estimator sensor, melalui penguji yang sudah tersedia; tidak ada koneksi/perintah ke kendaraan fisik.

Kualifikasi menggabungkan jalur 2, yaw awal 0,1 rad, offset lateral 0,15 m, seed 91, arus dunia `(0, 0,02, 0) m/s`, prior estimasi `(0,10, −0,10) m` dan cahaya normal. Setelah selesai, hold aktif diukur selama 30 detik, kemudian fault sengaja dipublikasikan untuk menguji disarm dan decay gaya. Ini berbeda dari stop motor-off yang memang bisa hanyut dalam arus.

ARENA standar memakai layout alternatif 1, blue drum 2, urutan R–Y–B, seed 42, prior estimasi `(0,10, −0,10) m`, tanpa arus, cahaya normal, GUI dan kedua POV. Jalur payload ke blue drum diuji terpisah dari fixture pinger/pickup laporan 62.

## Hasil kualifikasi

Run pertama lulus dengan pelintasan penuh kedua arah, surface dan hold aktif. Start–pelintasan kedua **22,682 s**, start–surface **25,742 s**, start–stop **29,960 s**. Angka stop pada mode ini adalah penyelesaian misi sebelum penahanan aktif, bukan pemadaman thrust; pemadaman dibuktikan terpisah melalui fault setelah jendela hold.

Galat estimasi maksimum XY **0,147650 m**, depth 0,004506 m dan yaw 0,008092 rad, seluruhnya di bawah batas referensi. Jendela hold **29,988 s** (toleransi penguji untuk permintaan 30 s), drift XY maksimum **0,005219 m** dan perubahan kedalaman maksimum 0,006383 m. Fault setelah hold berhasil mengunci disarm dan menghasilkan gaya nol. Shutdown bersih.

[Rekaman kualifikasi](../ros2_ws/evidence/collision-regression-20261112/qualification-current-prior.json), [kondisi](../ros2_ws/evidence/collision-regression-20261112/qualification-conditions.json).

## Kegagalan shutdown dan perbaikan penguji

Percobaan ARENA pertama menyelesaikan seluruh tugas: payload masuk blue drum 2, skor simulator 210,39058 tanpa penalti, thrust–surface 220,314 s, galat XY maksimum 0,156691 m. GUI dan kedua POV terverifikasi, kendaraan stop dengan gaya nol. Namun penerimaan keseluruhan **ditolak** karena server Gazebo tidak selesai setelah SIGINT/SIGTERM dan launch memakai SIGKILL. Rekaman gagal [arena-blue2.json](../ros2_ws/evidence/collision-regression-20261112/arena-blue2.json) dan log tetap disimpan.

Urutan lama menutup GUI sebelum mengirim pause. Karena GUI memiliki `on_exit=Shutdown()`, keluarnya GUI sudah memicu SIGINT launch; permintaan pause/stop berikutnya terlambat pada run gagal (`paused_before_shutdown=false`). Kedua penguji kini mengirim pause dan memberi waktu drain terlebih dahulu, lalu menutup GUI. Fallback service-stop, SIGINT, deteksi SIGKILL dan kriteria shutdown bersih tetap ada. Respons pause kualifikasi kini diperiksa dari isi `data: true`, sama dengan ARENA, bukan sekadar exit code CLI.

Ini menghilangkan race pada urutan permintaan teardown; belum membuktikan penyebab internal deadlock Gazebo. Suite simulator dijalankan ulang setelah perubahan: **183 tes lulus**. Build tidak diulang karena perubahan hanya script penguji yang dibaca langsung, bukan paket runtime/C++.

Kualifikasi GUI/dua POV sesudah perbaikan diterima: respons pause `data: true`, shutdown bersih, start–pelintasan kedua 22,706 s, start–surface 25,798 s dan start–stop 30,698 s. [Rekaman](../ros2_ws/evidence/collision-regression-20261112/qualification-paused.json).

## Hasil ARENA setelah perbaikan

Pengulangan dengan kondisi yang sama **diterima**, termasuk GUI dan kedua POV. Payload `payload` terbukti masuk blue drum **2**, seluruh flare jatuh sesuai R–Y–B, surface Square +20, stop motor-off dengan gaya nol, dan tidak ada penalti. Skor simulator **210,40156**, thrust–surface **219,948 s**. Galat estimasi maksimum XY **0,164689 m**, depth 0,004786 m dan yaw 0,008530 rad; seluruhnya lulus referensi.

`paused_before_shutdown=true` dan `shutdown_clean=true`; server tidak memerlukan SIGKILL. [Rekaman penerimaan](../ros2_ws/evidence/collision-regression-20261112/arena-blue2-paused.json). Verifier bukti memeriksa payload pertama di drum 2, deteksi seluruh flare, isolasi pose referee, kontrak sensor, tujuh thruster, akurasi, kondisi stop dan cleanup.

Total tahap ini: **empat misi selesai, tiga penerimaan lulus, satu kegagalan shutdown awal tetap ditolak**. Tiga penerimaan adalah kualifikasi arus/prior, kualifikasi GUI sesudah perbaikan, dan ARENA GUI sesudah perbaikan. PID launch keempat percobaan tidak tersisa. Bukti dua shutdown bersih sesudah perubahan merupakan regresi terbatas, bukan jaminan tidak ada deadlock Gazebo dalam semua kondisi.

## Bukti

Direktori [collision-regression-20261112](../ros2_ws/evidence/collision-regression-20261112/) menyimpan kondisi, hash source/aset, console log dan rekaman JSON tiap percobaan. Ringkasan akhir: [verification.json](../ros2_ws/evidence/collision-regression-20261112/verification.json), [verifier](../ros2_ws/evidence/collision-regression-20261112/verify.py), [cleanup](../ros2_ws/evidence/collision-regression-20261112/cleanup.json), [hash penguji sesudah perubahan](../ros2_ws/evidence/collision-regression-20261112/checker-hashes-after.json), dan [183 tes unit](../ros2_ws/evidence/collision-regression-20261112/unit-tests-after-shutdown.log). Graphify diperbarui setelah perubahan kode.

Angka waktu adalah waktu simulator; pengujian ini bukan benchmark berpasangan untuk mengklaim peningkatan kecepatan.

## Mengulang pengujian

Dari `/home/rasya/AUV/ros2_ws`, jalankan satu per satu dengan nama output baru:

```bash
bash tools/ros.sh python tools/check_qualification.py --vehicle-model dynamic --lane 2 --yaw .1 --lateral-offset .15 --surface-hold --conditions evidence/collision-regression-20261112/qualification-conditions.json --output evidence/collision-regression-repeat/qualification.json
```

Buat direktori output ARENA sebelum menjalankannya:

```bash
mkdir -p evidence/collision-regression-repeat
bash tools/ros.sh python tools/check_arena.py --vehicle-model dynamic --scene-variant 1 --blue-drum 2 --order R-Y-B --gui --pov --conditions evidence/collision-regression-20261112/arena-conditions.json --output evidence/collision-regression-repeat/arena-blue2.json
```

## Batas

Dua fixture tambahan tidak membuktikan seluruh kombinasi arus/layout atau banyak pengulangan. Collision tetap box batas luar mesh; massa, inertia, propulsi dan sensor belum dikalibrasi pada AUV fisik. Pengujian ini tidak menguji mekanisme servo, hidrofon atau pickup nyata.
