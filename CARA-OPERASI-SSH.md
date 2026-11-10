# Operasi AUV lewat SSH

Alur aktif: **VS Code laptop → Wi-Fi → SSH Jetson → program di Jetson**. GUI web lama diarsipkan di `/home/aero/AUV/GUI-prototype` pada Jetson; folder GUI laptop dihapus sesuai konfirmasi pengguna; layanan `hydroships.service` dinonaktifkan. Tidak diperlukan server HTTP untuk perintah di halaman ini.

## Membuka proyek

Pada laptop yang telah dikonfigurasi:

```bash
ssh auv-wifi
# Atau buka workspace Jetson langsung dari laptop:
code --remote ssh-remote+auv-wifi /home/aero/AUV
```

Di VS Code: `Remote-SSH: Connect to Host…` → `auv-wifi` → buka `/home/aero/AUV`. Terminal dan extension workspace berjalan di Jetson; file yang diedit adalah file Jetson. Simpan perubahan melalui Git secara sengaja; folder laptop tidak otomatis ikut berubah. Jangan melakukan sinkronisasi dua arah tanpa memeriksa perubahan kedua sisi.

Alias lokal pada `~/.ssh/config`:

```sshconfig
Host auv-wifi
    HostName 192.168.67.167
    User aero
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes
    ServerAliveInterval 15
    ServerAliveCountMax 3
```

Alamat di atas adalah DHCP Wi-Fi yang terverifikasi pada 4 November 2026, bukan alamat statis. Jika berubah, perbarui `HostName` setelah memeriksa alamat Jetson/AP. Reservasi DHCP pada router belum diterapkan. Host key Wi-Fi dicocokkan dengan host key Jetson yang sudah dikenal; jangan mematikan pemeriksaan host key. Private key tetap di laptop, tidak disalin ke AUV/repo.

## Jetson: perangkat dan telemetry

```bash
cd /home/aero/AUV
bash tools/auv.sh devices
bash tools/auv.sh telemetry /dev/serial/by-id/usb-ArduPilot_Pixhawk1_230021000D51383236333932-if00 --seconds 10
```

Pembaca telemetry bersifat pasif: menerima MAVLink tanpa mengirim heartbeat, kontrol, perubahan parameter atau permintaan stream. Jika autopilot tidak menyiarkan heartbeat, perintah gagal dengan `ok: false`; ini tidak membuktikan perangkat rusak. Jangan membuka perangkat yang sama dari aplikasi lain secara bersamaan. Nilai `SCALED_PRESSURE` belum membuktikan keberadaan sensor kedalaman eksternal.

Environment khusus pembaca ini sudah disiapkan pada Jetson. Untuk instalasi ulang:

```bash
python3 -m venv .venv-vehicle
.venv-vehicle/bin/python -m pip install -r tools/requirements-vehicle.txt
.venv-vehicle/bin/python -m pip check
```

ROS Humble tetap memakai Python sistem/wrapper workspace; jangan mengaktifkan venv GUI lama. Profil tujuh thruster bersama berada di [config/propulsion.json](config/propulsion.json); geometri mixer fisik tetap memerlukan kalibrasi.

## Kamera

```bash
bash tools/auv.sh camera-check /dev/v4l/by-id/usb-Sonix_Technology_Co.__Ltd._exploreHD_USB_Camera_SN00009-video-index0
```

Perintah mencoba menerima 60 frame pada MJPG 640 × 480 dengan permintaan 30 FPS, maksimal 20 detik. Frame dibuang, tidak dikirim ke laptop. Exit 124 berarti timeout; jangan menganggapnya lulus. Capture terbatas 60 frame telah berhasil; percobaan awal sebelum format/FPS disetel mengalami timeout. Satu buffer drop tercatat, sehingga 30 FPS stabil belum terbukti. Pengujian capture belum sama dengan deteksi objek, kalibrasi kamera atau integrasi kamera fisik ke ROS. Kamera simulator/persepsinya tetap dijalankan melalui launch SAUVC di bawah.

## Laptop: simulasi dan persepsi tanpa jendela

Gazebo tersedia pada laptop; pemeriksaan Jetson saat migrasi tidak menemukan executable `ign`. Jalankan simulator di laptop sampai dependensi Jetson memang diperlukan dan divalidasi.

```bash
cd /home/rasya/AUV
# Pilih satu:
bash tools/auv.sh sim-start qualification
# bash tools/auv.sh sim-start arena
# bash tools/auv.sh sim-start pinger

bash tools/auv.sh status
bash tools/auv.sh logs
# Ctrl+C hanya menutup pengamatan log. Menghentikan simulasi:
bash tools/auv.sh sim-stop
```

Wrapper menggunakan launch SAUVC yang sudah ada dengan `headless:=true`, kamera dan persepsi tetap aktif. Satu unit `auv-simulation.service` mencegah dua mode dimulai bersamaan melalui wrapper. Hentikan simulasi manual yang memakai domain/partition sama sebelum memakai wrapper. Jika workspace belum dibuild, jalankan `bash ros2_ws/tools/ros.sh build --symlink-install`.

Unit systemd berjalan terpisah dari terminal dan tidak otomatis restart atau dimulai saat boot. Menutup SSH/VS Code tidak menghentikannya. `sim-stop` mengirim SIGINT ke grup proses simulasi. Ini penghentian proses simulator, bukan emergency stop kendaraan fisik. Untuk POV simulator opsional, lihat [panduan simulator](ros2_ws/CARA-RUNNING.md).

## Putus koneksi dan batas integrasi fisik

Kelangsungan proses saat dua sesi SSH dibuka/ditutup telah diuji pada Jetson; putus sinyal radio, reboot dan pemulihan VS Code secara visual belum diuji. `Linger=yes` ditemukan pada Jetson. Tidak ada perubahan konfigurasi radio, router atau failsafe Pixhawk pada tahap ini.

Misi fisik ROS → Pixhawk belum dihubungkan. Perintah `sim-start` tidak menggerakkan Pixhawk. Sebelum menjalankan misi fisik, perlu adapter kontrol, pemeriksaan sensor, kalibrasi, mekanisme abort lokal dan kebijakan kehilangan pengawasan yang tervalidasi. Failsafe input pilot Pixhawk tetap berlaku; kontinuitas proses Linux tidak menghilangkan failsafe tersebut.

## Arsip GUI

Source, data dan environment lama ada di `/home/aero/AUV/GUI-prototype` pada Jetson. Folder GUI di laptop telah dihapus sesuai konfirmasi pengguna. Unit lama dicadangkan di `~/.local/state/auv-ssh-migration/20261104T025526/` pada Jetson. Venv/build yang dipindah mengandung path lama: buat ulang sebelum menghidupkan prototipe secara sengaja. Untuk membaca source/panduan GUI historis, buka folder arsip Jetson melalui Remote SSH. Tautan lama laporan ke folder GUI laptop merupakan lokasi historis.

## Uji terisolasi kamera fisik → ROS/persepsi

Uji ini tidak menjalankan misi atau membuka Pixhawk. Pastikan kamera tidak sedang dipakai aplikasi lain. Pada Jetson dengan OpenCV, NumPy dan ROS Humble tersedia:

```bash
cd /home/aero/AUV
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=187 ROS_LOCALHOST_ONLY=1
export PYTHONPATH="$PWD/ros2_ws/src/sauvc_sim:${PYTHONPATH:-}"
export FASTRTPS_DEFAULT_PROFILES_FILE="$PWD/ros2_ws/src/sauvc_sim/config/fastdds-images.xml"
timeout --signal=INT --kill-after=15 75 /usr/bin/python3 \
  ros2_ws/tools/check_physical_camera.py \
  /dev/v4l/by-id/usb-Sonix_Technology_Co.__Ltd._exploreHD_USB_Camera_SN00009-video-index0 \
  --seconds 30 --output /tmp/physical-camera-verification.json
```

Perlu source script/detektor dan profil XML tersedia di checkout Jetson. Bukti laporan 55 menggunakan salinan source laptop di direktori evidence terisolasi karena source Jetson berbeda; bukan sinkronisasi/deployment ke checkout Jetson. `timeout` membatasi uji bila driver capture macet. Periksa exit code **dan** `accepted` pada JSON; laporan parsial akibat kegagalan bukan bukti lulus.

Topik uji: `/physical_test/front/image_raw` dan `/physical_test/front/detections`. Penamaan `front` adalah peran input pengujian, bukan bukti orientasi pemasangan kamera. Kalibrasi masih pinhole simulator, sehingga jarak/arah metrik dan CameraInfo tidak boleh dipakai untuk kontrol fisik. Latensi diukur mulai pembacaan host selesai; bukan exposure-to-detection. Setelah capture berhenti, pengujian menunggu status stale lalu menghentikan proses persepsi.

Uji integrasi sintetis di laptop, tanpa kamera fisik:

```bash
cd /home/rasya/AUV
ROS_DOMAIN_ID=187 ROS_LOCALHOST_ONLY=1 \
  bash ros2_ws/tools/ros.sh python tools/test_physical_camera_check.py
```

## Wi-Fi dan reboot: hasil pemeriksaan 4 November 2026

Profil Wi-Fi Jetson kini menonaktifkan power saving dan terus mencoba autoconnect. Satu reboot terkontrol pulih ke SSH sekitar 47,5 detik; 30 koneksi Wi-Fi dan tiga siklus radio off/on lulus. Rekoneksi terukur 5,43–6,46 detik. Ini pengujian terbatas, bukan jaminan semua kondisi radio. IP masih DHCP.

GUI tetap nonaktif setelah reboot. Tidak ada misi fisik yang dimulai otomatis. Sebelum reboot berikutnya, hentikan proses pengujian dan simpan pekerjaan; terminal Remote SSH akan terputus dan perlu tersambung kembali.

Pixhawk pada uji ini hanya USB tanpa daya thruster; parameter propulsi cocok, tetapi uji gerak belum dilakukan. Detail, backup konfigurasi dan rollback: [laporan 56](plan/56-wifi-reboot-dan-kesiapan-pixhawk.md).
