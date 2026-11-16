# 68 — Ketahanan optik air dan kehilangan depth

14 November 2026, Asia/Jakarta. Melanjutkan laporan 67: uji kehilangan depth secara selektif, lalu ukur batas deteksi pada atenuasi lebih tinggi. Parameter gaya, kecepatan, freshness, guard dan referee tidak diubah.

## Uji depth selektif

Penguji menjalankan misi kualifikasi dinamis dengan efek 0,025/m. Setelah thrust dimulai, bridge gambar asli dijeda menggunakan SIGSTOP; bridge pengganti hanya meneruskan RGB asli dari sensor Gazebo, tanpa depth. Bridge clock/sensor/kendali tetap aktif. Ini injeksi pada transport nyata simulator, bukan meminta controller mengabaikan kamera.

Setelah grace 0,5 s untuk paket yang masih diproses, observer menghitung RGB yang terus diterima, depth dan output filtered yang berhenti. Controller harus ABORT karena `stale_camera`; pemeriksa normal sengaja keluar 1 karena misi terputus. Verifier fault menilai alasan abort, zero command, posisi diam, gaya tujuh thruster nol dan shutdown, bukan kelulusan misi lengkap. Bridge asli di-SIGCONT untuk cleanup; bridge pengganti juga dihentikan dan harus keluar bersih.

Run awal lulus: 25 pesan RGB depan dan 26 bawah, depth/output keduanya nol selama jendela pengamatan; ABORT sekitar 2,05 s wall setelah injeksi. Thrust pertama 26,554 s simulasi, injeksi 36,054 s. [Bukti fault awal](../ros2_ws/evidence/water-robustness-20261114/depth-verification.json).

## Temuan batas sebelum perbaikan

| Kasus | Hasil awal |
|---|---|
| Kualifikasi 0,05/m, jalur 2, yaw 0,08 | ABORT `gate_lost`, stop/gaya nol/shutdown lulus |
| Kualifikasi 0,10/m, jalur 3, offset 0,15 m | ABORT `gate_lost`, lihat laporan run asli |
| ARENA extended 0,05/m | ABORT `mission_or_state_timeout` pada APPROACH_FLARE; stop/gaya nol/shutdown lulus |

[Summary awal](../ros2_ws/evidence/water-robustness-20261114/runner.json) dan seluruh log kegagalan tetap disimpan. Efek air lebih kuat menggeser rasio RGB sehingga mask oranye asli tidak menemukan gate. Replay gambar gate simulator dengan atenuasi sintetis menunjukkan koreksi warna terbatas dapat memulihkan pasangan tiang; ini diagnosis pendukung, bukan bukti perbaikan misi sebelum penerimaan ulang.

## Perbaikan terbatas gate kualifikasi

[gate_detection.py](../ros2_ws/src/sauvc_sim/sauvc_sim/gate_detection.py) memprioritaskan deteksi asli. Jika gagal dan rata-rata sampel gambar menunjukkan cast biru/hijau, ia mencoba satu koreksi grey-world dengan gain kanal dibatasi 0,5…2. Perhitungan pasangan tiang, rasio geometri, span, arah dan jarak menggunakan kode yang sama. Input hanya RGB; controller tidak menerima parameter air atau depth.

Tes baru memeriksa pemulihan gate pada cast air, range/bearing, BGR dan padding baris; satu tiang, ubin dan latar air kosong tetap ditolak. **193 tes unit lulus**. Fallback tidak mengubah deteksi objek flare/drum ARENA; kegagalan ARENA 0,05/m belum dinyatakan selesai.

## Penerimaan ulang

Source, aset dan binary dibekukan pada [manifest akhir](../ros2_ws/evidence/water-robustness-20261114/final/source-sha256.json). Antara batch awal dan akhir hanya `gate_detection.py` serta tesnya yang berubah.

| Pengujian akhir | Hasil | Thrust–surface | Galat XY maksimum |
|---|---|---:|---:|
| Depth selektif, air 0,025/m | Lulus respons fault: ABORT, gaya nol dan cleanup | Bukan misi lengkap | Tidak dipakai sebagai syarat misi lengkap |
| Kualifikasi 0,05/m, jalur 2/yaw 0,08 | **Lulus**, sebelumnya `gate_lost` | 27,264 s | 1,76 cm |
| Kualifikasi 0,10/m, jalur 3/offset 0,15 | **Belum lulus**, tetap `gate_lost`; stop/gaya nol/shutdown lulus | — | Tidak dianggap kelulusan misi |
| Baseline jernih, jalur 2/yaw 0,08 | **Lulus** | 26,694 s | 3,31 cm |
| ARENA extended 0,025/m, layout 1, Y–B–R, pinger drum 4 | **Lulus**, 290,73330 poin, penalti 0, pickup/retensi dan Square | 208,890 s | 9,67 cm |

Depth fault pada revisi akhir kembali lulus: **26 pesan RGB di masing-masing kamera**, depth dan output nol setelah grace 0,5 s. Controller abort sekitar **2,10 s wall** setelah injeksi; semua command/gaya akhir nol dan shutdown bersih. Injection terjadi 9,436 s simulasi setelah thrust pertama. Tidak ada replay output atau auto-resume misi setelah depth dipulihkan untuk cleanup.

Seluruh run akhir shutdown bersih; PID launch dan bridge pengganti tidak tersisa. **Tiga misi lengkap diterima dan satu respons fault diterima; satu percobaan kualifikasi padat tidak diterima.** Verifier menyimpan `all_stress_missions_accepted=false` dan tidak mengubah kegagalan awal menjadi hasil lulus. [Verifikasi akhir](../ros2_ws/evidence/water-robustness-20261114/final/verification.json), [summary runner](../ros2_ws/evidence/water-robustness-20261114/final/runner.json).

Selain 193 tes unit, **12 replay negatif dari capture simulator** (dinding, ubin dan background air dengan variasi cast) tidak menghasilkan gate palsu. [Bukti replay negatif](../ros2_ws/evidence/water-robustness-20261114/negative-replay.json). Input RGBD/POV tidak diputihkan; koreksi hanya dipakai internal detektor gate saat fallback.

Kegagalan ARENA 0,05/m tetap terbuka: skor sempat mencatat Navigation, kontak flare kuning dan merah, tetapi flare biru tidak tercatat sebelum timeout. Ini bukti tugas belum lengkap, bukan konfirmasi unik salah klasifikasi warna. Perbaikan gate kualifikasi tidak dinyatakan menyelesaikan persepsi/pendekatan flare ARENA.

Tidak ada peningkatan kecepatan yang diklaim. Pengujian headless terpilih ini bukan pengulangan seluruh matriks 18 kasus atau bukti kemampuan seluruh rentang koefisien 0…0,5/m.

## Batas

Ini pengujian simulator dan koreksi warna heuristik, bukan kalibrasi air nyata atau bukti keandalan semua pencahayaan/layout. Gain dibatasi agar perubahan warna tidak bebas membesar; geometri dan pemeriksa independen tetap diperlukan. Nilai atenuasi bukan NTU. Default tetap nol; profil air ringan 0,025/m tetap satu-satunya profil ARENA yang ditargetkan untuk penerimaan pada revisi ini. Ketahanan ARENA pada air lebih kuat, refraksi, partikel dan validasi fisik masih terbuka.

## Mengulang dan tindak lanjut

Dari `ros2_ws`, script fault dan runner beserta kondisi disimpan dalam direktori bukti. Gunakan direktori baru untuk percobaan baru; script fault menolak menimpa laporan yang telah ada. Untuk pemeriksaan bukti akhir saat source masih sesuai manifest:

```bash
bash tools/ros.sh python evidence/water-robustness-20261114/final/verify.py
```

Cara menjalankan mode air ringan tetap [CARA-RUNNING.md](../ros2_ws/CARA-RUNNING.md). Prioritas berikutnya adalah diagnosis persepsi/proyeksi flare pada ARENA 0,05/m; kualifikasi 0,10/m juga belum didukung oleh detektor saat ini. Jangan menaikkan profil ARENA yang direkomendasikan sebelum regresi tersebut lulus.

Kelanjutan 16 November: [laporan 69](69-rulebook-dan-perbaikan-halo-biru-arena.md) mendiagnosis halo biru palsu dan menerima dua ARENA 0,05/m serta regresi 0,025/m setelah koreksi kontras. Kegagalan awal di laporan ini tetap riwayat; kualifikasi 0,10/m belum terselesaikan.

Kelanjutan: [laporan 70](70-kualifikasi-optik-010-dan-median-warna.md) menyelesaikan kasus kualifikasi 0,10/m pada tiga jalur terpilih; kegagalan yang tercatat di sini tetap menjadi bukti historis.
