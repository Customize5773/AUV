# Simulasi arena SAUVC — 22 Oktober 2026

Pengguna meminta simulasi ROS untuk **Qualification Arena(s)** dan **The Arena**, lalu memilih workspace terpisah di `/home/rasya/AUV/ros2_ws`. Package baru `sauvc_sim` berada dalam Git repositori AUV yang sama; workspace KKI `/home/rasya/ros2_ws` dan platform `hydroships/ros2_ws` tidak diubah.

Acuan daring yang diperiksa: [rulebook resmi SAUVC](https://sauvc.org/rulebook/), masih edisi **2026 v6.1.0**, pembaruan halaman 27 November 2025. Dimensi mengikuti teks serta label diagram, bukan skala piksel gambar. Ini arena latihan berbasis aturan 2026, belum validasi aturan 2027.

## Implementasi

- Satu launch dengan pilihan `arena:=qualification` atau `arena:=finals`.
- Kolam interior 25 × 16 m, kedalaman 1,2 m di ujung dan 1,6 m di tengah, dasar miring serta dinding dengan collision.
- Dua jalur kualifikasi, garis start 1 m, gerbang pada x=10 m dengan bukaan bersih 1,5 m serta penanda oranye.
- Final: start permukaan 1,4 × 1,4 m, gerbang pada x=16 m (bukaan 1,5 × 1 m), orange flare diameter 15 cm, tiga flare berwarna tinggi 80 cm/diameter 1,6 cm, serta empat drum terbuka diameter 60 cm/kedalaman 30 cm.
- AUV latihan kotak, kamera depan/bawah 640 × 480, odometri ground truth, serta `Twist` untuk gerak tiga dimensi/yaw. Gravitasi badan dimatikan; kendali ideal tanpa model thruster atau hidrodinamika.
- Wrapper Python 3.10 memuat Humble dan overlay lokal. ROS domain 86 dan Ignition partition `sauvc_practice` memisahkan eksperimen dari KKI. Virtualenv lokal menyediakan NumPy Python 3.10 untuk menghindari paket NumPy Python 3.12 sistem.

Arena dibuat sebagai SDF sementara oleh launch; properti berupa primitif lokal sehingga tidak memerlukan unduhan model. Generator juga bisa mengekspor file SDF. [README workspace](../ros2_ws/README.md) memuat koordinat, asumsi geometri, topic dan perintah lengkap.

## Bukti pemeriksaan langsung

`colcon build --symlink-install` melalui wrapper lulus. Lima tes `unittest` lulus, memeriksa persamaan permukaan collision lantai, bukaan gerbang, dimensi/zona properti, drum terbuka dan penanda visual. `ign sdf -k` menyatakan kedua arena **Valid**.

Pengujian runtime membuka simulator per arena, menunggu data ROS nyata, mengirim perintah menyelam/maju/berputar/berhenti dan memeriksa respons odometri. Pengujian memakai kamera aktif; tidak ada hasil sintetis dari executor HydroShips.

| Hasil | Kualifikasi | Final |
| --- | --- | --- |
| Pesan clock | 4397 | 4346 |
| Pesan odometri | 262 | 259 |
| Frame depan / bawah | 66 / 87 | 70 / 86 |
| Resolusi dan encoding | 640 × 480 RGB8 | 640 × 480 RGB8 |
| Z sebelum / sesudah menyelam | −0,050 / −0,447 m | −0,050 / −0,444 m |
| X sebelum / sesudah maju | 0,300 / 1,192 m | 0,700 / 1,590 m |
| Perubahan yaw | 0,739 rad | 0,739 rad |
| Setelah perintah berhenti | Perpindahan <5 cm selama 1 s | Perpindahan <5 cm selama 1 s |
| Pemeriksaan data + gerak + kamera | Lulus | Lulus |

GUI final juga dibuka dan diperiksa secara visual; kolam, start, gerbang, flare, serta empat drum tampil. Sudut pandang awal dan latar disesuaikan agar arena terlihat. Kedua uji headless menutup simulator serta bridge dengan bersih. Saat uji GUI dihentikan otomatis melalui `timeout`/SIGINT, wrapper Ruby Ignition melaporkan `Errno::ESRCH` saat shutdown; ini keterbatasan shutdown GUI yang masih dicatat, terpisah dari hasil kamera/gerak.

Artefak lokal diabaikan Git:

- [Hasil kualifikasi](../ros2_ws/evidence/qualification.json) dan [log](../ros2_ws/evidence/qualification.log).
- [Hasil final](../ros2_ws/evidence/finals.json) dan [log](../ros2_ws/evidence/finals.log).
- [Preview arena final](../ros2_ws/evidence/finals-arena-preview.png), [kamera depan final](../ros2_ws/evidence/finals-front.png), dan [kamera bawah final](../ros2_ws/evidence/finals-bottom.png).

## Batas dan langkah berikutnya

Uji ini membuktikan geometri arena, aliran data sensor dan respons perintah gerak. Belum menjalankan kualifikasi penuh, U-turn dan lintasan balik, atau tugas final secara autonomous. Belum tersedia FSM SAUVC, estimasi posisi berbasis sensor, deteksi objek, akustik pinger, pelepas/pengambil bola, bola flare dinamis, scoring/contact referee, randomisasi arena atau integrasi executor HydroShips. Posisi properti dan ketebalan konstruksi adalah asumsi latihan yang didokumentasikan.

Perintah kecepatan bertahan sampai diganti; menghentikan publisher tidak otomatis menghentikan AUV. Kirim Twist nol untuk berhenti. Langkah berikutnya adalah node tugas kualifikasi yang mengendalikan kedalaman, mendeteksi gerbang, melewatkan seluruh badan, berbalik, lalu kembali melalui gerbang dengan pemeriksaan benturan/surfacing.
