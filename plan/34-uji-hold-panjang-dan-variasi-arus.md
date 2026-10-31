# 34 — Uji hold panjang dan variasi arus

1 November 2026. Kelanjutan [laporan 33](33-sinkronisasi-kamera-dan-estimator.md). **Pengujian selesai: 134 tes unit lulus; empat misi kualifikasi selesai, tetapi hanya 3/4 run diterima. Hold 180 detik lulus pada 2/3 kasus.** Lingkup: kualifikasi dinamis, hold lebih lama, dan besar/arah arus berbeda antar-run.

## Penguji durasi panjang

`check_qualification.py` dan `check_arena.py` menerima `--hold-duration` (default 30 detik, minimum 30, hanya bersama `--surface-hold`). Waktu menunggu mengikuti timestamp lintasan simulator, dengan setidaknya lima detik settling sebelum jendela pengukuran. Batas waktu wall-clock bertambah untuk menampung durasi hold; proses simulator yang mati tetap terdeteksi ketika menunggu.

`verify_hold` mengukur seluruh durasi yang diminta, bukan hanya 30 detik terakhir. Bukti mencantumkan awal/akhir jendela, durasi aktual dan gap sampel maksimum. Persyaratan tetap drift XY <10 cm dan kedalaman <3 cm; cakupan waktu harus lengkap dalam toleransi 0,1 detik dan gap lintasan maksimum 0,1 detik. Setelah pengukuran, fault diinjeksi untuk membuktikan disarm terkunci serta gaya thruster nol.

Perubahan ini pada alat pengujian; pengendali, estimator dan model gaya tidak diubah. Tidak perlu membangun ulang plugin native. 134 tes unit lulus, termasuk contoh drift lambat yang lulus pada 30 detik namun gagal pada 180 detik, durasi tidak lengkap, data terputus dan argumen durasi tidak sah.

## Matriks

Semua arus konstan selama satu run, dalam koordinat world. Arah berbeda diuji antar-run; perubahan arah di tengah run belum dimodelkan pada tahap ini.

| Kasus | Seed | Arus world XYZ (m/s) | Besar (m/s) | Jendela hold |
| --- | ---: | --- | ---: | ---: |
| baseline-30 | 91 | (0; 0,02; 0) | 0,02 | 30 s |
| lateral-180 | 91 | (0; 0,02; 0) | 0,02 | 180 s |
| reverse-180 | 42 | (0; −0,05; 0) | 0,05 | 180 s |
| diagonal-180 | 7 | (0,06; 0,08; 0) | 0,10 | 180 s |

Runner serial mempertahankan seluruh hasil, termasuk kegagalan, dan memeriksa hash source sebelum setiap run. Manifest/perintah/checkpoint: `ros2_ws/evidence/long-hold-final-2027/summary.json`. Selesainya batch tidak otomatis berarti semua kasus diterima; lihat `all_passed` dan hasil tiap run.

Batas: belum uji ARENA, GUI/POV, arus berubah sepanjang waktu, atau hardware. Variasi seed dan arus pada matriks ini tidak memisahkan pengaruh masing-masing secara statistik. Hold memakai estimasi dead reckoning; kelulusan durasi pendek tidak membuktikan penahanan posisi absolut tanpa batas waktu.

Percobaan awal pada `evidence/long-hold-2027/` gagal sebelum simulasi berjalan: DDS menolak domain ID 233 karena perhitungan port melebihi batas. Runner diperbaiki memakai domain terisolasi 88; kegagalan setup disimpan terpisah dan tidak dihitung sebagai uji kemampuan hold.

## Hasil

| Kasus | Durasi aktual (s) | Drift XY fisik (cm) | Drift kedalaman (cm) | Drift XY estimasi (cm) | Penerimaan |
| --- | ---: | ---: | ---: | ---: | --- |
| baseline-30 | 29.988 | 2.09 | 0.67 | 0.38 | Lulus |
| lateral-180 | 179.996 | 12.05 | 0.78 | 0.41 | Gagal: drift XY >10 cm |
| reverse-180 | 179.996 | 3.33 | 1.15 | 0.90 | Lulus |
| diagonal-180 | 179.996 | 8.91 | 1.03 | 1.57 | Lulus |

Keempat misi selesai dan seluruh run lulus referensi akurasi estimator (XY <20 cm), pemisahan ground truth, cakupan jendela, uji fault/disarm/gaya nol, serta shutdown bersih. Gap lintasan maksimum 0,034 detik. Satu-satunya pemeriksaan yang gagal adalah drift XY hold pada `lateral-180`; ini tidak disamarkan oleh kelulusan misi atau ambang akurasi estimator yang berbeda.

## Batas yang ditemukan

Pada `lateral-180`, posisi estimasi bergeser hanya 0,41 cm sementara posisi fisik bergeser 12,05 cm. Kalibrasi DVL dari 57 sampel menghasilkan bias X 0,000382455 m/s. Model sensor menyuntikkan bias X 0,001 m/s, sehingga selisihnya sekitar 0,000617545 m/s; akumulasi selama 180 detik sekitar 11,12 cm. Angka ini sejalan dengan drift yang diukur dan menunjukkan keterbatasan referensi dead reckoning pada hold panjang. Nilai bias bawaan simulator hanya dibaca untuk analisis, tidak diberikan kepada estimator/pengendali. Baseline 30 detik memakai seed, arus dan hasil kalibrasi yang sama, tetapi drift masih 2,09 cm.

Kasus diagonal lulus dengan drift 8,91 cm, menyisakan margin sekitar 1,09 cm. Karena seed dan arus berbeda antar-kasus, hasil tersebut tidak membuktikan bahwa arus lebih kuat selalu lebih mudah ditahan. Semua hasil tetap terbatas pada fixture yang diuji.

**Hold jangka panjang belum dapat dinyatakan andal.** Prioritas berikutnya adalah memvalidasi kualitas/ketidakpastian kalibrasi DVL sebelum pelepasan penahan, lalu mengulang kasus panjang. Untuk drift jangka panjang, referensi posisi independen juga perlu dipertimbangkan. Jangan mempelajari bias dengan menganggap kendaraan yang sudah bebas hanyut sebagai diam. Tidak ada tuning pengendali atau pelonggaran ambang pada tahap pengujian ini.

Bukti lokal: [verification.json](../ros2_ws/evidence/long-hold-final-2027/verification.json), [manifest dan perintah](../ros2_ws/evidence/long-hold-final-2027/summary.json), [134 tes unit](../ros2_ws/evidence/long-hold-final-2027/unit-tests.log). `experiment_complete=true` berarti pengujian selesai; `all_passed=false` mencatat kegagalan penerimaan. Artefak `evidence/` diabaikan Git.

Contoh mengulang satu kasus ke output baru:

```bash
cd /home/rasya/AUV/ros2_ws
bash tools/ros.sh python tools/check_qualification.py --vehicle-model dynamic --surface-hold --hold-duration 180 --conditions evidence/long-hold-final-2027/lateral-180-conditions.json --output evidence/long-hold-recheck-01/result.json
```

`--hold-duration` mengatur pengukuran pada harness, bukan durasi otomatis mode kendaraan. Mode `surface_hold:=true` pada launch tetap menahan posisi sampai dihentikan atau terjadi fault.

Perbaikan kualitas kalibrasi sebelum start dan penerimaan lanjut dicatat pada [laporan 35](35-kualitas-kalibrasi-dvl-sebelum-start.md). Hasil gagal di atas tetap merupakan bukti versi pengendali saat pengujian laporan 34.
