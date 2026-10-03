# HydroShips — implementasi versi pertama

Implementasi dimulai setelah pengguna menyetujui rencana aplikasi mandiri dengan fokus Jetson–Pixhawk. Pengguna kemudian menetapkan bahwa source harus berada dalam repositori **AUV2027**. Folder `hydroships/` kini berisi berkas biasa dalam Git AUV2027; gitlink yang sempat terbentuk sudah diganti dengan source aplikasi.

## Hasil

- Antarmuka Vue/TypeScript: Dashboard, Koneksi, Telemetri, Parameter, Sistem, dan Log; desktop serta ponsel.
- Backend FastAPI dengan satu thread pemilik I/O MAVLink, WebSocket ke browser, dan SQLite untuk konfigurasi/kejadian.
- USB serial dengan pilihan perangkat hasil pemindaian dan identitas stabil untuk reconnect. Transport ini sudah diimplementasikan, tetapi belum diuji pada Pixhawk fisik.
- Transport UDP lokal untuk simulator/perangkat lunak MAVLink eksternal. Demo bawaan menghasilkan paket MAVLink dan diberi penanda tersendiri.
- Pembacaan parameter lengkap dengan pengulangan indeks yang hilang, ekspor `.params`, perubahan satu nilai, dan verifikasi respons. Perubahan daftar/jumlah parameter mewajibkan pembacaan ulang.
- Koneksi putus membatalkan transaksi, mengosongkan cache kendaraan, dan mengganti ID sesi. Perubahan tidak otomatis diulang.
- CPU, RAM, penyimpanan, uptime, serta sembilan sensor thermal Jetson terbaca dari host.
- Maksimum 10.000 kejadian; rekaman telemetri JSONL dirotasi menjadi maksimal 8 berkas × 8 MiB.

Alamat utama: **http://127.0.0.1:8081**. Panduan pemasangan dan operasi ada di [README aplikasi](../hydroships/README.md).

## Bukti pengujian

| Pemeriksaan | Hasil |
| --- | --- |
| Build frontend + TypeScript | Lulus |
| Alur backend/API | 11 pengujian lulus; [output](../hydroships/evidence/backend-tests.txt) |
| Browser demo | Enam halaman desktop/mobile, tanpa overflow, perubahan parameter, ekspor, unduh log, disconnect; [hasil](../hydroships/evidence/browser-check.json) |
| Browser SITL baca-saja | Enam halaman, dialog parameter buka/batal, ekspor, unduh rekaman; [hasil](../hydroships/evidence/sitl-browser/browser-check.json) |
| ArduSub SITL ARM64 | Firmware 4.5.7; 1.377/1.377 parameter terbaca; [hasil](../hydroships/evidence/sitl-check.json) |
| Perubahan parameter SITL | `PILOT_SPEED_DN`: 0 → 1 → 0, seluruh respons dikonfirmasi; nilai awal dipulihkan |
| Putus/sambung SITL | Proses simulator dihentikan sementara dengan SIGSTOP lalu dilanjutkan SIGCONT; kehilangan heartbeat terdeteksi, sesi berganti, daftar parameter terbaca kembali |
| Restart/crash aplikasi | Restart biasa dan SIGKILL berhasil dipulihkan systemd, konfigurasi sama sebelum/sesudah; [hasil](../hydroships/evidence/service-check.json) |
| Startup otomatis | User service enabled dan `Linger=yes`; **reboot host belum diuji** |
| Uji ketahanan 60 menit | Lulus: 3.600,02 detik, 718 pemeriksaan, tanpa kegagalan; `completed: true`, `ok: true`; [hasil](../hydroships/evidence/soak-sitl.json) |
| Rotasi log setelah uji ketahanan | Lulus: maksimal delapan berkas, masing-masing tidak melebihi 8 MiB; [hasil](../hydroships/evidence/log-retention-check.json) |
| Pixhawk fisik, USB cabut/pasang | Belum diuji; perangkat belum tersedia pada pengujian ini |

Browser demo dan pemeriksaan awal SITL tidak mencatat error JavaScript, HTTP gagal, atau permintaan aset eksternal. Peringatan deprecation dari dependensi test client dicatat pada output pytest; seluruh pengujian tetap lulus.

Screenshot lokal: [dashboard demo](../hydroships/evidence/dashboard-demo.png), [parameter demo](../hydroships/evidence/parameters-demo.png), [dashboard ponsel](../hydroships/evidence/dashboard-mobile.png), [dashboard SITL](../hydroships/evidence/sitl-browser/dashboard-demo.png). Berkas hasil runtime/screenshot tidak dimasukkan ke Git oleh konfigurasi aplikasi; perintah untuk membuat ulang bukti tersedia di README.

## Simulator dan uji ketahanan

ArduSub dibangun native pada Jetson dari branch `Sub-4.5`, commit **`abe1721cf52535af6eb2340e5cabed430dac76b5`**. Hash SHA-256 binary saat diuji:

```text
3b6791d7482357138d3e6f373fd918384d6bf2bd23e9b2bf4dc1e05e9f045ef8
```

Source build berada di `/home/aero/.cache/hydroships/ardupilot-sub45`, virtualenv build di `/home/aero/.cache/hydroships/sitl-venv`. Konfigurasi: `waf configure --board sitl --disable-tests`; build: `waf sub -j4`. Dependency dan submodule mengikuti source ArduPilot tersebut. Simulator memakai model `vectored`, defaults `Tools/autotest/default_params/sub.parm`, kecepatan 1×, serta keluaran serial0 `udpclient:127.0.0.1:14560`. Tidak ada perintah arm atau gerak yang dikirim.

Uji ketahanan awal tidak valid karena ada permintaan koneksi baru selama pengukuran; arsipnya dipertahankan di `hydroships/evidence/soak-sitl-interrupted.json`. Uji berikutnya dipisahkan agar pemakaian dashboard utama tidak mengubah sesinya:

| Unit sementara | Fungsi |
| --- | --- |
| `hydroships-sitl.service` | Simulator untuk dashboard utama, UDP 14560 |
| `hydroships-validation.service` | Backend validasi pada loopback 8082, data terpisah di cache |
| `hydroships-sitl-validation.service` | Simulator validasi instance 1, UDP 14570 |
| `hydroships-soak.service` | Pemeriksaan baca-saja setiap lima detik selama 3.600 detik wall-clock |

Uji ketahanan memeriksa health HTTP, heartbeat, identitas sesi, kelengkapan parameter, pertambahan pesan, dan RSS aplikasi. Pengujian selesai pada 4 Oktober 2026, sekitar 00.15–01.15 WIB, selama 3.600,02 detik wall-clock. Seluruh 718 pemeriksaan lulus tanpa pergantian sesi atau kehilangan heartbeat yang terdeteksi. Penghitung pesan bertambah dari 1.666 menjadi 1.337.091 (1.335.425 pesan selama pengukuran). RSS berada pada 59,4–61,7 MiB.

Pada pemeriksaan akhir, backend dan simulator validasi serta simulator dashboard sudah tidak aktif. Layanan utama `hydroships.service` tetap aktif pada port 8081 dalam keadaan terputus dari kendaraan, siap untuk koneksi berikutnya. Unit simulator/validasi bersifat sementara dan tidak diaktifkan otomatis pada boot. Build frontend dan pemeriksaan browser baca-saja juga diulang setelah perubahan tema/favicon di workspace, dengan hasil lulus.

## Pekerjaan berikutnya yang memerlukan hardware

1. Identifikasi model dan firmware Pixhawk, lalu cadangkan parameter aktual.
2. Uji pemilihan USB, hak akses serial, deteksi heartbeat, dan seluruh pembacaan telemetri.
3. Uji cabut/pasang menggunakan identitas perangkat stabil; pastikan tidak berpindah ke perangkat lain.
4. Validasi sumber kedalaman dan acuan permukaan. `VFR_HUD.alt` saat ini ditampilkan sebagai altitude, bukan kedalaman.
5. Uji reboot Jetson saat pekerjaan desktop dapat dihentikan, kemudian periksa layanan, konfigurasi, dan koneksi ulang.

Kamera, flashing firmware, perintah aktuator, penggantian mode, dan pelaksana misi belum termasuk versi pertama yang disetujui.
