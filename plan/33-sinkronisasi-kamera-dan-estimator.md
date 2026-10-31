# 33 — Sinkronisasi kamera dan estimator kualifikasi

30 Oktober 2026. Kelanjutan [laporan 32](32-surface-hold-dan-koreksi-prior.md), khusus konsistensi koreksi prior posisi. **Selesai: 132 tes unit dan tujuh run kualifikasi lulus.** Hasil pengujian 30 Oktober diverifikasi dan laporan difinalisasi 1 November 2026; source masih cocok dengan manifest, tanpa mengulang runtime pada tanggal finalisasi.

## Perbaikan

Callback kamera sebelumnya langsung memanggil `observe_gate`. Jika timestamp gambar lebih baru daripada timestamp paket instrumen terakhir, umur gambar negatif sehingga observasi ditolak dan rangkaian konfirmasi direset. Urutan callback yang berbeda dapat menghambat tiga konfirmasi berurutan, walaupun gambar dan sensor sama-sama masih segar. Log lama tidak mencatat seluruh pasangan timestamp, sehingga penyebab setiap penolakan pada run lama tidak bisa dipastikan dari artefak tersebut saja.

Runtime kini menyimpan satu observasi gate terbaru. Jika waktu estimator belum menyusul, observasi menunggu paket instrumen valid berikutnya. Setelah waktunya sesuai, observasi dikonsumsi sekali sebelum publikasi odometri. Frame lama/duplikat tidak mengganti observasi yang lebih baru. Pengamatan dibuang setelah keluar fase FIND_GATE/ALIGN. Health mencatat `gate_deferred_frames` untuk menunjukkan berapa frame yang perlu menunggu sensor.

Batas umur gambar 0–0,12 detik, tiga konfirmasi, jarak, sudut, inovasi dan gain koreksi tetap berlaku. Tidak ada perluasan toleransi galat 20 cm atau pemakaian ground truth oleh pengendali. Penggunaan tetap membutuhkan gate yang posisi/ukurannya disurvei; ini bukan solusi untuk layout tidak diketahui atau kamera yang belum dikalibrasi.

## Verifikasi

Build berhasil dan 132 tes unit lulus. Tes regresi mencakup urutan kamera sebelum sensor, konsumsi satu kali, duplikat, observasi kedaluwarsa dan pergantian fase. Kegagalan tes sebelum perbaikan disimpan.

Penerimaan terarah terdiri dari tujuh run serial: prior seed 91/jalur 3 sebanyak tiga kali, prior seed 7/jalur 1, prior seed 42/jalur 2, nominal, dan hold berarus seed 91. Lima run prior wajib menerima setidaknya satu koreksi gate, selain syarat misi, akurasi dan shutdown yang sudah ada. Hold tetap memerlukan bukti drift jendela 30 detik dan disarm/gaya nol setelah fault.

Manifest source, kondisi, perintah dan checkpoint: `ros2_ws/evidence/gate-sync-2027/summary.json`. Source dibekukan selama batch; hasil lama tidak ditimpa. ARENA, GUI/POV, arus yang lebih besar, hold jangka panjang, dan hardware tidak termasuk pengujian tahap ini.

## Hasil penerimaan

| Kasus | Galat XY maksimum (cm) | Koreksi gate | Frame menunggu sensor |
| --- | ---: | ---: | ---: |
| prior-91-1 | 14.79 | 13 | 14 |
| prior-91-2 | 14.88 | 19 | 13 |
| prior-91-3 | 15.01 | 14 | 15 |
| prior-7 | 14.71 | 17 | 23 |
| prior-42 | 14.43 | 13 | 23 |
| nominal | 3.38 | 17 | 26 |
| hold-91 | 3.49 | 19 | 36 |

Kelima kasus prior menerima koreksi (13–19 kali). Galat maksimum prior 14,43–15,01 cm, dengan margin terburuk 4,99 cm terhadap ambang 20 cm. Pada laporan 32, galat terburuk adalah 18,24 cm dan satu run tidak menerima koreksi. Ini perbandingan batch terbatas, bukan jaminan semua kondisi.

Regresi nominal dan hold berarus 0,02 m/s juga lulus. Drift hold pada jendela 30 detik adalah 2,36 cm XY dan 0,73 cm kedalaman; setelah fault, disarm terkunci dan gaya thruster turun ke nol. Keenam run motor-off membuktikan gaya nol. Seluruh run lulus pemisahan ground truth, referensi akurasi dan shutdown bersih.

Bukti lokal: [verification.json](../ros2_ws/evidence/gate-sync-2027/verification.json), [manifest/perintah](../ros2_ws/evidence/gate-sync-2027/summary.json), [build](../ros2_ws/evidence/gate-sync-2027/build.log), [132 tes unit](../ros2_ws/evidence/gate-sync-2027/unit-tests.log), dan [tes sebelum perbaikan](../ros2_ws/evidence/gate-sync-2027/before-tests.log). Artefak `evidence/` diabaikan Git. Pengulangan dapat dilakukan dengan salinan `run.py` pada folder bukti baru dari direktori workspace.

Pengujian hold lebih lama dan variasi arus dilanjutkan pada [laporan 34](34-uji-hold-panjang-dan-variasi-arus.md).
