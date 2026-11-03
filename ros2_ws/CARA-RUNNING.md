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
bash tools/ros.sh python tools/pov_viewer.py front
```

## 4. Terminal 3 — POV kamera bawah

```bash
cd /home/rasya/AUV/ros2_ws
export ROS_DOMAIN_ID=86
export IGN_PARTITION=sauvc_practice
bash tools/ros.sh python tools/pov_viewer.py bottom
```

Susun ketiga jendela agar Gazebo dan kedua POV terlihat bersamaan. Jika gambar kecil, perbesar jendela viewer. Penampil langsung berlangganan gambar berlabel pada kamera yang dipilih; tidak perlu memilih topic. Tutup melalui tombol jendela atau Ctrl+C pada terminal viewer. Penampil berjalan dalam satu proses Qt/ROS agar shutdown tidak meninggalkan anak proses RQt.

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

Model dinamis kini memakai penahan fisik virtual saat preflight. Kalibrasi bias DVL horizontal memerlukan sinyal `deployment_held=true`; penahan dilepas pada thrust pertama dan tidak dipasang kembali saat stop. Setelah DIVE, perintah gerak atau pelepasan penahan, estimasi bias dibekukan. Sampel tidak cukup berarti koreksi tidak diterapkan. Ini memodelkan kendaraan yang benar-benar ditahan saat penempatan, bukan kalibrasi saat bebas hanyut. Perintah launch tetap sama. Rincian: [laporan 31](../plan/31-kalibrasi-dvl-dalam-arus.md). Prosedur serta konfirmasi penahan belum divalidasi pada AUV fisik.

## 8. Pengujian keandalan berulang tanpa jendela

Matriks terdiri dari 12 kualifikasi dan enam ARENA, dengan variasi seed sensor, prior posisi, pencahayaan dan arus. Runner menjalankan kasus satu per satu pada domain 230/partition `sauvc_reliability_matrix`. Hentikan simulator lain yang memakai pasangan tersebut; jangan mengubah source selama batch.

```bash
cd /home/rasya/AUV/ros2_ws
bash tools/ros.sh build --symlink-install
bash tools/ros.sh python tools/check_reliability.py --output evidence/reliability-run-01
```

Folder output wajib baru. `summary.json` menyimpan seluruh hasil, termasuk kegagalan; exit code 1 berarti ada kasus yang tidak diterima. Gunakan `--suite qualification`, `--suite arena`, atau `--case q-prior-91` untuk membatasi pengujian. Ctrl+C menghentikan harness aktif dan mencatat kasus terputus. Hasil dan batas pembuktian ada pada [laporan 30](../plan/30-pengujian-keandalan-berulang.md).


## Menahan posisi setelah surface dalam arus

Tambahkan `surface_hold:=true` pada launch autonomous dinamis, misalnya:

```bash
cd /home/rasya/AUV/ros2_ws
bash tools/ros.sh launch sauvc_sim arena.launch.py autonomous:=true surface_hold:=true
```

Untuk ARENA, tambahkan `arena:=finals`. Jalankan satu simulator setiap kali. Perintah POV di atas tetap berlaku.

Default `surface_hold:=false` mematikan motor setelah surface. Dalam mode hold, DONE berarti misi selesai tetapi thruster tetap aktif mempertahankan estimasi posisi, kedalaman dan heading saat mulai STOP. Pantau dengan `bash tools/ros.sh topic echo /sauvc/surface_hold/status`. Fault/abort atau feedback kedaluwarsa mengunci disarm dan gaya nol; pemulihan stream tidak otomatis melanjutkan hold. Ctrl+C menutup simulasi. Kriteria, hasil uji dan batasnya ada pada [laporan 32](../plan/32-surface-hold-dan-koreksi-prior.md).


## Menunggu kualitas kalibrasi DVL

Pada mode dinamis, kualifikasi dan ARENA kini menunggu sedikitnya 200 sampel DVL saat kendaraan tertahan dan indikator ketidakpastian bias horizontal ≤0,0004 m/s, kemudian aliran data stabil dua detik. Fase WAIT/WAIT_READY dapat lebih lama; tidak perlu mengirim perintah gerak untuk mempercepatnya. Jika belum siap sampai batas startup 45 detik, misi dibatalkan.

Pantau `bash tools/ros.sh topic echo /sauvc/state/health`: `dvl_bias_samples`, `dvl_bias_uncertainty_mps`, dan `dvl_calibration_ready`. Sensor yang `valid=true` belum tentu siap untuk start. Prosedur ini memerlukan penahan independen; jangan menganggap kendaraan bebas hanyut sebagai referensi diam. Rincian dan hasil penerimaan: [laporan 35](../plan/35-kualitas-kalibrasi-dvl-sebelum-start.md).


## Isolasi bridge kamera

Default semua launch sekarang `bridge_layout:=isolated`: `sauvc_camera_bridge` menangani gambar depan/bawah, sedangkan `sauvc_bridge` menangani clock, sensor dan kendali. Perintah kualifikasi, ARENA serta POV di atas otomatis memakai susunan ini. Untuk diagnosis A/B gunakan `bridge_layout:=single`; pemeriksa juga menerima `--bridge-layout single` atau `--bridge-layout isolated`. Tanpa override, penguji memakai default launch. Batas pengaman tetap sama. Hasil dan batas: [laporan 43](../plan/43-isolasi-bridge-kamera-dan-sensor.md).

## Diagnosis jeda native–ROS–estimator

Gunakan folder baru untuk setiap run. Perintah berikut mengevaluasi simulator lokal dengan domain/partition terpisah. Pada ketiga terminal jalankan persiapan yang sama:

```bash
cd /home/rasya/AUV/ros2_ws
export ROS_DOMAIN_ID=97
export IGN_PARTITION=sauvc_diag_manual
mkdir -p evidence/diag-manual-001
```

Terminal 1 — penguji kualifikasi dan dua POV:

```bash
bash tools/ros.sh python tools/check_qualification.py --vehicle-model dynamic --gui --pov --output evidence/diag-manual-001/check.json
```

Setelah `ign topic -l` menampilkan `/sauvc/sensors` dan `/sauvc/dynamics/telemetry`, segera mulai kedua probe selama preflight, sebelum DIVE/thrust pertama.

Terminal 2 — observer native:

```bash
bash tools/ros.sh python tools/native_transport_probe.py --output evidence/diag-manual-001/native.jsonl
```

Terminal 3 — observer ROS dan sampel host:

```bash
bash tools/ros.sh python tools/ros_transport_probe.py --output evidence/diag-manual-001/ros.jsonl
```

Setelah penguji selesai, Ctrl+C pada kedua observer agar berkas ditutup. Analisis offline:

```bash
bash tools/ros.sh python tools/analyze_transport.py --native evidence/diag-manual-001/native.jsonl --ros evidence/diag-manual-001/ros.jsonl --checker evidence/diag-manual-001/check.json --output evidence/diag-manual-001/diagnosis.json
```

Analyzer menolak capture yang tidak mencakup awal/akhir jendela. Untuk replay contoh yang sudah diuji, gunakan perintah pada [laporan 42](../plan/42-diagnosis-lokasi-stale-sensors.md). Label diagnosis menyatakan batas lokasi yang didukung rekaman, bukan otomatis akar masalah spesifik DDS/rendering. Dua POV ditata pada X11 dan subscriber/window diverifikasi. Fallback cleanup grup RQt dapat memerlukan SIGKILL; field `pov_cleanup_forced_groups` mencatatnya. Ini terpisah dari shutdown Gazebo/probe dan pengaman kendaraan.

## QoS gambar mentah

Publisher `/sauvc/camera_front/image_raw` dan `/sauvc/camera_bottom/image_raw` memakai BEST_EFFORT, keep_last, depth 1. Gunakan subscriber sensor-data/BEST_EFFORT; klien yang mewajibkan RELIABLE tidak akan tersambung. Perintah POV berlabel di atas tidak berubah. Diagnosis native/ROS dengan metadata tanpa piksel dijelaskan pada [laporan 49](../plan/49-diagnosis-transport-kamera.md).

## Shared memory untuk gambar 640×480

Setelah pembaruan profil gambar, jalankan sekali:

```bash
bash tools/ros.sh build --symlink-install
```

Launch memuat `config/fastdds-images.xml` secara otomatis untuk proses penerbit gambar, dengan kapasitas SHM 16 MiB dan UDP tetap tersedia. Perintah misi/POV di atas tidak berubah. Tidak perlu mengubah sysctl atau profil DDS global. [Reproduksi dan penerimaan perbaikan](../plan/50-akar-kehilangan-frame-shared-memory.md).

## Urutan menutup observer diagnostik

Jika menjalankan observer native/ROS tambahan, akhiri pencatatan setelah misi DONE dan pastikan rekaman mencakup STOPPED; lalu hentikan observer sebelum menutup GUI/server Gazebo. Harness pada [laporan 51](../plan/51-regresi-pinger-dan-transport-jetson.md) menguji urutan ini sambil tetap mewajibkan shutdown bersih. Ini tidak mengubah cara menjalankan misi biasa tanpa observer.
