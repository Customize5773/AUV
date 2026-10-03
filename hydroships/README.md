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

Mode demo memakai kendaraan MAVLink sederhana dalam proses terpisah secara threading. Ini **bukan ArduSub SITL**, bukan simulasi fisika, dan bukan bukti hardware. Badge demo selalu tampil; data CPU/RAM/suhu tetap berasal dari Jetson nyata.

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
- Tidak ada perintah arm/disarm, ganti mode, kendali aktuator, flashing firmware, kamera, atau pelaksana misi dalam versi ini.
- Sistem ditujukan untuk satu operator pada Jetson/SSH tunnel. Pengaturan host/origin dibatasi untuk mencegah permintaan browser lintas situs; ini bukan pengganti autentikasi jika kelak dipublikasikan di jaringan.

## Pengujian

```bash
env -u PYTHONPATH .venv/bin/python -m pip install -e '.[test]'
env -u PYTHONPATH .venv/bin/python -m pytest -q
env -u PYTHONPATH .venv/bin/python -m playwright install chromium
env -u PYTHONPATH .venv/bin/python scripts/check-browser.py
```

Pengujian browser menghubungkan **demo**, mengubah parameter demo, mengunduh hasil, memeriksa enam halaman desktop/mobile, lalu memutus demo. Skrip menolak berjalan jika koneksi perangkat/SITL sedang aktif.

Untuk memeriksa antarmuka dengan koneksi yang sudah aktif tanpa mengubah parameter atau koneksi:

```bash
env -u PYTHONPATH .venv/bin/python scripts/check-browser.py --read-only --output evidence/sitl-browser
```

Setelah terhubung ke simulator/perangkat yang hendak diuji, jalankan uji ketahanan baca-saja:

```bash
env -u PYTHONPATH .venv/bin/python scripts/soak.py --seconds 3600 --output evidence/soak.json
```

Hasil baru lulus jika `completed: true` dan `ok: true`. File diperbarui selama pengujian. Jangan mengganti koneksi atau restart layanan selama satu sesi uji.

Hasil pengujian dan pekerjaan hardware yang tersisa dicatat di [laporan implementasi](../plan/07-hydroships.md).

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
