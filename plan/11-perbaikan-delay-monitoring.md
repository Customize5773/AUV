# Perbaikan jeda monitoring Pixhawk–Jetson

Tanggal: 12 Oktober 2026. Validasi menggunakan Pixhawk1 USB / ArduSub 4.1.0 yang tersambung langsung ke Jetson.

## Temuan dan perubahan

Snapshot telemetri sudah segar, tetapi `/api/live` dibatasi 2 Hz (setiap 500 ms). Halaman Autonomous mengambil telemetri melalui polling 1 Hz sehingga tampak lebih lambat.

WebSocket kini mengirim snapshot sekitar 10 Hz. Halaman Autonomous memakai snapshot live dari induk aplikasi; polling 1 Hz tetap digunakan untuk status runtime, graph, rencana, dan riwayat. Relay kendaraan menuju ROS 2 juga dinaikkan menjadi 10 Hz. Grafik tetap mengambil sampel setiap 500 ms agar jendela 120 titik tetap sekitar 60 detik.

## Hasil pengukuran

Probe membaca 40 snapshot melalui WebSocket lokal pada Jetson, sebelum dan sesudah layanan diperbarui.

| Metrik | Sebelum | Sesudah |
|---|---:|---:|
| Median interval pembaruan | 501,8 ms | 101,7 ms |
| Median usia sampel roll saat diterima klien | 69,9 ms | 58,2 ms |
| Usia maksimum sampel roll | 112,3 ms | 110,7 ms |

Interval pembaruan mengukur frekuensi pengiriman snapshot. Usia sampel dihitung dari timestamp penerimaan MAVLink oleh Jetson; bukan pengukuran waktu dari gerakan fisik sensor sampai layar. Hasil tidak mencakup latensi jaringan browser pada komputer lain.

Probe dapat diulang dari direktori `hydroships`:

```bash
env -u PYTHONPATH .venv/bin/python scripts/check-live-latency.py --output evidence/pixhawk/latency-after.json
```

## Validasi

- Build frontend berhasil; 15 tes backend dengan ROS 2 lulus.
- Layanan utama sudah menggunakan perubahan, terhubung kembali ke Pixhawk yang sama, dan runtime ROS siap.
- 893 parameter lengkap dan identik sebelum/sesudah restart. Pixhawk tetap disarmed; tidak ada misi dijalankan untuk validasi ini.
- Browser membaca enam halaman desktop tanpa mutasi API, error JavaScript, atau kegagalan HTTP; lebar 1280/1440/1920 tidak overflow.
- Subscriber ROS menerima enam frame kendaraan serial segar dengan counter MAVLink bertambah.
- Bukti lokal tersimpan di `hydroships/evidence/pixhawk/latency-before.json`, `latency-after.json`, `ros-latency.json`, dan `browser-latency/` (direktori evidence diabaikan Git).

Tidak ada perubahan baud rate, firmware, parameter Pixhawk, atau frekuensi stream yang diminta dari autopilot. Perubahan mengurangi jeda pada jalur monitoring aplikasi.
