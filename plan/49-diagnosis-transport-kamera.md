# 49 — Diagnosis transport kamera dan QoS frame terbaru

Tanggal: 3 November 2026. Status: mitigasi QoS kamera dan regresi final terverifikasi; akar unik abort kamera historis belum ditutup.

## Bukti lokasi jeda

Pada run gagal laporan 48, persepsi depan kehilangan frame segar sekitar dua detik sementara kamera bawah masih menerima frame. Rekaman itu belum memuat observer gambar native/ROS mentah, sehingga penyebab unik insiden lama tidak dinyatakan sudah diketahui.

Observer native baru mencatat waktu CLOCK_MONOTONIC, timestamp gambar, ukuran dan jumlah byte; tidak menulis piksel. ROS observer mendapat opsi `--images` untuk metadata raw front/bottom, default tetap tidak berlangganan raw tambahan. Keduanya memiliki heartbeat agar jeda observer sendiri tidak disalahartikan sebagai kegagalan kamera. Source native dibangun memakai ABI protobuf 3.12 yang sudah dipakai plugin Fortress; binary berada di `build/native_camera_probe`.

Uji bridge sengaja dijeda 0,6 detik sesudah DIVE: native front/bottom tetap berjarak sekitar 0,10 detik, sedangkan gap ROS menjadi 1,163/0,742 detik. Mission, dua POV, shutdown dan ketiga probe lulus. Ini memvalidasi instrumen untuk gangguan bridge, bukan reproduksi akar masalah historis.

Tiga baseline GUI nominal juga menunjukkan gap front native 0,144–0,173 detik tetapi ROS 1,105–1,500 detik. Frame yang diterima memiliki delay native→ROS beberapa milidetik; sejumlah frame hilang, bukan seluruh aliran tertahan dalam antrean panjang. Ini mempersempit anomali terukur ke jalur setelah penerimaan native, belum membedakan callback bridge dan middleware DDS secara unik.

## Profil yang dipertahankan

Hanya publisher gambar diberi override QoS `best_effort`, `keep_last`, depth 1. Semua consumer raw yang digunakan runtime/checker memakai sensor-data QoS dan tetap kompatibel. Mapping topik, sensor/kendali kritis, guard, controller, estimator, model gaya, timeout dan FPS kamera tidak diubah. Pada layout single, override tetap hanya mengenai publisher Image; proses terpisah tetap default.

Profil ini memberi prioritas frame baru dan menghindari ketergantungan pada pengiriman ulang gambar lama. Parameter kedua kamera dikonfirmasi lewat layanan get_parameters, dan introspeksi endpoint mengonfirmasi BEST_EFFORT; endpoint depth dilaporkan 0 oleh middleware sehingga bukan bukti depth aktual. Bukti depth 1 berasal dari parameter bridge yang dibaca langsung.

Ros_gz_bridge mendukung [override QoS publisher](https://github.com/gazebosim/ros_gz/blob/humble/ros_gz_bridge/src/factory.hpp#L62). Dependensi baru tidak dipasang.

## Pembandingan kualifikasi GUI

Semua run memakai lane 1 seed 7, model dinamis, dua POV, native camera metadata dan observer native/ROS sensor yang sama. Run dijalankan serial; source/hash per tahap dipertahankan.

| Profil | Misi selesai | Penerimaan | Gap ROS depan maksimum per run | Gap ROS bawah maksimum per run |
| --- | --- | --- | --- | --- |
| Baseline RELIABLE | 3/3 | 3/3 | 1,200 / 1,500 / 1,105 s | 0,607 / 0,589 / 0,602 s |
| BEST_EFFORT, depth 1 | 3/3 | 3/3 | 0,908 / 0,897 / 1,000 s | 0,595 / 0,837 / 0,696 s |
| Ditambah publikasi asinkron kamera | 3/3 | **2/3** | 0,803 / 0,810 / 0,704 s | 0,502 / 0,408 / 0,600 s |

Percobaan asinkron didukung oleh [RMW Fast DDS](https://github.com/ros2/rmw_fastrtps/blob/humble/README.md#change-publication-mode): mode sinkron dapat menahan thread pemanggil saat pengiriman. Dalam eksperimen, env asinkron hanya ada pada proses kamera; bridge kritis tetap tanpa override. Akan tetapi satu run mengalami segfault bridge kritis saat shutdown; tidak diklaim disebabkan oleh asinkron, tetapi run tetap gagal penerimaan. **Asinkron tidak dipromosikan menjadi default dan sudah dibatalkan.** Bukti gagal dipertahankan.

Profil final sama dengan snapshot tiga run BEST_EFFORT. Tidak ada stale_camera spontan pada sembilan run pembandingan ini; itu tidak membuktikan kejadian lama sudah hilang. Perubahan gap antartahap merupakan pengamatan tiga run, bukan estimasi kausal atau statistik keandalan pada beban host terkontrol.

177 tes unit lulus, termasuk metadata gambar tanpa piksel dan pembatasan QoS hanya pada kamera.

Pada subscriber persepsi, gap frame segar depan baseline adalah 1,201 / 1,488 / 1,503 s. Profil final menjadi 0,615 / 0,500 / 0,711 s. Ini lebih relevan untuk misi dibanding raw observer saja: pada profil baru, persepsi dapat menerima frame ketika raw observer mengalami kehilangan, sehingga gap satu subscriber bukan bukti semua subscriber kehilangan frame yang sama.

Regresi ARENA GUI dengan dua POV pada snapshot final lulus: thrust–surface 226,960 detik, skor simulator 210,1912, penalti 0; kontak flare, payload masuk drum, Square dan stop terverifikasi. Gap frame segar depan/bawah selama window aktif maksimum 0,926/0,758 s. Ketiga probe dan checker exit 0, shutdown bersih tanpa cleanup paksa.

Uji `camera_loss` final sengaja menghentikan data setelah thrust: ABORT terverifikasi, perintah dan gaya thruster nol, stationary serta shutdown bersih. Jadi pengaman tidak dilonggarkan untuk mendapatkan hasil lulus.

Snapshot final identik dengan tiga run BEST_EFFORT, termasuk rollback asinkron. Ini penerimaan empat misi final (tiga kualifikasi + satu ARENA) dan satu respons fault yang diharapkan; eksperimen asinkron gagal tetap dicatat terpisah.

## Bukti dan pengulangan

Artefak: `ros2_ws/evidence/camera-transport-2027/`, dengan tahap `bridge-gap/`, `nominal/`, `latest-frame/`, `async-latest/`, `arena-final/`, `qos-parameters.json` serta log build/tes. Semua hasil gagal dan percobaan yang dibatalkan disimpan terpisah.

Dari `ros2_ws/`, setelah build dan memilih domain/partition sama dengan simulator:

```bash
mkdir -p evidence/camera-manual
IGN_PARTITION=sauvc_practice build/native_camera_probe evidence/camera-manual/native.jsonl
# Terminal lain:
ROS_DOMAIN_ID=86 bash tools/ros.sh python tools/ros_transport_probe.py --images --output evidence/camera-manual/ros.jsonl
```

Hentikan kedua observer dengan Ctrl+C setelah uji. `bash tools/ros.sh build --symlink-install` juga membangun native probe. Metadata memakai satu clock monotonic host; jangan membandingkan wall_s dari mesin berbeda tanpa sinkronisasi/bukti clock.

## Batas dan berikutnya

Masih perlu lebih banyak pengulangan dan pelokalan callback bridge versus DDS ketika terjadi gap besar/abort nyata. Observer raw menambah subscriber dan dapat mengubah beban pengujian; hasil bukan pengamatan tanpa instrumen. Belum diuji di Jetson atau kendaraan fisik. Tidak ada perubahan parameter, perintah gerak atau akses Pixhawk pada tahap ini.

Ringkasan assert bukti, hash source/binary probe, pembandingan gap dan kegagalan yang dipertahankan: [verification.json](../ros2_ws/evidence/camera-transport-2027/verification.json). Laporan ARENA: [a-nominal-7.json](../ros2_ws/evidence/camera-transport-2027/arena-final/a-nominal-7.json). Tidak ada klaim seluruh penyebab stale_camera sudah selesai atau seluruh percobaan lulus.
