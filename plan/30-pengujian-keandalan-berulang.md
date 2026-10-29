# 30 — Pengujian keandalan berulang

29 Oktober 2026. Melanjutkan [penerimaan laporan 29](29-validasi-flare-dan-penerimaan-ulang.md). **Pengujian selesai: matriks 18 kasus menyelesaikan seluruh tugas misi, 14 memenuhi seluruh kriteria penerimaan dan empat kasus arus ditolak. Satu pengulangan tambahan kasus prior posisi menyelesaikan misi tetapi gagal akurasi.** Tujuan tahap ini mengukur batas keberhasilan, bukan menyimpulkan keandalan kolam nyata dari satu fixture yang lulus.

Tindak lanjut khusus kalibrasi DVL: [laporan 31](31-kalibrasi-dvl-dalam-arus.md). Hasil di bawah tetap bukti sebelum penahan preflight; tidak ditimpa oleh pengujian baru.

## Matriks yang ditetapkan

`tools/check_reliability.py` menjalankan satu simulator setiap kali pada ROS domain 230 dan partition `sauvc_reliability_matrix`. Setiap run menyimpan kondisi JSON, command, hasil lengkap, controller/referee dan log. Folder output harus baru. Hash source diperiksa sebelum setiap run; perubahan source menghentikan batch agar hasil versi berbeda tidak tercampur.

- **12 kualifikasi:** seed instrumen 7, 42 dan 91, masing-masing nominal, prior posisi salah, cahaya redup dan arus. Kasus prior memakai offset penempatan nyata +0,15 m/yaw +0,10 rad pada jalur 1–3, ditambah galat prior XY dunia (+0,10; −0,10 m) yang tidak diberikan sebagai koreksi kepada controller.
- **6 ARENA:** dua baseline blue drum dengan seed 7 dan 91, satu varian prior posisi, satu varian cahaya, satu varian arus, dan satu pinger/pickup dengan seed 91. Layout 0/1 dan urutan flare berbeda sesuai manifest; belum pengacakan posisi properti bebas.
- Arus tetap **0,02 m/s**, world +Y untuk kualifikasi dan world +X untuk ARENA, berlaku sejak preflight sampai shutdown. Tidak dihilangkan ketika motor berhenti.
- Cahaya 70% mengurangi ambient dan diffuse lampu pada renderer. Ini tidak menyimulasikan kekeruhan atau hamburan cahaya air.
- Seed mengubah noise tekanan, IMU/magnetometer dan DVL pada plant dinamis. Noise akustik memiliki generator terpisah dan tidak ikut diacak oleh parameter ini.

Kondisi ditambahkan melalui `conditions_file:=...` pada launch dan `--conditions ...` pada kedua harness. Koefisien thrust/drag dan profil tujuh thruster tetap berasal dari konfigurasi bersama. `prior_error` hanya menggeser prior estimator, bukan spawn/model fisika. Validasi menolak nama kondisi salah, seed di luar uint32, vektor tidak finite atau pencahayaan di luar rentang yang didukung.

## Kriteria dan asumsi

Misi harus selesai menurut controller dan referee, gaya/perintah menjadi nol, kendaraan memenuhi pemeriksaan diam dan Gazebo menutup bersih. Akurasi dinilai terpisah dengan batas yang tetap: XY 0,20 m, kedalaman 0,03 m dan heading 0,03 rad. Driver memerlukan kelulusan keduanya. Kegagalan shutdown, galat estimasi dan tugas misi dilaporkan terpisah.

Kalibrasi DVL preflight mengasumsikan kendaraan ditahan diam horizontal. Simulator saat ini tidak memiliki penahan mekanik pada spawn; kasus arus menguji kendaraan yang bebas bergerak sejak awal. Arus juga dapat membawa kendaraan setelah motor dinonaktifkan. Karena itu hasil kasus arus harus dibaca bersama kedua asumsi ini, bukan diselesaikan dengan menyembunyikan gerakan atau melonggarkan kriteria.

Harness kualifikasi sekarang memberi kesempatan kendaraan dinamis untuk settle hingga 40 s bila belum diam, sama seperti pemeriksaan ARENA. Penghitungan galat heading pada harness ARENA menggunakan quaternion lengkap agar roll/pitch tidak dianggap sebagai galat yaw.

## Perbaikan dari batch diagnostik

Batch awal tersedia di `evidence/reliability-matrix-qualification/`. Sepuluh run selesai sebelum pemeriksaan hash menghentikan batch karena source diperbaiki. Satu run nominal menyelesaikan misi tetapi shutdown Gazebo memerlukan SIGKILL; akar kegagalan penutupan belum dibuktikan. Kasus prior seed 7 menyelesaikan misi dengan galat XY 0,2037 m, sedikit melewati referensi. Replay kausal menemukan keterlambatan filter kecepatan ikut terintegrasi sebagai galat posisi: pemisahan kecepatan untuk odometri dari kecepatan yang dihaluskan untuk kontrol menurunkan galat replay kasus itu menjadi sekitar 0,151 m.

Estimator kini mengintegrasikan pengukuran DVL terkoreksi bias secara langsung; filter kecepatan tetap digunakan oleh feedback propulsi. Test transien memastikan percepatan tidak menghasilkan lag posisi dari filter tersebut. **120 tes unit lulus.** Pada run langsung versi baru, prior seed 7 lulus dengan galat XY 0,1501 m dan nominal seed 7 dengan 0,0285 m. Tidak ada koordinat ground truth yang dimasukkan sebagai koreksi estimator.

Kasus arus seed 7 menyelesaikan kualifikasi tetapi gagal pemeriksaan diam dan akurasi. Replay tanpa lag tidak menghilangkan bias yang dipelajari dari drift preflight. Hasil ini dipertahankan sebagai kegagalan penerimaan, meskipun tugas kualifikasi selesai.

Diagnosis preflight pada batch awal: bias DVL lateral yang sebenarnya −0,001 m/s pada sensor virtual diperkirakan menjadi +0,0101 m/s (seed 7) dan +0,00937 m/s (seed 42) saat terkena arus. Selisih sekitar 1 cm/s berasal dari gerakan yang ikut dipelajari. Nilai bias simulator hanya digunakan untuk analisis setelah run, tidak diberikan kepada estimator. Detail berada di `preflight-current-diagnosis.json`.

## Hasil kualifikasi versi baru

Seluruh 12 run menyelesaikan tugas dan menonaktifkan thruster, dengan shutdown bersih. Sembilan memenuhi seluruh kriteria penerimaan. Tiga kasus arus gagal syarat diam dan akurasi; keberhasilan tugasnya tetap dicatat terpisah dari penerimaan keseluruhan.

| Kelompok, masing-masing seed 7/42/91 | Misi selesai | Diterima | Galat XY maksimum terburuk | Rentang start–surface |
| --- | ---: | ---: | ---: | ---: |
| Nominal | 3/3 | 3/3 | 0,0614 m | 27,352–27,436 s |
| Prior XY salah (+0,10; −0,10 m), penempatan/yaw berbeda | 3/3 | 3/3 | 0,1997 m | 27,262–27,482 s |
| Ambient/diffuse 70% | 3/3 | 3/3 | 0,0578 m | 27,270–27,302 s |
| Arus silang 0,02 m/s sejak preflight | 3/3 | 0/3 | 0,3969 m | 27,294–28,514 s |

Prior seed 91 sangat dekat ambang 0,20 m. [Pengulangan terpisah](../ros2_ws/evidence/reliability-prior91-repeat/summary.json) dengan source dan kondisi sama menghasilkan **0,201002 m**, sehingga gagal referensi akurasi; misi tetap DONE, start–surface 28,140 s, start–stop 32,900 s, perintah/gaya nol, stationary dan shutdown bersih. Run pertama mencapai 0,199692 m: margin penerimaan memang tidak stabil. Seed yang sama tidak menjamin urutan/jadwal callback ROS identik. Hasil ulang tidak menggantikan run pertama. Tiga seed belum cukup untuk menyimpulkan toleransi posisi awal itu andal pada seluruh kondisi. Perubahan ini memperbaiki integrasi posisi, bukan bukti optimasi kecepatan thruster.

## Hasil ARENA versi baru

| Kasus | Misi selesai | Penerimaan | Galat XY maksimum | Thrust–surface |
| --- | --- | --- | ---: | ---: |
| Nominal seed 7, blue drum 1 | Ya | Lulus | 0,0898 m | 227,034 s |
| Nominal seed 91, blue drum 1 | Ya | Lulus | 0,1151 m | 227,238 s |
| Prior salah, layout 1, blue drum 2, R-Y-B | Ya | Lulus | 0,1836 m | 219,090 s |
| Cahaya 70%, blue drum 3, Y-B-R | Ya | Lulus | 0,1362 m | 190,960 s |
| Arus world +X 0,02 m/s | Ya | Gagal diam dan akurasi | 1,0594 m | 238,526 s |
| Pinger drum 4, seed 91, layout 1, Y-B-R | Ya | Lulus | 0,0852 m | 206,642 s |

Keenam run di atas memperoleh Square +20 dan penalti 0, dengan perintah/gaya akhir nol, kontrol berbasis sensor dan shutdown bersih. Kasus arus tetap ditolak walaupun tugas selesai. Galat kedalaman 0,00536 m dan yaw 0,00812 rad masih memenuhi referensi; galat horizontal tidak. Bias DVL lateral yang dipelajari pada preflight menjadi −0,01115 m/s, dibanding bias virtual sebenarnya −0,001 m/s. Gerakan akibat arus kembali ikut dipelajari sebagai bias. Waktu antarlayout/urutan berbeda tidak menjadi bukti perbandingan kecepatan yang setara.

Pinger/pickup membuktikan acquisition, seluruh badan keluar target zone, retrieval bola yang sama dan retensi fisik sampai akhir. Skor simulator 290,80074, termasuk Square +20 dan penalti 0. Ini bukti mekanisme simulator, bukan hidrofon/gripper kendaraan nyata.

## Bukti akhir

- [Verifikasi gabungan](../ros2_ws/evidence/reliability-matrix-final/verification.json): 19 report beserta hash artefak, konsistensi source, hasil build/tes dan kegagalan yang masih terbuka; `all_accepted=false`.
- [Manifest dan hasil 18 kasus](../ros2_ws/evidence/reliability-matrix-final/summary.json): 12 kualifikasi (9 diterima) dan enam ARENA (5 diterima). Seluruh 18 misi selesai dan shutdown bersih. Source tetap sama sepanjang batch; kasus gagal tetap ada dalam ringkasan.
- [Pemeriksaan ulang prior seed 91](../ros2_ws/evidence/reliability-prior91-repeat/summary.json): satu run tambahan gagal akurasi. Total akhir pada versi source yang sama **19 misi selesai, 14 diterima dan lima ditolak**. Ini hitungan percobaan terpilih, bukan estimasi probabilitas sukses.
- [Build](../ros2_ws/evidence/reliability-matrix-final/build.log) berhasil dan [120 tes unit](../ros2_ws/evidence/reliability-matrix-final/unit-tests.log) lulus. Tes unit tidak menggantikan hasil runtime yang gagal.
- [Replay sebelum/sesudah perbaikan estimator](../ros2_ws/evidence/reliability-matrix-qualification/replay-velocity.json) dan [diagnosis bias saat preflight berarus](../ros2_ws/evidence/reliability-matrix-qualification/preflight-current-diagnosis.json) menjelaskan dua masalah berbeda.

Seluruh artefak runtime berada di folder `evidence/` lokal yang diabaikan Git. Batch diagnostik sepuluh run dipisahkan dari 18 run versi akhir; tidak digunakan untuk mengubah penyebut atau menyembunyikan kegagalan.

## Pekerjaan lanjutan

1. **Preflight dalam arus:** modelkan prosedur kendaraan benar-benar ditahan, atau gunakan referensi pengamatan independen untuk memisahkan gerakan dari bias DVL. Jangan menggunakan bias/noise simulator atau odometri ground truth sebagai koreksi controller. Deteksi gyro/akselerometer rendah saja tidak membuktikan kendaraan diam saat terbawa arus dengan kecepatan konstan.
2. **Definisi stop dalam arus:** thruster nol dan menahan posisi adalah dua kondisi fisik berbeda. Jika proyek memerlukan station keeping setelah surface, itu memerlukan mode aktif tersendiri. Batch ini tetap menguji stop dengan thruster nol dan tidak mengubah kriteria agar kasus arus tampak lulus.
3. **Margin prior posisi:** pengulangan sudah membuktikan kasus ini bisa melewati batas 0,20 m. Perbaiki penetapan prior atau koreksi posisi dari pengamatan sensor, lalu ulangi pasangan kasus yang sama dan perluas variasi prior/heading. Jangan menambahkan koordinat ground truth atau menaikkan ambang untuk menutup kegagalan.
4. **Cakupan yang belum diuji ulang:** GUI/POV dan injeksi gangguan memakai bukti historis laporan 27. Batch ini headless; air keruh, refleksi berat, layout acak luas, kalibrasi kendaraan nyata dan hardware belum tercakup. Satu shutdown macet pada batch diagnostik belum memiliki akar masalah yang terkonfirmasi.

## Menjalankan ulang

Gunakan folder output baru untuk setiap batch; run lama tidak ditimpa.

```bash
cd /home/rasya/AUV/ros2_ws
bash tools/ros.sh build --symlink-install
bash tools/ros.sh python tools/check_reliability.py --suite all --output evidence/reliability-run-01
# Satu kasus untuk pemeriksaan ulang
bash tools/ros.sh python tools/check_reliability.py --case q-prior-91 --output evidence/reliability-prior-recheck-01
```

`--suite qualification` atau `--suite arena` membatasi batch. Ctrl+C meneruskan penghentian ke harness dan mencatat kasus yang terputus. `summary.json` diperbarui setelah setiap run. Waktu dirangkum per kelompok skenario dari misi yang selesai, dengan jumlah penerimaan dilaporkan terpisah, sehingga kegagalan akurasi/shutdown tidak tersembunyi dalam statistik waktu.

Hasil batch versi baru disimpan di `evidence/reliability-matrix-final/`. Kondisi arus saat ini memengaruhi drag kendaraan; belum merupakan simulasi aliran air atau drift hidrodinamis payload. Generator geometri dan profil dasar kolam tetap asumsi latihan.
