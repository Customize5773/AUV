# Simulasi SAUVC — ROS 2 Humble + Gazebo Fortress

Panduan perintah kualifikasi, ARENA dan kedua POV: [Cara running simulator](CARA-RUNNING.md).

Workspace SAUVC terpisah dalam repositori AUV. Package `sauvc_sim` menyediakan **Qualification Arena(s)** dan **The Arena / finals**, AUV latihan berbentuk kotak, dua kamera, odometri, dan perintah gerak ROS 2. Tidak memerlukan model dari internet atau workspace KKI.

**Profil default: SAUVC 2027.2.1**, diperiksa dari [rulebook resmi](https://sauvc.org/rulebook/) pada 26 Oktober 2026. Launch, generator arena dan pemeriksa misi memakai `edition:=2027` / `--edition 2027`. Edisi 2026 hanya tersedia sebagai regresi eksplisit. Migrasi dan bukti runtime: [laporan 24](../plan/24-migrasi-dan-uji-arena-2027.md); sumber terkunci: [arsip 2027](../doc/sources/rulebook-2027-published/README.md). Bagian bukti bertanggal sebelum migrasi adalah hasil historis 2026. Matriks sebelum perbaikan penahan preflight: **120 tes unit lulus; 18 misi selesai, 14 diterima dan empat kasus arus gagal diam/akurasi**. Matriks terdiri dari 12 kualifikasi dan enam ARENA dengan variasi seed sensor, prior posisi, cahaya 70% dan arus 0,02 m/s. Seluruhnya shutdown bersih. Estimator kini memisahkan integrasi DVL dari filter kecepatan kontrol. Satu pengulangan tambahan prior gagal pada galat 0,2010 m; total 14 dari 19 run diterima. Batas prior dan kegagalan arus dijelaskan pada [laporan 30](../plan/30-pengujian-keandalan-berulang.md). Batch ini headless; GUI/POV dan injeksi gangguan tetap bukti historis [laporan 27](../plan/27-kalibrasi-dvl-dan-penerimaan-gui.md). Lima fixture dan 98/98 uji label perturbasi dari tahap sebelumnya tercatat pada [laporan 29](../plan/29-validasi-flare-dan-penerimaan-ulang.md). Kelulusan fixture/label tidak membuktikan keandalan seluruh kondisi atau kesiapan kolam nyata.

**Perbaikan terbaru — DVL dalam arus:** build dan 121 tes unit lulus. Empat kasus arus + satu nominal menyelesaikan misi dan lulus referensi akurasi; dua lulus penerimaan keseluruhan, tiga kualifikasi arus masih gagal diam akhir. Penahan preflight virtual memberi referensi diam yang dikonfirmasi sebelum kalibrasi, lalu dilepas pada thrust pertama. ARENA berarus turun dari galat 1,0594 m menjadi 0,0651 m. Prosedur ini memerlukan kendaraan tertahan; kalibrasi bebas hanyut serta station keeping belum diselesaikan. Bukti dan batas: [laporan 31](../plan/31-kalibrasi-dvl-dalam-arus.md).

## Menjalankan

Prasyarat: ROS 2 Humble, Gazebo **Fortress / ignition-gazebo6**, `ros_gz_bridge`, `colcon`, Python 3.10, compiler C++, `pkg-config`, dan header development Gazebo Fortress. Pada Ubuntu 22.04 gunakan paket ROS yang sesuai dari instalasi setempat. Mesin ini memakai Ubuntu 24.04 dengan ROS Humble Python 3.10, sehingga semua perintah melalui wrapper berikut:

```bash
cd /home/rasya/AUV/ros2_ws
bash tools/ros.sh build --symlink-install

# Tiga jalur kualifikasi, jarak gerbang sekitar 10 m; lane:=1/2/3
bash tools/ros.sh launch sauvc_sim arena.launch.py arena:=qualification

# Hentikan dengan Ctrl+C sebelum membuka arena lain
bash tools/ros.sh launch sauvc_sim arena.launch.py arena:=finals
```

GUI menampilkan arena dari atas secara miring; seret mouse untuk memutar pandangan. `headless:=true` menjalankan server tanpa jendela. Kamera tetap membutuhkan rendering; tambahkan `cameras:=false` untuk pengujian fisika tanpa kamera/GPU.

Wrapper memuat hanya instalasi ROS Humble dan overlay workspace ini. Default `ROS_DOMAIN_ID=86` serta `IGN_PARTITION=sauvc_practice` memisahkan simulasi dari KKI/platform HydroShips; gunakan nilai yang sama pada semua terminal SAUVC. Jalankan satu arena per domain/partition. Tidak ada proses kendaraan fisik atau MAVLink yang dijalankan.

Jika Python 3.10 memuat NumPy sistem milik Python 3.12, siapkan virtualenv lokal. Perintah berikut juga bekerja bila `ensurepip` Python 3.10 belum tersedia, asalkan Python 3 sistem menyediakan pip dengan opsi `--python`:

```bash
/usr/bin/python3.10 -m venv --without-pip --system-site-packages .venv-ros310
python3 -m pip --python .venv-ros310/bin/python install --ignore-installed \
  numpy==1.26.4 packaging==25.0 netifaces==0.11.0
bash tools/ros.sh build --symlink-install
```

Wrapper memilih `.venv-ros310/bin/python` jika tersedia dan mengabaikan paket user-site. `SAUVC_PYTHON` dapat menunjuk interpreter Python 3.10 lain. Build/log/virtualenv/evidence diabaikan Git.

## Geometri dan koordinat

Koordinat dunia: `x=0…50`, `y=0…25`, `z=0` permukaan. Kualifikasi menghadap +x; ARENA menghadap +y. Controller/referee ARENA menggunakan koordinat lokal `U=y`, `V=42−x`; arah +U menuju target zone. Gerak ROS tetap memakai kerangka badan.

| Komponen | Profil latihan 2027 |
| --- | --- |
| Kolam | 50 × 25 m; shelf −1,28 m, slope menuju −2 m lalu dasar datar |
| Kualifikasi | Tiga gate pada x=10, y=3,5/12,5/22; lebar bersih 1,5 m, menggantung sekitar 1 m dari permukaan |
| Start ARENA | Dunia (34; 0,7), penanda 1,4 × 1,4 m |
| Gate ARENA | Lokal (U=12,7; V=8), bukaan 1,5 × 1,5 m dari dasar |
| Orange flare | Tinggi 1,5 m, lokal (6; 8) |
| Flare target | Biru (16,5; 21), merah (18; 14), kuning (16,2; 6) lokal; tinggi tiang 0,8 m |
| Target zone | Mat hijau 8 × 2 m; lokal U=21…23, V=14…22 |
| Drum | Dunia y=22, x=21/23/25/27; diameter 60 cm, kedalaman 30 cm |
| Surfacing Square | Pusat dunia (11,1; 7), bukaan 2 × 2 m, marker biru 0,3 m di bawah permukaan |
| AUV latihan | Kotak 60 × 40 × 20 cm; profil bersama 4 thruster horizontal + 3 vertikal |

Posisi setiap prop dan ukuran konstruksi adalah fixture latihan, bukan koordinat resmi hasil pengukuran diagram. Shelf 1,8 m dan slope 17,5 m ditafsirkan untuk pemodelan; diagram resmi tidak berskala. Gunakan `edition:=2026` hanya untuk mengulang bukti lama.

Ketebalan tiang gerbang 5 cm, ketebalan drum 2 cm, posisi properti, massa dan ukuran AUV adalah asumsi latihan. Dasar tiap properti mengikuti kedalaman lokal di posisi pusatnya. Drum berdinding 32 segmen; penanda permukaan tidak memiliki collision. Bola flare dan payload kini benda dinamis dengan collision dan gravitasi. Plugin latihan menahan bola, melepas penyangga flare saat hull menyentuh tiang, lalu membiarkan fisika menggerakkannya. Ini pendekatan mekanisme latihan, tanpa dinamika tiang lentur atau drag bola di air.

## Kontrol dan sensor

| Topic ROS 2 | Tipe | Fungsi |
| --- | --- | --- |
| `/clock` | `rosgraph_msgs/msg/Clock` | Waktu simulasi |
| `/sauvc/cmd_vel` | `geometry_msgs/msg/Twist` | Perintah kecepatan badan |
| `/sauvc/odom` | `nav_msgs/msg/Odometry` | Ground truth 3D untuk referee/logger, 30 Hz |
| `/sauvc/state/odom` | `nav_msgs/msg/Odometry` | Estimasi sensor untuk kendali dinamis kualifikasi/ARENA |
| `/sauvc/camera_front/image_raw` | `sensor_msgs/msg/Image` | Kamera depan |
| `/sauvc/camera_bottom/image_raw` | `sensor_msgs/msg/Image` | Kamera bawah |

Contoh di terminal kedua, setelah simulator berjalan:

```bash
cd /home/rasya/AUV/ros2_ws

# Menyelam sekitar 40 cm, lalu berhenti
bash tools/ros.sh topic pub --rate 10 --times 20 /sauvc/cmd_vel \
  geometry_msgs/msg/Twist '{linear: {z: -0.2}}'
bash tools/ros.sh topic pub --once /sauvc/cmd_vel geometry_msgs/msg/Twist '{}'

# Maju; Ctrl+C mengakhiri publisher, kemudian kirim stop secara eksplisit
bash tools/ros.sh topic pub --rate 10 /sauvc/cmd_vel \
  geometry_msgs/msg/Twist '{linear: {x: 0.3}}'
bash tools/ros.sh topic pub --once /sauvc/cmd_vel geometry_msgs/msg/Twist '{}'

bash tools/ros.sh topic echo /sauvc/odom --once
```

Pada model `ideal`, plugin kecepatan mempertahankan perintah terakhir; kirim Twist kosong untuk berhenti. Gravitasi badan dimatikan dan `/sauvc/odom` adalah ground truth. Model ini dipertahankan untuk latihan manual dan pembanding eksplisit. Kualifikasi serta ARENA autonomous visual memakai model `dynamic` secara default melalui `vehicle_model:=auto`; model tersebut memakai gaya thruster dan estimasi sensor seperti bagian berikut.

## Pemeriksaan

```bash
cd /home/rasya/AUV/ros2_ws
bash tools/ros.sh python -m unittest discover -s src/sauvc_sim/test -v

# Ekspor arena ke SDF untuk dibuka langsung / diperiksa
bash tools/ros.sh python -m sauvc_sim.arena --arena finals --output /tmp/sauvc-finals.sdf
ign sdf -k /tmp/sauvc-finals.sdf

# Hentikan simulator lain dahulu. Setiap pemeriksaan membuka/menutup simulator sendiri.
bash tools/ros.sh python tools/check_sim.py --arena qualification --output evidence/qualification.json
bash tools/ros.sh python tools/check_sim.py --arena finals --output evidence/finals.json
```

Lima tes geometri memeriksa kedalaman permukaan collision, lebar bersih gerbang, zona/dimensi properti, drum terbuka, dan visual tanpa collision. Pemeriksaan runtime menunggu clock/odom/kamera, mengirim perintah menyelam/maju/berputar/berhenti, lalu menyimpan JSON, log dan frame PPM. Tanpa dukungan rendering dapat memakai `--no-cameras`, tetapi hasil tersebut tidak membuktikan kamera berfungsi.

**Batas model:** dinamika tujuh thruster/drag/buoyancy tersedia untuk kualifikasi dan ARENA autonomous visual, dengan koefisien latihan yang belum diukur pada kendaraan fisik. Controller memakai estimasi sensor; ground truth dipisahkan ke referee/logger. Pinger TDOA virtual dan pickup berbasis kontak/latch tersedia. Integrasi executor fisik HydroShips belum divalidasi. Hasil simulator tidak membuktikan kesiapan kendaraan fisik.


## Kualifikasi autonomous

`vehicle_model:=auto` memilih model **dinamis** untuk kualifikasi dan ARENA autonomous `vision`; latihan manual tetap ideal secara default. `vehicle_model:=ideal` memilih pembanding lama secara eksplisit. `speed_scale` tetap menerima `(0,8]`, tetapi model dinamis membatasi target kecepatan sesuai profil gaya yang diuji: surge 0,9 m/s, sway 0,6 m/s, heave 0,3 m/s dan yaw 0,7 rad/s. Akselerasi/pengereman berlangsung melalui gaya dan inersia. Tabel berikut khusus profil **ideal** lama, bukan kemampuan thruster fisik atau model dinamis:

| Gerak | Profil awal (1×) | Default cepat (8×) |
| --- | --- | --- |
| Maju / menjauh dari gate | 0,3 m/s | 2,4 m/s |
| Melintas gate setelah alignment | 0,25 m/s | 2,0 m/s |
| Menyelam / surface | 0,2 m/s | 1,6 m/s |
| Putar U-turn | 0,5 rad/s | 4,0 rad/s |

Koreksi heading dari kamera dibatasi tersendiri karena kamera tetap 10 Hz. Di dekat gate, kendaraan menyelesaikan alignment sebelum maju cepat agar tidak berosilasi. Keberhasilan tetap memerlukan dua pelintasan penuh, U-turn, tanpa benturan, surface sesudah finish dan stop aktual.

Result menambahkan `start_to_surface_elapsed` dan `start_to_stop_elapsed`, dihitung dari gerak pertama terukur; preflight tidak masuk durasi gerak. `elapsed` tetap menyimpan waktu lintasan gate. `--speed-scale 1` pada runner dapat dipakai untuk pembanding; contoh default cepat:

```bash
bash tools/ros.sh python tools/check_qualification.py --vehicle-model ideal --output evidence/qualification-speed/fast.json
```

```bash
cd /home/rasya/AUV/ros2_ws
bash tools/ros.sh build --symlink-install
# GUI, gaya thruster dan estimasi sensor, kamera untuk alignment gate
bash tools/ros.sh launch sauvc_sim arena.launch.py autonomous:=true
# Jalur kedua; yaw dalam radian, offset dalam meter
bash tools/ros.sh launch sauvc_sim arena.launch.py autonomous:=true lane:=2 lateral_offset:=0.2 yaw:=0.174533
# Pembanding berbasis koordinat ground truth, bukan navigasi visual
bash tools/ros.sh launch sauvc_sim arena.launch.py autonomous:=true mode:=odom
# Pembanding kecepatan ideal dengan kamera
bash tools/ros.sh launch sauvc_sim arena.launch.py autonomous:=true vehicle_model:=ideal
```

Misi berjalan otomatis setelah input mengalir stabil selama preflight. AUV menyelam, mencari/mengarah ke gate, lewat seluruh badan, menjauh agar kedua tiang kembali masuk kamera setelah U-turn, lalu lewat kembali. Jarak tambahan sebelum U-turn adalah 0,6 m pada model dinamis (sebelumnya 1,8 lalu 1,0 m), dengan pengereman langsung saat ambang tercapai; model ideal tetap 1,8 m. Pada model dinamis, perpindahan fase memakai estimasi posisi dan bidang gate hasil kamera, dengan margin lewat 0,6 m; referee menilai pelintasan aktual secara terpisah. AUV lalu naik dan mematikan thrust saat surface, kemudian mengapung serta berhenti melalui fisika. `DONE` memerlukan pengesahan surface/stop aktual dari referee. Waktu lintasan dan surface penutup dicatat terpisah; `ABORT` terminal tanpa resume otomatis.

Mode `vision` memakai segmentasi oranye/struktur dua tiang dari frame kamera; tidak memerlukan YOLO atau OpenCV. Model dinamis memakai `/sauvc/state/odom` hasil estimasi tekanan, gyro/magnetometer dan DVL. Model ideal memakai ground truth. Bidang gate saat terlalu dekat berasal dari range/bearing citra terakhir. Mode `odom` memakai model ideal dan koordinat gate yang diketahui, sebagai pembanding terpisah.

Pemeriksa independen membaca odometri simulator dan kontak; envelope mencakup badan, nose/kamera, yaw/roll/pitch. Pelintasan pusat badan saja tidak cukup. Gerbang salah, keluar bukaan, kontak, muncul sebelum finish, atau balik tanpa U-turn tidak lulus. Sentuhan dinding pada start diberi pengecualian terbatas; kontak berikutnya gagal. Pengawas menjadi penulis kecepatan Gazebo saat autonomous, membatasi kecepatan dan mengirim nol saat perintah kedaluwarsa 0,5 s atau data sensor/pemeriksa macet 2 s wall clock. Arena manual tetap memerlukan perintah stop eksplisit seperti sebelumnya.

| Topic tambahan | Tipe | Fungsi |
| --- | --- | --- |
| `/sauvc/mission/cmd_vel` | `geometry_msgs/msg/Twist` | Masukan controller ke pengawas |
| `/sauvc/contacts` | `ros_gz_interfaces/msg/Contacts` | Kontak nyata dan heartbeat kosong sekitar 30 Hz |
| `/sauvc/qualification/state` | `std_msgs/msg/String` | State controller |
| `/sauvc/qualification/result` | `std_msgs/msg/String` | JSON putusan pemeriksa, waktu, surface, stop, alasan gagal |
| `/sauvc/guard/fault` | `std_msgs/msg/String` | Alasan pengawas menghentikan perintah |

Stock Contact system Fortress hanya menerbitkan ketika benturan. Plugin kecil `contact_monitor.cc` membaca komponen kontak fisika hull dan juga menerbitkan frame kosong agar kesiapan serta putusnya sensor dapat diuji. Wrapper membangunnya sebelum colcon; `.so` hasil build tidak disimpan di Git. Plugin wajib tersedia untuk kedua arena.

Pada host campuran Ubuntu 24.04 / Fortress 22.04 ini, header Protobuf sistem 3.21 tidak cocok dengan binary Fortress ber-ABI 3.12. Header 3.12 diekstrak lokal ke `.native-deps/protobuf-3.12`; script memilih header tersebut dan `libprotobuf.so.23` yang sudah tersedia. Paket sistem tidak diganti. Pada Ubuntu 22.04 yang konsisten, header sistem dipakai langsung. Untuk menyiapkan ulang host campuran ini:

```bash
mkdir -p .native-deps/protobuf-3.12
curl --fail --location https://archive.ubuntu.com/ubuntu/pool/main/p/protobuf/libprotobuf-dev_3.12.4-1ubuntu7.22.04.6_amd64.deb --output .native-deps/protobuf-3.12.deb
dpkg-deb -x .native-deps/protobuf-3.12.deb .native-deps/protobuf-3.12
```

Uji lengkap membuka dan menutup simulator sendiri; hentikan launch lain pada domain yang sama dahulu:

```bash
bash tools/ros.sh python -m unittest discover -s src/sauvc_sim/test -v
bash tools/ros.sh python tools/check_qualification.py --mode vision --output evidence/qualification-autonomous/vision.json
bash tools/ros.sh python tools/check_qualification.py --mode odom --output evidence/qualification-autonomous/odom.json
bash tools/ros.sh python tools/check_qualification.py --mode vision --lane 2 --lateral-offset=-0.2 --yaw=-0.174533 --output evidence/qualification-autonomous/offset.json
bash tools/ros.sh python tools/check_qualification.py --fault command_loss --output evidence/qualification-autonomous/command-loss.json
bash tools/ros.sh python tools/check_contacts.py
```

`--gui` membuka GUI pada pemeriksaan misi. `--fault controller_freeze` pada runner benar-benar mengirim SIGSTOP ke proses controller; pengawas terpisah harus mendeteksi hilangnya perintah dan menghentikan AUV. Proses dilanjutkan kembali hanya untuk cleanup setelah pengujian. `--fault camera_loss|odom_loss|contact_loss|clock_loss|command_loss` memutus penerimaan/penerbitan terkait setelah 8 s simulasi untuk menguji penghentian; tidak digunakan pada peluncuran normal. Pada skenario gangguan, `passed` pada laporan runner berarti **uji penghentian lulus**, sementara `mission_passed` harus false. Laporan menyimpan state, putusan, trajectory, perintah aktual, verifikasi penyebab gangguan, dan status shutdown; file pendamping `-controller.json` dan `-referee.json` memisahkan bukti keduanya.

Hasil implementasi dan batas pembuktiannya tercatat pada [laporan kualifikasi](../plan/15-hasil-kualifikasi-autonomous.md). Ringkasan lokal [verification.json](evidence/qualification-autonomous/verification.json) memuat 19 pemeriksaan runtime, termasuk enam misi visual nominal serta enam uji gangguan/pembekuan controller.

## Model gaya dan estimasi sensor

`vehicle_model:=dynamic` mengaktifkan gravitasi dan plugin gaya `VehicleDynamics`, serta menghapus `VelocityControl`. Tujuh thruster abstrak (T1–T4 horizontal, T5–T7 vertikal) menghasilkan wrench melalui posisi/arah masing-masing. Gaya mengikuti `F=Fmax*u*abs(u)` dengan batas ±20 N horizontal/±40 N vertikal dan respons orde satu τ=0,15 s. Pengendali kecepatan mengalokasikan wrench menjadi tujuh input `u` dan mengerem melalui thrust balik. Pose atau kecepatan aktual tidak di-set langsung.

Drag translasi/rotasi mengikuti `-D*v-Q*v*abs(v)`. Buoyancy memakai `rho*g*V_submerged`, pusat apung di atas pusat massa, dan volume terendam yang berkurang ketika mendekati permukaan. Parameter awal di [dynamics.yaml](src/sauvc_sim/config/dynamics.yaml): massa 20 kg, displaced volume 20,5 L, air tawar 1000 kg/m³. Preset sedikit positif buoyancy sehingga setelah thrust dimatikan kendaraan mengapung pada waterline. Collision box tetap 60×40×20 cm; volume efektif mewakili frame yang sebagian tergenang. Ini model drag diagonal dan buoyancy pendekatan untuk badan hampir datar, belum CFD/added-mass/Coriolis penuh atau model thruster terkalibrasi. Arus konfigurasi default nol.

| Topic | Isi / pengguna |
| --- | --- |
| `/sauvc/sensors` | JSON instrumen: waktu simulasi, gyro rad/s, accelerometer m/s², magnetometer µT (nominal 100 Hz), tekanan Pa dan DVL body-FLU m/s (nominal 20 Hz), status timeout aktuator; semua dengan noise/bias contoh |
| `/sauvc/state/odom` | `nav_msgs/Odometry` hasil AHRS komplementer + tekanan/DVL; dibaca controller dan propulsion |
| `/sauvc/state/health` | Validitas, sumber dan alasan invalid; sensor wajib kedaluwarsa 0,25 s sim atau aliran paket macet 0,3 s wall clock membuat state invalid |
| `/sauvc/thrusters` | `std_msgs/String`, enam nilai ternormalisasi −1…1 dipisah spasi; hanya `propulsion` yang menulis pada autonomous |
| `/sauvc/dynamics/telemetry` | Gaya thruster aktual (N), buoyancy dan timeout; untuk pencatatan pengujian |
| `/sauvc/qualification/status` | Hanya phase/reason/passed dari referee; tanpa koordinat atau event pose untuk controller dinamis |
| `/sauvc/arena/status` | Status tugas/kegagalan ARENA tanpa koordinat ground truth untuk controller/guard dinamis |
| `/sauvc/arena/result` | Laporan rinci referee ARENA hanya untuk pencatat/pemeriksa pada model dinamis |
| `/sauvc/odom` dan `/sauvc/qualification/result` | Ground truth dan laporan rinci hanya untuk referee/logger pada model dinamis |

Estimator mengintegrasikan gyro dan mengoreksi heading dari magnetometer, memakai accelerometer saat hampir diam, memprediksi kedalaman dari DVL lalu mengoreksinya dengan tekanan. XY merupakan dead reckoning DVL dengan orientasi terestimasi dan prior deployment pada garis start; tidak ada GPS/pose world yang disuntikkan ke estimator. Covariance adalah perkiraan diagnostik, bukan EKF terkalibrasi; drift tidak dikoreksi secara global. Sensor virtual ini tidak membuktikan bahwa DVL/IMU/depth sensor fisik sudah tersedia atau terpasang.

Bias DVL horizontal dikalibrasi dari ≥20 sampel preflight dengan konfirmasi `deployment_held=true`. Fixed joint ke penopang statis menahan kendaraan simulator pada titik penempatan; penahan dilepas sekali pada thrust pertama. Kalibrasi dibekukan saat DIVE/perintah gerak atau penahan dilepas. Metadata penahan adalah boolean, tidak berisi pose ground truth. Health memuat `dvl_bias_xy_mps`, `dvl_bias_samples` dan `dvl_calibrating`. Sampel tidak cukup berarti koreksi tidak diterapkan. Ini prosedur kalibrasi tertahan; kendaraan bebas hanyut tetap memerlukan referensi tambahan. Rincian: [laporan 31](../plan/31-kalibrasi-dvl-dalam-arus.md).

Tidak ada fallback ground truth ketika instrumen hilang. Pada `STOP`/`DONE`/`ABORT`, propulsion mengunci status disarm dan mengirim tujuh nol; lag thrust, drag dan buoyancy tetap berlaku sehingga gerak tidak berhenti seketika. Watchdog plant memutus target thrust jika perintah aktuator macet >0,5 s wall clock. Saat controller dibekukan tetapi estimator/propulsion masih sehat, pengawas mengirim target kecepatan nol untuk pengereman/hover. Referee mengesahkan stop dari pose fisika yang stabil; sukses surface juga memerlukan seluruh gaya thruster kembali mendekati nol pada alat uji.

```bash
# Mode baru: default auto untuk autonomous qualification vision
bash tools/ros.sh python tools/check_qualification.py --output evidence/qualification-dynamics/mission.json
# Pulse gaya, pengereman aktif, drag pasif dan apung tanpa motor
bash tools/ros.sh python tools/check_dynamics.py --output evidence/qualification-dynamics/characterization.json
# Putus instrumen; pilihan lain: imu_loss, dvl_loss, actuator_loss, controller_freeze
bash tools/ros.sh python tools/check_qualification.py --vehicle-model dynamic --fault pressure_loss --output evidence/qualification-dynamics/pressure-loss.json
```

Koefisien gaya dan noise harus diukur/dikalibrasi sebelum dipakai untuk kendaraan fisik. Kecepatan ideal lama 8,8 s start–surface tidak menjadi tolok ukur performa model gaya. Laporan lanjutan: [dinamika dan estimasi sensor](../plan/18-dinamika-dan-estimasi-sensor.md).

## Deteksi gate, flare dan drum dari kamera

Node `perception` aktif secara default ketika kamera aktif, pada arena qualification maupun finals. Node ini hanya membaca dua topic gambar; tidak membaca odometri, posisi properti atau ID objek world, dan tidak mengirim perintah gerak. `perception:=false` menonaktifkannya; `cameras:=false` juga tidak meluncurkan node persepsi.

```bash
cd /home/rasya/AUV/ros2_ws
bash tools/ros.sh build --symlink-install
bash tools/ros.sh launch sauvc_sim arena.launch.py arena:=finals
# Terminal lain pada domain/partition yang sama
bash tools/ros.sh topic echo /sauvc/perception/front --once
bash tools/ros.sh topic echo /sauvc/perception/bottom --once
# Dua terminal terpisah untuk POV depan dan bawah dengan label deteksi
bash tools/ros.sh run rqt_image_view rqt_image_view /sauvc/perception/front/image_annotated
bash tools/ros.sh run rqt_image_view rqt_image_view /sauvc/perception/bottom/image_annotated
```

Jika viewer gagal dengan `No module named PyQt5` / `PyQt5.sip`, pasang binding Qt pada virtualenv **ROS**, bukan virtualenv HydroShips:

```bash
cd /home/rasya/AUV/ros2_ws
python3 -m pip --python .venv-ros310/bin/python install --ignore-installed PyQt5==5.15.11
```

Wrapper `tools/ros.sh` juga mengarahkan executable turunan `#!/usr/bin/env python3` ke interpreter ROS. Perintah viewer tetap dapat dipanggil ketika virtualenv HydroShips sedang aktif.

Gambar berlabel tersedia pada `/sauvc/perception/front/image_annotated` dan `/sauvc/perception/bottom/image_annotated` (`sensor_msgs/msg/Image`, RGB8). Kotak magenta menunjukkan bbox, tanda silang putih menunjukkan pusat, dan teks menunjukkan kelas objek. POV berlabel dibatasi maksimal 5 FPS wall clock agar beban viewer tidak mengambil waktu deteksi; input kamera/deteksi tetap 10 Hz simulasi. Antrean gambar hanya menyimpan frame terbaru, dan hasil deteksi tidak menunggu viewer. Gambar mempertahankan timestamp/frame ID kamera sumber; label digambar dengan huruf kapital. Topic kamera asli tetap menjadi masukan detektor. Anotasi hanya dikerjakan ketika ada subscriber gambar, memakai NumPy tanpa dependensi imaging tambahan.

Jika kamera macet >1 s atau citra invalid, gambar berlabel diganti panel hitam bertuliskan `CAMERA STALE - NO DETECTIONS` atau `INVALID CAMERA IMAGE`; panel status berukuran 640×480 dan memakai timestamp node, bukan frame kamera. Pemeriksaan `fresh`/`valid_image` pada JSON tetap wajib untuk konsumen navigasi.

| Kamera | Label deteksi |
| --- | --- |
| Depan, qualification | `qualification_gate`: pasangan tiang oranye, memakai detektor gate kualifikasi yang sudah ada |
| Depan, finals | `navigation_gate`: dua tiang berpenanda merah–hijau; `orange_flare`, `blue_flare`, `red_flare`, `yellow_flare`: warna dan bentuk tiang memanjang |
| Bawah, finals | `blue_drum`, `red_drum`: kandidat daerah berwarna membulat; red drum dibedakan sebagai pembanding, tidak otomatis menjadi target payload |

Topic `/sauvc/perception/front` dan `/sauvc/perception/bottom` bertipe `std_msgs/msg/String`, berisi JSON dengan `fresh`, `valid_image`, `stamp`, `frame_id`, dimensi gambar, `processing_ms` dan `detections`. Tiap objek memuat `label`, `bbox`, `center_px`, `error_normalized`, `bearing` dan `partial`. `bbox=[x_min,y_min,x_max,y_max]` memakai batas kanan/bawah eksklusif; error pusat citra dinormalisasi −1…+1, +x ke kanan dan +y ke bawah. `bearing` adalah sudut horizontal pada citra, bukan heading world. Pada kamera bawah arah perintah badan tetap membutuhkan transformasi kamera.

Gate juga memuat `span_px` dan `distance_estimate_m`, estimasi proyeksi dari jarak antartiang model 1,55 m dan HFOV simulator 1,22173 rad. Ini bukan pengukuran kedalaman sensor. Pasangan marker harus memenuhi bentuk/overlap; satu tiang tidak dianggap gate. Untuk drum, citra yang terpotong batas frame, terlalu kecil, atau seluruh frame berwarna biru ditolak. Tidak ada confidence probabilistik yang dikarang: hasilnya kandidat warna/bentuk, bukan pengenal 3D yang sudah dikalibrasi.

Jika gambar tidak diterima lebih dari 1 s wall clock, node menerbitkan `fresh=false`, `valid_image=false` dan `detections=[]`. Frame dengan format/buffer tidak valid juga mengosongkan deteksi. Konsumen harus memeriksa `fresh` dan `valid_image` sebelum memakai hasil.

```bash
# Alat uji membuka/menutup simulator sendiri; jangan jalankan arena lain pada domain sama
bash tools/ros.sh python -m unittest discover -s src/sauvc_sim/test -v
bash tools/ros.sh python tools/check_perception.py --arena finals --output evidence/perception/finals.json
bash tools/ros.sh python tools/check_perception.py --arena qualification --output evidence/perception/qualification.json
```

Alat uji menempatkan AUV pada sudut pandang yang diketahui melalui service simulator, lalu memeriksa pesan deteksi dari frame kamera aktual. Koordinat tersebut hanya milik harness pengujian, tidak disalurkan ke detektor. Ini pengujian persepsi, bukan navigasi ARENA autonomous. JSON dan frame PPM disimpan lokal di `evidence/perception/`; [laporan deteksi kamera](../plan/16-hasil-deteksi-kamera.md) menjelaskan hasil dan gambar bukti. Runtime tetap hanya memerlukan NumPy yang sudah dipakai, tanpa OpenCV/YOLO atau model unduhan.

## Tracking dan proyeksi kamera

Deteksi menambahkan `track_id`, `track_hits`, dan `confirmed` setelah tiga pengamatan. Asosiasi memakai kelas, posisi serta prediksi gerak pusat citra; track bertahan maksimum 0,7 s timestamp gambar tanpa pengamatan. Objek yang hilang tidak diterbitkan sebagai deteksi prediksi. Citra invalid, kamera kedaluwarsa atau waktu mundur menghapus track; ID tidak digunakan ulang saat reset.

`/sauvc/camera_front/camera_info` dan `/sauvc/camera_bottom/camera_info` memuat `sensor_msgs/CameraInfo` untuk kamera **simulator**: HFOV 1,22173 rad, piksel persegi, principal point di tengah citra dan distorsi nol. `camera_geometry.py` memuat transformasi optik ke badan FLU: depan di `(0.32,0,0)`, bawah di `(0,0,-0.12)` dan menghadap ke bawah. Perhitungan ini bukan hasil kalibrasi DWE fisik; kamera nyata membutuhkan K, distorsi dan ekstrinsik terukur.

Kandidat yang cukup lengkap mendapat `position_body_m` dan `range_method`, dari ukuran antartiang gate 1,55 m, tinggi flare 0,8 m, diameter orange flare 0,15 m atau drum 0,6 m. Range gate mengasumsikan pandangan mendekati tegak lurus. Drum diproyeksikan ke pusat rim yang terlihat. Objek terpotong yang tidak mendukung estimasi tidak diberi posisi metrik. Tidak ada pose world properti yang dibaca detektor.

Untuk Navigation, controller mengoreksi posisi gate memakai dua sinar tiang dan yaw pada timestamp gambar. Koreksi memakai orientasi bidang gate pada fixture kolam (normal world X), tanpa mengetahui lokasi bidangnya. Landmark gate baru diterima jika span tiang ≥10% lebar citra. Ini mencegah proyeksi miring mengunci posisi terlalu pendek dan membuat AUV berhenti sebelum belakang badan melintas. Nilai range pada JSON kamera tetap estimasi tegak lurus; koreksi bidang dilakukan di controller.

Flare dengan tinggi citra <30 px tetap dapat diberi label, tetapi tidak dipakai untuk estimasi jarak. Controller memasangkan hasil kamera dengan interpolasi pose pada timestamp gambar (buffer sekitar 8 s, toleransi 50 ms di batas buffer), bukan pose saat callback diterima. Landmark statis baru memerlukan tiga estimasi posisi yang konsisten; pembaruan yang melompat >0,75 m ditolak. Jika satu warna terpecah menjadi beberapa komponen, kandidat yang paling sesuai dengan landmark dipilih, sehingga fragmen tidak menggeser target yang sudah diketahui.

## ARENA autonomous dari kamera

**Model default ARENA kini dinamis**, memakai plant tujuh thruster dan estimator tekanan/IMU/magnetometer/DVL seperti kualifikasi. Controller/guard membaca `/sauvc/state/odom` dan `/sauvc/arena/status`, tanpa posisi ground truth. Referee dan logger membaca `/sauvc/odom`/`/sauvc/arena/result`. Pilih `vehicle_model:=ideal` hanya untuk membandingkan bukti lama. Detail, drift dan bukti penerimaan: [laporan 26](../plan/26-arena-dinamika-dan-estimasi-sensor.md).

```bash
cd /home/rasya/AUV/ros2_ws
bash tools/ros.sh build --symlink-install
bash tools/ros.sh launch sauvc_sim arena.launch.py arena:=finals autonomous:=true flare_order:=B-R-Y
# Fixture berbeda, urutan dari penyelenggara berbeda, lokasi drum biru ditukar
bash tools/ros.sh launch sauvc_sim arena.launch.py arena:=finals autonomous:=true scene_variant:=1 blue_drum:=3 flare_order:=Y-B-R
```

Jalankan satu launch saja pada domain/partition yang sama. Misi: menyelam dalam starting zone → menghindari orange flare → lewat gate seluruh badan → menerima urutan warna → menyentuh flare sesuai urutan dan menunggu bukti bola jatuh → mencari blue drum dengan kamera bawah → alignment titik payload → drop → menunggu payload masuk → mencari marker Surfacing Square → alignment → surface → stop otomatis. Navigation didahulukan sesuai [rulebook terbit](https://sauvc.org/rulebook/). Urutan warna bawaan adalah masukan penyelenggara simulasi; referee baru mengirimkannya pada `/sauvc/arena/flare_order` sesudah Navigation. Urutan harus permutasi B, R, Y.

Controller menyimpan posisi target hasil proyeksi kamera + odometri AUV, memakai target terkonfirmasi, dan tidak berlangganan topic posisi bola/objek simulator. Search area memakai dimensi kolam/zona latihan. Saat objek sangat dekat dan keluar FOV, pendekatan terakhir dibatasi terhadap perkiraan target yang sudah diamati. Payload berada 0,20 m di depan dan 0,18 m di bawah pusat badan, sehingga tidak menutup kamera bawah; alignment memperhitungkan offset tersebut.

Referee terpisah mengetahui layout simulator untuk memeriksa envelope pelintasan, kontak, urutan bola flare yang turun minimal 12 cm, dan payload pertama berada dalam radius dalam drum serta dekat dasar selama >0,5 s. Perintah `release` dan `DONE` controller tidak cukup untuk lulus. Kontak orange flare menggagalkan attempt. Pada profil 2027, kontak gate utama dan pool diproses sebagai penalti serta automatic abort sesuai ledger; penerimaan misi lengkap tetap mensyaratkan flare, acquisition dan surface/stop. Bonus inspeksi ukuran/berat fisik tidak dimasukkan.

Status: `/sauvc/arena/state`, hasil independen: `/sauvc/arena/result`. Pengawas tetap satu-satunya penulis kecepatan autonomous: timeout perintah 0,5 s, input sensor/referee 2 s wall clock, terminal gagal tidak resume otomatis. Timestamp gambar yang tidak maju tidak memperpanjang kesegaran input.

```bash
bash tools/ros.sh python tools/check_perception.py --robustness --output evidence/vision-robustness/finals.json
bash tools/ros.sh python tools/check_vision_robustness.py --source evidence/vision-robustness/finals.json --output evidence/vision-robustness/perturbations.json
bash tools/ros.sh python tools/check_arena_physics.py --output evidence/arena-autonomous/physics.json
bash tools/ros.sh python tools/check_arena.py --output evidence/arena-autonomous/nominal.json
bash tools/ros.sh python tools/check_arena.py --scene-variant 1 --blue-drum 3 --order Y-B-R --output evidence/arena-autonomous/alternate.json
```

Alat uji membuka/menutup simulator sendiri; gunakan domain/partition terpisah bila simulator lain berjalan. Hasil kamera terkendali dan perturbasi frame terpisah dari bukti misi penuh. Pengujian dengan DWE/kolam nyata belum dilakukan.

Hasil dan batas pengujian terintegrasi dicatat dalam [laporan ARENA autonomous](../plan/17-hasil-arena-autonomous.md).

Penilaian ARENA kini tersedia sebagai `score` pada `/sauvc/arena/result`: poin tugas, bonus urutan/waktu/surface, penalti dan total attempt. Profil 2027 memasukkan bonus Square dan awal timer sejak thrust; rincian migrasi ada pada [laporan 24](../plan/24-migrasi-dan-uji-arena-2027.md). Konsep awal servo payload ada pada [laporan 19](../plan/19-penilaian-arena-dan-rancangan-servo.md).

Mode tambahan ARENA: `bash tools/ros.sh launch sauvc_sim arena.launch.py arena:=finals autonomous:=true extended:=true`. Mode ini memakai pinger virtual untuk red drum, kemudian keluar sepenuhnya dari target zone, kembali mengambil bola yang sama, mempertahankannya sampai surface di Square, lalu stop. Pelintasan gate tambahan hanya berlaku pada profil historis 2026. `pinger_drum:=0` memilih red drum pertama; indeks 1–4 memilih red drum tertentu dan harus berbeda dari `blue_drum`. Mode biasa tanpa `extended` tetap memilih blue drum. Bukti serta batas model aktuator/acoustics ada pada [laporan 20](../plan/20-pinger-pickup-dan-servo-simulator.md).


Sinkronisasi 7 thruster (26 Oktober 2026): profil canonical di [propulsion.json](../hydroships/backend/hydroships/propulsion.json), ditautkan dari `src/sauvc_sim/config/propulsion.json` dan disertakan pada share package saat install. Python allocator dan plugin gaya memakai geometri yang sama melalui SDF; tiga thruster vertikal dialokasikan dengan momen roll/pitch target nol. Posisi/sudut, gaya maksimum dan dinamika adalah asumsi latihan, belum matriks `CUSTOM_7T` yang diverifikasi dari firmware. Pembalikan `MOT_x_DIRECTION` dicatat sebagai konfigurasi ESC, tidak dikalikan ulang ke gaya ideal simulator. Controller misi tetap mengendalikan surge/sway/heave/yaw; rank geometri enam tidak berarti kontrol aktif 6-DoF sudah diimplementasikan. Profil default kini 2027; bukti pada laporan 23 adalah snapshot sebelum migrasi. Bukti: [laporan 23](../plan/23-sinkronisasi-7-thruster.md).
