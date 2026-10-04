# HydroShips

Aplikasi onboard untuk Jetson–Pixhawk, bagian dari repositori **AUV2027**. Backend Python/FastAPI, antarmuka Vue/TypeScript, dan komunikasi pymavlink. Ubuntu Jetson tetap menjadi OS host.

## Menjalankan

Python 3.10+ dan Node.js 22.12+ diperlukan untuk pemasangan/build. Setelah build, layanan hanya memerlukan Python; aset browser disajikan lokal tanpa CDN.

Dari folder `hydroships/`:

```bash
python3 -m venv .venv
env -u PYTHONPATH .venv/bin/python -m pip install -r requirements.lock
env -u PYTHONPATH .venv/bin/python -m pip install --no-deps -e .
cd frontend
npm ci
npm run build
cd ..
env -u PYTHONPATH .venv/bin/python -m hydroships
```

Buka **http://127.0.0.1:8081**. Pada Jetson sesi pengembangan, Node tersedia di `/home/aero/.local/share/hydroships-tools/node-v22.23.3-linux-arm64/bin`; tambahkan direktori itu ke `PATH` saat menjalankan npm.

Untuk akses dari laptop melalui SSH:

```bash
ssh -L 8081:127.0.0.1:8081 aero@ALAMAT_JETSON
```

Kemudian buka alamat localhost yang sama pada laptop. Layanan default hanya mendengarkan loopback. Aplikasi belum memiliki akun/operator login untuk jaringan publik.

## Alur penggunaan

1. Buka **Koneksi**. Pilih USB serial, UDP lokal untuk SITL, atau demo.
2. Untuk Pixhawk, pilih perangkat dari daftar port dan baud rate yang sesuai. Identifikasi autopilot menggunakan heartbeat dan AUTOPILOT_VERSION.
3. **Dashboard** dan **Telemetri** menampilkan data yang diterima. Nilai yang tidak tersedia ditampilkan sebagai `—`; data kedaluwarsa diberi label.
4. **Parameter** membaca seluruh daftar otomatis, mengulang permintaan indeks yang hilang, dan menyediakan ekspor `.params`. Perubahan satu parameter memerlukan konfirmasi operator, ArduSub yang teridentifikasi, kondisi disarmed, serta daftar lengkap. Aplikasi memeriksa respons nilai dari autopilot.
5. **Sistem** menampilkan data Linux host dan sensor suhu Jetson. Nama kendaraan dapat disimpan dari halaman ini.
6. **Log** menyimpan riwayat kejadian dan rekaman pesan MAVLink yang diterima dalam JSONL. Unduh rekaman yang ingin dipertahankan sebelum rotasi menggantikannya.
7. **Autonomous** menyusun dan menguji alur misi menggunakan ROS 2 Humble di Jetson. Tersedia rencana bertahap, timeout, pembatalan, riwayat, ekspor JSON, dan diagnostik node/topic. Respons tugas bawaan sintetis; kendali kendaraan belum dihubungkan. [Panduan platform dan integrasi modul](ros2_ws/README.md).

Mode demo memakai kendaraan MAVLink sederhana dalam proses terpisah secara threading. Ini **bukan ArduSub SITL**, bukan simulasi fisika, dan bukan bukti hardware. Badge demo selalu tampil; data CPU/RAM/suhu tetap berasal dari Jetson nyata.

### Membandingkan cadangan parameter

Pada halaman **Parameter**, tunggu daftar lengkap lalu pilih tampilan **Bandingkan cadangan** dan klik **Pilih file**. Gunakan `.params` hasil tombol **Ekspor** pada **Daftar parameter**; formatnya lima kolom: system ID, component ID, nama, nilai, tipe. Ukuran maksimal 1 MiB. Komentar `#` dan baris kosong diterima; nama duplikat, angka/tipe tidak valid, atau beberapa target dalam satu file ditolak dengan nomor baris.

Hasil membedakan nilai/tipe yang berubah, parameter hanya di file, hanya di kendaraan, dan yang sama. FLOAT32 dibandingkan pada presisi protokol agar pembulatan desimal saat ekspor tidak menghasilkan perbedaan palsu. ID file yang berbeda ditandai; ID yang sama belum memastikan kendaraan fisik yang sama.

File diproses lokal di browser dan tidak diterapkan ke autopilot. **Unduh perbandingan** menyimpan JSON berisi nilai kedua sisi, waktu perbandingan, sesi, identitas, dan sumber koneksi. Hasil merupakan snapshot saat file dipilih; pilih ulang file untuk memperbaruinya. Hasil dibersihkan ketika koneksi/daftar parameter tidak lagi siap, sesi berubah, atau halaman Parameter ditinggalkan. Fitur ini bisa dicoba dengan demo tanpa hardware.

Nilai `Altitude autopilot` berasal dari `VFR_HUD.alt`, belum merupakan kedalaman terhadap permukaan air. Konversi kedalaman memerlukan pemeriksaan sensor, firmware, dan acuan permukaan pada perangkat nyata.

## Layanan systemd

Setelah pemasangan dan build selesai, hentikan proses manual pada port 8081, lalu:

```bash
bash scripts/install-service.sh
systemctl --user status hydroships.service
systemctl --user restart hydroships.service
journalctl --user -u hydroships.service -n 50 --no-pager
```

Unit berjalan sebagai pengguna biasa, memakai satu worker MAVLink, dan mulai ulang saat proses gagal. Secara default user service mulai saat pengguna login. Startup sebelum login memerlukan lingering:

```bash
loginctl enable-linger "$USER"
loginctl show-user "$USER" -p Linger
```

Perintah tersebut mengikuti kebijakan izin host. `enabled` atau `Linger=yes` belum membuktikan keberhasilan reboot; hasil reboot harus dicatat sebagai pengujian tersendiri. Aplikasi tidak menghubungkan perangkat otomatis setelah startup; pilihan koneksi terakhir tersedia di halaman Koneksi.

Untuk menghentikan/menghapus aktivasi otomatis:

```bash
systemctl --user disable --now hydroships.service
```

## Penyimpanan dan batas versi pertama

- Konfigurasi dan maksimum 10.000 kejadian berada di `.data/hydroships.sqlite3`; rekaman berada di `.data/telemetry/`, maksimal 8 berkas × 8 MiB. Direktori ini diabaikan Git.
- `HYDROSHIPS_DATA_DIR` dapat menentukan lokasi penyimpanan. Hentikan layanan sebelum menyalin seluruh direktori untuk backup, termasuk berkas SQLite WAL jika masih ada.
- Putus koneksi membatalkan operasi parameter tertunda, membersihkan cache kendaraan, dan membuat ID sesi baru. Perubahan tidak otomatis dikirim ulang. Jika timeout terjadi, baca ulang nilai: perangkat mungkin sudah menerapkannya sebelum respons hilang.
- Port serial hanya boleh dipilih dari hasil pemindaian. Sambung ulang otomatis memerlukan path `/dev/serial/by-id` dan nomor serial yang cocok. Port tanpa identitas stabil memerlukan koneksi ulang manual.
- Satu worker menangani seluruh I/O MAVLink. Sesi browser tidak membuka port sendiri. Autopilot lain dengan system/component ID berbeda tidak boleh mengubah data kendaraan terpilih.
- Perubahan parameter dibatasi pada tipe numerik ArduPilot yang didukung. Tipe integer diperiksa rentangnya dan ketepatan representasi float32. Batas semantik setiap parameter tetap mengikuti firmware; metadata rentang parameter belum diintegrasikan.
- Tidak ada perintah arm/disarm, ganti mode, kendali aktuator, flashing firmware, atau kamera. Pelaksana misi ROS 2 tersedia untuk uji software; algoritme autonomous dan adapter kendaraan belum diimplementasikan.
- Sistem ditujukan untuk satu operator pada Jetson/SSH tunnel. Pengaturan host/origin dibatasi untuk mencegah permintaan browser lintas situs; ini bukan pengganti autentikasi jika kelak dipublikasikan di jaringan.

## Pengujian

```bash
env -u PYTHONPATH .venv/bin/python -m pip install -e '.[test]'
env -u PYTHONPATH .venv/bin/python -m pytest -q
env -u PYTHONPATH .venv/bin/python -m playwright install chromium
env -u PYTHONPATH .venv/bin/python scripts/check-browser.py
cd frontend
npm test
cd ..
```

Pengujian browser menghubungkan **demo**, mengubah parameter demo, mengunduh hasil, memeriksa enam halaman desktop/mobile, lalu memutus demo. Skrip juga memeriksa pembandingan cadangan, ekspor laporan, penolakan file invalid/terlalu besar, peringatan ID berbeda, dan pembersihan hasil saat disconnect. Pembandingan diverifikasi tidak mengirim permintaan perubahan. Skrip menolak berjalan jika koneksi perangkat/SITL sedang aktif. `npm test` memakai test runner bawaan Node untuk parser dan perbandingan parameter.

Untuk memeriksa antarmuka dengan koneksi yang sudah aktif tanpa mengubah parameter atau koneksi:

```bash
env -u PYTHONPATH .venv/bin/python scripts/check-browser.py --read-only --output evidence/sitl-browser
```

Fokus antarmuka saat ini adalah browser desktop. Tambahkan `--desktop-only` untuk memeriksa enam halaman pada lebar 1280, 1440, dan 1920 piksel tanpa pengujian ponsel. Dashboard memisahkan status Jetson dari sumber autopilot; header tetap terlihat saat menggulir. Pada Parameter, daftar dan pembanding cadangan memiliki tampilan terpisah, dan kepala tabel tetap terlihat saat daftar digulir. Tautan keyboard **Lewati navigasi** membawa fokus langsung ke konten halaman.

Setelah terhubung ke simulator/perangkat yang hendak diuji, jalankan uji ketahanan baca-saja:

```bash
env -u PYTHONPATH .venv/bin/python scripts/soak.py --seconds 3600 --output evidence/soak.json
```

Hasil baru lulus jika `completed: true` dan `ok: true`. File diperbarui selama pengujian. Jangan mengganti koneksi atau restart layanan selama satu sesi uji.

Hasil pengujian dan pekerjaan hardware yang tersisa dicatat di [laporan implementasi](../plan/07-hydroships.md).

### Validasi langsung Jetson

Jalankan dari folder `hydroships/` pada Jetson yang menjalankan layanan lokal port 8081:

```bash
env -u PYTHONPATH .venv/bin/python scripts/check-jetson.py
```

Pemeriksaan mencocokkan proses aplikasi, model/arsitektur, CPU, kapasitas RAM/disk, uptime, dan sensor thermal dengan host; memeriksa startup systemd serta integritas SQLite. Sepuluh sampel diambil selama sekitar 27 detik. Bukti tersimpan di `evidence/jetson-check.json`.

Untuk menguji restart dan pemulihan proses setelah SIGKILL, putuskan koneksi kendaraan terlebih dahulu, kemudian tambahkan `--restart`. Opsi ini memutus layanan web sementara, memastikan PID berganti, dan membandingkan konfigurasi sebelum/sesudah. Skrip menolak tahap tersebut bila kendaraan masih terhubung. Pengujian tidak melakukan reboot Jetson atau mengganti mode daya. [Hasil validasi Jetson](../plan/08-validasi-jetson-hydroships.md).

### ArduSub SITL asli

Build opsional memerlukan Git, GCC/G++, make, rsync, Python/venv, serta internet saat mengambil source/dependensi. Script mengunci commit yang sudah diuji dan menggunakan cache di luar repositori:

```bash
bash scripts/build-sitl.sh
mkdir -p "$HOME/.cache/hydroships/sitl-manual"
cd "$HOME/.cache/hydroships/sitl-manual"
"$HOME/.cache/hydroships/ardupilot-sub45/build/sitl/bin/ardusub" \
  --model vectored --speedup 1 \
  --defaults "$HOME/.cache/hydroships/ardupilot-sub45/Tools/autotest/default_params/sub.parm" \
  --serial0 udpclient:127.0.0.1:14560 --serial1 none --serial2 none \
  --home=-35.363261,149.165230,0,0
```

Kemudian pilih **UDP lokal** dengan alamat `127.0.0.1:14560` pada halaman Koneksi. Jalankan hanya satu simulator pada port/instance yang sama. Simulator yang dibuat pada sesi pengembangan berjalan sebagai unit sementara `hydroships-sitl.service`; hentikan unit itu sebelum memakai perintah manual di atas. Firmware simulator tidak diunggah ke Pixhawk.

## Struktur

```text
hydroships/
├── backend/hydroships/   # API, pemilik koneksi MAVLink, monitor, penyimpanan, demo
├── frontend/src/         # Enam halaman Vue, state WebSocket, CSS lokal
├── scripts/             # Instalasi user service, verifikasi browser, uji ketahanan
├── tests/               # Alur protokol, kegagalan koneksi, API, persistensi
├── requirements.lock    # Versi dependensi runtime yang diuji
└── evidence/            # Hasil pengujian lokal, diabaikan Git
```

Referensi protokol: [MAVLink heartbeat](https://mavlink.io/en/services/heartbeat.html), [parameter](https://mavlink.io/en/services/parameter.html), [pymavlink](https://mavlink.io/en/mavgen_python/). Arsitektur fitur mengacu pada [BlueOS](https://blueos.cloud/docs/latest/development/core/); aplikasi ini tidak menyalin source BlueOS atau GUI-ROV.
