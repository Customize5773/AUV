# BlueOS pada Jetson — pengujian tanpa periferal

Konfigurasi untuk Jetson Orin NX / Ubuntu 22.04 / L4T 36.4.7. Menggunakan image resmi BlueOS **1.4.6** untuk ARM64, dikunci pada digest, dengan frontend dan adapter Jetson lokal. Status terbaru dicatat dalam [laporan adaptasi](../../plan/06-adaptasi-blueos-jetson.md); [laporan awal](../../plan/05-blueos-tanpa-periferal.md) menyimpan kondisi sebelum adaptasi.

Dasar: [rilis 1.4.6](https://github.com/bluerobotics/BlueOS/releases/tag/1.4.6), commit `9b9e1643bc8cd2ca5ed843c0addde3d723475290`; contoh Compose dan skrip startup resmi ditelaah sebelum menyusun profil ini.

Profil ini menjalankan antarmuka dan layanan inti untuk evaluasi. Docker socket, perangkat periferal, jaringan host, dan PID host tidak dipasang. Pengelolaan Wi-Fi/Ethernet, commander, extension manager, serta version chooser dinonaktifkan; kontrol/pemanggilan otomatisnya dihilangkan dari frontend khusus ini. Model dan thermal sysfs dipasang baca-saja. Statistik proses/jaringan tetap berasal dari konteks container; ini belum validasi seluruh integrasi Jetson.

Tidak ada GPU pass-through, pengujian kamera, firmware upload, atau kendali aktuator pada tahap ini. Konfigurasi ini belum untuk robot produksi. Patch frontend, source adapter, instruksi build, dan rollback ada di [folder jetson](jetson/README.md). Image basis tidak diubah; berkas adaptasi dipasang dari workspace.

## Menjalankan

Dari direktori `/home/aero/AUV2027` dengan akun yang memiliki akses Docker:

```bash
docker compose -f deploy/blueos/compose.yaml config -q
docker compose -f deploy/blueos/compose.yaml pull
docker compose -f deploy/blueos/compose.yaml up -d
docker compose -f deploy/blueos/compose.yaml ps
```

Alamat di browser Jetson: **http://127.0.0.1:8080**. Port hanya diterbitkan pada loopback. Untuk komputer lain, gunakan SSH tunnel bila akses SSH sudah tersedia:

```bash
ssh -L 8080:127.0.0.1:8080 aero@ALAMAT_JETSON
```

Lalu buka alamat localhost yang sama pada komputer tersebut.

Muat ulang dengan **Ctrl+Shift+R** setelah perubahan frontend. Wizard otomatis tidak ditampilkan pada profil ini; pilih **Skip tour** jika tur pengantar muncul. Nama kendaraan tersimpan saat ini adalah **HydroShips**, hostname Beacon `hydro`. Status autopilot belum terhubung masih dapat muncul.

## Verifikasi dan penghentian

```bash
python3 deploy/blueos/check-services.py --output plan/evidence/blueos-http-check.json
docker compose -f deploy/blueos/compose.yaml logs --tail 100 core
docker compose -f deploy/blueos/compose.yaml restart core
```

Ulangi pemeriksaan HTTP setelah restart container. Lakukan pemeriksaan browser terpisah untuk memastikan aplikasi tampil dan API berfungsi; lulus HTTP saja tidak membuktikan rendering atau integrasi hardware.

Hasil adaptasi 1 Oktober 2026: 14 pemeriksaan HTTP/API, termasuk platform/suhu Jetson. Healthcheck Docker memeriksa nginx dan adapter sensor. Persistensi nama/hostname/pengaturan diuji dengan membuat ulang container. Bukti browser dan batas pengujian ada di laporan terbaru.

```bash
docker compose -f deploy/blueos/compose.yaml down
```

Perintah `down` mempertahankan volume konfigurasi dan data. Profil memakai `restart: no`; tidak otomatis aktif ketika host reboot.

## Akses Docker pada sesi

Pemeriksaan awal menunjukkan daemon aktif, tetapi akun sesi belum dapat membuka socket. Bila operator memberikan akses sementara melalui terminal lokal:

```bash
sudo setfacl -m u:aero:rw /var/run/docker.sock
```

Akses ini setara hak administratif melalui Docker, hanya untuk akun `aero`; kata sandi diisi lokal. Untuk menghapus entri ACL tambahan setelah pekerjaan:

```bash
sudo setfacl -x u:aero /var/run/docker.sock
```

Ini tidak mengubah grup permanen; akses dapat hilang saat socket dibuat ulang. Jangan mengganti izin socket menjadi dapat ditulis semua pengguna.
