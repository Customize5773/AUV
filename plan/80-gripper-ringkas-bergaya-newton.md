# Gripper ringkas bergaya Newton

**Riwayat bentuk dengan rahang rigid terbuka.** Aktuasi rahang berikutnya: [laporan 81](81-aktuasi-rahang-dan-release-terukur.md).

19 November 2026. Mengikuti permintaan batang **5–10 cm** dan referensi Newton Subsea Gripper dari pengguna. Dipilih **8 cm dari bawah hull ke atas kepala**, tetap di tengah dan tanpa slider.

## Bentuk yang diterapkan

- Rumah aktuator silinder hitam, flange metal dan pin biru.
- Dua rahang capit berongga dengan tepi melengkung dan gigi kecil di sisi dalam.
- Kepala menghadap ke bawah untuk peran payload AUV. Titik grip tetap `(0, 0, −0,21) m`.
- Batang SDF panjang 10 cm mencakup 2 cm dudukan di dalam hull; bagian di bawah hull 8 cm. Pusat bola 11 cm di bawah hull. Dengan rahang yang lebih panjang, ujung terendah sekitar 16,4 cm di bawah hull.

Bentuk ini geometri prosedural asli yang **terinspirasi tampilan Newton**, bukan CAD produk resmi. Skala, massa, aktuator dan performa produk Newton tidak diadopsi. Referensi: [Newton Subsea Gripper — Blue Robotics](https://bluerobotics.com/store/thrusters/grippers/newton-gripper-asm-r2-rp/).

![Detail kepala gripper dalam pose terbuka](../ros2_ws/evidence/gripper-newton-20261119/empty/initial.png)

[Tampilan keseluruhan AUV dengan bola awal](../ros2_ws/evidence/gripper-newton-20261119/initial.png). Render berasal dari Gazebo, dengan lampu inspeksi hanya di world capture. Tampilan detail menghilangkan payload hanya pada salinan world inspeksi agar rahang terlihat; model misi tetap memuat bola.

## Pemeriksaan

Build dua paket selesai dan **201 tes lulus**. Tes mencakup panjang batang, dudukan fixed, celah drop serta envelope. Collision mengikuti primitif visual rahang, termasuk rangka berongga; bukan box padat yang menutup lubang rahang. Uji native release dengan collision aktif membuktikan bola latihan 40 mm terlepas dan jatuh lebih dari 1 m. Pada 110 snapshot awal, bola terpasang pada titik grip yang sama dengan selisih tercatat 0 m pada resolusi telemetri.

| Fixture dinamis 2027 | Hasil |
|---|---|
| ARENA blue drum, seed 91, air 0,05/m | **210,1426 poin**, thrust–surface **228,580 s**, penalti nol |
| Kualifikasi jalur 3, offset 0,15 m, seed 42, air 0,10/m | Gate kedua **22,792 s**, thrust–surface **25,376 s**, thrust–stop **29,796 s** |

Kedua run DONE, stationary, command/gaya akhir nol serta shutdown bersih. Pemeriksa sensor dan akurasi estimator lulus. Seluruh runtime tersebut memakai source/aset yang sama dengan manifest final; 98 file diverifikasi. Pengujian misi berjalan tanpa GUI; gambar di atas adalah render inspeksi terpisah.

Draft telapak bulat sebelum referensi Newton tetap disimpan di `evidence/gripper-compact-20261119/`; pengujian misinya dihentikan saat pengguna mengarahkan perubahan bentuk. Draft itu tidak dinyatakan sebagai penerimaan model akhir.

## Batas fungsi

**Pickup dasar drum kembali belum didukung dengan batang pendek ini.** Clearance hull pada pendekatan mendatar menjadi **−17 cm**. Unit test mengonfirmasi extended ditolak sebelum command gerak; tidak ada penerimaan runtime extended baru pada revisi ini. Keberhasilan pickup [laporan 79](79-gripper-fixed-panjang-dan-pickup-selesai.md) berlaku untuk batang panjang sebelumnya.

Rahang baru masih berpose terbuka dan rigid. Gerak piston, buka-tutup rahang, gaya jepit dan driver Newton belum dimodelkan. Release/latch simulator tetap mekanisme ideal sebelumnya. Ini perubahan bentuk simulator, bukan validasi desain fabrikasi, kemampuan Newton asli atau hardware kendaraan.

## Bukti dan pengulangan

[Verifikasi gabungan](../ros2_ws/evidence/gripper-newton-20261119/verification.json) · [skrip pemeriksa](../ros2_ws/evidence/gripper-newton-20261119/verify.py) · [manifest source/aset](../ros2_ws/evidence/gripper-newton-20261119/source-sha256.json) · [201 tes](../ros2_ws/evidence/gripper-newton-20261119/unit-tests-final.log) · [build](../ros2_ws/evidence/gripper-newton-20261119/build.log).

[ARENA](../ros2_ws/evidence/gripper-newton-20261119/blue/mission.json) · [kualifikasi](../ros2_ws/evidence/gripper-newton-20261119/qualification/mission.json) · [release native](../ros2_ws/evidence/gripper-newton-20261119/release/physics.json) · [referensi desain](../ros2_ws/evidence/gripper-newton-20261119/reference.json) · [cara running](../ros2_ws/CARA-RUNNING.md).

```bash
cd /home/rasya/AUV/ros2_ws
bash tools/ros.sh python evidence/gripper-newton-20261119/verify.py
```

Perintah memeriksa bukti tersimpan, geometri dan hash; tidak menjalankan hardware. Source/manifest laporan sebelumnya tetap bukti historis dan dapat menolak revisi baru.
