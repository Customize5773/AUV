# Simulasi SAUVC — ROS 2 Humble + Gazebo Fortress

Workspace SAUVC terpisah dalam repositori AUV. Package `sauvc_sim` menyediakan **Qualification Arena(s)** dan **The Arena / finals**, AUV latihan berbentuk kotak, dua kamera, odometri, dan perintah gerak ROS 2. Tidak memerlukan model dari internet atau workspace KKI.

Acuan: [rulebook resmi](https://sauvc.org/rulebook/), **2026 v6.1.0**, diperiksa 22 Oktober 2026. Ini belum konfirmasi aturan 2027. [Diagram kualifikasi](../doc/sources/rulebook-images/arena-2026-qualifiers.png) dan [diagram final](../doc/sources/rulebook-images/arena-2026-finals.png) tersedia lokal. Diagram tidak berskala; koordinat properti dipilih untuk latihan, bukan hasil pengukuran piksel.

## Menjalankan

Prasyarat: ROS 2 Humble, Gazebo **Fortress / ignition-gazebo6**, `ros_gz_bridge`, `colcon`, dan Python 3.10. Pada Ubuntu 22.04 gunakan paket ROS yang sesuai dari instalasi setempat. Mesin ini memakai Ubuntu 24.04 dengan ROS Humble Python 3.10, sehingga semua perintah melalui wrapper berikut:

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

**Batas versi awal:** belum ada FSM autonomous SAUVC, deteksi objek, penilaian lomba/contact referee, randomisasi properti, akustik pinger, mekanisme pelepas/pengambil bola, atau integrasi executor HydroShips. Kualifikasi resmi memerlukan seluruh badan melewati gerbang, U-turn, lalu seluruh badan melewati gerbang kembali tanpa benturan/surfacing. Uji gerak singkat tidak membuktikan keberhasilan kualifikasi atau tugas final. Implementasi berikutnya dapat dimulai dari navigasi kualifikasi dengan kamera dan pengendali tugas terpisah.
