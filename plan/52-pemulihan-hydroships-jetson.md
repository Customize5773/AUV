# 52 — Pemulihan HydroShips Jetson

Tanggal: 4 November 2026. Ruang lingkup: memulihkan layanan aplikasi, tanpa mengubah parameter, arm, mode atau keluaran motor Pixhawk.

## Penyebab dan perbaikan

Unit user systemd masih menunjuk `/home/aero/AUV2027/hydroships`, padahal repo aktif berada di `/home/aero/AUV/hydroships`. Interpreter `.venv/bin/python` lama adalah tautan rusak (`unsupported reparse tag 0xa000000c`). Layanan berulang kali gagal start.

- Unit dan data lama dicadangkan di `/home/aero/.local/state/hydroships-recovery/20261104T024356` sebelum perubahan.
- Loop layanan dihentikan; environment Linux Python 3.10 dibuat di `.venv-recovery-20261104T024356` dengan `requirements.lock` yang sama dengan laptop, lalu paket dipasang editable tanpa mengubah dependensi.
- Environment lama dipertahankan sebagai `.venv.invalid-20261104T024356`; `.venv` kini symlink ke environment baru. Direktori environment baru tidak dipindah agar shebang tetap valid.
- Installer repo `bash scripts/install-service.sh` menghasilkan unit dengan working directory dan interpreter dari repo aktif. Tidak ada perubahan kode aplikasi atau parameter Pixhawk.

## Bukti penerimaan

1. Instalasi dependensi, `pip check` dan impor modul backend lulus.
2. Backend staging memakai port 8083, direktori data terpisah dan ROS dimatikan: health sehat, kendaraan disconnected, frontend HTTP 200. Proses staging dihentikan sebelum cutover.
3. Layanan produksi `active/running`, PID 6721. Tujuh sampel dengan interval sekitar lima detik semuanya menunjukkan API sehat, frontend HTTP 200 dan PID tetap. Counter restart historis 2220 tidak bertambah selama observasi; bukan berarti belum pernah restart.
4. `/api/autonomy` menunjukkan runtime `ready`, tanpa error, tanpa misi aktif. Driver tugas masih `synthetic`; ini bukan bukti kontrol fisik.
5. Versi backend 0.1.2, koneksi kendaraan tetap `disconnected`.

Bukti: [verification.json](../hydroships/evidence/jetson-recovery-20261104/verification.json), [persiapan](../hydroships/evidence/jetson-recovery-20261104/prepare-result.json), [cutover dan sampel](../hydroships/evidence/jetson-recovery-20261104/finish-result.json), [status ROS](../hydroships/evidence/jetson-recovery-20261104/autonomy.json).

## Batas

Pengujian ini memverifikasi startup dan aliran status aplikasi, bukan streaming kamera fisik, kendali thruster atau misi kolam. Suite lengkap backend dan uji reboot Jetson belum dijalankan. Binding layanan tetap loopback `127.0.0.1:8081`; akses laptop dapat memakai SSH tunnel. Backup unit/data dan environment lama tetap tersedia, tidak dihapus.
