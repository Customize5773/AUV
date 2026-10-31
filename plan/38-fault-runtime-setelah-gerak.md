# 38 — Fault kamera, command dan aliran runtime setelah gerak

1 November 2026. Status: build dan 146 tes unit lulus; sembilan run runtime diterima (delapan respons fault dan satu misi normal). Kelanjutan laporan 37 untuk jadwal fault non-native; penyebab stale_sensors spontan historis tetap terbuka.

## Perubahan

`FaultSchedule` dipakai bersama runtime kualifikasi, command guard, dan runtime ARENA. Penghitung dimulai sekali dari perintah mission/cmd_vel nonnol yang finite; perintah nol selama preflight tidak mengaktifkan injeksi. Fault kualifikasi dipicu setelah delapan detik, ARENA setelah 12 detik. Penghitung tidak di-reset oleh perintah berikutnya. Batas freshness dan watchdog aktual tidak berubah.

Fault clock memakai timestamp paket clock yang masuk, sehingga tetap terputus setelah clock lokal konsumen membeku. Fault kamera, odometry dan contact tetap berupa pengabaian callback pada konsumen; ini bukan pemutusan perangkat nyata. Command loss menghentikan publikasi perintah misi. Controller freeze menggunakan SIGSTOP terhadap proses controller milik pengujian setelah thrust teramati +8 detik, lalu SIGCONT pada cleanup.

Log `FAULT_INJECTED` menyimpan jenis fault, waktu perintah pertama dan waktu injeksi. Penguji mencocokkannya dengan gaya thruster pertama >0,05 N: selisih waktu start <0,2 detik dan injeksi dalam delay hingga delay+0,3 detik (pencuplikan callback). Angka ini toleransi bukti injeksi, bukan pelonggaran timeout pengaman. Native fault dari laporan 37 tetap memakai jadwal tersendiri setelah pelepasan penahan.

Tes unit memeriksa preflight panjang, perintah nol/nonfinite, start yang tidak bergeser, clock loss, fault nonaktif, serta penolakan bukti injeksi yang tidak ada/salah jenis/terjadi sebelum thrust. Profil ideal controller_freeze tetap dapat memulai penghitung dari perintah gerak teramati; penerimaan tahap ini memakai model dinamis.

Matriks: camera_loss, command_loss, odom_loss, contact_loss, clock_loss, controller_freeze pada kualifikasi; satu kualifikasi normal; camera_loss dan command_loss pada ARENA. Pengujian serial, headless, dengan manifest source tetap. Tidak ada optimasi gain atau kecepatan pada tahap ini.

## Hasil akhir

| Kasus | Waktu injeksi sejak perintah gerak/thrust | Hasil |
|---|---|---|
| qualification-camera_loss | 8.092–8.092 s sejak perintah | Respons fault lulus, gaya nol |
| qualification-command_loss | 8.048–8.048 s sejak perintah | Respons fault lulus, gaya nol |
| qualification-odom_loss | 8.004–8.026 s sejak perintah | Respons fault lulus, gaya nol |
| qualification-contact_loss | 8.018–8.018 s sejak perintah | Respons fault lulus, gaya nol |
| qualification-clock_loss | 8.002–8.002 s sejak perintah | Respons fault lulus, gaya nol |
| qualification-controller_freeze | 8.002 s sejak thrust | Guard stop saat controller beku, gaya nol |
| qualification-nominal | — | Misi lengkap, start–surface 27,668 s |
| arena-camera_loss | 12.012–12.012 s sejak perintah | Respons fault lulus, gaya nol |
| arena-command_loss | 12.016–12.016 s sejak perintah | Respons fault lulus, gaya nol |

Seluruh run lulus verifikasi kalibrasi sebelum thrust, isolasi ground truth dari kontrol, dan shutdown bersih. Penilaian delapan fault berarti misi sengaja digagalkan dengan respons pengaman yang benar, bukan delapan misi berhasil sampai surface. Controller yang dibekukan dilepas kembali pada cleanup; guard tetap mengunci keluaran nol.

Bukti: [verification.json](../ros2_ws/evidence/runtime-faults-2027/verification.json). Folder yang sama memuat manifest source/library native, perintah, laporan mentah, log injeksi, build dan tes. Hash sesuai implementasi pada verifikasi akhir. Pemeriksaan jeda penerimaan dan umur sensor dari laporan 36 tetap tersedia pada penguji kualifikasi.

## Batas dan langkah berikutnya

Penyebab stale_sensors spontan pada run historis masih belum diketahui; kelulusan fault terkontrol tidak membuktikan gangguan itu telah hilang. ARENA odom/contact/clock, profil ideal, misi ARENA penuh, GUI/POV dan hardware belum diuji ulang pada revisi ini. Jadwal native dari laporan 37 tidak diubah di sini.

Tahap berikutnya dapat kembali ke benchmark fase kualifikasi untuk mencari waktu yang bisa dipangkas, dengan diagnostik dan penerimaan pelintasan penuh tetap aktif. Hold panjang tetap pengujian diagnostik seperlunya, bukan sasaran lomba utama.
