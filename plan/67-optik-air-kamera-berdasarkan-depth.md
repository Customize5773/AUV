# 67 — Optik air kamera berdasarkan depth render

14 November 2026, Asia/Jakarta. Melanjutkan visual kolam laporan 66 dengan **mode optik air opsional** untuk kedua kamera. Baseline tetap `water_attenuation=0`; parameter bukan ukuran kekeruhan air SAUVC yang telah diukur.

## Implementasi dan lingkup

[water_optics.py](../ros2_ws/src/sauvc_sim/sauvc_sim/water_optics.py) memproses gambar sebelum topic raw yang dipakai persepsi/navigasi. Saat aktif, dua sensor simulator menjadi RGBD pada resolusi tetap 640 × 480, 10 Hz. RGB jernih dan depth dipetakan ke `/sauvc/optics/{front,bottom}/{rgb,depth}`; hanya gambar berpengaruh air yang diterbitkan sebagai `/sauvc/camera_{front,bottom}/image_raw`. Konversi kamera mengikuti [implementasi RGBD Sensors 6 resmi](https://github.com/gazebosim/gz-sensors/blob/ign-sensors6/src/RgbdCameraSensor.cc).

RGB dan depth wajib memiliki timestamp capture yang sama. Cache dibatasi tiga capture per kamera, menolak replay output lama; kehilangan depth tidak menerbitkan ulang gambar sebelumnya. Header capture asli dipertahankan. Publisher/subscriber memakai BEST_EFFORT, keep-last satu frame. Bridge gambar tetap terpisah dari clock/sensor/kendali dan memakai profil SHM gambar yang sudah ada.

Depth hanya dipakai untuk membentuk efek optik, bukan estimasi posisi navigasi. Pengendali tetap memakai gambar, tekanan/IMU/magnetometer dan DVL virtual. Tidak mengubah thrust, model air/gaya, kecepatan, guard, referee atau batas freshness.

Untuk setiap kanal RGB digunakan pendekatan:

`I = J × exp(−k × r) + B × (1 − exp(−k × r))`

`r` diperoleh dari depth proyeksi dan faktor ray pinhole kamera. `k = water_attenuation × [1,4; 1; 0,7]` per meter, warna latar `B = [38; 82; 92]` pada skala 0–255. Nilai tidak hingga dipetakan ke batas depth, bukan menghasilkan NaN pada gambar. Ini model RGB homogen sederhana: bukan implementasi optik spektral terkalibrasi. [Akkaynak–Treibitz, CVPR 2018](https://openaccess.thecvf.com/content_cvpr_2018/html/Akkaynak_A_Revised_Underwater_CVPR_2018_paper.html) menjelaskan mengapa koefisien atenuasi dan backscatter nyata memerlukan model/pengukuran lebih rinci; angka latihan ini tidak disamakan dengan model revisi tersebut.

## Diagnosis performa dan percobaan awal

Percobaan pertama gagal preflight `startup_missing_data`, kendaraan tetap tanpa thrust dan shutdown bersih. Pengukuran lokal menemukan biaya filter sekitar 82 ms/frame, sehingga dua kamera 10 Hz melampaui kapasitas satu proses. Penetapan buffer ROS dari `bytes` menyebabkan validasi Python per elemen. Menggunakan `array('B', ...)` menghindari loop tersebut. Pada 50 frame sintetis resolusi penuh, p50 **18,66 ms**, p95 **25,97 ms** di laptop ini. Ini biaya filter saja, bukan latensi sensor-ke-kendali dan bukan benchmark Jetson. [Benchmark](../ros2_ws/evidence/water-optics-20261114/filter-benchmark.json).

Kualifikasi GUI/POV berikutnya lulus setelah perbaikan buffer. Antrean akhir kemudian dipastikan depth satu. Satu ARENA GUI berikutnya berakhir karena GUI Gazebo keluar sebelum preflight selesai; log tidak menunjukkan abort navigasi sebelum GUI berhenti. Penyebab penutupan GUI belum ditentukan. Bukti percobaan awal disimpan, tidak ditulis ulang. Penerimaan akhir memakai headless dengan rendering kamera aktif untuk memisahkan pengujian optik dari lifecycle jendela desktop.

## Verifikasi

Build dan tes unit: 191 tes lulus. Tes baru mencakup atenuasi nol, ketergantungan jarak/kanal, nilai depth invalid, ukuran/stride/endian, pasangan timestamp, cache terbatas, tanpa replay saat depth hilang, QoS antrean satu dan pemetaan bridge tanpa bypass RGB jernih.

Observer menerima sedikitnya lima pasangan RGB/depth/output untuk masing-masing kamera: nilai piksel berubah sesuai efek, timestamp/header tetap, publisher output tunggal BEST_EFFORT dan depth tidak dilanggan pengendali. Discovery FastDDS Humble melaporkan History UNKNOWN/depth 0, sehingga discovery tidak dipakai sebagai bukti depth antrean; nilai depth satu diverifikasi dari konfigurasi sumber dan tes unit. [Bukti observer](../ros2_ws/evidence/water-optics-20261114/acceptance/pairing.json).

**Empat pengujian akhir headless diterima**, pada kode akhir dengan antrean satu frame dan rendering kamera aktif:

| Pengujian | Hasil | Thrust–surface | Galat XY maksimum |
|---|---|---:|---:|
| Kualifikasi, air ringan 0,025/m | DONE, pelintasan penuh, surface/stop | 26,384 s | 1,75 cm |
| ARENA extended, air ringan, layout 1, Y–B–R, pinger drum 4 | DONE, 290,75574 poin, penalti 0; reacquisition, pickup dan retensi sampai surface | 208,142 s | 12,34 cm |
| Kualifikasi baseline, efek nonaktif | DONE, surface/stop | 26,020 s | 3,26 cm |
| Kehilangan kamera dengan mode air aktif | ABORT yang diharapkan; zero command, diam, gaya nol | Bukan misi selesai | Tidak dinilai sebagai akurasi misi |

Injeksi kehilangan kamera dimulai pada 34,756 s, setelah thrust pertama 26,618 s. Semua shutdown bersih dan PID launch berakhir. Fault dinilai terhadap respons abort yang benar, bukan syarat misi selesai/akurasi yang memang tidak dihitung untuk misi terputus. Observer akhir menerima tujuh pasangan depan dan lima pasangan bawah. [Verifikasi akhir](../ros2_ws/evidence/water-optics-20261114/acceptance/verification.json), [summary runner](../ros2_ws/evidence/water-optics-20261114/acceptance/runner.json), [hash source/aset](../ros2_ws/evidence/water-optics-20261114/acceptance/source-sha256.json).

Tidak ada klaim peningkatan waktu atau akurasi dari satu perbandingan ini. Matriks 18/18 laporan 65 belum diulang dengan efek air aktif. Kegagalan preflight awal, run GUI awal dan koreksi oracle discovery QoS tetap tersedia pada direktori bukti induk; tidak diganti menjadi hasil lulus. Tes unit pada profil akhir berjumlah **191**, bukan angka 190 sebelum tes QoS ditambahkan.

## Menjalankan

Dari root repo, build dahulu; kemudian pilih satu misi:

```bash
cd /home/rasya/AUV/ros2_ws
bash tools/ros.sh build --symlink-install

# Kualifikasi dengan efek air ringan
bash tools/ros.sh launch sauvc_sim arena.launch.py edition:=2027 autonomous:=true conditions_file:="$PWD/src/sauvc_sim/config/water-light.json"

# Atau ARENA
bash tools/ros.sh launch sauvc_sim arena.launch.py edition:=2027 arena:=finals autonomous:=true conditions_file:="$PWD/src/sauvc_sim/config/water-light.json"
```

POV tetap memakai topic annotated yang sama; lihat [CARA-RUNNING.md](../ros2_ws/CARA-RUNNING.md). Hilangkan `conditions_file` untuk baseline jernih. Berkas kondisi lain dapat menambahkan `"water_attenuation": 0.025`; nilai valid 0…0,5 per meter, tanpa mengubah `light_scale` atau parameter arus.

[Preview kamera depan dengan efek air](../ros2_ws/evidence/water-optics-20261114/acceptance/front-water.png) dan [pasangan jernih](../ros2_ws/evidence/water-optics-20261114/acceptance/front-clear.png) berasal dari capture yang sama.

## Batas

Belum ada hamburan multipel, partikel dinamis, refraksi, pemisahan medium udara–air sepanjang ray, kalibrasi spektral, kekeruhan kolam nyata atau gelombang fisik. Efek diterapkan pada gambar kamera, bukan fog global pada tampilan arena. RGBD menambah beban rendering/transport; kelulusan satu profil ringan tidak membuktikan seluruh rentang atenuasi atau semua perangkat. DWE fisik tidak memperoleh sensor depth baru dari fitur ini. Tidak ada aktuasi hardware pada tahap ini.
