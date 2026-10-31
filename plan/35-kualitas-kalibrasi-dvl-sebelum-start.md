# 35 — Kualitas kalibrasi DVL sebelum start

1 November 2026. Kelanjutan kegagalan hold 180 detik pada [laporan 34](34-uji-hold-panjang-dan-variasi-arus.md). Status: implementasi dan matriks penerimaan selesai; 5/6 percobaan diterima, satu gagal akibat gangguan sensor saat hold.

## Perubahan

Estimator tetap mempelajari bias horizontal hanya saat `deployment_held=true`, kecepatan DVL kecil dan gyro tenang. Selain rata-rata, estimator kini menghitung jumlah kuadrat penyimpangan secara online (Welford). Indikator ketidakpastian horizontal adalah `2 * sqrt((M2_x + M2_y) / (n * (n - 1)))`, dalam m/s.

Kualitas dinyatakan siap bila sedikitnya 200 sampel diterima dan indikator tersebut ≤0,0004 m/s. Nilai ini setara anggaran drift 7,2 cm selama 180 detik, menyisakan sebagian batas 10 cm untuk respons kontrol dan galat lain. Ini indikator dua standard error gabungan dengan asumsi sampel independen, **bukan jaminan probabilistik atau batas galat hardware**. Angka bias bawaan simulator tidak digunakan oleh estimator atau syarat kesiapan.

Health menambahkan `dvl_bias_uncertainty_mps` (null sebelum dua sampel) dan `dvl_calibration_ready`. Kualifikasi dan ARENA menunggu kualitas siap serta aliran data stabil dua detik sebelum memulai. Batas startup 45 detik tetap berlaku; kegagalan kualitas yang teramati dilaporkan sebagai `dvl_calibration_not_ready`. Metadata kesehatan sensor tetap terpisah dari kesiapan kalibrasi, sehingga sensor sehat selama pengumpulan data tidak dianggap hilang.

Kalibrasi tetap dibekukan saat misi/perintah gerak dimulai atau penahan dilepas. Tidak ada pembelajaran bias saat kendaraan bebas hanyut. Gain kontrol, gaya thruster dan batas drift hold tidak diubah. Preflight dapat memakan waktu lebih lama; waktu persiapan dicatat terpisah dari waktu sejak thrust pertama.

## Verifikasi

Build berhasil dan 139 tes unit lulus. Tes mencakup sampel terlalu sedikit meskipun scatter nol, penolakan rata-rata yang masih bising, pengurangan ketidakpastian saat sampel bertambah, pembekuan setelah pelepasan, serta menunggu/timeout kesiapan pada kedua jenis misi. Penguji juga menolak kesiapan yang baru muncul sesudah thrust atau kendaraan yang bergerak saat preflight.

Harness kualifikasi dan ARENA memeriksa health terakhir sebelum gaya thruster pertama >0,05 N, kualitas kalibrasi yang dibekukan, dan perpindahan fisik preflight <1 mm. Pemeriksa memakai ground truth hanya untuk evaluasi. Matriks serial: dua pengulangan lateral 180 detik (seed 91, arus 0,02 m/s), diagonal 180 detik (seed 7, arus 0,10 m/s), kualifikasi nominal motor-off, dan ARENA blue drum berarus 0,02 m/s motor-off. Manifest source/perintah: `ros2_ws/evidence/dvl-quality-2027/summary.json`.

Batas: asumsi independensi sampel belum divalidasi terhadap DVL nyata, noise berkorelasi, bias termal atau bias berubah setelah kalibrasi. Pinger, GUI/POV dan matriks fault lama belum diuji ulang. Fault yang waktunya tetap relatif terhadap awal simulasi dapat terjadi selama preflight yang kini lebih panjang; ini tidak sama dengan bukti fault setelah kendaraan mulai bergerak. Uji fault hold tetap diinjeksi sesudah jendela hold penuh.

Percobaan pertama lateral-180 lulus (drift 2,10 cm). Pengulangan pertama mengalami gap lintasan 4,93 detik dan `stale_sensors` setelah misi selesai; pengaman mengunci disarm, sehingga kendaraan kemudian hanyut dan pemeriksaan hold gagal. Kalibrasi sebelum thrust tetap lulus. Kegagalan disimpan di `evidence/dvl-quality-2027/`; pengulangan dan sisa matriks dilanjutkan tanpa perubahan source/timeout pada `evidence/dvl-quality-rerun-2027/`. Ini tetap kegagalan runtime, bukan dihapus sebagai keberhasilan.

## Hasil akhir

| Kasus | Diterima | Sampel bias | Persiapan sampai thrust (s simulasi) | Drift hold 180 s (cm) |
|---|---|---|---|---|
| lateral-180 | Ya | 501 | 28.314 | 2.10 |
| lateral-repeat-180 | Tidak: stale_sensors | 500 | 28.292 | 29.85 |
| lateral-repeat-180 | Ya | 500 | 28.224 | 2.07 |
| diagonal-180 | Ya | 498 | 28.160 | 1.86 |
| nominal | Ya | 472 | 26.756 | — (motor-off) |
| arena-current | Ya | 473 | 26.814 | — (motor-off) |

Dua hold lateral yang diterima mencatat 2,10 dan 2,07 cm, dibanding 12,05 cm pada laporan 34. Hold diagonal turun dari 8,91 menjadi 1,86 cm. Ini perbandingan fixture simulator yang sama, bukan bukti semua kondisi. Keenam percobaan lulus kualitas kalibrasi sebelum thrust, preflight tanpa perpindahan fisik, serta shutdown bersih. Tiga hold yang diterima juga lulus injeksi abort setelah jendela hold: disarm dan gaya nol.

Kualifikasi yang diterima mencatat start–surface 27,466–28,530 detik. Persiapan sampai thrust kini 26,756–28,314 detik simulasi, terpisah dari metrik waktu misi. ARENA blue drum berarus lulus dengan galat XY maksimum 6,18 cm, payload settled di blue drum, Surface Square, motor-off, thrust–surface 227,132 detik dan skor simulator 210,18604. Ini hasil profil aturan yang tersimpan di repo, bukan pemeriksaan pembaruan rulebook pada tanggal pengujian.

Bukti gabungan: [verification.json](../ros2_ws/evidence/dvl-quality-acceptance-2027/verification.json), mencakup semua enam percobaan, hash laporan/source, perintah, health sebelum thrust, serta hasil hold. Build dan 139 tes unit lulus; log tersimpan bersama batch penerimaan. Source kedua batch identik dan cocok dengan file implementasi saat verifikasi.

**Yang masih terbuka:** penyebab gangguan sensor/gap lintasan 4,93 detik pada satu percobaan belum diselesaikan. Guard bekerja dengan disarm; akibatnya kendaraan tidak lagi menahan arus. Karena itu hasil ini tidak boleh disebut penerimaan 100% atau hold yang andal pada seluruh kondisi. Prioritas berikutnya adalah menelusuri gangguan aliran sensor tersebut dan menyesuaikan waktu injeksi fixture fault agar benar-benar menguji fase sesudah start. Validasi sensor fisik dan noise berkorelasi tetap diperlukan.
