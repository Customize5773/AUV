# Penerimaan gripper pendek dan tetap

18 November 2026. Mengikuti pilihan pengguna: **tetap pendek, di tengah body, tanpa mekanisme memanjang**. Laporan ini menggantikan versi slider pada [laporan 74](74-gripper-tengah-pendek-dan-bola-awal.md) sebagai status aktif. Pengujian kendaraan fisik dikecualikan.

Gripper memakai fixed joint pada `(0, 0, −0,18) m`; pusat bola 8 cm di bawah hull. Payload awal memakai titik dan link yang sama, ditahan joint pemuatan sampai release. Tidak ada slider. Kamera bawah tetap berada 16 cm di depan pusat body. Bukaan collision jari 42 mm tetap dipertahankan agar bola 40 mm dapat jatuh.

Penerimaan tambahan pada source yang sama serta diagnosis reach ada di [laporan 76](76-diagnosis-reach-fixed-dan-fixture-tambahan.md).

## Perbaikan dan hasil

Fixture tes yang masih mengimpor konstanta slider telah diselaraskan dengan gripper tetap. Pemeriksaan retensi tetap memakai transform roll/pitch/yaw penuh dan toleransi 7,5 cm; bola berjarak 8 cm atau attachment hilang tetap ditolak. Plugin telemetri juga menunggu link gripper tersedia sebelum membaca pose.

Build plugin/paket selesai dan **197 tes lulus**. Manifest **98 file source, konfigurasi, binary dan aset** cocok sebelum/sesudah penerimaan. Tidak ada perubahan source produksi selama run.

| Uji revisi fixed | Hasil |
|---|---|
| Kualifikasi dinamis, jalur 3, offset 0,15 m, seed 42, atenuasi 0,10/m | DONE; gate kedua **24,948 s**, thrust–surface **28,076 s**, thrust–stop **33,006 s**; galat XY maksimum **1,74 cm** |
| ARENA blue drum dinamis, seed 91, atenuasi 0,05/m, Gazebo dan dua POV | DONE; **210,14872 poin**, thrust–surface **228,376 s**, penalti nol; galat XY maksimum **5,58 cm** |
| Extended/pickup | **Ditolak sesuai batas konfigurasi**, sebelum thrust: `fixed_gripper_unreachable`; semua sampel gaya thruster nol, deployment tetap ditahan, perpindahan **0 m** |
| Posisi awal bola | **110 snapshot** menunjukkan attachment aktif, payload belum dilepas, bola berimpit dengan titik grip pada resolusi telemetri |

Kedua misi lengkap memenuhi pemeriksa yang sudah ada: estimator sensor, tujuh thruster, posisi terhadap ground truth independen, stationary, command/gaya akhir nol dan shutdown bersih. Blue drum membuktikan pelintasan gate, tiga bola flare jatuh, payload masuk dan settling di blue drum, bonus Square serta surface–stop. Dua jendela POV terverifikasi, rekaman encoder keluar 0, dan cleanup viewer tidak dipaksa.

![Render gripper pendek tetap dengan bola awal](../ros2_ws/evidence/gripper-fixed-20261118/initial.png)

Gambar berasal dari spectator Gazebo. Lampu inspeksi hanya dipakai pada world capture, bukan arena penerimaan. Bentuk fisik, servo dan kemampuan menjepit belum divalidasi.

## Yang masih kurang

**Pickup dari dasar drum belum didukung dengan gripper pendek tetap.** Untuk pendekatan mendatar saat ini, pusat bola di dasar adalah floor + 0,04 m. Dengan offset gripper −0,18 m, pusat body perlu floor + 0,22 m; bawah hull menjadi floor + 0,12 m, sedangkan bibir drum floor + 0,32 m. Clearance adalah **−0,20 m**. Karena itu profil extended ditolak sebelum bergerak; penolakan ini bukan kelulusan pinger/pickup. Tidak mengubah drum, menonaktifkan collision, menambah slider atau memindahkan bola untuk membuat hasil seolah lulus.

Mekanisme/strategi pickup yang kompatibel dengan pilihan tetap pendek masih memerlukan keputusan desain. Tidak ada klaim bahwa seluruh kemungkinan pendekatan sudah dievaluasi. Hasil di atas hanya fixture terpilih pada simulator; kapal nyata, kalibrasi dan semua kondisi kolam belum terbukti.

Rulebook yang diperiksa pada 18 November tetap **2027.3.2**, tanpa perubahan terhadap arsip resmi. Batas jangkauan di atas adalah batas model/strategi latihan, bukan syarat mekanisme dari rulebook. [Bukti pemeriksaan](../doc/sources/rulebook-check-20261118.json).

## Bukti dan pengulangan

- [Verifikasi gabungan](../ros2_ws/evidence/gripper-fixed-20261118/verification.json) · [skrip verifikasi](../ros2_ws/evidence/gripper-fixed-20261118/verify.py) · [manifest](../ros2_ws/evidence/gripper-fixed-20261118/source-sha256.json).
- [Kualifikasi](../ros2_ws/evidence/gripper-fixed-20261118/qualification/mission.json) · [ARENA](../ros2_ws/evidence/gripper-fixed-20261118/blue/mission.json) · [video dua POV](../ros2_ws/evidence/gripper-fixed-20261118/blue/pov.mp4).
- [Penolakan extended](../ros2_ws/evidence/gripper-fixed-20261118/extended-rejected/verification.json) · [telemetri awal](../ros2_ws/evidence/gripper-fixed-20261118/initial-physics.json).
- [Tes](../ros2_ws/evidence/gripper-fixed-20261118/unit-tests.log) · [build](../ros2_ws/evidence/gripper-fixed-20261118/build.log) · [cara running](../ros2_ws/CARA-RUNNING.md).

```bash
cd /home/rasya/AUV/ros2_ws
bash tools/ros.sh python evidence/gripper-fixed-20261118/verify.py
```

Verifikasi di atas membaca bukti tersimpan dan menolak bila manifest source/binary/aset berubah; tidak menjalankan kendaraan. Untuk pengulangan misi baru, gunakan folder output baru dari panduan running.


Catatan revisi 19 November: controller kualifikasi kemudian dioptimalkan pada [laporan 78](78-optimasi-awal-kualifikasi-dinamis.md). Manifest dalam laporan ini merujuk source sebelum optimasi; verifikasi source aktif tersedia pada laporan 78.
