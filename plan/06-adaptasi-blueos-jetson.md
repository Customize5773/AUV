# Adaptasi BlueOS–Jetson dan persistensi HydroShips

Tanggal: 1 Oktober 2026. Tindak lanjut profil awal pada [laporan 05](05-blueos-tanpa-periferal.md). Alamat tetap **http://127.0.0.1:8080**.

## Perubahan

1. **Antarmuka khusus profil uji:** kontrol dan pemanggilan otomatis untuk pengelolaan Wi-Fi/Ethernet, commander, extension manager, serta pembaruan BlueOS dikeluarkan dari antarmuka. Banner menjelaskan fitur yang belum tersedia. Wizard instalasi firmware tidak otomatis muncul. API kegagalan nyata tidak diganti dengan respons sukses palsu.
2. **Platform dan suhu Jetson:** adapter baca-saja menambahkan objek `jetson` pada API platform dan data sembilan sensor thermal Linux. Widget memperbarui suhu melalui endpoint terpisah setiap dua detik; snapshot sistem utama tetap memakai upstream. API `model` upstream tetap dipakai karena sebenarnya sudah dapat mengidentifikasi Orin NX; error `UnknownModel` sebelumnya berasal dari API `platform`.
3. **Konteks informasi:** tab About memberi label `Container OS` dan `Container hostname`. CPU/model/kernel dapat berasal dari host, tetapi statistik proses/jaringan tetap konteks container.
4. **Akses melalui port 8080:** redirect nginx dibuat relatif agar port tidak hilang pada probe MAVLink. Subhalaman Vue yang dibuka langsung sekarang mengembalikan HTTP 200.
5. **Inisialisasi frontend:** listener parameter MAVLink dimulai setelah evaluasi modul selesai. Ini mengatasi dependensi melingkar yang muncul saat build antarmuka disesuaikan.

Source/perubahan ada di [folder adaptasi](../deploy/blueos/jetson/README.md), termasuk patch, adapter, konfigurasi nginx, instruksi build ulang, dan rollback. Basis image tetap resmi BlueOS 1.4.6; frontend lokal diberi identitas `jetson-bench/1.4.6-0-g9b9e1643`.

## Pengujian dan bukti

- Empat unit test adapter memeriksa konversi mili-Celsius, trip point kritis, suhu puncak, dan kegagalan saat sensor hilang/tidak valid.
- Build frontend lulus validasi upstream atas 56 berkas JavaScript. Konfigurasi nginx dan Compose lulus pemeriksaan.
- [14 pemeriksaan HTTP/API](evidence/blueos-jetson-http.json) mencakup layanan awal serta adapter, platform, dan suhu.
- [Perbandingan suhu API dengan Linux](evidence/blueos-jetson-thermal-comparison.json): sembilan sensor sesuai, dengan toleransi 2°C untuk perubahan antara pembacaan berurutan.
- [Persistensi](evidence/blueos-jetson-persistence.json): `HydroShips`, `hydro`, dan data Bag of Holding sama sebelum dan sesudah pembuatan ulang container. Cadangan sebelum perubahan ada di `plan/evidence/blueos-backup/`.
- [Hasil browser](evidence/blueos-jetson/blueos-browser-check.json) menyimpan teks halaman serta error HTTP/JavaScript yang diamati. Screenshot: [utama](evidence/blueos-jetson/blueos-browser-home.png), [video](evidence/blueos-jetson/blueos-browser-video.png), [sistem/suhu](evidence/blueos-jetson/blueos-browser-system.png), [About/model](evidence/blueos-jetson/blueos-browser-about.png).
- Hasil browser akhir: tiga route langsung HTTP 200, model/suhu/HydroShips tampil, **nol exception JavaScript, nol HTTP 502, dan nol request ke layanan yang dinonaktifkan**. Respons tersisa adalah 503 vehicle type tanpa autopilot serta 404/400 untuk aset/kustomisasi opsional. Container akhir berstatus `healthy`.
- [Manifest hasil build](evidence/blueos-jetson-build.json) mencatat versi dan hash berkas.

## Cara menggunakan

Muat ulang halaman dengan **Ctrl+Shift+R** agar browser memakai frontend baru. Buka **System Information → System Monitor** untuk suhu, dan **About** untuk model. Tema/pilihan tampilan browser dapat berbeda dari browser pengujian.

Pemeriksaan rutin dari root workspace:

```bash
python3 deploy/blueos/check-services.py
docker compose -f deploy/blueos/compose.yaml ps
```

Healthcheck Docker sekarang mencakup nginx dan adapter sensor. Profil masih `restart: no`; belum otomatis aktif setelah reboot host.

## Batas pengujian

- Tidak ada kamera/Pixhawk. Status autopilot belum terhubung dan HTTP 503 pada data firmware/vehicle type tetap mungkin; belum ada pengujian kendali/telemetri perangkat nyata.
- Peak suhu adalah maksimum sejak adapter dimulai. Ambang kritis berasal dari trip point kernel; tidak ada berarti N/A. Deteksi undervoltage/throttling khusus Raspberry Pi tidak didukung oleh adapter.
- Data pengaturan telah diuji melalui pembuatan ulang container, bukan reboot Jetson atau pemulihan dari kerusakan disk. Nama mDNS `hydro` tersimpan, tetapi resolusi `hydro.local` dari komputer lain belum diuji pada bridge network ini.
- Aset kustom opsional yang belum dibuat masih dapat menghasilkan 404/400. Jangan mengartikan pengurangan notifikasi sebagai bukti semua fitur BlueOS telah tersedia.
