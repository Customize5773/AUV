# 60 — Evaluasi ulang body dan kualitas mesh AUV

Tanggal: 12 November 2026. Pengguna menyerahkan pilihan orientasi/skala sementara kepada implementasi. Konvensi tetap **+X depan, +Y kiri, +Z atas**, dengan ukuran latihan sekitar **51,85 × 38,69 × 20 cm**. Ini belum ukuran fisik AUV yang diukur.

## Temuan utama

### 1. Penyederhanaan sebelumnya mengubah panel terlalu jauh — diperbaiki

Pembanding FBX penuh menunjukkan cover merah membulat dengan bukaan thruster, rangka bawah hitam dan pelat samping yang utuh. Mesh 230.463 segitiga sebelumnya menghilangkan sebagian permukaan tersebut dan membuat beberapa bagian tampak terpotong. Koreksi normals saja tidak memperbaiki kehilangan geometri, sehingga kandidat yang hanya memperbaiki normals tidak dipakai.

Referensi pembanding diekspor dari FBX penuh melalui Assimp, dengan pemusatan, rotasi dan skala yang sama; geometri terpencil di luar assembly disaring seperti proses produksi. Ini membandingkan detail sebelum/sesudah simplifikasi pada importer yang sama, bukan verifikasi terhadap CAD di aplikasi pembuat aslinya.

| Runtime lama | FBX penuh melalui Assimp | Revisi runtime |
|---|---|---|
| ![Body lama](../ros2_ws/evidence/body-audit-20261112/before-render/gazebo-model.png) | ![Referensi FBX penuh](../ros2_ws/evidence/body-audit-20261112/source-render/gazebo-model.png) | ![Body revisi](../ros2_ws/evidence/body-audit-20261112/quality-final-render/gazebo-model.png) |

Ketiga gambar adalah renderer Gazebo dengan kamera/pose yang sama. Alat pickup tambahan dan bola awal disembunyikan hanya pada world pembanding agar body terlihat; posisi gripper produksi dari laporan 59 tetap dipakai pada runtime extended.

### 2. Normal permukaan dirata-ratakan melewati tepi tajam — diperbaiki

Konverter kini memisahkan kelompok permukaan pada sudut 30° sebelum menghitung normals, dan membuang segitiga dengan luas di bawah `1e-14 m²`. Tepi pelat tetap tegas sementara bagian lengkung masih dapat dihaluskan. Dua tes konversi memeriksa pelat tipis, luas/bounds, normals box pada tepi 90° serta pembuangan face degenerat.

Simplifikasi kini memakai pemeriksaan per-part: galat luas maksimum 1,5% dan perubahan bounding box maksimum 0,5 mm. Jika kandidat melampaui batas, jumlah face dinaikkan atau geometri asal dipertahankan. Batas ini bukan pengukuran Hausdorff atau jaminan seluruh detail CAD sama persis; hasil juga diperiksa secara visual terhadap FBX penuh.

| Data mesh | Sebelumnya | Revisi |
|---|---:|---:|
| Segitiga runtime | 230.463 | 816.288 |
| Komponen/objek | 62 | 62 |
| Material | 59 | 59 |
| Dimensi visual | 0,51849 × 0,38688 × 0,20000 m | Hampir sama, selisih pembulatan submikrometer pada bounds |
| Diagnostik sudut normals p95 | 75,79° | 21,82° |
| Ukuran OBJ revisi | — | 80.291.709 byte, di bawah batas aset 100 MB |

Galat luas per-part terbesar pada kandidat yang dipakai 1,4358%; perubahan bounds per-part terbesar 0,4171 mm. Guard dihitung sebelum ekspor; OBJ memakai enam desimal (resolusi koordinat 1 mikrometer) untuk menjaga ukuran file, sehingga ini bukan sertifikasi toleransi CAD setelah serialisasi. Warna diffuse material sebelum/sesudah cocok. Masih ada anomali kecil pada sebagian normals dan sambungan CAD; tidak mengklaim mesh telah menjadi solid manifold yang bersih. Jumlah boundary/nonmanifold edge pada assembly multi-part juga tidak cukup untuk menyimpulkan CAD rusak atau menentukan volume air yang dipindahkan.

Tradeoff yang dipilih: mempertahankan panel utama dan bentuk asli dengan biaya render lebih besar daripada versi 230 ribu face. Target 300 ribu pada konverter bukan batas paksa; pemeriksaan geometri mengambil prioritas. Hasil tetap lebih ringan dari sumber 2.066.827 segitiga.

### 3. Collision lebih besar dari visual — batas realisme yang masih terbuka

Collision tetap box **60 × 40 × 20 cm**, dengan inertia box latihan. Dibanding visual, box melampaui badan sekitar **4,08 cm pada masing-masing ujung X** dan **0,66 cm pada masing-masing sisi Y**. Ini dapat membuat kontak/ambang pelintasan dinilai pada volume yang tidak terlihat. Pada posisi awal, visual juga tidak tampak menyentuh dinding meskipun collision box menyentuhnya.

Collision tidak diubah dalam revisi visual ini. Penyamaan collision harus ikut menyelaraskan envelope referee, start-wall, kamera dan uji kontak/pelintasan; bukan sekadar mengganti angka ukuran visual. Pemeriksaan dimensi tersedia pada [metrics.json](../ros2_ws/evidence/body-audit-20261112/final/metrics.json).

![Proyeksi body, collision dan titik pemasangan](../ros2_ws/evidence/body-audit-20261112/final/body-views.png)

Proyeksi di atas untuk pemeriksaan geometri/bounds; penilaian shading memakai gambar renderer Gazebo sebelumnya. Marker pickup menunjukkan pusat tangkap, bukan seluruh visual dudukan.

### 4. Mesh belum menentukan model fisik kendaraan

Model berupa assembly rangka, cover dan tabung. Massa 20 kg, inertia, volume buoyancy 20,5 L, koefisien drag dan koordinat tujuh thruster tetap parameter latihan, bukan hasil ekstraksi material/COM/COB dari CAD. Profil propulsi sendiri menandai geometri sebagai `assumed_training_geometry` dan mixer fisik belum terverifikasi. Posisi thruster yang tampak di mesh belum dipetakan ke output T1–T7 secara semantik.

Posisi kamera tetap berada di luar batas body: front di x +0,32 m dan bottom di z −0,12 m. Itu pemeriksaan penempatan geometris, bukan kalibrasi pemasangan atau intrinsics kamera nyata. Gripper pickup tetap `(−0,20, 0, −0,40) m` sesuai laporan 59.

Metadata FBX mencatat `UnitScaleFactor=0.1`; skala latihan aktif tetap dipertahankan. Metadata unit memerlukan interpretasi saat impor, dan tidak menjadi bukti ukuran fisik terukur. [Penjelasan unit pada proyek Assimp](https://github.com/assimp/assimp/issues/775), [capture metadata](../ros2_ws/evidence/body-audit-20261112/fbx-metadata.txt).

## Perubahan dan verifikasi

`prepare_auv_mesh.py` memakai simplifikasi dengan pemeriksaan geometri serta pemisahan normals tepi tajam. OBJ/MTL/metadata runtime diperbarui, batas aset pada tes disesuaikan menjadi 900 ribu segitiga dan 100 MB, serta resep konversi offline menambahkan SciPy sebagai backend graph. Tidak ada dependensi runtime ROS baru. Backup mesh lama disimpan pada direktori evidence `active-before`.

- Build dan **180 tes simulator lulus**.
- **2 tes konversi offline lulus**; suite ini terpisah dari tes simulator.
- Packaging OBJ/MTL/JSON byte-identik dengan aset aktif.
- **Kualifikasi dinamis GUI + kedua POV lulus**, DONE, gaya thruster akhir nol dan shutdown bersih; start–surface 25,782 detik simulasi. Ini bukti fungsional satu run, bukan benchmark percepatan.
- ARENA/extended belum diulang setelah revisi body ini; hasil laporan 59 memakai mesh sebelumnya.

Bukti akhir: [verification.json](../ros2_ws/evidence/body-audit-20261112/verification.json), [kualifikasi](../ros2_ws/evidence/body-audit-20261112/qualification.json), [tes simulator](../ros2_ws/evidence/body-audit-20261112/unit-tests.log), [tes konversi](../ros2_ws/evidence/body-audit-20261112/conversion-tests.log), [packaging](../ros2_ws/evidence/body-audit-20261112/packaging.json).

Belum dilakukan: validasi dimensi/massa dan mixer fisik, CFD, penutupan manifold CAD, benchmark FPS/VRAM panjang, seluruh variasi layout/arus, atau migrasi collision agar mengikuti bentuk visual. Bentuk body visual kini mendekati referensi FBX jauh lebih baik, sementara batas fisika tersebut tetap perlu ditangani terpisah.

Pembaruan penerimaan: ARENA extended dengan aset body yang sama kemudian lulus pada [laporan 61](61-penerimaan-extended-body-revisi.md), termasuk retensi bola hingga stop dan shutdown bersih. Batas collision dan kalibrasi fisik tetap berlaku.
