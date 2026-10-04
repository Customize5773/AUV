# Cara Menjalankan dan Mematikan HydroShips (AUV2027)

> HydroShips adalah aplikasi yang berjalan di Ubuntu Jetson

## Catatan

- Langkah instalasi dan build biasanya cukup dilakukan sekali. Ulangi jika source atau dependensi frontend berubah.
- Jalankan aplikasi dengan **satu cara saja**: manual dari terminal **atau** sebagai layanan `systemd`. Jangan jalankan keduanya bersamaan.
- Alamat aplikasi: <http://127.0.0.1:8081>

## A. Persiapan dan build pertama kali

1. Buka Terminal.
2. Masuk ke folder aplikasi:

   ```bash
   cd ~/AUV2027/hydroships
   ```

3. Buat virtual environment Python:

   ```bash
   python3 -m venv .venv
   ```

4. Pasang dependensi Python:

   ```bash
   env -u PYTHONPATH .venv/bin/python -m pip install -r requirements.lock
   ```

5. Pasang aplikasi HydroShips ke virtual environment:

   ```bash
   env -u PYTHONPATH .venv/bin/python -m pip install --no-deps -e .
   ```

6. Masuk ke folder frontend:

   ```bash
   cd ~/AUV2027/hydroships/frontend
   ```

7. Jika perintah `npm` tidak ditemukan dan Node tersedia pada lokasi berikut, tambahkan Node ke `PATH`:

   ```bash
   export PATH="/home/aero/.local/share/hydroships-tools/node-v22.23.3-linux-arm64/bin:$PATH"
   ```

8. Pastikan Node.js dan npm tersedia. Node.js harus versi 22.12 atau lebih baru:

   ```bash
   node --version
   npm --version
   ```

9. Pasang dependensi frontend:

   ```bash
   npm ci
   ```

10. Build frontend:

    ```bash
    npm run build
    ```

11. Kembali ke folder HydroShips:

    ```bash
    cd ..
    ```

## B. Menjalankan manual dari terminal

1. Jika HydroShips berjalan sebagai layanan `systemd`, hentikan layanan terlebih dahulu:

   ```bash
   systemctl --user stop hydroships.service
   ```

   Jika layanan belum pernah dipasang, pesan bahwa unit tidak ditemukan bisa diabaikan.

2. Masuk ke folder aplikasi:

   ```bash
   cd ~/AUV2027/hydroships
   ```

3. Jalankan aplikasi:

   ```bash
   env -u PYTHONPATH .venv/bin/python -m hydroships
   ```

4. Tunggu sampai terminal menampilkan bahwa server berjalan.
5. Buka browser di Jetson dan kunjungi <http://127.0.0.1:8081>.
6. Buka halaman **Koneksi**, lalu pilih **Demo** untuk mencoba tanpa Pixhawk.
7. Biarkan terminal yang menjalankan aplikasi tetap terbuka.
8. Untuk mematikan aplikasi, fokuskan terminal tersebut lalu tekan **Ctrl+C**.

## C. Menjalankan sebagai layanan otomatis (opsional)

Pilih cara ini jika ingin mengelola aplikasi dengan `systemd`. Jangan jalankan HydroShips manual bersamaan.

1. Hentikan proses manual yang mungkin sedang berjalan dengan **Ctrl+C**.
2. Masuk ke folder aplikasi (frontend harus sudah dibuild):

   ```bash
   cd ~/AUV2027/hydroships
   ```

3. Pasang dan mulai layanan:

   ```bash
   bash scripts/install-service.sh
   ```

4. Periksa status layanan:

   ```bash
   systemctl --user status hydroships.service
   ```

5. Buka browser ke <http://127.0.0.1:8081>.
6. Untuk menghentikan aplikasi:

   ```bash
   systemctl --user stop hydroships.service
   ```

7. Untuk menjalankannya kembali:

   ```bash
   systemctl --user start hydroships.service
   ```

8. Untuk memulai ulang layanan:

   ```bash
   systemctl --user restart hydroships.service
   ```

9. Untuk melihat log:

   ```bash
   journalctl --user -u hydroships.service -n 50 --no-pager
   ```

## D. Mematikan Ubuntu Jetson

Langkah di atas hanya mematikan aplikasi HydroShips, bukan Ubuntu atau Jetson. Jika memang ingin mematikan seluruh Jetson, simpan pekerjaan terlebih dahulu, lalu jalankan:

```bash
sudo poweroff
```

Tunggu sampai Jetson benar-benar mati sebelum memutus daya.
