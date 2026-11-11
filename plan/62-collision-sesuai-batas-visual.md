# 62 — Collision sesuai batas visual AUV

Tanggal: 12 November 2026. Kelanjutan laporan 60–61: collision box lama lebih panjang 4,08 cm di tiap ujung X daripada visual.

## Perubahan

Batas mesh OBJ terpaket menjadi acuan tunggal `vehicle_geometry.py`, melalui metadata konversi yang dibulatkan sesuai enam desimal ekspor OBJ. Tes membaca vertex OBJ sebenarnya dan membandingkannya dengan metadata serta ukuran collision SDF.

| Sumbu FLU | Minimum (m) | Maksimum (m) | Ukuran (m) |
|---|---:|---:|---:|
| X, depan | −0,259243 | 0,259243 | 0,518486 |
| Y, kiri | −0,193438 | 0,193438 | 0,386876 |
| Z, atas | −0,100000 | 0,100000 | 0,200000 |

Collision `hull` tetap box, kini mengikuti AABB mesh tersebut. Spawn kualifikasi menyentuh dinding berdasarkan proyeksi badan pada yaw awal; x nominal berubah dari 0,30 menjadi 0,259243 m. Prior estimator memakai geometri yang sama dengan heading sensor, tanpa membaca pose ground truth.

Envelope referee memutar seluruh sudut hull menurut roll/pitch/yaw. Origin kamera depan x=0,32 m dan kamera bawah z=−0,12 m tetap untuk proyeksi gambar, tetapi tidak dimasukkan sebagai volume fisik: keduanya sensor frame tanpa housing collision. Pemeriksaan start, pelintasan penuh kedua arah, target-zone exit dan surface memakai batas hull baru; envelope tool ARENA tetap ditambahkan terpisah. Toleransi referee, guard, speed, jarak U-turn dan kontrak sensor tidak dilonggarkan.

Gripper tetap pada `(−0,20, 0, −0,40) m` dari laporan 59, termasuk dudukannya. Tinggi hull tidak berubah sehingga clearance hull–rim nominal 2 cm saat pickup tetap. Mesh visual, kamera, massa/inertia, buoyancy, drag dan matriks thruster tidak diubah pada tahap ini.

## Verifikasi

Build lulus; **183 tes simulator lulus**, termasuk tiga tes geometri baru: vertex OBJ versus collision, start ber-yaw dan prior estimator, serta batas pelintasan penuh dua arah dengan selisih ±1 mm. Fixture yang sebelumnya memakai x=0,30 m disesuaikan; start lama yang tidak menyentuh dinding kini ditolak. Pemeriksaan pitch/roll tetap diuji.

Bukti disimpan di [collision-fit-20261112](../ros2_ws/evidence/collision-fit-20261112/): [unit-tests.log](../ros2_ws/evidence/collision-fit-20261112/unit-tests.log), [build.log](../ros2_ws/evidence/collision-fit-20261112/build.log), dan [hash source/aset](../ros2_ws/evidence/collision-fit-20261112/source-hashes.json). Log tes awal yang gagal akibat fixture lama juga dipertahankan.

Dua kualifikasi dinamis diterima oleh checker dan verifier akurasi:

| Kasus | Start–pelintasan kedua | Start–surface | Start–stop | Galat XY maks. |
|---|---:|---:|---:|---:|
| Jalur 1 nominal, GUI + dua POV | 22,874 s | 26,034 s | 30,794 s | 0,033764 m |
| Jalur 3, yaw 0,22 rad, offset lateral 0,10 m, headless | 22,770 s | 25,898 s | 30,794 s | 0,034617 m |

Keduanya memakai seed sensor 42, arus nol, prior nol; seluruh badan melewati gate dua kali, surface, stop, gaya akhir nol dan shutdown bersih. [Verifikasi kualifikasi](../ros2_ws/evidence/collision-fit-20261112/qualification-verification.json). Waktu bukan pembandingan berpasangan untuk mengklaim peningkatan kecepatan.

ARENA extended juga **diterima pada percobaan pertama**: dinamis tujuh thruster, scene variant 1, blue drum 3, pinger drum 4, urutan Y–B–R, seed 91, arus/prior nol. GUI dan kedua POV terverifikasi.

| Pemeriksaan extended | Hasil |
|---|---|
| Misi | DONE; seluruh flare jatuh, pelintasan penuh, acquisition, keluar penuh target zone, pickup, surface Square dan stop |
| Skor simulator | 290,77908 poin; penalti 0; acquisition +50, retrieval +60, Square +20 |
| Thrust–surface | 207,364 s simulasi |
| Payload | Kontak/bola masuk drum pinger 4, kemudian pickup bola `payload` yang sama |
| Retensi | 1.330 snapshot attachment konsisten dari grasp +1 s sampai STOPPED; tanpa retention lost |
| Estimasi | Galat XY maks. 0,147661 m; depth 0,004652 m; yaw 0,013038 rad; seluruhnya di bawah batas referensi |
| Kendali | Sensor-only, pose referee terisolasi, kontrak sensor/DVL dan tujuh thruster lulus; gaya akhir nol dan stationary |
| Shutdown | Bersih; PID launch ketiga run tidak tersisa |

Bukti: [extended.json](../ros2_ws/evidence/collision-fit-20261112/extended.json), [verification.json](../ros2_ws/evidence/collision-fit-20261112/verification.json), [verifier](../ros2_ws/evidence/collision-fit-20261112/verify.py), [conditions.json](../ros2_ws/evidence/collision-fit-20261112/conditions.json), [cleanup.json](../ros2_ws/evidence/collision-fit-20261112/cleanup.json). Tidak ada percobaan runtime gagal atau pengulangan untuk memperoleh hasil ini. Graphify diperbarui setelah perubahan kode.

## Mengulang penerimaan

Dari `/home/rasya/AUV/ros2_ws`, gunakan nama output baru agar bukti penerimaan ini tetap tersimpan:

```bash
bash tools/ros.sh python tools/check_qualification.py --vehicle-model dynamic --gui --pov --output evidence/collision-fit-repeat/qualification.json
bash tools/ros.sh python tools/check_qualification.py --vehicle-model dynamic --lane 3 --yaw .22 --lateral-offset .10 --output evidence/collision-fit-repeat/qualification-yaw.json
bash tools/ros.sh python tools/check_arena.py --vehicle-model dynamic --extended --scene-variant 1 --blue-drum 3 --pinger-drum 4 --order Y-B-R --gui --pov --conditions evidence/collision-fit-20261112/conditions.json --output evidence/collision-fit-repeat/extended.json
```

Jalankan satu per satu, setelah run sebelumnya selesai menutup Gazebo.

## Batas

Collision sesuai batas terluar visual, bukan mengikuti permukaan tiap panel atau rongga rangka. Ukuran ini tetap normalisasi latihan yang diizinkan pengguna; ukuran AUV fisik belum dikonfirmasi. Housing kamera fisik dan geometri mekanisme nyata belum dimodelkan. Massa/inertia dan koefisien air/thruster masih pendekatan latihan; hasil simulasi tidak membuktikan kalibrasi atau performa AUV nyata.
