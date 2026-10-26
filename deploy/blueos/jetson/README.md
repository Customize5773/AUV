# Adaptasi Jetson untuk profil uji tanpa periferal

Basis: BlueOS 1.4.6, commit `9b9e1643bc8cd2ca5ed843c0addde3d723475290`. Modifikasi lokal ini bukan rilis resmi BlueOS atau validasi perangkat keras AUV.

## Isi

- `frontend.patch`: perubahan terhadap source resmi. Menghapus pemanggilan/kontrol layanan yang sengaja dinonaktifkan, menambahkan keterangan profil, melewati wizard perangkat, memperjelas konteks OS container, dan menunda listener parameter MAVLink untuk menghindari dependensi melingkar saat modul dimuat.
- `frontend-dist/`: hasil build yang sedang digunakan; dipasang baca-saja ke container.
- `monitor.py`: HTTP lokal port 9140; membaca model dan sensor melalui mount baca-saja. Tidak menjalankan perintah host atau menulis sysfs.
- `locations.conf` dan `nginx.conf`: meneruskan API platform/suhu ke adapter dan memperbaiki status HTTP halaman Vue saat dibuka langsung. Snapshot `/system-information/system` tetap berasal dari upstream; widget suhu diperbarui melalui endpoint suhu terpisah setiap dua detik.
- `start.sh`: menjalankan layanan upstream lalu adapter dalam sesi tmux; adapter dimulai ulang jika prosesnya berhenti.
- `test_monitor.py`: uji konversi mili-Celsius, ambang kritis, suhu puncak, dan sensor hilang/tidak valid.
- `check-browser.py`: pemeriksaan halaman/route, model/suhu, dan ketiadaan request layanan nonaktif. Memerlukan Python Playwright + Chromium ARM64; nama `HydroShips` menjadi ekspektasi khusus pengujian ini. Pada sesi ini lingkungan pengujian tersedia di `/tmp/auv-blueos-browser`.

`platform` mengembalikan objek `jetson`, bukan status Raspberry Pi palsu. API `model` tetap memakai linux2rest asli. Suhu puncak (`maximum_temperature`) adalah maksimum teramati sejak adapter dimulai, ditampilkan sebagai **Peak (session)**; bukan batas maksimum spesifikasi chip. Ambang kritis diambil dari trip point kernel; jika tidak ada, nilainya `null`/N/A. Status undervoltage/throttling khusus Raspberry Pi tidak tersedia.

## Build ulang

Persyaratan: Git, Docker, Python 3, serta [Bun 1.3.14](https://github.com/oven-sh/bun/releases/tag/bun-v1.3.14), sesuai versi pada Dockerfile upstream. Tidak perlu memasang Bun sebagai layanan atau mengubah OS. Dari root workspace:

```bash
BUN_BIN=/path/to/bun-1.3.14 bash deploy/blueos/jetson/build-frontend.sh
python3 deploy/blueos/jetson/test_monitor.py
docker compose -f deploy/blueos/compose.yaml up -d --force-recreate
python3 deploy/blueos/check-services.py
```

Script mengambil source pada commit terkunci, submodule pada commit upstream, dependensi dengan frozen lockfile, serta data parameter dari image terkunci. Build gagal jika patch tidak cocok. Direktori source build dipertahankan di `/tmp` untuk pemeriksaan; frontend sebelumnya disimpan di direktori build tersebut. Mount frontend mengacu ke direktori saat container dibuat, sehingga container harus dibuat ulang setelah build.

Lisensi source BlueOS tersedia dalam `LICENSE-upstream.md`; source asli dapat diperoleh melalui URL/commit di atas dan perubahan lokal seluruhnya ada dalam `frontend.patch`. Frontend menampilkan versi `jetson-bench/1.4.6-0-g9b9e1643` agar tidak dianggap build resmi yang tidak dimodifikasi.

## Rollback

```bash
docker compose -f deploy/blueos/compose.upstream.yaml up -d --force-recreate
```

Ini menggunakan image/frontend asli dan volume data yang sama. Adapter dan mount host baca-saja dilepas dari profil. Notifikasi/keterbatasan profil awal akan kembali. Untuk mengaktifkan adaptasi lagi, gunakan `compose.yaml`. Jangan menambahkan `down -v` jika ingin mempertahankan konfigurasi HydroShips.

Port tetap `127.0.0.1:8080`. Tidak ada akses kamera/Pixhawk/GPU atau startup otomatis setelah reboot. Uji browser dilakukan terpisah dari healthcheck; healthcheck terbaru memeriksa nginx dan ketersediaan sensor adapter.
