# Pelaksanaan BlueOS tanpa periferal

**Catatan historis:** dokumen ini merekam pengujian awal. Perbaikan platform/suhu dan frontend berikutnya dicatat pada [laporan 06](06-adaptasi-blueos-jetson.md). `compose.yaml` kini menggunakan adaptasi tersebut; profil asli disimpan sebagai `compose.upstream.yaml`.

Tanggal: 1 Oktober 2026. **Antarmuka dan layanan inti BlueOS 1.4.6 berhasil berjalan pada Jetson Orin NX yang tersedia.** Ini hasil uji meja tanpa kamera/Pixhawk; integrasi perangkat keras dan kesiapan robot belum terbukti.

Buka **http://127.0.0.1:8080** melalui browser di Jetson. Container `auv-blueos-bench-core-1` dibiarkan berjalan. Panduan menjalankan/menghentikan ada pada [README deployment](../deploy/blueos/README.md).

## Konfigurasi yang dijalankan

- Image resmi `bluerobotics/blueos-core:1.4.6`, ARM64, dikunci pada digest `sha256:729e10290212c4ec5b3d2978afac8fe6973d8b5e4a45dd26d73ba7d5fe8567a3`.
- Ubuntu 22.04.5 / L4T 36.4.7 host tetap digunakan. BlueOS berjalan sebagai container dengan basis Debian, bukan mengganti OS Jetson.
- [Compose](../deploy/blueos/compose.yaml): port hanya loopback 8080; empat volume persisten; batas RAM container 4 GiB; runtime `runc`; tanpa GPU/perangkat fisik, Docker socket, jaringan/PID host, atau mode privileged.
- `cable_guy`, `wifi`, `commander`, `kraken`, dan `versionchooser` dinonaktifkan. Fitur pengelolaan jaringan, perintah host, ekstensi, dan pembaruan versi belum tersedia pada profil ini.
- Pengguna memberikan ACL socket Docker untuk akun `aero`; akses sudah berhasil. Tidak ada container sebelumnya saat pemeriksaan awal. ACL dapat hilang ketika socket dibuat ulang.

Sumber implementasi: [rilis resmi 1.4.6](https://github.com/bluerobotics/BlueOS/releases/tag/1.4.6), commit `9b9e1643bc8cd2ca5ed843c0addde3d723475290`. Tidak ada patch kode BlueOS; penyesuaian dilakukan melalui Compose.

## Hasil pengujian

| Pemeriksaan | Hasil |
| --- | --- |
| Container dan nginx | Aktif; healthcheck `/status` berhasil |
| HTTP/API | 11 pemeriksaan lulus: frontend, nginx, schema helper/settings/autopilot, daftar serial, sumber/stream video, CPU, memori, MAVLink REST |
| Browser Chromium ARM64 | Halaman utama, Video Streams, dan System Information tampil; navigasi menu bekerja |
| Video | API aktif; tidak ada stream yang dikonfigurasi. Sumber sintetis/redirect bukan kamera DWE |
| Autopilot | API aktif; daftar serial kosong, firmware HTTP 503 karena tidak ada board berjalan |
| Restart container | Lulus; 11 pemeriksaan kembali berhasil dalam 19,5 detik sejak perintah restart. Status akhir `healthy` |

Bukti tersimpan:

- [Manifest versi](evidence/blueos-deployment-manifest.json), [HTTP awal](evidence/blueos-http-check.json), [HTTP setelah restart](evidence/blueos-http-after-restart.json), [hasil restart](evidence/blueos-restart-check.json).
- [Hasil browser termasuk error](evidence/blueos-browser-check.json), [status periferal/platform](evidence/blueos-peripheral-status.json).
- Screenshot [halaman utama](evidence/blueos-browser-home.png), [video](evidence/blueos-browser-video.png), dan [sistem](evidence/blueos-browser-system.png).

Browser pengujian memakai lingkungan Python terpisah di `/tmp/auv-blueos-browser`; browser tidak dipasang sebagai layanan sistem. Wizard dilewati dengan **Remind me later**, lalu dialog ditutup; tidak ada konfigurasi kendaraan atau firmware yang diterapkan. Nama **BlueROV2** pada tampilan adalah bawaan aplikasi, bukan identifikasi robot tim.

## Batas yang ditemukan

1. `/system-information/platform` mengembalikan HTTP 500 `UnknownModel`; pengenalan platform Jetson pada layanan ini belum berfungsi.
2. `/system-information/system/temperature` mengembalikan daftar kosong; widget suhu masih `Loading`. CPU, memori, dan disk tampil, tetapi informasi OS/proses/jaringan dibaca dalam konteks container dan tidak semuanya mewakili host.
3. Layanan yang dinonaktifkan menghasilkan HTTP 502/notifikasi. Browser juga mencatat error JavaScript terkait request tersebut. Tampilan berhasil dirender, tetapi antarmuka belum bebas error.
4. Tanpa autopilot, endpoint firmware/vehicle type mengembalikan 503 dan layanan video mencoba menyambung ulang ke MAVLink. Ini sesuai kondisi tanpa board; belum membuktikan komunikasi Pixhawk.
5. Beberapa aset/kustomisasi opsional yang belum dibuat menghasilkan 404/400. Akses langsung subhalaman pada image upstream dapat mengembalikan HTTP 404 meskipun shell tampil; mulai dari alamat utama dan gunakan menu.
6. Healthcheck Docker hanya menguji nginx. Gunakan skrip pemeriksaan HTTP untuk verifikasi layanan yang lebih luas.

## Langkah setelah tahap ini

Prioritas adaptasi berikutnya adalah pengenalan platform/suhu Jetson dan perapian fitur/notifikasi yang tidak tersedia. Sesudah itu, uji satu kamera DWE dan Pixhawk saat perangkat tersedia, termasuk kebutuhan akses perangkat dan GPU yang nyata.

Restart container tidak sama dengan reboot Jetson. Profil memakai `restart: no`: belum otomatis menyala setelah reboot. Uji boot otomatis, persistensi setelah pembuatan ulang container, stream kamera, MAVLink perangkat nyata, dan kendali robot masih menjadi pekerjaan P1/P2/P3 berikutnya.
