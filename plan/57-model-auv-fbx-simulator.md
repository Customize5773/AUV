# 57 — Model AUV SAUVC 2027 v1 di simulator

Tanggal: 11 November 2026. Model sumber pengguna: [`ros2_ws/sauvc 2027 v1.fbx`](../ros2_ws/sauvc%202027%20v1.fbx), SHA-256 `7aa2d4b6773298ec1015dfc17eca0b231dfd6a09514734f49b638b2ffa198c5f`.

## Implementasi

Visual kotak dan penanda hidung lama diganti mesh turunan FBX untuk kendaraan `sauvc_auv`. Berlaku pada kualifikasi dan ARENA, profil ideal maupun dinamis. Aset OBJ/MTL dan metadata masuk `package_data`; tidak membutuhkan importer FBX saat simulator berjalan.

Collision tetap satu box 0,6 × 0,4 × 0,2 m dengan nama `hull`, agar kontak dan pemeriksa pelintasan penuh tetap konsisten. Massa, inertia, model gaya tujuh thruster, estimator, posisi kamera dan titik pelepasan payload tidak diubah. Thruster pada mesh adalah visual statis; geometri ini bukan hasil kalibrasi thrust atau buoyancy.

Source berisi 2.066.827 segitiga. Sebanyak 2.340 segitiga jauh dari assembly utama dibuang. Vertex berimpit disatukan sebelum penyederhanaan agar bagian CAD tidak berubah menjadi fragmen. Hasil akhir 230.463 segitiga; target penyederhanaan adalah perkiraan, bukan jaminan jumlah tepat.

Assembly dipusatkan, sumbu panjang sumber −Y diarahkan sementara ke +X kendaraan, dan skala uniform disesuaikan agar muat envelope collision lama. Ukuran visual sekitar 0,5185 × 0,3869 × 0,2000 m. **Ini skala latihan, bukan dimensi AUV nyata yang dikonfirmasi.** Arah depan fisik juga belum dikonfirmasi pengguna. Metadata numerik ada di [sauvc_2027_v1.json](../ros2_ws/src/sauvc_sim/sauvc_sim/meshes/sauvc_2027_v1.json).

Konversi COLLADA awal tidak lolos loader Gazebo. OBJ digunakan pada implementasi akhir; loader native mengonfirmasi batas mesh yang benar. Konversi awal sebelum penyatuan vertex juga menghasilkan fragmen; masalah tersebut diperbaiki sebelum penerimaan akhir. Screenshot di bawah berasal dari renderer Gazebo setelah perbaikan, bukan render CAD terpisah.

![Model AUV di renderer Gazebo](../ros2_ws/evidence/auv-mesh-20261111/gazebo-model.png)

## Cara menjalankan

Perintah launch yang ada tetap berlaku; model baru otomatis dipakai:

```bash
cd /home/rasya/AUV/ros2_ws
bash tools/ros.sh launch sauvc_sim arena.launch.py arena:=qualification autonomous:=true
# Untuk ARENA, hentikan launch sebelumnya lalu:
bash tools/ros.sh launch sauvc_sim arena.launch.py arena:=finals autonomous:=true
```

Untuk membuka POV depan/bawah gunakan [panduan simulator](../ros2_ws/CARA-RUNNING.md). Tidak ada koneksi Pixhawk dari perubahan ini.

## Reproduksi aset offline

Simulator memakai aset yang sudah dihasilkan; langkah ini hanya diperlukan jika FBX berubah. Memerlukan header/library Assimp dan compiler C++.

```bash
cd /home/rasya/AUV
c++ ros2_ws/tools/export_auv_fbx.cc -lassimp -o /tmp/export_auv_fbx
/tmp/export_auv_fbx 'ros2_ws/sauvc 2027 v1.fbx' /tmp/auv-source.glb
python3 -m venv /tmp/auv-mesh-tools
/tmp/auv-mesh-tools/bin/pip install trimesh==5.2.0 fast-simplification==0.2.0 scipy==1.11.4
/tmp/auv-mesh-tools/bin/python ros2_ws/tools/prepare_auv_mesh.py \
  /tmp/auv-source.glb ros2_ws/src/sauvc_sim/sauvc_sim/meshes/sauvc_2027_v1.obj
bash ros2_ws/tools/ros.sh build --symlink-install
```

Filter geometri terpencil dan arah sumbu pada converter khusus untuk source v1 ini; source revisi harus diperiksa kembali. Periksa screenshot dan metadata setelah regenerasi, bukan hanya keberhasilan ekspor.

## Verifikasi

Build lulus. Seluruh **179 tes unit simulator lulus**, termasuk tes baru resolusi mesh/material, hash, envelope, collision dan posisi kamera. Staging `setup.py build_py` membuktikan OBJ/MTL/JSON terpaket dengan byte identik. [Log loader native](../ros2_ws/evidence/auv-mesh-20261111/native-mesh-loader.log), [tes unit](../ros2_ws/evidence/auv-mesh-20261111/unit-tests.log), [packaging](../ros2_ws/evidence/auv-mesh-20261111/packaging.json).

Kualifikasi percobaan GUI pertama menyelesaikan misi, kedua POV terverifikasi, tetapi shutdown server memerlukan SIGKILL. Run tersebut dipertahankan sebagai kegagalan penerimaan (`qualification-final.json`), bukan dihitung lulus penuh. Pengulangan akhir dan ARENA kemudian lulus penuh:

| Pengujian akhir dengan GUI + dua POV | Hasil |
|---|---|
| Kualifikasi dinamis | DONE, dua pelintasan dan U-turn sah; waktu resmi 22,818 s, start–surface 25,878 s, start–stop 30,740 s |
| ARENA dinamis | DONE; gate, flare B–R–Y, payload masuk blue drum, Surfacing Square; 210,20308 poin, penalti nol, thrust–surface 226,564 s |
| Kedua run akhir | POV depan/bawah terverifikasi; thruster akhir nol, kendaraan berhenti, shutdown bersih tanpa cleanup paksa POV |

Bukti akhir: [verification.json](../ros2_ws/evidence/auv-mesh-20261111/verification.json), [kualifikasi](../ros2_ws/evidence/auv-mesh-20261111/qualification-accepted.json), [ARENA](../ros2_ws/evidence/auv-mesh-20261111/arena-final.json). Run kualifikasi headless awal pada mesh konversi pendahuluan bukan penerimaan aset final. Kegagalan shutdown GUI awal tetap dipertahankan; hasil ini bukan bukti bahwa semua kejadian shutdown intermiten telah diselesaikan.

Cakupan runtime akhir: satu kualifikasi jalur 1 dan satu ARENA blue drum, default kondisi tanpa arus. Extended pinger/pickup dan seluruh variasi layout/arus belum diulang dengan visual ini. Dimensi/massa/drag nyata tetap memerlukan kalibrasi; model FBX yang diimplementasikan adalah visual.

Pembaruan 12 November: regresi extended pinger/pickup dengan model yang sama diterima pada [laporan 58](58-regresi-pinger-model-auv.md), termasuk keluar zona, bola yang sama dan retensi hingga stop. Batas variasi layout/arus di atas tetap berlaku.

Pembaruan visual 12 November: kualitas simplifikasi diperbaiki setelah pembandingan FBX penuh; mesh aktif menjadi 816.288 segitiga dengan guard luas/bounds dan normals tepi tajam. Lihat [laporan 60](60-evaluasi-body-dan-kualitas-mesh.md); statistik 230.463 di atas adalah revisi awal.
