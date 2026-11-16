# 64 — Konsistensi dan benchmark setelah revisi collision

13–14 November 2026, Asia/Jakarta. Penerimaan selesai secara bertahap: perbaikan timestamp kamera, diagnosis/perbaikan shutdown bridge, pengulangan kasus gagal dan GUI, lalu tiga regresi ARENA. Optimasi kecepatan baru **tidak dipromosikan**.

## Acuan aturan

Pemeriksaan 14 November: [rulebook resmi](https://sauvc.org/rulebook/) masih **2027.3.2**, diperbarui 30 Oktober 2026. Perbandingan master dengan commit arsip identik: nol commit/file berubah. Tidak memerlukan migrasi aturan baru. [Bukti pemeriksaan](../doc/sources/rulebook-check-20261114.json).

## Konsistensi dan keputusan kecepatan

Baseline dibekukan: lima seed 7/42/91/123/2026 pada masing-masing tiga jalur, satu arus/hold dan dua prior posisi. **18/18 diterima**, akurasi, stop dan shutdown lulus. Pelintasan kedua 22,630–22,858 s; surface 25,698–25,986 s; stop 29,744–30,974 s. [Verifikasi baseline](../ros2_ws/evidence/qualification-consistency-20261113/verification.json).

Tiga kandidat diuji pada enam kondisi identik. Masing-masing menyelesaikan 6/6 misi, tetapi gagal kriteria performa: setiap pasangan harus mempercepat surface tanpa memperlambat pelintasan kedua, dan median stop tidak boleh memburuk.

| Kandidat | Regresi pelintasan kedua yang menggagalkan promosi | Bukti |
|---|---|---|
| Kedalaman 0,50 m | Jalur 3 seed 7: +0,424 s | [Verifikasi](../ros2_ws/evidence/qualification-depth-050-20261113/verification.json) |
| Gain vertikal 2,0, kedalaman 0,60 m | Arus/hold: +0,848 s | [Verifikasi](../ros2_ws/evidence/qualification-heave-20-20261113/verification.json) |
| Kedalaman 0,50 m + syarat capture pasca-turn | Arus/hold +0,464 s; prior jalur 2 +0,248 s | [Verifikasi](../ros2_ws/evidence/qualification-postturn-050-20261113/verification.json) |

Final tetap **kedalaman 0,60 m, gain vertikal 1,5**. Thrust, yaw, jarak U-turn, model air, guard dan toleransi referee tidak diubah. Angka kandidat tidak dinyatakan sebagai peningkatan default.

Perbaikan navigasi yang dipertahankan: `Runtime.image` meneruskan timestamp capture ke deteksi; `FIND_RETURN_GATE` dinamis 2027 menolak gambar yang diambil sebelum akhir U-turn, meskipun baru diterima. Satu tes dengan header Image membuktikan penolakan frame lama dan penerimaan frame pasca-turn. Ini memperbaiki kontrak frame, belum membuktikan penyebab unik seluruh variasi alignment historis.

## Diagnosis dan perbaikan shutdown

Batch berikutnya menyelesaikan **18/18 misi**, tetapi hanya **17/18 penerimaan**. Kasus `q-lane3-123` gagal shutdown: `parameter_bridge` global crash −11 setelah eskalasi SIGTERM. Laporan crash milik PID tersebut menunjukkan penghancuran publisher FastDDS (`DataWriterImpl::get_topic`, `delete_datawriter`, `rmw_destroy_publisher`). [Summary asli](../ros2_ws/evidence/postturn-final-20261114/qualification/summary.json) tetap menyimpan kegagalan.

Package lokal [sauvc_bridge](../ros2_ws/src/sauvc_bridge/README.md) memakai konversi ROS/Gazebo terpasang dan YAML yang sama. Signal hanya meminta loop berhenti; executor berhenti dahulu, endpoint/node dilepas sebelum `rclcpp::shutdown()`. Launch memakai executable lokal ini. Tidak mengubah paket global ROS. Diagnosis dan urutan lifecycle mengacu pada [upstream #977](https://github.com/gazebosim/ros_gz/pull/977), [#952](https://github.com/gazebosim/ros_gz/pull/952) dan [#951](https://github.com/gazebosim/ros_gz/issues/951). [Bukti diagnosis](../ros2_ws/evidence/postturn-final-20261114/bridge-diagnosis.json).

Build kedua package lulus. Verifikasi:

- **184 tes Python lulus**: baseline 183 + kontrak timestamp. Tes tuning eksperimental dilepas bersama kandidatnya.
- CTest native mengirim pesan nyata pada tiga arah bridge, memeriksa pelepasan kepemilikan; **10 pengulangan × tiga arah lulus**. Publisher Gazebo eksternal dipakai karena factory terpasang mengabaikan pesan intraprocess; percobaan oracle awal yang keliru tetap tersimpan.
- **10/10 uji proses SIGINT/SIGTERM** keluar 0, tanpa cleanup paksa. [Verifikasi signal](../ros2_ws/evidence/postturn-final-20261114/bridge-signals/verification.json).
- Kasus gagal diulang setelah perbaikan: **1/1 diterima**, official 23,568 s, surface 26,660 s, stop 31,624 s, shutdown bersih. [Summary rerun](../ros2_ws/evidence/postturn-final-20261114/qualification-bridge-rerun/summary.json).
- Kualifikasi GUI + kedua POV **1/1 diterima**, shutdown bersih. [Bukti GUI](../ros2_ws/evidence/postturn-final-20261114/qualification-gui.json).

Ini penerimaan **bertahap**, bukan klaim seluruh 18 kasus diulang memakai bridge baru. Controller, runtime, referee, estimator, dinamika dan konfigurasi gaya tetap sama antara batch dan rerun; hash diperiksa verifier. Statistik 18 kasus dengan rerun pengganti dan satu GUI: pelintasan kedua **22,730–23,662 s**, surface **25,824–26,786 s**, stop **30,070–32,196 s**. Tidak membuktikan peningkatan waktu terhadap baseline.

Bridge lokal hanya memerlukan konfigurasi YAML yang dipakai workspace dan bergantung pada SDK Humble terpasang. Build memilih ABI Protobuf 3.12/YAML-CPP 0.7 yang sesuai pada host ini; tidak mengganti library sistem. Upgrade SDK memerlukan build dan uji native ulang.

## Regresi ARENA final

Ketiganya memakai dinamika tujuh thruster, estimator sensor, GUI dan kedua POV. Seluruhnya DONE, penalti nol, bonus Square +20, shutdown bersih dan semua PID launch sudah berakhir. Kondisi dan hash source dibekukan.

| Kasus | Skor | Thrust–surface | Galat XY maksimum |
|---|---:|---:|---:|
| Cahaya 70%, blue drum 3, urutan Y–B–R | 211,22794 | 192,402 s | 14,43 cm |
| Arus 0,02 m/s, surface hold | 210,16450 | 227,850 s | 6,78 cm |
| Layout alternatif, pinger drum 4, pickup | 290,73252 | 208,916 s | 10,72 cm |

Hold aktif 29,988 s menghasilkan drift maksimum **0,49 cm**. Thruster aktif selama hold; fault berikutnya memverifikasi disarm dan gaya nol. Ini berbeda dari default motor-off.

Extended membuktikan drop ke drum berpinger, seluruh badan keluar target zone, kembali mengambil **bola yang sama**, lalu retensi hingga akhir pada **1.320 snapshot**. [Verifikasi tiga ARENA](../ros2_ws/evidence/arena-postturn-final-20261114/verification.json).

[Verifikasi gabungan](../ros2_ws/evidence/postturn-final-20261114/verification.json) diterima dan tetap mencatat `all_initial_attempts_accepted=false`. Log build, tes native/Python, summary, kondisi, hash dan verifier tersedia dalam direktori bukti tersebut.

## Menjalankan ulang

Dari `ros2_ws`, gunakan output baru agar bukti tidak tertimpa:

```bash
bash tools/ros.sh build --symlink-install
bash tools/ros.sh python tools/check_reliability.py --profile qualification-speed --suite qualification --output evidence/qualification-speed-ulangan
```

Panduan GUI/POV: [CARA-RUNNING.md](../ros2_ws/CARA-RUNNING.md). Verifier bukti tahap ini:

```bash
bash tools/ros.sh python evidence/arena-postturn-final-20261114/verify.py
bash tools/ros.sh python evidence/postturn-final-20261114/verify.py
```

## Batas dan pekerjaan berikutnya

Konsistensi membaik dalam kasus yang diuji, tetapi peningkatan kecepatan universal belum terbukti. Pengujian lifecycle menutup reproduksi/diagnosis shutdown saat ini, bukan jaminan tidak ada crash lain. Belum mencakup seluruh arus, layout, cahaya dan kondisi air nyata.

Pengguna mengonfirmasi Raspberry Pi, Jetson dan DWE tersedia, **kapal belum selesai**. [Kesiapan kalibrasi fisik](../doc/12-kesiapan-kalibrasi-fisik.md) mencatat massa, buoyancy, posisi/arah thruster, PWM–thrust dan uji basah yang belum tersedia. Kalibrasi DWE udara RMS 0,590 px masih provisional; empat tes collector/fitter/preview lulus tanpa capture baru. Tidak ada aktuasi atau misi fisik pada tahap ini.

Kelanjutan: [laporan 65](65-penerimaan-penuh-bridge-terkelola.md) mengulang seluruh 18 kualifikasi pada source bridge terkelola yang sama; 18/18 diterima tanpa retry. Kegagalan awal pada laporan ini tetap menjadi riwayat bukti.
