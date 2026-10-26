# Sinkronisasi konfigurasi 7 thruster

Tanggal: **26 Oktober 2026, Asia/Jakarta**. Konfigurasi yang diselaraskan: **T1–T4 horizontal, T5–T7 vertikal**, dengan output SERVO1–SERVO7 seperti [pembacaan Pixhawk](22-pixhawk-konfigurasi-7-thruster.md). Source mixer `CUSTOM_7T` dan geometri fisik rinci belum tersedia. Pekerjaan ini tidak mengganti firmware atau menulis parameter Pixhawk.

**Status: sinkronisasi profil dan pengujian software selesai.** Model simulator sudah tujuh thruster; HydroShips menampilkan serta merelay tujuh kanal. Ini bukan klaim bahwa geometri/matriks hardware telah berhasil direplikasi persis. Geometri arena tetap baseline **2026**; migrasi rulebook **2027.2.1** pada laporan 21 masih pekerjaan terpisah.

## Satu sumber profil

Profil canonical: [hydroships/backend/hydroships/propulsion.json](../hydroships/backend/hydroships/propulsion.json). File [ros2_ws/src/sauvc_sim/config/propulsion.json](../ros2_ws/src/sauvc_sim/config/propulsion.json) adalah symlink ke sumber tersebut. Build ROS menyertakannya di share/config; paket wheel HydroShips juga menyertakannya. Tidak ada salinan konfigurasi source kedua yang harus diperbarui manual.

Profil memuat nomor motor/output, fungsi output, kelompok horizontal/vertikal, parameter pembalik motor dari snapshot Pixhawk, serta geometri latihan. `hardware_mixer_verified=false` tetap eksplisit.

| Motor | Kelompok | Output | Fungsi | Arah parameter |
| --- | --- | --- | --- | --- |
| T1 | Horizontal | SERVO1 | 33 | +1 |
| T2 | Horizontal | SERVO2 | 34 | +1 |
| T3 | Horizontal | SERVO3 | 35 | −1 |
| T4 | Horizontal | SERVO4 | 36 | +1 |
| T5 | Vertikal | SERVO5 | 37 | −1 |
| T6 | Vertikal | SERVO6 | 38 | +1 |
| T7 | Vertikal | SERVO7 | 39 | −1 |

## Model simulator

Allocator Python dan plant C++ kini memakai **tujuh input/force**, termasuk watchdog, disarm, jalur error dan shutdown. Posisi/arah plant dikirim lewat SDF dari profil yang sama dengan allocator.

Empat thruster horizontal mempertahankan geometri latihan ±45° yang sebelumnya dipakai. Tiga vertikal diasumsikan pada dua titik depan `(0,18, ±0,15, 0)` m dan satu titik belakang `(−0,18, 0, 0)` m, dengan sumbu positif Z pada body FLU. Ini **asumsi**, bukan hasil pembacaan mixer Pixhawk. Parameter `MOT_x_DIRECTION` tidak dikalikan ulang ke gaya ideal: ia dicatat sebagai koreksi keluaran ESC pada hardware, sedangkan tanda gaya simulator mengikuti sumbu ideal yang didefinisikan profil.

Matriks alokasi berukuran **6×7**, rank 6 untuk geometri latihan ini. Target surge/sway/heave/yaw tetap berasal dari controller empat sumbu; target momen roll/pitch nol dipakai agar tiga vertikal tidak menimbulkan momen akibat pembagian gaya sama rata. Ini tidak menambahkan kontrol aktif roll/pitch atau membuktikan kemampuan 6-DoF kendaraan nyata. Gaya maksimum, drag, buoyancy, massa dan noise tetap koefisien latihan yang belum terkalibrasi.

## HydroShips dan relay ROS

Snapshot kendaraan memuat `propulsion`, dengan hasil perbandingan `FRAME_CONFIG`, SERVO1–7_FUNCTION dan MOT_1–7_DIRECTION terhadap profil. Status match berarti pemetaan parameter cocok, bukan matriks custom telah diverifikasi. Status berbeda/belum tersedia/stale ditampilkan terpisah.

SERVO_OUTPUT_RAW dipetakan ke `thruster_1_pwm`…`thruster_7_pwm` hanya saat fungsi output terkonfirmasi sebagai motor yang diharapkan. Output gripper atau motor di luar profil tidak ikut dihitung. Dashboard menampilkan tujuh baris, kelompok dan PWM teramati; data disembunyikan saat mapping tidak cocok/koneksi kedaluwarsa. Demo memakai profil yang sama dengan PWM sintetis dan label DEMO, tanpa klaim fisika atau gerak motor.

Metadata profil dan field PWM diteruskan melalui `/auv2027/vehicle/state`; jalur pengirim console dan expiry relay ikut diperbarui. `HYDROSHIPS_ROS_PYTHON` memungkinkan pemilihan interpreter child ROS yang sesuai ABI pada host pengembangan; default `/usr/bin/python3` dipertahankan untuk instalasi Jetson yang sesuai.

## Bukti penerimaan

- **86 tes simulator lulus**, termasuk dimensi/rank alokasi, penggunaan tiga vertikal dengan momen seimbang, disarm tujuh kanal dan kontrak geometri.
- Karakterisasi Gazebo lulus **8 pemeriksaan**, termasuk jumlah tujuh kanal, akselerasi, tracking, braking, drag, buoyancy dan thrust off.
- Dua misi kualifikasi dinamis lulus `DONE`/`COMPLETE`: jalur 1 nominal dan jalur 2 dengan offset −0,2 m/−10°. Keduanya surface, stasioner, perintah/thrust nol, navigasi dari estimasi sensor dan shutdown bersih. Ini dua run baru, bukan pengulangan seluruh matriks penerimaan lama.
- Gangguan aktuator lulus penghentian aman `ABORT`; keberhasilan gangguan bukan keberhasilan misi.
- **19 tes backend lulus termasuk integrasi ROS/DDS nyata**, tanpa skip pada run penerimaan akhir. Metadata tujuh motor diverifikasi pada subscriber terpisah.
- Build frontend/TypeScript dan tes frontend lulus. Browser desktop serta panel pada viewport 390 px diperiksa: tujuh baris, DEMO, PWM stale tersembunyi dan tidak ada error JavaScript. Halaman lama memiliki overflow horizontal 13 px pada ringkasan koneksi; panel baru tidak menambah overflow tersebut. Ini tidak dinyatakan sebagai penerimaan mobile seluruh aplikasi.
- Browser/worker HydroShips membaca **893 parameter Pixhawk** secara langsung; mapping sesuai, tujuh kanal tampil dan board tetap disarmed. Tidak ada event penulisan parameter. Tidak ada perintah arming, motor test, flashing atau perubahan output fisik yang ditambahkan.
- Paket wheel memuat profil canonical; konfigurasi terpasang ROS cocok dengan sumber.

Artefak: `ros2_ws/evidence/propulsion-7t/` untuk simulator dan `hydroships/evidence/propulsion-7t/` untuk backend/browser/device. Ringkasan [verification.json](../ros2_ws/evidence/propulsion-7t/verification.json) mencatat hasil dan hash source. Folder bukti lokal diabaikan Git. Log awal kegagalan setup/ABI tidak dihitung sebagai penerimaan akhir. Metadata `checked_on` pada tiga JSON run simulator masih memakai tanggal hardcoded runner lama (25 Oktober); eksekusi sinkronisasi ini dilakukan 26 Oktober dan dicatat pada ringkasan. Runner kini memakai tanggal dinamis zona Asia/Jakarta untuk run berikutnya; artefak lama tidak ditulis ulang diam-diam.

## Batas dan langkah lanjutan

Untuk meniru hardware secara tepat, diperlukan source mixer custom/tabel faktor dan posisi/sudut tiap thruster. Setelah tersedia, ubah geometri/asumsi yang sesuai dan ulangi penerimaan. Servo payload, supply, driver/kanal serta kalibrasi motor/kolam tetap belum dikonfirmasi atau diuji. Konfigurasi tujuh thruster ini tidak otomatis memigrasikan layout dan aturan simulator ke 2027.
