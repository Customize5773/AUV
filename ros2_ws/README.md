# Simulasi SAUVC — ROS 2 Humble + Gazebo Fortress

Workspace SAUVC terpisah dalam repositori AUV. Package `sauvc_sim` menyediakan **Qualification Arena(s)** dan **The Arena / finals**, AUV latihan berbentuk kotak, dua kamera, odometri, dan perintah gerak ROS 2. Tidak memerlukan model dari internet atau workspace KKI.

Acuan: [rulebook resmi](https://sauvc.org/rulebook/), **2026 v6.1.0**, diperiksa ulang 25 Oktober 2026. [Usulan 2027](https://github.com/sauvc/rulebook/pull/25) masih terbuka; geometri simulator ini tetap edisi 2026. [Diagram kualifikasi](../doc/sources/rulebook-images/arena-2026-qualifiers.png) dan [diagram final](../doc/sources/rulebook-images/arena-2026-finals.png) tersedia lokal. Diagram tidak berskala; koordinat properti dipilih untuk latihan, bukan hasil pengukuran piksel.

## Menjalankan

Prasyarat: ROS 2 Humble, Gazebo **Fortress / ignition-gazebo6**, `ros_gz_bridge`, `colcon`, Python 3.10, compiler C++, `pkg-config`, dan header development Gazebo Fortress. Pada Ubuntu 22.04 gunakan paket ROS yang sesuai dari instalasi setempat. Mesin ini memakai Ubuntu 24.04 dengan ROS Humble Python 3.10, sehingga semua perintah melalui wrapper berikut:

```bash
cd /home/rasya/AUV/ros2_ws
bash tools/ros.sh build --symlink-install

# Dua jalur kualifikasi, jarak gerbang 10 m
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

Satuan meter, `x=0…25` dari dinding start menuju target, `y=0…16` melintang kolam, `z=0` permukaan dan z negatif di bawah air. AUV menghadap +x. Gerak menggunakan kerangka badan: +x maju, +y kiri, +z naik; yaw positif berputar ke kiri.

| Komponen | Implementasi |
| --- | --- |
| Kolam | Interior 25 × 16 m, empat dinding dengan collision |
| Dasar | Dua bidang miring: −1,2 m pada x=0/25; −1,6 m pada x=12,5 |
| Gerbang kualifikasi | Dua jalur pada (10,4) dan (10,12); bukaan bersih 1,5 m; dari dasar ke permukaan; penanda oranye |
| Start kualifikasi | Garis 1 m pada dinding x=0; AUV di (0,3; 4; −0,05), belakang badan menyentuh dinding |
| Start final | Penanda permukaan 1,4 × 1,4 m, pusat (0,7; 8); AUV di pusat |
| Gerbang final | (16,8), bukaan 1,5 m × 1 m; sisi port merah, starboard hijau |
| Orange flare | (6,8), diameter 15 cm, dasar sampai permukaan |
| Flare target | Biru (11,11), merah (14,12), kuning (12,4); tiang diameter 1,6 cm, tinggi 80 cm |
| Drum | Empat pada x=24, y=12,5/9,5/6,5/3,5; satu biru, tiga merah; diameter luar 60 cm, kedalaman 30 cm, atas terbuka |
| AUV latihan | Kotak 60 × 40 × 20 cm, massa contoh 20 kg; kamera depan/bawah 640 × 480, 10 Hz |

Ketebalan tiang gerbang 5 cm, ketebalan drum 2 cm, posisi properti, massa dan ukuran AUV adalah asumsi latihan. Dasar tiap properti mengikuti kedalaman lokal di posisi pusatnya. Drum berdinding 32 segmen; penanda permukaan tidak memiliki collision. Bola di atas flare hanya visual statis.

## Kontrol dan sensor

| Topic ROS 2 | Tipe | Fungsi |
| --- | --- | --- |
| `/clock` | `rosgraph_msgs/msg/Clock` | Waktu simulasi |
| `/sauvc/cmd_vel` | `geometry_msgs/msg/Twist` | Perintah kecepatan badan |
| `/sauvc/odom` | `nav_msgs/msg/Odometry` | Odometri ground truth 3D, 30 Hz |
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

Plugin kecepatan mempertahankan perintah terakhir; **menghentikan publisher tidak otomatis menghentikan AUV**. Kirim Twist kosong untuk berhenti. Kendali ini ideal, gravitasi badan dimatikan, belum memodelkan thruster, drag, buoyancy, atau dinamika ArduSub. Cocok untuk latihan arena/persepsi/alur navigasi; parameter kendali kendaraan asli belum dapat divalidasi dengannya. Odometri adalah ground truth, bukan estimasi sensor.

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

**Batas model:** belum ada dinamika thruster/drag/buoyancy, randomisasi properti, akustik pinger, mekanisme pelepas/pengambil bola, misi ARENA autonomous, atau integrasi executor HydroShips. Hasil kualifikasi pada model ideal tidak membuktikan kesiapan kendaraan fisik atau kepatuhan edisi 2027.


## Kualifikasi autonomous

Default autonomous kini memakai **`speed_scale:=8.0`** untuk meminimalkan waktu dari gerak pertama sampai surface. Parameter yang sama diterapkan pada controller dan pengawas; `speed_scale:=1.0` mengembalikan profil awal. Rentang yang diterima `(0, 8]`; ini batas rekayasa simulator, bukan batas thruster hardware.

| Gerak | Profil awal (1×) | Default cepat (8×) |
| --- | --- | --- |
| Maju / menjauh dari gate | 0,3 m/s | 2,4 m/s |
| Melintas gate setelah alignment | 0,25 m/s | 2,0 m/s |
| Menyelam / surface | 0,2 m/s | 1,6 m/s |
| Putar U-turn | 0,5 rad/s | 4,0 rad/s |

Koreksi heading dari kamera dibatasi tersendiri karena kamera tetap 10 Hz. Di dekat gate, kendaraan menyelesaikan alignment sebelum maju cepat agar tidak berosilasi. Keberhasilan tetap memerlukan dua pelintasan penuh, U-turn, tanpa benturan, surface sesudah finish dan stop aktual.

Result menambahkan `start_to_surface_elapsed` dan `start_to_stop_elapsed`, dihitung dari gerak pertama terukur; preflight tidak masuk durasi gerak. `elapsed` tetap menyimpan waktu lintasan gate. `--speed-scale 1` pada runner dapat dipakai untuk pembanding; contoh default cepat:

```bash
bash tools/ros.sh python tools/check_qualification.py --output evidence/qualification-speed/fast.json
```

```bash
cd /home/rasya/AUV/ros2_ws
bash tools/ros.sh build --symlink-install
# GUI, kamera sebagai sumber alignment gate, jalur pertama
bash tools/ros.sh launch sauvc_sim arena.launch.py autonomous:=true
# Jalur kedua; yaw dalam radian, offset dalam meter
bash tools/ros.sh launch sauvc_sim arena.launch.py autonomous:=true lane:=2 lateral_offset:=0.2 yaw:=0.174533
# Pembanding berbasis koordinat ground truth, bukan navigasi visual
bash tools/ros.sh launch sauvc_sim arena.launch.py autonomous:=true mode:=odom
```

Misi berjalan otomatis setelah clock, odometri, heartbeat kontak, pemeriksa dan kamera mengalir stabil selama preflight. AUV menyelam, mencari/mengarah ke gate, lewat seluruh badan, menjauh agar kedua tiang kembali masuk kamera setelah U-turn, lalu lewat kembali. Sesudah pemeriksa menyatakan pelintasan balik lengkap, AUV langsung naik vertikal dan berhenti. Waktu resmi kualifikasi dan surface penutup dicatat terpisah. `DONE` memerlukan surface serta perintah nol dan posisi stabil; `ABORT` terminal tanpa resume otomatis. Ctrl+C menutup semua proses milik launch.

Mode `vision` memakai segmentasi oranye/struktur dua tiang dari frame nyata; tidak memerlukan YOLO atau OpenCV. Odometri tetap dipakai untuk kedalaman, putaran dan perjalanan pendek ketika gate sudah terlalu dekat untuk terlihat lengkap. Estimasi bidang gate pada fase tersebut berasal dari jarak/bearing citra terakhir. Mode `odom` menggunakan koordinat gate yang diketahui dan diberi label terpisah.

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
