# Cara menjalankan kualifikasi dan ARENA SAUVC 2027

Diperbarui **19 November 2026**. Halaman rulebook resmi dicek 19 November dan masih menampilkan **2027.3.2**, diperbarui penyelenggara 30 Oktober. Pemeriksaan repo resmi terhadap arsip dilakukan 18 November: [bukti repo/arsip](../doc/sources/rulebook-check-20261118.json); [pemeriksaan halaman 19 November](evidence/qualification-start-20261119/rulebook-check.json).

**Konfigurasi terbaru:** batang gripper 8 cm dari bawah hull ke atas telapak, titik grip `(0, 0, −0,21) m`. Tetap di tengah dan tanpa slider. Kepala terinspirasi Newton memakai dua rahang capit berongga, gigi kecil, rumah aktuator hitam serta pin biru. Bentuk ini bukan emulasi aktuator Newton asli. Kamera bawah tetap 16 cm di depan pusat body.

Dua rahang kini bergerak saat release/grip; release menunggu posisi buka aktual. Build, **202 tes** serta uji native normal/macet lulus. [Aktuasi dan video](../plan/81-aktuasi-rahang-dan-release-terukur.md). Regresi dinamis blue drum dan kualifikasi jalur 3 juga diterima pada laporan 81; hasil rahang rigid sebelumnya tersimpan pada laporan 80. Pickup dasar drum belum didukung dengan batang pendek ini; clearance −17 cm. Hasil extended laporan 79 adalah versi panjang sebelumnya.

Gunakan **tiga terminal**: satu untuk simulator, satu untuk POV depan, dan satu untuk POV bawah. Pilih salah satu misi pada Terminal 1.

**Tampilan atas arena** ada di jendela Gazebo; atur sudut pandangnya dengan mouse. Kamera AUV yang tersedia adalah **kamera depan dan bawah**, bukan kamera atas. Perintah POV di panduan ini menampilkan label deteksi.

## 1. Persiapan

Untuk penggunaan pertama atau setelah kode simulator berubah, jalankan:

```bash
cd /home/rasya/AUV/ros2_ws
bash tools/ros.sh build --symlink-install
```

**Build wajib setelah perubahan gripper fixed**, karena plugin C++ dan geometri berubah. Fixture tes sudah diselaraskan; penerimaan versi panjang tersimpan pada laporan 79; versi ringkas bergaya Newton ada pada laporan 80. Tidak perlu build ulang setiap kali menjalankan misi pada source yang sama. Virtualenv HydroShips boleh tetap aktif; wrapper `tools/ros.sh` memilih Python ROS sendiri.

## 2. Terminal 1 — pilih misi

### Kualifikasi otomatis

Alur: menyelam → melewati gate seluruh badan → U-turn → melewati gate kembali → surface → stop.

```bash
cd /home/rasya/AUV/ros2_ws
export ROS_DOMAIN_ID=86
export IGN_PARTITION=sauvc_practice
bash tools/ros.sh launch sauvc_sim arena.launch.py edition:=2027 arena:=qualification autonomous:=true vehicle_model:=dynamic lane:=1
```

Ganti `lane:=1` menjadi `lane:=2` atau `lane:=3` untuk jalur lainnya. Waktu kualifikasi resmi berakhir setelah pelintasan penuh kedua; surface–stop merupakan penutup tambahan proyek.

### ARENA — blue drum

Alur: menyelam → menghindari orange flare → melewati gate → menjatuhkan bola flare sesuai urutan → drop payload ke blue drum → menuju Surfacing Square → surface → stop.

```bash
cd /home/rasya/AUV/ros2_ws
export ROS_DOMAIN_ID=86
export IGN_PARTITION=sauvc_practice
bash tools/ros.sh launch sauvc_sim arena.launch.py edition:=2027 arena:=finals autonomous:=true vehicle_model:=dynamic flare_order:=B-R-Y
```

`B-R-Y` berarti biru → merah → kuning. Masukan urutan ini mewakili urutan yang diberikan penyelenggara simulasi sesudah Navigation.

### ARENA extended/pickup — pratinjau dengan batang pendek

Gripper pendek saat ini memiliki clearance pickup −17 cm. `autonomous:=true extended:=true` ditolak dengan `fixed_gripper_unreachable` sebelum bergerak. Untuk melihat arena/pinger tanpa menjalankan misi:

```bash
cd /home/rasya/AUV/ros2_ws
export ROS_DOMAIN_ID=86
export IGN_PARTITION=sauvc_practice
bash tools/ros.sh launch sauvc_sim arena.launch.py edition:=2027 arena:=finals autonomous:=false extended:=true vehicle_model:=dynamic scene_variant:=1 blue_drum:=3 pinger_drum:=4 flare_order:=Y-B-R
```

Pickup yang lulus pada laporan 79 memakai titik grip z = −0,40 m; hasil itu tidak berlaku pada batang pendek sekarang. Jangan menonaktifkan collision atau pemeriksaan jangkauan untuk memaksa pickup.

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

### ABORT: fixed_gripper_unreachable

Pesan ini sesuai batas batang pendek saat ini: titik grip z = −0,21 m menghasilkan clearance nominal −17 cm. Gunakan blue drum tanpa extended, atau pratinjau `autonomous:=false`. Mengulang misi dengan geometri yang sama tidak menambah jangkauan.

### Misi abort karena stale_front / stale_bottom

Pesan ini berarti hasil kamera valid dengan timestamp baru tidak diterima selama batas pengaman. Jangan melanjutkan run yang sudah `ABORT`; hentikan launch, pastikan hanya satu simulator berjalan, lalu ulangi. Catat pesan tambahan tentang jeda frame dan timestamp jika terulang.

POV berlabel dibatasi maksimal **5 FPS wall clock** untuk mengurangi beban tampilan; kamera tetap dikonfigurasi **10 Hz simulasi**. Batas pengaman kamera tetap 2 detik. Detail perbaikan dan keterbatasan: [laporan 25](../plan/25-perbaikan-pov-dan-stale-camera.md).

Panduan ini untuk simulator. Kualifikasi dan ARENA autonomous visual memakai model gaya tujuh thruster serta estimator sensor secara default; ground truth hanya untuk referee/pencatat. Gunakan `vehicle_model:=ideal` untuk pembanding historis. Detail: [laporan 26](../plan/26-arena-dinamika-dan-estimasi-sensor.md); perintah di atas tidak menjalankan output thruster/servo hardware. Detail teknis: [README workspace](README.md).


## 7. Verifikasi otomatis dengan Gazebo dan kedua POV

Perintah berikut menjalankan pemeriksa untuk **pengulangan baru**. Penerimaan terpilih revisi fixed terbaru ada pada laporan 79; contoh lane/kondisi di bawah tidak semuanya dijalankan ulang. Penguji menyimpan bukti dan menutup simulator/viewer. Gunakan folder output baru dan hentikan launch lain pada domain/partition yang sama dahulu. `--pov` memerlukan `--gui`.

Kualifikasi dengan Gazebo dan kedua POV:

```bash
cd /home/rasya/AUV/ros2_ws
export ROS_DOMAIN_ID=222
export IGN_PARTITION=sauvc_gui_verification
bash tools/ros.sh python tools/check_qualification.py --edition 2027 --vehicle-model dynamic --gui --pov --lane 1 --output evidence/gui-fixed-qualification-01/check.json
```

ARENA blue drum dengan Gazebo dan kedua POV, **jalankan sesudah pengujian kualifikasi selesai**:

```bash
cd /home/rasya/AUV/ros2_ws
export ROS_DOMAIN_ID=222
export IGN_PARTITION=sauvc_gui_verification
bash tools/ros.sh python tools/check_arena.py --edition 2027 --vehicle-model dynamic --gui --pov --output evidence/gui-fixed-blue-01/check.json
```

Viewer yang keluar selama run menggagalkan verifikasi tampilan. Extended tidak dapat dipakai sebagai penerimaan misi lengkap pada batang pendek ini; kasus tersebut ditolak sebelum thrust.

Model dinamis kini memakai penahan fisik virtual saat preflight. Kalibrasi bias DVL horizontal memerlukan sinyal `deployment_held=true`; penahan dilepas pada thrust pertama dan tidak dipasang kembali saat stop. Setelah DIVE, perintah gerak atau pelepasan penahan, estimasi bias dibekukan. Sampel tidak cukup berarti koreksi tidak diterapkan. Ini memodelkan kendaraan yang benar-benar ditahan saat penempatan, bukan kalibrasi saat bebas hanyut. Perintah launch tetap sama. Rincian: [laporan 31](../plan/31-kalibrasi-dvl-dalam-arus.md). Prosedur serta konfirmasi penahan belum divalidasi pada AUV fisik.

## 8. Pengujian keandalan berulang tanpa jendela

Matriks historis terdiri dari 12 kualifikasi dan enam ARENA, dengan variasi seed sensor, prior posisi, pencahayaan dan arus. Runner menjalankan kasus satu per satu pada domain 230/partition `sauvc_reliability_matrix`. Hentikan simulator lain yang memakai pasangan tersebut; jangan mengubah source selama batch.

```bash
cd /home/rasya/AUV/ros2_ws
bash tools/ros.sh build --symlink-install
bash tools/ros.sh python tools/check_reliability.py --output evidence/reliability-run-01
```

Matriks penuh mencakup `a-pinger-91`, yang belum didukung batang pendek. Hasil seluruh matriks karena itu tidak dapat dinyatakan lulus pada konfigurasi ini; gunakan `--suite qualification` atau `--case a-nominal-7` untuk uji terpilih.

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

Pada mode optik air, subscriber internal RGB/depth memakai depth 3 untuk mempertahankan pasangan capture yang tiba terpisah. Keluaran raw tetap depth 1, timestamp capture dan batas stale tetap dipertahankan. Reproduksi dan pengulangan GUI dicatat pada [laporan 72](../plan/72-antrean-pasangan-rgb-depth-dan-pov.md).

## Shared memory untuk gambar 640×480

Setelah pembaruan profil gambar, jalankan sekali:

```bash
bash tools/ros.sh build --symlink-install
```

Launch memuat `config/fastdds-images.xml` secara otomatis untuk proses penerbit gambar, dengan kapasitas SHM 16 MiB dan UDP tetap tersedia. Perintah misi/POV di atas tidak berubah. Tidak perlu mengubah sysctl atau profil DDS global. [Reproduksi dan penerimaan perbaikan](../plan/50-akar-kehilangan-frame-shared-memory.md).

## Urutan menutup observer diagnostik

Jika menjalankan observer native/ROS tambahan, akhiri pencatatan setelah misi DONE dan pastikan rekaman mencakup STOPPED; lalu hentikan observer sebelum menutup GUI/server Gazebo. Harness pada [laporan 51](../plan/51-regresi-pinger-dan-transport-jetson.md) menguji urutan ini sambil tetap mewajibkan shutdown bersih. Ini tidak mengubah cara menjalankan misi biasa tanpa observer.

## Mode optik air pada kedua kamera

Mode ini menambahkan pelemahan warna/kontras terhadap jarak render per piksel. Default tetap jernih; aktifkan profil ringan secara eksplisit:

```bash
cd /home/rasya/AUV/ros2_ws
bash tools/ros.sh build --symlink-install

# Pilih satu mode setiap kali
bash tools/ros.sh launch sauvc_sim arena.launch.py edition:=2027 autonomous:=true conditions_file:="$PWD/src/sauvc_sim/config/water-light.json"
# Atau ARENA
bash tools/ros.sh launch sauvc_sim arena.launch.py edition:=2027 arena:=finals autonomous:=true conditions_file:="$PWD/src/sauvc_sim/config/water-light.json"
```

Topic POV annotated depan/bawah tetap sama. Efek hanya pada gambar kamera; overview arena mempertahankan visual kolam. Nilai latihan `water_attenuation=0.025` per meter bukan hasil kalibrasi air SAUVC. Nilai 0 menonaktifkan RGBD/filter dan memakai jalur kamera baseline. Resolusi, update rate dan batas freshness tetap. Model ini belum mencakup refraksi, partikel, gelombang fisik atau pemisahan medium udara–air. [Implementasi, preview dan bukti — laporan 67](../plan/67-optik-air-kamera-berdasarkan-depth.md).

Bukti optik sebelum revisi gripper fixed: profil ringan 0,025/m dan dua fixture ARENA 0,05/m lulus setelah perbaikan halo biru; kualifikasi 0,05/m lulus pada kasus terpilih. Kualifikasi 0,10/m kini lulus pada tiga jalur terpilih setelah fallback median warna ([laporan 70](../plan/70-kualifikasi-optik-010-dan-median-warna.md)). Default/profil ringan tidak dinaikkan otomatis. Jangan menyamakan rentang parameter yang diterima parser dengan rentang keberhasilan seluruh misi. [Laporan 69](../plan/69-rulebook-dan-perbaikan-halo-biru-arena.md); riwayat batas sebelumnya pada [laporan 68](../plan/68-ketahanan-optik-air-dan-depth-loss.md).
