# 39 — Benchmark fase kualifikasi dan percepatan U-turn

1 November 2026. Status: enam run diterima, baseline dan kandidat pada ketiga jalur; kandidat dipertahankan karena seluruh pasangan lebih cepat. Tujuan: memangkas waktu misi sah dengan pemeriksa pelintasan penuh tetap aktif.

## Acuan dan batas

[Rulebook resmi](https://sauvc.org/rulebook/) diperiksa ulang: 2027.3.2, diperbarui 30 Oktober 2026. Syarat inti kualifikasi yang dibandingkan dengan arsip 2027.2.1 tetap sama. Catatan dan batas audit: [pemeriksaan sumber](../doc/sources/rulebook-2027.3.2-check.md). Fixture/metadata simulator pada benchmark tetap 2027.2.1; hasil ini tidak membuktikan migrasi seluruh ARENA ke versi terbaru.

Waktu yang dibandingkan: start hingga seluruh badan melintasi gate kedua kali (`elapsed`) dan start–surface tambahan proyek. Persiapan kalibrasi sebelum thrust tetap dicatat terpisah.

## Perubahan kandidat

Riwayat controller baseline menunjukkan U-turn sekitar 6,5 detik. Batas yaw saat TURN adalah 0,5 rad/s, sedangkan jalur kontrol/allocator sudah membatasi permintaan fisik sampai 0,7 rad/s. Kandidat menggunakan batas 0,7 rad/s khusus TURN dinamis dengan gain akhir tetap 1,8. Kontrol ideal tetap memakai nilai sebelumnya. Tidak mengubah geometri gate, margin pelintasan/clearance 0,6 m, massa, thrust maksimum, hydrodynamics atau estimator.

147 tes unit lulus. Tes tambahan memeriksa batas permintaan yaw dinamis, taper saat mendekati sudut akhir dan perilaku ideal sebelumnya. Uji runtime tetap diperlukan untuk menilai waktu aktual, kestabilan heading dan kontak.

## Matriks berpasangan

Baseline dijalankan sebelum source diubah; kandidat dijalankan setelah build. Masing-masing serial: lane 1 seed 42; lane 2 seed 91 dengan yaw awal 0,08 rad; lane 3 seed 7 dengan offset lateral 0,15 m. Arus nol, cahaya normal, prior error nol. Satu run per profil/kondisi: ini perbandingan fixture, belum statistik keandalan atau benchmark kendaraan nyata. Kedua tahap menyimpan manifest source, kondisi, perintah, riwayat fase, trajectory dan hasil referee. Diagnostik umur sensor/jeda penerimaan tetap aktif.

## Hasil

| Jalur | Pelintasan kedua baseline → kandidat (s) | Start–surface baseline → kandidat (s) | U-turn baseline → kandidat (s) |
|---|---|---|---|
| lane1 | 24.410 → 22.848 | 27.470 → 25.942 | 6.500 → 4.800 |
| lane2 | 24.686 → 22.748 | 27.746 → 25.842 | 6.548 → 4.800 |
| lane3 | 24.554 → 22.778 | 27.648 → 25.838 | 6.498 → 4.800 |

Pelintasan kedua lebih cepat 1,562–1,938 detik (sekitar 6,4–7,9% pada pasangan ini). Start–surface lebih cepat 1,528–1,904 detik. Start–stop kandidat 30,292–30,976 detik, dibanding baseline 31,894–32,672 detik; waktu settling/referee menyebabkan selisih stop tidak sama dengan selisih U-turn. Galat XY maksimum kandidat 3,30–3,74 cm, masih di bawah batas 20 cm. Semua kasus lulus referee untuk pelintasan penuh dua kali, surface/stop, kualitas kalibrasi sebelum thrust, sensor-only control, gaya akhir nol dan shutdown bersih.

Bukti: [verification.json](../ros2_ws/evidence/qualification-speed-2027/verification.json). Tersimpan perintah, hash laporan, waktu setiap fase dan manifest kedua tahap. Satu-satunya source yang berbeda adalah `qualification.py` dan tesnya; file kondisi setiap pasangan identik. Hash kandidat cocok dengan implementasi pada pemeriksaan akhir. Build dan 147 tes unit lulus.

Perubahan batas TURN 0,7 rad/s dipertahankan. Ini permintaan yaw untuk model simulator, bukan kalibrasi kemampuan putar AUV nyata. Angka tidak membuktikan optimum global atau konsistensi statistik: hanya tiga pasangan, arus nol dan kondisi terang. Pengulangan/arus/kondisi persepsi lain serta validasi hardware masih diperlukan. Penyebab stale_sensors spontan historis belum teridentifikasi. Matriks fault laporan 38, GUI dan misi ARENA penuh tidak diulang pada tahap ini.
