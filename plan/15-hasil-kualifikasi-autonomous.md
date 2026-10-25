# Implementasi kualifikasi autonomous SAUVC

Tanggal: **25 Oktober 2026, Asia/Jakarta**. Pengguna menyetujui implementasi kualifikasi terlebih dahulu. **Status: kualifikasi autonomous selesai diimplementasikan dan diverifikasi pada model latihan ideal.**

## Acuan dan cakupan

[Rulebook terbit](https://sauvc.org/rulebook/) diperiksa ulang: **2026 v6.1.0**. [Usulan 2027 PR #25](https://github.com/sauvc/rulebook/pull/25) masih terbuka pada pemeriksaan sesi ini. Implementasi menggunakan dua jalur dan geometri 2026 yang sudah tersedia, tidak menyatakan kesesuaian terhadap geometri usulan 2027.

Alur: **menyelam -> melintas gate dengan seluruh badan -> menjauh secukupnya -> U-turn -> melintas gate kembali dengan seluruh badan -> langsung surface vertikal -> berhenti otomatis**. Waktu lintasan berhenti pada pelintasan balik lengkap. Surface berikutnya adalah penutup simulasi sesuai permintaan pengguna, bukan syarat tambahan poin kualifikasi.

## Implementasi

- `qualification.py`: FSM dengan umpan balik kedalaman/heading, deadline, pencarian gate terbatas, fase melintas dan urutan surface/stop terminal.
- `gate_detection.py`: deteksi pasangan tiang oranye pada frame kamera sebenarnya menggunakan NumPy, termasuk sisi balik yang lebih gelap; tidak memakai posisi gate ground truth sebagai pengganti citra.
- `referee.py`: pemeriksa independen untuk seluruh envelope termasuk bagian menonjol dan orientasi 3D, bukaan gerbang yang dipilih, U-turn, kontak, batas kolam, permukaan, serta penghentian aktual.
- `runtime.py`: adapter ROS untuk controller, pemeriksa dan pengawas perintah dalam proses berbeda; controller tidak menulis langsung ke Gazebo saat autonomous.
- `contact_monitor.cc`: membaca kontak fisika hull dan menerbitkan heartbeat kosong agar tidak adanya benturan dapat dibedakan dari sumber kontak yang tidak aktif.
- Launch manual tetap tersedia; `autonomous:=true` mengaktifkan kualifikasi. Mode `vision` menjadi default, `odom` adalah pembanding yang diberi label terpisah.

Odometri tetap ground truth untuk kedalaman, heading dan gerakan pendek ketika gate terlalu dekat untuk terlihat lengkap. Pada mode visual, estimasi bidang gate untuk fase tersebut berasal dari range/bearing citra terakhir. Pemeriksa boleh memakai geometri world yang diketahui dan tidak mempercayai klaim keberhasilan controller.

## Validasi

Pemeriksaan logika/geometri: **20 tes lulus**. Kedua world juga lulus validasi `ign sdf -k`. Build package dan plugin kontak berhasil.

| Pemeriksaan runtime | Bukti yang diperiksa |
| --- | --- |
| Tiga misi visual per jalur, dua jalur | Enam lintasan lengkap: pelintasan pergi penuh, U-turn, pelintasan balik penuh, surface sesudah finish, perintah nol dan posisi stabil |
| Offset +0,2 m / +10° dan −0,2 m / −10° | Kamera mengoreksi approach; kedua misi mencapai `DONE`; pengujian ulang cleanup keduanya bersih |
| Pembanding odometri | Misi penuh lulus, diberi label `odom` |
| Putus kamera, perintah, odometri, kontak dan clock | Lima skenario menghentikan gerak; alasan timeout sesuai gangguan terverifikasi, misi tidak dilaporkan berhasil |
| Proses controller dibekukan dengan SIGSTOP | Pengawas terpisah menghasilkan `guard:stale_command`; perintah nol dan kendaraan stasioner, tanpa mengandalkan controller yang dibekukan |
| Benturan hull–gate sengaja | Pesan kontak fisika menyebut hull AUV dan tiang gate; heartbeat kosong juga terbukti mengalir |
| Regresi qualification dan finals | Clock, odometri, dua kamera, dive/forward/yaw/stop tetap lulus |
| GUI | Misi mencapai `DONE`; penutupan otomatis terakhir melalui API `/server_control` bersih, tidak memerlukan pemaksaan |

Contoh run GUI terakhir: gerak mulai pada t=3,060 s, pelintasan pergi penuh t=41,276 s, U-turn terverifikasi t=53,550 s, pelintasan balik penuh t=64,464 s. Waktu lintasan **61,404 s simulasi**. Surface tercapai t=68,204 s dan stop terverifikasi t=69,292 s. Saat finish, pusat AUV x≈9,668 m dan seluruh envelope sudah bebas dari gate x=10 m; ascent berlangsung di lokasi tersebut, tanpa kembali ke dinding start.

Ringkasan akhir [verification.json](../ros2_ws/evidence/qualification-autonomous/verification.json) mencatat **19 pemeriksaan runtime lulus**, terpisah dari 20 tes logika/geometri. Matriks awal tetap disimpan sebagai riwayat diagnosis; hasil terakhir tiap kasus menjadi acuan ringkasan akhir. [Grafik lintasan](../ros2_ws/evidence/qualification-autonomous/qualification-trajectory.png) dan [cuplikan GUI](../ros2_ws/evidence/qualification-autonomous/qualification-gui.mp4) tersedia lokal; cuplikan video tidak mencakup seluruh fase awal misi.

Bukti sesi ini disimpan di [`ros2_ws/evidence/qualification-autonomous/`](../ros2_ws/evidence/qualification-autonomous/), terpisah dari bukti simulator dasar 22 Oktober. Hasil `passed` pada skenario gangguan berarti penghentian aman lulus; `mission_passed` tetap false.

## Perbaikan dari pengujian

U-turn pertama terlalu dekat sehingga kedua tiang tidak kembali masuk bidang pandang; kendaraan kini menjauh 1,8 m dari titik pelintasan keluar sebelum berputar. Ambang kecerahan awal tidak mengenali sisi balik gate yang berada dalam bayangan; perbandingan warna kini menerima sisi tersebut. Keduanya diberi pemeriksaan terarah, dan mode visual diuji ulang penuh.

Saat beberapa renderer dijalankan bersamaan, startup dapat membuat clock macet sebelum kendaraan bergerak. Pengawas menghentikan percobaan tersebut; misi kini menunggu clock maju sebelum mengaktifkan gerak. Ini tidak melonggarkan timeout saat lintasan berlangsung.

Proses GUI dan server dipisahkan di launch agar lifecycle dimiliki ROS launch, menghindari jalur fork Ruby yang sebelumnya menghasilkan `Errno::ESRCH`. Handler ROS mempertahankan context sampai penerbitan stop dan cleanup selesai, serta menandai permintaan berhenti tanpa melempar exception di tengah konversi pesan native. Runner GUI meminta server berhenti melalui API sebelum penutupan GUI.

Sebagian laporan matriks awal memuat keberhasilan lintasan tetapi kegagalan cleanup; hasil historis tersebut tidak dianggap bukti shutdown bersih. Run GUI terakhir, gangguan dan regresi setelah perbaikan diperiksa lagi. `mission_passed` dan `shutdown_clean` sengaja dipisahkan; `passed` runner terbaru membutuhkan keduanya. Penutupan interaktif melalui Ctrl+C masih memakai mekanisme signal/fallback milik ROS launch; hasil API runner tidak dijadikan bukti bahwa setiap kondisi renderer pada Ctrl+C selalu bersih.

Pada host Ubuntu 24.04 dengan Fortress berbasis 22.04, header Protobuf 3.12 disiapkan di workspace lokal untuk membangun plugin terhadap ABI terpasang; tidak mengganti paket sistem. Perintah persiapan dan menjalankan tersedia dalam [README workspace](../ros2_ws/README.md).

## Batas hasil

Model masih kotak dengan kecepatan ideal; tidak ada thruster, hidrodinamika, ArduSub atau kendali hardware. Pengujian ini tidak membuktikan performa kendaraan fisik. Misi ARENA, bola flare, payload drum, pinger dan Target Reacquisition belum diimplementasikan.


## Menjalankan

```bash
cd /home/rasya/AUV/ros2_ws
bash tools/ros.sh build --symlink-install
bash tools/ros.sh launch sauvc_sim arena.launch.py autonomous:=true
```

Gunakan `lane:=2` untuk jalur kedua dan `mode:=odom` hanya untuk pembanding berbasis koordinat. Petunjuk pemeriksaan dan dependensi lokal lengkap ada di [README workspace](../ros2_ws/README.md). Bukti JSON/video/grafik merupakan artefak lokal yang diabaikan Git; laporan ini menyimpan ringkasan hasil untuk repositori.


## Optimasi kecepatan start sampai surface

Permintaan lanjutan pengguna: memprioritaskan waktu tercepat dari start sampai surface. Default autonomous kini `speed_scale:=8.0`: maju maksimal 2,4 m/s, melintas 2,0 m/s, vertikal 1,6 m/s dan U-turn 4,0 rad/s. Controller dan pengawas memakai parameter yang sama; batas `(0, 8]` adalah batas profil simulasi yang diuji, bukan angka kemampuan thruster fisik.

Uji ulang pembanding 1× mencapai surface dalam **65.212 s** sejak gerak pertama. Enam percobaan visual nominal 8× (tiga per jalur) mencapai surface dalam **8.670–9.248 s**, median **8.806 s**: durasi berkurang **86.5%**, atau sekitar **7.41×** lebih cepat. Dua skenario offset ±0,2 m / ±10° juga lulus; seluruh delapan misi visual tersebut tetap melewati gate penuh dua arah, U-turn, tanpa benturan, lalu surface dan berhenti.

Koreksi heading dari citra dibatasi tersendiri sesuai kamera 10 Hz; di dekat gate AUV menyelesaikan alignment sebelum maju cepat. Menaikkan gain koreksi kamera secara langsung 8× terbukti membuat approach balik tidak stabil pada uji awal; perbaikan ini mencegah tambahan kecepatan berubah menjadi osilasi. Deadline, pemeriksa geometri, persyaratan U-turn, kontak dan kriteria surface tidak dilonggarkan.

**22 tes logika/geometri lulus**. Matriks profil cepat berisi enam misi nominal, dua offset, serta putus kamera, putus perintah dan pembekuan proses controller: **11 pemeriksaan lulus**, dengan perintah nol dan kendaraan stasioner pada gangguan. Bukti disimpan terpisah di [folder kecepatan](../ros2_ws/evidence/qualification-speed/); [perbandingan waktu](../ros2_ws/evidence/qualification-speed/comparison.json) mencatat angka di atas. Uji pembanding 1× memakai source yang sama dengan profil cepat. Durasi memakai waktu simulasi dari gerak pertama; preflight tidak termasuk. Clock/faktor real-time fisika tidak dipercepat untuk mendapatkan angka ini.

Result menambahkan `start_to_surface_elapsed` dan `start_to_stop_elapsed`; `elapsed` tetap durasi lintasan gate. Bukti awal 20 tes/19 pemeriksaan runtime di atas merupakan snapshot sebelum optimasi kecepatan. Profil cepat belum dikalibrasi pada hardware atau model hidrodinamika dan tidak membuktikan batas kecepatan maksimum global/kemampuan robot fisik.

Ulangan GUI profil cepat terakhir juga lulus: start sampai surface **8,908 s**, stop terverifikasi **10,030 s**, dan penutupan API server bersih. Satu percobaan GUI sebelumnya menyelesaikan misi tetapi macet saat teardown renderer; laporan kegagalan cleanup tetap disimpan dan tidak dihitung sebagai shutdown bersih.
