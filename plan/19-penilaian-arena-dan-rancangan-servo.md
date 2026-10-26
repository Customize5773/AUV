# Penilaian ARENA dan rancangan pelepas payload

Tanggal: **25 Oktober 2026, Asia/Jakarta**. Scope: bukti bola/payload pada simulator, rincian skor attempt, dan konsep mekanik servo. Tidak ada perintah hardware, perubahan PWM atau pengujian servo fisik.

## Acuan dan cara menghitung

[Rulebook resmi](https://sauvc.org/rulebook/) diperiksa pada tanggal di atas: 2026 v6.1.0. Modul [arena_scoring.py](../ros2_ws/src/sauvc_sim/sauvc_sim/arena_scoring.py) memisahkan perhitungan poin dari keberhasilan latihan yang lebih ketat. Hasil tersedia pada `score` di `/sauvc/arena/result`, dengan `scoring_policy=strict_training_abort`.

| Komponen | Perhitungan |
| --- | --- |
| Navigation | 15 setelah pelintasan seluruh badan |
| Target Acquisition | Blue 30; red dengan pinger 50; red lain 10; hanya bola pertama |
| Communication & Localization | 20 untuk setiap bola flare yang jatuh; tambahan 60 bila ketiganya sesuai urutan |
| Target Reacquisition | 60 bila bola yang sama diambil setelah pelintasan gate tambahan dan tetap dibawa sampai akhir |
| Surface | Tambahan 5 ketika surface benar-benar teramati |
| Waktu | `max(0, 900−run_time)*0.03` jika Navigation dan sedikitnya satu tugas lain memperoleh poin |
| Kontak | Gate −2, lantai/dinding −5, kontak badan/luar drum −5 |
| Automatic abort | Akumulasi kontak lantai/dinding >10 detik atau lima episode kontak |

Kontak kontinu tidak dihitung ulang sebagai kontak baru setiap frame. Dalam simulasi, kontak lantai/dinding yang bersamaan dikelompokkan menjadi satu episode; ini asumsi penghitungan yang perlu disamakan dengan keputusan juri. Bonus ukuran/berat tidak otomatis dimasukkan karena memerlukan inspeksi kendaraan dan kelulusan kualifikasi. Nilai total ini adalah skor attempt simulator, bukan pengesahan hasil kompetisi.

Ada ketidakkonsistenan di contoh rulebook: jumlah komponen contoh 4 adalah 85, sementara total tertulis 105; contoh abort 3/5/6 tidak mencantumkan bonus waktu walaupun paragraf Timing Bonus berlaku pada akhir attempt. Implementasi mengikuti tabel poin dan formula, bukan menyalin total contoh tersebut. Tes mencatat pilihan ini secara eksplisit. Konfirmasi penyelenggara diperlukan jika interpretasi penilaian lomba berbeda.

## Integrasi bukti fisik

Referee tidak memberikan poin hanya karena controller meminta release. Bola flare harus turun >12 cm dari posisi tertahan setelah kontak legal. Payload pertama harus teramati di bagian dalam drum dekat dasar selama >0,5 detik. Poin acquisition tidak bergantung pada penyelesaian flare karena rulebook mengizinkan tugas setelah Navigation dalam urutan berbeda. Keberhasilan misi latihan tetap mensyaratkan ketiga flare, blue drum, surface dan stop.

Latihan tetap abort pada kontak gate/lantai/dinding/drum, flare salah urutan atau surface sebelum seluruh target latihan selesai. Ledger mempertahankan poin yang sudah diperoleh sebelum abort. Karena latihan lebih ketat, ledger tidak berarti kendaraan akan terus berjalan melalui seluruh penalti yang diizinkan rulebook; automatic-abort 10 detik/lima kontak juga diuji terpisah pada modul penilaian.

Perhitungan red-pinger dan reacquisition tersedia dan diuji dengan event sintetis. Dunia latihan belum mempunyai pinger atau mekanisme pickup/retensi fisik; runtime tidak menerbitkan bukti reacquisition dan tidak memberikan poin tersebut. Jangan menyebutnya misi empat tugas SAUVC lengkap. Komponen poin utama misi yang tersedia adalah Navigation + flare + blue drum + bonus waktu/surface.

Mekanisme bola simulator tetap penyangga virtual yang dilepas setelah kontak, lalu gravitasi/collision menggerakkan bola. Ini tidak memodelkan rak servo, tiang lentur, drag atau buoyancy bola di air. Uji fisika khusus mengatur pose AUV untuk mengisolasi mekanisme; misi penuh tidak memakai teleport.

## Rancangan servo

[Dokumen mekanik](../mechanical/payload-servo/README.md) dan [model OpenSCAD](../mechanical/payload-servo/dropper.scad) menyediakan konsep satu bola: tabung ID 48 mm, rak putar dan pivot untuk servo. Rancangan menampung bola sampai 45 mm, dengan posisi tertutup dan terbuka sekitar 120°. Offset titik pelepasan harus diukur dan dimasukkan kembali ke controller.

Ukuran bracket, spline servo, endpoint PWM, catu daya, seal, bearing dan pengujian retensi belum difinalisasi karena perangkat belum ditentukan. OpenSCAD tidak tersedia di lingkungan ini sehingga file belum dirender/diuji fabrikasi. Tidak ada klaim servo nyata telah bekerja. Daftar uji meja dan uji basah ada di dokumen mekanik.

## Bukti penerimaan

Bukti lokal disimpan di `ros2_ws/evidence/arena-score-servo/`. Build dan 76 tes lulus; tes meliputi komponen poin, contoh rulebook beserta ketidakkonsistenannya, bola pertama, retensi pickup, kontak kontinu/berulang, akhir attempt, poin pada abort, dan integrasi bola teramati.

Jam skor simulator dimulai pada event `START` referee (penempatan awal kendaraan), dan berhenti saat surface pertama atau abort, sehingga waktu menunggu startup ikut tercatat. Ini berbeda dari metrik start–surface kualifikasi; durasi skor tidak diambil dari waktu stop. Event skor tidak diberikan kepada controller sebagai koordinat target.


Penerimaan runtime baru:

- [Misi penuh](../ros2_ws/evidence/arena-score-servo/nominal.json): `DONE`/`COMPLETE`, tiga bola flare jatuh, payload menetap, surface dan stop; skor **190,3241** = 15 + 30 + 60 + 60 + 5 + 20,3241, penalti nol. Waktu skor 222,530 s. Harness pemeriksaan tambahan menghitung ulang total dari timestamp event START/SURFACE.
- [Uji fisika](../ros2_ws/evidence/arena-score-servo/physics.json): bola tertahan stabil, flare jatuh setelah kontak, payload menetap >0,5 s dan request release berulang tidak mengembalikan bola ke AUV. Pose hanya diatur oleh harness uji mekanisme ini.
- [Putus perintah](../ros2_ws/evidence/arena-score-servo/abort.json): `ABORT`, perintah nol, posisi stasioner dan skor final nol tanpa bonus surface.

Ketiganya menutup bersih tanpa kill paksa. [verification.json](../ros2_ws/evidence/arena-score-servo/verification.json) mencatat hasil, ruang lingkup dan hash sumber. Dua perbaikan edge case terakhir (surface parsial dan timestamp tidak valid) diverifikasi oleh suite final 76 tes; misi penuh berjalan sebelum dua perubahan cabang tersebut, dengan jalur nominal yang sama. Pengujian full ARENA masih menggunakan gerak ideal/odometri ground truth. Tidak ada klaim mekanisme servo telah diuji secara fisik.

Tindak lanjut: [laporan 20](20-pinger-pickup-dan-servo-simulator.md) menambahkan mode simulator `extended` untuk sumber pinger, pickup berbasis kontak dan retensi. Keterangan tidak tersedianya bukti runtime pada laporan 19 adalah snapshot sebelum mode tersebut; status fabrikasi/servo fisik tetap belum diuji.
