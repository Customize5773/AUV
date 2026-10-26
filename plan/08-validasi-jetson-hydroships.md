# Validasi HydroShips langsung di Jetson

Diperiksa pada **4 Oktober 2026**, langsung pada Jetson yang menjalankan HydroShips. Pemeriksaan tidak melalui PC perantara. Pixhawk dan kamera tidak diperlukan untuk pemeriksaan host ini.

## Hasil

| Pemeriksaan | Hasil |
| --- | --- |
| Host | NVIDIA Jetson Orin NX Engineering Reference Developer Kit, ARM64, Ubuntu 22.04.5, L4T 36.4.7 |
| Proses aplikasi | Python lokal dalam user service `hydroships.service`, namespace filesystem sama dengan host |
| HTTP dan worker | Lulus; layanan aktif pada `127.0.0.1:8081` |
| Metrik CPU/RAM/disk/uptime | Cocok dengan pembacaan host; kapasitas RAM 15,28 GiB, filesystem data 115,38 GiB |
| Sensor thermal | Sembilan zona terbaca; rentang sampel 51,2–55,5 °C, selisih maksimum API/sysfs 1,281 °C karena waktu sampling |
| RAM proses HydroShips | Maksimum 53,2 MiB selama pengukuran |
| Restart layanan | Pulih dalam 1,003 detik, PID berganti dan konfigurasi tetap sama |
| Pemulihan setelah SIGKILL | Pulih otomatis dalam 4,011 detik; penghitung restart systemd bertambah |
| SQLite | `PRAGMA quick_check` menghasilkan `ok` setelah pengujian lifecycle |
| Startup | Unit enabled, `Linger=yes`; sebelum pengujian, proses teramati mulai 23,656 detik setelah boot saat ini |

Sepuluh sampel metrik diambil selama 27,207 detik. Semua 20 pemeriksaan pada eksekusi final lulus. Ini merupakan pemeriksaan saat beban desktop berjalan, bukan stress test termal/GPU. `tegrastats` berhasil membaca metrik native dan `nvpmodel -q` melaporkan MAXN; mode daya tidak diubah.

## Bukti dan batas pemeriksaan

- [Hasil final](../hydroships/evidence/jetson-check.json).
- [Pembacaan tool NVIDIA](../hydroships/evidence/jetson-native-tools.json).
- [Eksekusi awal dan bukti startup boot](../hydroships/evidence/jetson-check-initial.json): metrik dan restart lulus, tetapi tahap SIGKILL berhenti karena skrip memakai opsi systemd yang tidak tersedia pada versi host. Skrip diperbaiki ke `--kill-who=main`, lalu seluruh pemeriksaan diulang dan lulus.

Boot ID yang diamati: `e8093e0a-4286-45b1-9814-ce07b4b5726b`. Pengamatan startup tersebut menunjukkan layanan berjalan pada boot saat ini; **reboot terkontrol dengan pengukuran sebelum/sesudah belum dilakukan**. Sesi Jetson tidak direboot dalam pengujian ini. Integrasi Pixhawk, kamera, dan validasi kendaraan tetap menunggu periferal.

Untuk mengulang, dari `hydroships/` jalankan:

```bash
env -u PYTHONPATH .venv/bin/python scripts/check-jetson.py
# Opsional saat tidak terhubung ke kendaraan; memutus layanan web sementara:
env -u PYTHONPATH .venv/bin/python scripts/check-jetson.py --restart
```

Pengukuran ketahanan 60 menit dengan ArduSub SITL tercatat terpisah pada [laporan implementasi](07-hydroships.md).
