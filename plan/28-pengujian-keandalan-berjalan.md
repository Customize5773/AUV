# 28 — Pengujian keandalan: dijeda

Status: **dijeda atas permintaan pengguna, “rehat dulu”**. Pengujian tidak dilanjutkan otomatis. Laporan 27 tetap snapshot penerimaan sebelum perubahan persepsi sesi ini.

## Pekerjaan tersimpan

Perubahan WIP pada object_detection.py menambahkan kontras biru lokal untuk pole tipis yang blur, menolak pemulihan pole terpotong, memilih pasangan marker Square dan menghindari label flare ganda pada marker. Tes unit bertambah menjadi 110 dan lulus. Pengujian label perturbasi pada frame tersimpan lulus 98/98, sebelumnya 97/98. Ini belum membuktikan estimasi jarak/posisi atau keberhasilan kontrol.

Enam kualifikasi dinamis lulus: tiga jalur nominal dan tiga penempatan dengan offset lateral ±0,15 m serta yaw ±0,10 rad. Offset penempatan diketahui estimator; ini bukan uji ketidakpastian prior XY. Parameter tersedia pada qualification-summary.json. Semua memakai sensor seed 42 dan tanpa arus.

**Regresi ARENA belum selesai dan belum boleh dinyatakan diterima.** Tiga run baru selesai dengan ABORT `flare_contact_did_not_drop_ball`: a0-blue1-repeat, a1-blue2-alt dan a2-blue3. Output/gaya, tracking, target controller dan referee tersimpan. Kelulusan label 98/98 tidak menggantikan kegagalan closed-loop tersebut. Dua run pertama memakai detector sebelum guard partial terakhir; hash source setiap run tercatat.

Run a3-blue4-alt dihentikan karena pengguna meminta rehat; jangan dihitung sebagai kegagalan misi alami. a4-pinger1 belum dimulai. Driver sweep dihentikan sebelum server Gazebo ditutup lewat layanan server_control agar tidak memulai run berikutnya.

## Lanjutkan nanti

1. Telusuri regresi kontak flare akibat perubahan persepsi, termasuk bbox/height dan proyeksi metrik serta landmark yang terkunci. Penyebab spesifik belum dibuktikan.
2. Perbaiki dengan mempertahankan batas kontak, pelintasan dan keselamatan; kelulusan label saja tidak cukup.
3. Ulangi penerimaan ARENA lengkap pada source final yang sama dan folder bukti baru. Jangan menimpa percobaan gagal atau memasukkan run yang dihentikan pengguna ke statistik keberhasilan.
4. Selesaikan matriks blue drum 1–4 dan fixture pinger baru, lalu rangkum tingkat keberhasilan, galat dan waktu beserta jumlah sampelnya.

Bukti lokal: [paused-status.json](../ros2_ws/evidence/reliability-2027/paused-status.json), [ringkasan kualifikasi](../ros2_ws/evidence/reliability-2027/qualification-summary.json), [ringkasan ARENA](../ros2_ws/evidence/reliability-2027/arena-summary.json). Folder evidence diabaikan Git. Snapshot detector sebelum perubahan disimpan sebagai detector-before-reliability.py; source WIP tetap tersimpan, belum di-rollback. Driver tersimpan untuk referensi, tetapi memiliki guard menolak output lama dan bukan perintah resume langsung.
