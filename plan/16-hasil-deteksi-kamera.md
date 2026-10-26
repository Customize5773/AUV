# Hasil deteksi gate, flare dan drum dari kamera

Tanggal: **25 Oktober 2026, Asia/Jakarta**. Lingkup permintaan: meneruskan deteksi objek dari kamera sesudah kualifikasi otomatis selesai. **Status: detektor, build, tes dan pengujian frame simulator selesai.**

Lanjutan ketahanan deteksi, tracking, proyeksi kamera dan integrasi kontrol ARENA dicatat terpisah dalam [laporan 17](17-hasil-arena-autonomous.md). Batas controller pada dokumen ini menjelaskan lingkup tahap deteksi awal.

## Acuan dan batas pekerjaan

Pemeriksaan daring masih menunjukkan [rulebook terbit 2026 v6.1.0](https://sauvc.org/rulebook/) dan [usulan 2027 PR #25](https://github.com/sauvc/rulebook/pull/25) yang masih terbuka. Detektor menargetkan properti berwarna pada arena simulator 2026 yang sudah ada; geometri world tidak diubah pada pekerjaan ini.

Kualifikasi tetap memakai detektor pasangan tiang oranye yang sudah terbukti. ARENA memakai pasangan penanda merah–hijau untuk gate, bentuk tiang memanjang untuk orange/blue/red/yellow flare, serta kandidat drum biru dari kamera bawah. Red drum juga dibedakan sebagai pembanding negatif terhadap target biru.

Pekerjaan ini tidak menjalankan penghindaran orange flare, mendekati/menabrak flare, pelepasan payload, skor jatuhnya bola, atau controller misi ARENA. Deteksi objek tidak dianggap bukti task tersebut berhasil.

## Implementasi dan antarmuka

- `gate_detection.py`: fungsi pembacaan RGB/BGR dan stride dipakai bersama; hasil gate kualifikasi mendapat bounding box tanpa mengubah bidang bearing/range yang dipakai controller.
- `object_detection.py`: masker warna dan komponen tersambung berbasis run per baris; pemisahan flare, marker gate dan daerah drum memakai bentuk. Baris kosong dilewati agar kerja detektor tidak menghabiskan waktu kamera.
- `perception.py`: proses ROS terpisah, hanya berlangganan kamera depan/bawah. Hasil JSON dikirim pada `/sauvc/perception/front` dan `/sauvc/perception/bottom`; tidak ada langganan odometri/pose/ID objek world atau publisher perintah gerak.
- Launch mengaktifkan persepsi ketika kamera aktif; `perception:=false` tersedia untuk mematikannya. NumPy yang sudah terpasang digunakan tanpa penambahan dependensi runtime.
- Alat `tools/check_perception.py` memeriksa topic deteksi dan kamera melalui sudut pandang terkendali, menyimpan JSON/frame, dan memastikan hasil lama dibuang ketika kamera berhenti.

Keluaran berisi label, bbox piksel dari masker/penanda yang terdeteksi (bukan envelope fisik benda), pusat citra, error pusat ternormalisasi, penanda objek terpotong, timestamp/frame dan waktu pemrosesan. Estimasi jarak gate memakai ukuran model serta HFOV simulator; bukan pose world atau pengukuran kedalaman sebenarnya. Confidence probabilistik tidak diberikan karena pendekatan ini belum dikalibrasi sebagai model probabilistik.

`fresh` menandai kesegaran penerimaan frame, bukan jaminan timestamp dari kamera hardware sudah benar. Setelah >1 s tanpa penerimaan gambar, hasil kosong diterbitkan dengan status tidak segar. Citra invalid juga menghasilkan daftar kosong. Setiap konsumen harus memeriksa kedua flag `fresh` dan `valid_image`.

## Bukti pengujian

**32 tes logika/geometri lulus**, termasuk pengujian sebelumnya dan sepuluh tes deteksi baru. RGB/BGR, padding stride, frame invalid, komponen tipis, warna flare, penanda bercorak, gate satu tiang, blue/red drum, citra biru penuh, kandidat drum terpotong dan serialisasi JSON dicakup.

Uji runtime membaca pesan node persepsi yang berasal dari kamera Gazebo, bukan memanggil detektor dengan label/koordinat jawaban. Pada setiap sudut pandang dibutuhkan tiga frame berurutan yang memenuhi hasil yang diharapkan. Posisi kendaraan hanya diatur oleh harness agar objek masuk bidang pandang; ini bukan pembuktian navigasi autonomous.

| Skenario ARENA | Hasil |
| --- | --- |
| Gate depan dan gate dari arah balik | Pasangan marker merah–hijau terdeteksi |
| Orange, blue, red dan yellow flare | Keempat kelas terdeteksi pada frame sebenarnya |
| Hanya satu tiang gate terlihat | Tidak mengeluarkan label navigation gate |
| Kamera bawah pada lantai kosong | Tidak mengeluarkan label blue/red drum |
| Kamera bawah pada red drum | `red_drum` terdeteksi; tidak dilabeli blue drum |
| Kamera bawah pada blue drum | `blue_drum` terdeteksi; tidak dilabeli red drum |

Sepuluh skenario ARENA lulus. Pengujian kamera qualification juga lulus dengan label `qualification_gate` dan tanpa label flare. Pada kedua pengujian, simulator dipause sesudah deteksi, dan pesan lama pada kedua kamera terbukti dibuang (`fresh=false`, daftar kosong). Semua proses pengujian tersebut menutup bersih.

Regresi kualifikasi autonomous dengan node persepsi aktif mencapai `DONE`, dengan start sampai surface **9,382 s simulasi** dan stop terverifikasi **10,504 s** pada satu run. Ini satu pemeriksaan regresi, bukan median benchmark baru atau klaim bahwa waktu pemrosesan persepsi tidak menambah beban.

Setelah melewati baris masker yang kosong, waktu pemrosesan pada sepuluh sampel hasil runtime akhir berada sekitar **9–52 ms/frame**. Angka ini mengukur pemanggilan detektor pada mesin pengujian, bukan latensi ujung-ke-ujung atau jaminan throughput pada Jetson.

Ringkasan terakhir: [verification.json](../ros2_ws/evidence/perception/verification.json).

Bukti lokal: [ARENA](../ros2_ws/evidence/perception/finals.json), [qualification](../ros2_ws/evidence/perception/qualification.json), dan [regresi misi cepat](../ros2_ws/evidence/perception/qualification-fast-regression.json). Frame PPM asli dan PNG dengan kotak/label disimpan di folder yang sama, diabaikan Git. Contoh:

- [Gate depan](../ros2_ws/evidence/perception/navigation-gate-front.png).
- [Orange flare dan flare lain yang terlihat](../ros2_ws/evidence/perception/orange-flare-front.png).
- [Blue drum dari kamera bawah](../ros2_ws/evidence/perception/blue-drum-bottom.png).

## Lanjutan: tampilan deteksi langsung

Pengerjaan lanjutan pada 25 Oktober 2026 menambahkan topic RGB8 `/sauvc/perception/front/image_annotated` dan `/sauvc/perception/bottom/image_annotated`. Gambar memuat kotak magenta, label kelas dan titik pusat putih, dengan header/timestamp identik dengan frame kamera sumber. Kamera asli tetap menjadi masukan detektor. Anotasi hanya dibuat ketika ada subscriber, memakai NumPy tanpa dependensi baru. Gambar invalid diganti panel status; setelah kamera berhenti >1 s, panel `CAMERA STALE - NO DETECTIONS` menggantikan gambar lama, dengan timestamp node dan tanpa frame ID kamera sumber.

Alat uji kini mencocokkan JSON, frame asli dan anotasi melalui timestamp yang sama, serta menyimpan kedua gambar. Untuk deteksi positif, piksel anotasi harus berbeda dari sumber; pada frame tanpa deteksi piksel harus identik. Setelah pause, kedua topic anotasi harus berubah menjadi panel status tanpa kotak lama.

**36 tes lulus**, termasuk empat tes baru untuk kotak/pusat/teks, sumber yang tidak berubah, decoding BGR dengan padding, batas citra, frame invalid dan panel status. Uji Gazebo ulang lulus **10 skenario ARENA + 1 qualification**, termasuk kesesuaian header dan pembersihan gambar lama pada kedua kamera. Semua proses uji tersebut menutup bersih. Ini bukan pengulangan benchmark kecepatan atau pembuktian misi ARENA autonomous.

Bukti terbaru: [ringkasan](../ros2_ws/evidence/perception-overlay/verification.json), [ARENA](../ros2_ws/evidence/perception-overlay/finals.json), [qualification](../ros2_ws/evidence/perception-overlay/qualification.json), [gambar gate](../ros2_ws/evidence/perception-overlay/navigation-gate-annotated-front.png), dan [gambar blue drum](../ros2_ws/evidence/perception-overlay/blue-drum-annotated-bottom.png). Bukti uji awal di atas tetap disimpan sebagai riwayat. Halaman rulebook resmi diperiksa kembali dan masih menampilkan 2026 v6.1.0; perubahan ini tidak mengubah geometri atau urutan tugas.

Untuk melihat langsung, jalankan arena sesuai perintah di bawah, lalu di terminal lain:

```bash
bash tools/ros.sh run rqt_image_view rqt_image_view
```

Pilih topic `image_annotated` kamera depan atau bawah pada dropdown. Jendela rqt belum diperiksa secara visual pada sesi lanjutan ini; gambar yang diterbitkan telah diuji dan contoh tersimpannya telah diperiksa.

## Keterbatasan saat ini

Detektor berbasis warna/bentuk diuji pada citra simulator, belum video DWE, air keruh, caustics/refleksi kuat, occlusion berat atau pencahayaan kolam nyata. Kandidat bulat biru tidak membuktikan suatu benda adalah drum fisik; benda lain dengan warna/bentuk serupa dapat menghasilkan kandidat. Drum yang terpotong atau terlalu kecil sengaja tidak diterima. Salah satu tiang gate yang hilang juga tidak cukup untuk deteksi gate lengkap.

Arah alignment badan dan koordinat 3D, identitas tracking antarframe, kalibrasi kamera hardware, integrasi deteksi ke controller ARENA, penghindaran obstacle dan drop payload belum termasuk tahap ini.

## Menjalankan

```bash
cd /home/rasya/AUV/ros2_ws
bash tools/ros.sh build --symlink-install
bash tools/ros.sh launch sauvc_sim arena.launch.py arena:=finals
```

Hasil tersedia pada `/sauvc/perception/front` dan `/sauvc/perception/bottom`. Cara memeriksa serta kontrak keluaran ada dalam [README workspace](../ros2_ws/README.md).
