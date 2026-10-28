# Cara menjalankan kualifikasi dan ARENA SAUVC 2027

Gunakan **tiga terminal**: satu untuk simulator, satu untuk POV depan, dan satu untuk POV bawah. Pilih salah satu misi pada Terminal 1.

**Tampilan atas arena** ada di jendela Gazebo; atur sudut pandangnya dengan mouse. Kamera AUV yang tersedia adalah **kamera depan dan bawah**, bukan kamera atas. Perintah POV di panduan ini menampilkan label deteksi.

## 1. Persiapan

Untuk penggunaan pertama atau setelah kode simulator berubah, jalankan:

```bash
cd /home/rasya/AUV/ros2_ws
bash tools/ros.sh build --symlink-install
```

Tidak perlu build ulang setiap kali menjalankan misi. Virtualenv HydroShips boleh tetap aktif; wrapper `tools/ros.sh` memilih Python ROS sendiri.

## 2. Terminal 1 — pilih misi

### Kualifikasi otomatis

Alur: menyelam → melewati gate seluruh badan → U-turn → melewati gate kembali → surface → stop.

```bash
cd /home/rasya/AUV/ros2_ws
export ROS_DOMAIN_ID=86
export IGN_PARTITION=sauvc_practice
bash tools/ros.sh launch sauvc_sim arena.launch.py edition:=2027 arena:=qualification autonomous:=true lane:=1
```

Ganti `lane:=1` menjadi `lane:=2` atau `lane:=3` untuk jalur lainnya. Waktu kualifikasi resmi berakhir setelah pelintasan penuh kedua; surface–stop merupakan penutup tambahan proyek.

### ARENA — blue drum

Alur: menyelam → menghindari orange flare → melewati gate → menjatuhkan bola flare sesuai urutan → drop payload ke blue drum → menuju Surfacing Square → surface → stop.

```bash
cd /home/rasya/AUV/ros2_ws
export ROS_DOMAIN_ID=86
export IGN_PARTITION=sauvc_practice
bash tools/ros.sh launch sauvc_sim arena.launch.py edition:=2027 arena:=finals autonomous:=true flare_order:=B-R-Y
```

`B-R-Y` berarti biru → merah → kuning. Masukan urutan ini mewakili urutan yang diberikan penyelenggara simulasi sesudah Navigation.

### ARENA tambahan — pinger dan pickup

Mode ini memilih red drum berpinger, keluar sepenuhnya dari target zone setelah drop, kemudian mengambil kembali bola yang sama dan mempertahankannya sampai surface di Square.

```bash
cd /home/rasya/AUV/ros2_ws
export ROS_DOMAIN_ID=86
export IGN_PARTITION=sauvc_practice
bash tools/ros.sh launch sauvc_sim arena.launch.py edition:=2027 arena:=finals autonomous:=true extended:=true flare_order:=B-R-Y
```

## 3. Terminal 2 — POV kamera depan

Gunakan perintah yang sama untuk kualifikasi maupun ARENA:

```bash
cd /home/rasya/AUV/ros2_ws
export ROS_DOMAIN_ID=86
export IGN_PARTITION=sauvc_practice
bash tools/ros.sh run rqt_image_view rqt_image_view /sauvc/perception/front/image_annotated
```

## 4. Terminal 3 — POV kamera bawah

```bash
cd /home/rasya/AUV/ros2_ws
export ROS_DOMAIN_ID=86
export IGN_PARTITION=sauvc_practice
bash tools/ros.sh run rqt_image_view rqt_image_view /sauvc/perception/bottom/image_annotated
```

Susun ketiga jendela agar Gazebo dan kedua POV terlihat bersamaan. Jika gambar kecil, perbesar jendela viewer. Jika topic belum terpilih, pilih topic yang sesuai pada dropdown dan gunakan transport `raw` bila tersedia.

Untuk POV tanpa label, ganti topic depan dengan `/sauvc/camera_front/image_raw` dan topic bawah dengan `/sauvc/camera_bottom/image_raw`.

## 5. Menghentikan, mengulang, atau berganti misi

1. Tekan **Ctrl+C di Terminal 1**, lalu tunggu proses simulator selesai.
2. Jalankan kembali salah satu perintah misi di Terminal 1. Jangan menjalankan dua arena bersamaan pada domain/partition yang sama.
3. Viewer dapat tetap terbuka selama berganti misi. Saat simulator berhenti, gambar dapat menampilkan status kamera stale; gambar kembali setelah simulator baru mengirim frame. Jika viewer ikut tertutup, jalankan kembali Terminal 2/3.
4. Untuk menutup semuanya, tutup kedua jendela viewer atau hentikan Terminal 2/3 juga.

`DONE` dan `ABORT` adalah status terminal. Mengulang misi memerlukan restart launch. Menutup jendela Gazebo juga menutup launch simulator.

## 6. Jika ada masalah

### PyQt5 / PyQt5.sip tidak ditemukan

Binding Qt sudah dipasang pada laptop ini. Jika menyiapkan ulang virtualenv ROS, jalankan:

```bash
cd /home/rasya/AUV/ros2_ws
python3 -m pip --python .venv-ros310/bin/python install --ignore-installed PyQt5==5.15.11
```

Kemudian ulangi perintah viewer melalui `bash tools/ros.sh`.

### POV kosong

Pastikan simulator masih berjalan, `cameras` dan `perception` tidak dinonaktifkan, serta ketiga terminal memakai `ROS_DOMAIN_ID=86` dan `IGN_PARTITION=sauvc_practice` seperti contoh. Periksa publisher kamera dari terminal tambahan:

```bash
cd /home/rasya/AUV/ros2_ws
export ROS_DOMAIN_ID=86
export IGN_PARTITION=sauvc_practice
bash tools/ros.sh topic info /sauvc/perception/front/image_annotated
bash tools/ros.sh topic info /sauvc/perception/bottom/image_annotated
```

### Misi abort karena stale_front / stale_bottom

Pesan ini berarti hasil kamera valid dengan timestamp baru tidak diterima selama batas pengaman. Jangan melanjutkan run yang sudah `ABORT`; hentikan launch, pastikan hanya satu simulator berjalan, lalu ulangi. Catat pesan tambahan tentang jeda frame dan timestamp jika terulang.

POV berlabel dibatasi maksimal **5 FPS wall clock** untuk mengurangi beban tampilan; kamera tetap dikonfigurasi **10 Hz simulasi**. Batas pengaman kamera tetap 2 detik. Detail perbaikan dan keterbatasan: [laporan 25](../plan/25-perbaikan-pov-dan-stale-camera.md).

Panduan ini untuk simulator. Kualifikasi dan ARENA autonomous visual memakai model gaya tujuh thruster serta estimator sensor secara default; ground truth hanya untuk referee/pencatat. Gunakan `vehicle_model:=ideal` untuk pembanding historis. Detail: [laporan 26](../plan/26-arena-dinamika-dan-estimasi-sensor.md); perintah di atas tidak menjalankan output thruster/servo hardware. Detail teknis: [README workspace](README.md).


## 7. Verifikasi otomatis dengan Gazebo dan kedua POV

Perintah ini menjalankan misi penuh, menyimpan bukti, lalu menutup simulator dan viewer setelah pengujian. Pilih folder output baru agar bukti sebelumnya tetap tersimpan. Hentikan launch lain pada domain/partition yang sama dahulu.

```bash
cd /home/rasya/AUV/ros2_ws
export ROS_DOMAIN_ID=222
export IGN_PARTITION=sauvc_gui_verification
bash tools/ros.sh python tools/check_arena.py --vehicle-model dynamic --gui --pov --output evidence/gui-verification/blue.json
```

Untuk pinger/pickup, tambahkan `--extended --scene-variant 1 --blue-drum 3 --pinger-drum 4 --order Y-B-R` dan gunakan output berbeda. `--pov` memerlukan `--gui`; viewer yang keluar selama run menggagalkan verifikasi tampilan.

Estimator melakukan kalibrasi bias DVL horizontal pada preflight dengan asumsi kendaraan ditahan diam; setelah DIVE atau perintah gerak, estimasi bias dibekukan. Sampel tidak cukup berarti koreksi tidak diterapkan. Spawn simulator tidak memiliki penahan mekanik: arus sejak preflight dapat membuat gerakan kendaraan ikut dipelajari sebagai bias. Rincian penerimaan awal: [laporan 27](../plan/27-kalibrasi-dvl-dan-penerimaan-gui.md); pengujian arus: [laporan 30](../plan/30-pengujian-keandalan-berulang.md). Prosedur belum divalidasi pada AUV fisik.

## 8. Pengujian keandalan berulang tanpa jendela

Matriks terdiri dari 12 kualifikasi dan enam ARENA, dengan variasi seed sensor, prior posisi, pencahayaan dan arus. Runner menjalankan kasus satu per satu pada domain 230/partition `sauvc_reliability_matrix`. Hentikan simulator lain yang memakai pasangan tersebut; jangan mengubah source selama batch.

```bash
cd /home/rasya/AUV/ros2_ws
bash tools/ros.sh build --symlink-install
bash tools/ros.sh python tools/check_reliability.py --output evidence/reliability-run-01
```

Folder output wajib baru. `summary.json` menyimpan seluruh hasil, termasuk kegagalan; exit code 1 berarti ada kasus yang tidak diterima. Gunakan `--suite qualification`, `--suite arena`, atau `--case q-prior-91` untuk membatasi pengujian. Ctrl+C menghentikan harness aktif dan mencatat kasus terputus. Hasil dan batas pembuktian ada pada [laporan 30](../plan/30-pengujian-keandalan-berulang.md).
