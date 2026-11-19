# Diagnosis pickup dari titik mesh asli

19 November 2026. Melanjutkan ketidakpastian [laporan 76](76-diagnosis-reach-fixed-dan-fixture-tambahan.md): apakah pickup gagal hanya karena collision AABB mengisi ruang kosong pada model? Gripper tetap pendek di tengah, tanpa slider. Source produksi dan geometri latihan tidak diubah.

## Hasil

**Benturan pada grid yang diuji juga ditemukan dari titik mesh asli, bukan hanya box pembungkus.** Mengganti AABB dengan bentuk yang lebih presisi saja belum membuktikan pickup dapat dilakukan pada geometri sekarang. Belum ada pickup runtime baru yang dinyatakan lulus.

Input OBJ berisi **695.714 vertex**. Convex hull digunakan hanya untuk memilih **445 vertex asli** di batas luar; titik baru pada permukaan/volume convex hull tidak dipakai sebagai bukti benturan. Untuk pose yang belum tertolak, pemeriksaan diperluas ke sampel **5.436 vertex asli**. Titik yang dianggap berbenturan diperiksa terhadap box dinding drum dari SDF, dengan margin interior positif; titik di luar lantai menjadi alasan penolakan lainnya.

Grid tetap: **395.304 orientasi per posisi bola**, roll/pitch bertahap 2°, yaw 15°, enam posisi bola seperti laporan 76. Dari setiap grid:

| Pemeriksaan | Jumlah pose per posisi bola |
|---|---:|
| Titik mesh menembus lantai kolam | 381.024 |
| Lolos lantai tetapi titik mesh masuk dinding drum | 14.280 |
| Belum tertolak | **0** |

Pemeriksaan terhadap lantai memakai titik ekstrem sehingga minimum tinggi mesh terwakili. Pada empat posisi bola dekat sisi drum, tahap pertama menyisakan 2.567 pose; sampel vertex tambahan menolak seluruhnya. Pusat drum dan offset dekat pusat 2,4 cm sudah tertolak dari vertex ekstrem.

Ini pencarian diskret dengan titik grip berimpit pusat bola, bukan pembuktian untuk setiap orientasi kontinu, titik kontak, lokasi bola, lintasan atau kendaraan fisik. Tes titik dapat menunjukkan benturan; lolos tes titik pun tidak cukup membuktikan triangle/trajectory clearance. Collision gripper dan ketebalan dasar drum tidak digunakan untuk membuat penolakan ini.

## Contoh benturan yang bisa diperiksa

![Titik mesh asli berada di dalam dinding drum](../ros2_ws/evidence/gripper-mesh-reach-20261119/witness.png)

Pada pendekatan mendatar, pusat body perlu floor +22 cm agar gripper −18 cm berimpit dengan pusat bola floor +4 cm. **Vertex OBJ indeks 363550** berada pada body `(0,248447; 0,150147; 0,030863) m`. Setelah transform, titik tersebut berada di dalam solid `rim_3`, dengan jarak ke bidang pembatas terdekat sekitar **9,99 mm**. Ini contoh titik geometri di dalam solid, bukan pembacaan gaya kontak atau kedalaman penetrasi dari Gazebo.

Proyeksi gambar mengambil sampel vertex untuk keterbacaan; marker merah menggunakan vertex asli yang disimpan pada JSON. Plot tidak memakai ukuran body/drum yang diperkecil.

## Dampak pada progres

- Penerimaan tiga jalur kualifikasi dan dua layout ARENA blue drum tetap merujuk run 18 November, pada source yang sama. Pemeriksa bukti/manifest laporan 76 diperiksa ulang dan lulus; tidak ada klaim misi runtime baru pada sesi ini.
- **Pickup pendek tetap masih terbuka.** Mengubah timeout, melonggarkan collision atau menambah slider tidak diterapkan. Belum ada kandidat pose aman pada grid ini untuk diteruskan menjadi kontrol pickup.
- Data ini membantu keputusan geometri kendaraan/mekanisme. Dimensi dan bentuk fisik kendaraan tetap belum tervalidasi. Pengujian kendaraan fisik dikecualikan.

## Bukti dan pengulangan

[Hasil pencarian dan hash input](../ros2_ws/evidence/gripper-mesh-reach-20261119/verification.json) · [skrip pencarian](../ros2_ws/evidence/gripper-mesh-reach-20261119/check_mesh.py) · [contoh titik benturan](../ros2_ws/evidence/gripper-mesh-reach-20261119/witness.json) · [skrip plot/pemeriksa contoh](../ros2_ws/evidence/gripper-mesh-reach-20261119/plot_witness.py).

```bash
cd /home/rasya/AUV
OPENBLAS_NUM_THREADS=1 python3 ros2_ws/evidence/gripper-mesh-reach-20261119/check_mesh.py
OPENBLAS_NUM_THREADS=1 python3 ros2_ws/evidence/gripper-mesh-reach-20261119/plot_witness.py
```

Memakai NumPy, SciPy dan Matplotlib yang sudah tersedia pada Python laptop. Perintah hanya membaca geometri dan menyimpan hasil statis, tanpa membuka koneksi hardware.
