# 53 — Operasi SSH dan arsip GUI

4 November 2026. Pengguna mengonfirmasi operasi AUV tanpa GUI web: VS Code laptop mengedit repo Jetson melalui SSH wireless. GUI diminta dipindahkan ke `AUV/GUI-prototype`.

## Hasil implementasi

- Folder `hydroships` awalnya dipindahkan menjadi `GUI-prototype` pada laptop dan Jetson, termasuk source dan data lokal. Pengguna kemudian mengonfirmasi penghapusan folder GUI pada laptop; keadaan akhir mempertahankan arsip Jetson saja. Nama paket Python internal tetap `hydroships`; tidak diperlukan penggantian nama paket untuk mengarsipkan folder.
- Profil canonical tujuh thruster dipindahkan ke `config/propulsion.json`. Simulator dan GUI arsip memakai symlink relatif ke file itu. Simulator tidak bergantung pada folder GUI.
- Sebelum perpindahan Jetson, API diperiksa: kendaraan disconnected dan tidak ada misi berjalan. Unit `hydroships.service` dibackup, dinonaktifkan, dihentikan dan diarsipkan; setelah reload statusnya `not-found/inactive`, port 8081 tidak mendengarkan.
- Cadangan unit dan authorized_keys: `/home/aero/.local/state/auv-ssh-migration/20261104T025526`. Cadangan pemulihan laporan 52 tetap dipertahankan. Venv GUI yang ikut dipindah tidak dipakai kembali; perlu dibuat ulang jika arsip hendak dijalankan.
- SSH melalui Wi-Fi terbukti dari `192.168.67.123` ke Jetson `192.168.67.167`, menggunakan kunci publik laptop. Host key dibandingkan dengan koneksi Jetson yang sudah dikenal. Alias `auv-wifi` dan backup config SSH disimpan lokal. Extension Remote SSH sudah tersedia; perintah membuka workspace remote telah dijalankan. Interaksi editor secara visual belum diperiksa.
- `tools/auv.sh` menyediakan status/perangkat, telemetry pasif, capture kamera terbatas, serta start/stop/log simulator. Backend HTTP tidak digunakan. Environment `.venv-vehicle` terpisah dipasang dengan dependensi MAVLink terkunci dan `pip check` lulus.

## Validasi

| Pemeriksaan | Hasil |
|---|---|
| Unit simulator | 178 lulus |
| Tes profil pada GUI arsip | 3 lulus sebelum folder laptop dihapus pengguna |
| Tes operasi terminal | 4 lulus pada laptop, 4 pada Jetson |
| Kualifikasi melalui unit systemd laptop | DIVE hingga DONE; stop SIGINT bersih, tidak ada SIGKILL |
| Persistensi Jetson | Proses sleep uji mempunyai PID yang sama melalui dua koneksi SSH terpisah; kemudian dihentikan |
| Telemetry tanpa GUI | Capture pasif 10 detik, heartbeat/attitude/pressure/output diterima, disarmed |
| Status autopilot | `system_status=5` (CRITICAL); tahap ini tidak mengubah failsafe atau mengirim input pilot |
| Kamera awal | Timeout 20 detik pada konfigurasi yang ditemukan; dipertahankan sebagai kegagalan |
| Kamera final | MJPG 640 × 480, permintaan 30 FPS; 60 frame diterima, satu buffer drop; laporan interval sekitar 21–26 FPS |

`systemd-run --user` memisahkan simulasi dari terminal, tanpa autostart boot atau restart otomatis. Penghentian terminal pengamat log tidak menghentikan simulasi; operator memakai `sim-stop`. Kamera fisik diuji capture, belum dihubungkan ke persepsi ROS. Simulator dijalankan di laptop karena executable Gazebo `ign` tidak ditemukan pada Jetson saat pemeriksaan.

Bukti lokal: [verification.json](../evidence/ssh-migration-20261104/verification.json), [log simulator](../evidence/ssh-migration-20261104/simulation.log), [telemetry](../evidence/ssh-migration-20261104/telemetry.json), [capture kamera](../evidence/ssh-migration-20261104/camera-final.log), [persistensi sesi](../evidence/ssh-migration-20261104/session-persistence.json). Bukti diabaikan Git; panduan operasi ada di [CARA-OPERASI-SSH.md](../CARA-OPERASI-SSH.md).

Tes operasi sempat gagal pada sesi paralel setelah GUI lokal dihapus (laporan 54). Kontrak tes kini memeriksa profil canonical dan symlink simulator saja; GUI arsip bukan dependensi runtime. Empat tes operasi kembali lulus pada laptop.

## Yang belum ditutup

Alamat Wi-Fi masih DHCP. Tidak ada uji kehilangan sinyal radio, reboot, atau pemulihan visual editor. Capture kamera terbatas belum membuktikan 30 FPS stabil atau pengenalan target. Misi fisik ROS → Pixhawk, kalibrasi sensor/mixer dan mekanisme emergency stop fisik masih perlu diintegrasikan/diuji. `sim-stop` hanya menghentikan simulator. Tidak ada arm, perubahan parameter, mode atau keluaran motor pada tahap ini.

## Kondisi koneksi saat penutupan

Setelah pengujian berhasil, koneksi Wi-Fi ke `192.168.67.167` menjadi tidak terjangkau (`No route to host`). Sinkronisasi akhir revisi panduan dan tes ke Jetson gagal; source operasi yang sebelumnya teruji sudah berada di Jetson. Penyebab putusnya koneksi belum didiagnosis. Hasil SSH/Wi-Fi di atas merupakan bukti sebelum kejadian ini, bukan jaminan koneksi masih aktif.

## Kelanjutan: sinkronisasi dituntaskan

Pada pemeriksaan berikutnya tanggal 4 November 2026, Jetson kembali merespons. SSH Wi-Fi sempat berhasil tetapi satu koneksi kemudian timeout. Sinkronisasi dituntaskan melalui Ethernet `192.168.2.2`: enam berkas panduan/operasi diperiksa dengan SHA-256 yang sama, empat tes operasi Jetson lulus, dan layanan GUI tetap `not-found/inactive`. Salinan sebelum sinkronisasi berada di `/home/aero/.local/state/auv-ssh-sync/20261104T030411`. Penyebab koneksi wireless intermiten belum dipastikan; tahap ini bukan uji kestabilan Wi-Fi. Bukti: [sync-complete.json](../evidence/ssh-migration-20261104/sync-complete.json).

Kelanjutan diagnosis jaringan dan uji reboot terkontrol tersedia pada [laporan 56](56-wifi-reboot-dan-kesiapan-pixhawk.md).
