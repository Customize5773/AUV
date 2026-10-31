# 36 — Investigasi stale_sensors dan uji gangguan saat misi aktif

1 November 2026. Tujuan: mempersempit penyebab gangguan yang bisa menggagalkan misi tercepat, tanpa melonggarkan pengaman. Status: diagnostik dan pengujian selesai; **penyebab gangguan spontan lama belum teridentifikasi atau dinyatakan teratasi**.

## Temuan pada bukti lama

Pada percobaan gagal laporan 35, lompatan timestamp simulasi terbesar adalah 4,930 s untuk lintasan, 4,904 s untuk sensor/telemetry, 5,702 s untuk estimasi dan 5,762 s untuk timestamp sensor yang dilaporkan health. Ini bukan pengukuran langsung jeda penerimaan wall-clock. Health yang berulang dengan timestamp sensor tetap juga tidak berarti publisher health berhenti. Data lama tidak cukup untuk menetapkan apakah masalah bermula pada bridge, penjadwalan proses, atau host. Kegagalan lama tetap dipertahankan; dua pengulangan bersih tidak menghapusnya.

## Perubahan terbatas

- Health estimator menambahkan `sensor_age_wall_s`: waktu monotonic sejak callback sensor terakhir. Batas stale tetap 0,3 detik dan keputusan disarm tidak berubah.
- Penguji kualifikasi menyimpan `reception`: jumlah paket, waktu penerimaan terakhir, jeda maksimum dan kejadian jeda ≥0,1 detik untuk truth, sensor, telemetry, estimasi dan health. Waktu simulasi dan waktu penerimaan disimpan terpisah. Maksimum 1.000 kejadian; overflow dihitung, bukan disembunyikan. Ambang pencatatan bukan ambang abort.
- Snapshot diagnostik diambil sebelum penguji sengaja menghentikan simulator. Payload sensor tidak dimodifikasi; truth tetap khusus pemeriksa.
- Tidak ada perubahan gain, QoS, konfigurasi bridge, thruster, atau batas penerimaan. Tidak ditambahkan dependensi.

## Penerimaan

Build berhasil; **141 tes unit lulus**. Dua tes baru memeriksa perbedaan waktu simulasi/penerimaan, snapshot yang stabil, serta batas ukuran catatan.

| Kasus | Hasil | Drift hold 180 s | Umur paket maksimum di estimator selama misi/hold | Start–surface |
|---|---|---|---|---|
| Seed 91, arus lateral 0,02 m/s, pengulangan 1 | Lulus | 2,102 cm | 20,98 ms | 27,632 s |
| Seed 91, arus lateral 0,02 m/s, pengulangan 2 | Lulus | 2,098 cm | 14,02 ms | 27,378 s |
| Bridge dihentikan 1 s, tiga detik setelah DIVE | Respons fault lulus | Tidak menguji hold | Mencapai 1,002 s | Sengaja abort |

Dua run normal tidak memiliki health invalid sejak thrust pertama sampai akhir jendela hold. Pemeriksaan pelintasan, kualitas kalibrasi, akurasi, hold, disarm/gaya nol setelah injeksi fault akhir, dan shutdown lulus. Catatan penerimaan penguji memiliki beberapa jeda lebih besar daripada umur paket di estimator; jeda pencatat tidak boleh langsung disebut kehilangan sensor di pengendali.

Uji negatif memakai domain/partition terpisah dan hanya menghentikan PID bridge anak dari launch milik penguji. SIGCONT dikirim kembali melalui `finally`. Injeksi terikat kejadian DIVE, sehingga preflight yang lebih panjang tidak menggeser fault ke fase sebelum start. Jeda penerimaan sensor terukur 1,009 s; estimator melaporkan stale_sensors, misi ABORT, gaya akhir nol, shutdown bersih. Exit code checker adalah 1 karena misi sengaja digagalkan; pemeriksa respons fault terpisah lulus. Ini membuktikan respons pengaman dan kegunaan diagnostik, **bukan bukti bahwa bridge merupakan penyebab kegagalan historis**.

Bukti: [verification.json](../ros2_ws/evidence/stale-investigation-2027/verification.json), [analisis gap lama](../ros2_ws/evidence/stale-investigation-2027/historical-gaps.json), [injeksi](../ros2_ws/evidence/stale-investigation-2027/bridge-injection.json). Folder yang sama menyimpan perintah, hash source/laporan, log build/tes, raw report dan pemantauan host. Source cocok dengan manifest kedua run saat verifikasi.

## Batas dan tindak lanjut

Gangguan spontan tidak muncul kembali dalam dua pengulangan; belum ada dasar untuk mengganti konfigurasi bridge atau menyebut masalah selesai. Gunakan diagnostik yang kini otomatis tersimpan pada pengujian kualifikasi berikutnya untuk menghubungkan umur paket estimator dengan jeda penerimaan dan kondisi host ketika gangguan benar-benar terjadi. Jangan mengulang hold tanpa batas sebagai pengganti kemajuan misi.

Uji ini headless; ARENA, GUI/POV, perangkat nyata dan matriks fault lengkap belum diuji ulang. Fault bridge setelah DIVE hanya satu skenario tambahan, tidak menggantikan matriks lama. Sasaran utama tetap waktu misi sah dan tingkat keberhasilan sebelum transfer ke AUV nyata.
