# 42 — Diagnosis lokasi jeda stale_sensors

1 November 2026. Pelaksanaan tahap diagnosis rencana 40. **Status: instrumen dan validasi lokasi selesai; penyebab unik kejadian spontan historis tidak dapat ditentukan dari arsip lama.** Perbedaan status ini penting: uji terkontrol membuktikan kemampuan diagnosis dan fail-safe, bukan mengubah kegagalan lama menjadi keberhasilan.

## Masalah bukti lama dan hasil investigasi

Run gagal laporan 35 memiliki 297 health invalid `stale_sensors` dan empat `stale_actuator` setelah start, serta gap timestamp simulasi sekitar 4,9–5,8 s. Pesan stale_sensors menunjukkan callback sensor estimator tidak segar melewati batas wall-clock, tetapi tidak mengidentifikasi asal jeda. Arsip itu tidak menyimpan timestamp/urutan publikasi produsen atau observer native yang independen. Karena itu produsen, transport dan penjadwalan konsumen tidak dapat dibedakan secara unik pada kejadian tersebut. Snapshot dan hash laporan gagal tetap dipertahankan.

Pada matriks baru tidak teramati stale sensor spontan. Batas investigasi historis dicatat sebagai `unique_location_identifiable=false`, bukan `root_cause_resolved=true`. Tidak ada bukti untuk menetapkan kamera/QoS/bridge sebagai akar kejadian lama. Tidak dilakukan perubahan QoS atau pemisahan bridge berdasarkan dugaan.

## Instrumen yang ditambahkan

- Telemetry native memuat `producer_wall_s`, `sensor_sequence` dan `sensor_publish_duration_s`. JSON telemetry memakai presisi memadai untuk timestamp monotonic. Payload sensor navigasi tidak ditambah pose/waktu produsen; kontrol tetap memakai kontrak sensor sebelumnya.
- `native_transport_probe.py` mencatat kedatangan sensor dan telemetry melalui dua subscriber CLI Gazebo, di proses terpisah dari ROS. Heartbeat observer membantu mendeteksi pencatat yang tertunda.
- `ros_transport_probe.py` mengamati sensor, telemetry dan health dalam proses tersendiri. Heartbeat serta sampel host satu detik menyimpan pressure CPU/memory/I/O, load, cgroup dan statistik proses terkait.
- `transport_diagnosis.py` menghubungkan aliran dan umur paket estimator. Basis jam divalidasi dari timestamp produsen dan penerimaan; ketidakcocokan jam menghasilkan kesimpulan inconclusive.
- `analyze_transport.py` menyediakan analisis offline beserta hash input. Capture yang mulai sesudah thrust, tidak mencakup akhir jendela, atau tidak memiliki heartbeat yang mencakup jendela ditolak. Kasus input ROS terlambat diuji dan ditolak.

Classifier mempertahankan batas lokasi: `bridge_or_ros_transport_delay` tidak otomatis membuktikan blocking DDS; `producer_or_simulation_stall` tidak membedakan semua penyebab scheduler/rendering. Label publish blocking berarti interval wall-clock panjang di sekitar Publish, yang masih dapat mencakup descheduling proses; penetapan sebab spesifik memerlukan bukti tambahan. Gap pada CLI/native observer juga tidak boleh dianggap bukti produsen berhenti jika nomor urut menunjukkan paket terlewat.

## Validasi lokasi dengan gangguan yang diketahui

Seluruh PID yang dihentikan adalah anak proses penguji, diverifikasi dari process tree. SIGCONT dikirim kembali melalui finally. Tidak ada output hardware atau proses pengguna lain yang dihentikan.

| Injeksi setelah DIVE | Native sensor gap | ROS sensor gap | Health/umur sensor | Diagnosis teramati |
|---|---|---|---|---|
| Server Gazebo berhenti 1 s | 1,012 s | 1,012 s | Umur maksimum 0,997 s | Produsen/simulasi berhenti; sequence berlanjut tanpa loncatan |
| Bridge berhenti 1 s | 0,012 s | 1,008 s | Umur maksimum 0,992 s | Jeda setelah native, pada bridge/transport ROS |
| Estimator berhenti 2,5 s | 0,013 s | 0,016 s | Publikasi health gap 2,516 s | Jeda estimator/subscription; input ROS tetap mengalir |
| Pencatat ROS berhenti 1 s | 0,012 s | 1,011 s di pencatat itu | Umur sensor di kendaraan tetap ≤16,43 ms | Keterlambatan pencatat, misi kendaraan tetap lulus |

Tiga fault pada jalur kendaraan memicu abort/pengaman dan gaya akhir nol. Fault pencatat tidak mengabort kendaraan. Keempat klasifikasi cocok dengan target injeksi tanpa target tersebut diberikan kepada fungsi classifier. Batas stale 0,3 s dan watchdog 0,5 s tetap sama.

## Matriks nominal dan GUI

Matriks utama terdiri dari 11 run: empat respons fault, tiga headless (seed 42/91/7), tiga Gazebo GUI + dua POV dengan seed yang sama, dan satu hold 180 s seed 91 berarus lateral 0,02 m/s. Seluruhnya diterima pada kriteria masing-masing. Tujuh run nominal tidak memiliki kejadian stale sensor teramati.

| Kondisi | Umur sensor maksimum pada masing-masing run |
|---|---|
| Headless seed 42 / 91 / 7 | 22,40 / 15,61 / 22,78 ms |
| GUI + dua POV seed 42 / 91 / 7 | 16,09 / 27,12 / 73,37 ms |
| Hold 180 s | 15,58 ms; drift XY 2,097 cm |

Semua umur masih di bawah batas 300 ms. Pada puncak GUI seed 7, aliran native dan ROS tetap mempunyai gap maksimum sekitar 19 dan 36 ms; umur callback estimator mencapai 73 ms. Ini pengamatan keterlambatan konsumen yang belum mencapai stale, bukan bukti penyebab kejadian historis. Screenshot dicatat waktunya; puncak tersebut terjadi sekitar 22 s setelah capture, bukan selama capture. Sampel host disimpan untuk telaah, tanpa menyatakan beban GUI sebagai sebab tunggal.

Satu run per seed/kondisi belum membuktikan keandalan statistik atau semua beban. Hold panjang dipakai sekali untuk mencakup jendela kegagalan lama, bukan diulang tanpa batas.

## Perbaikan penguji POV dan catatan cleanup

Penguji kualifikasi kini mendukung `--gui --pov`, menata dua jendela kamera agar tidak bertumpuk, dan merekam subscriber kamera serta ID window yang dimiliki proses penguji. Filter PID diuji agar jendela pengguna lain tidak dipindahkan. Penataan memakai [pesan EWMH X11](https://specifications.freedesktop.org/wm/latest/ar01s04.html); backend Wayland belum diuji.

Kesalahan implementasi awal menempatkan verifikasi subscriber di jalur exception. Tiga GUI awal tetap disimpan sebagai data transport pendahuluan, tidak dijadikan penerimaan POV akhir. Kesalahan diperbaiki, lalu tiga run GUI diulang dengan `pov_verified=true` dan dua window terverifikasi. Satu eksperimen tambahan mensyaratkan viewer keluar tanpa SIGKILL dan gagal pada syarat tersebut, walaupun misi/transport lulus. Seluruh 16 percobaan simulator dipertahankan: 11 matriks utama, satu headless tambahan, tiga GUI pendahuluan, dan satu eksperimen cleanup ketat.

Uji viewer terpisah menunjukkan penutupan window/SIGINT masih meninggalkan proses RQt hidup. Upaya tersebut disimpan di close-debug. Cleanup grup viewer yang sudah ada dipertahankan: hanya grup milik penguji dihentikan, dan `pov_cleanup_forced_groups` tetap dicatat. **Gazebo dan kedua observer berhenti bersih; viewer Qt masih memerlukan cleanup paksa.** Tidak disebut sebagai normal exit Qt dan tidak dijadikan pelonggaran pengaman kendaraan.

Capture akhir yang diperiksa visual: [Gazebo + POV depan/bawah](../ros2_ws/evidence/transport-location-2027/pov-accepted/gui42-desktop.png).

## Bukti dan reproduksi

Build native berhasil dan **157 tes unit lulus**. Tes mencakup parsing frame native, tujuh signature/clock cases dan kepemilikan window; matriks runtime memvalidasi empat lokasi gangguan nyata pada proses pengujian. Analisis CLI diputar ulang pada seluruh 16 rekaman; hasil klasifikasi sesuai koleksi awal. Negative check menolak capture ROS yang dimulai setelah thrust.

[verification.json](../ros2_ws/evidence/transport-location-2027/verification.json) menyimpan semua upaya, hash laporan/input/source, diagnosis replay dan batas kesimpulan. Folder yang sama memuat JSONL native/ROS, statistik host, process tree, screenshot, log serta snapshot penguji sebelum perbaikan POV. Snapshot/hash menjelaskan perbedaan source antar tahap; perubahan setelah tahap awal hanya pada tooling POV/tes, bukan pipeline fisik/estimator yang sedang didiagnosis. Source kolektor tahap akhir cocok dengan repo saat verifikasi.

Contoh replay dari folder ros2_ws:

```bash
bash tools/ros.sh python tools/analyze_transport.py   --native evidence/transport-location-2027/pov-accepted/gui42-native.jsonl   --ros evidence/transport-location-2027/pov-accepted/gui42-ros.jsonl   --checker evidence/transport-location-2027/pov-accepted/gui42.json   --output evidence/transport-location-2027/gui42-manual-analysis.json
```

Untuk fault terkontrol, tambahkan `--injection` dengan file injeksi dalam folder faults. Probe dan CLI adalah alat evaluasi, tidak memasok ground truth ke navigasi.

## Penutupan tahap diagnosis

Tahap diagnosis lokasi telah tervalidasi pada data nominal dan gangguan terkontrol. Investigasi kejadian lama berakhir dengan keterbatasan bukti yang dinyatakan, dan tidak boleh dilaporkan sebagai bug spontan yang sudah diperbaiki. Pada kejadian berikutnya, simpan kedua log sejak sebelum thrust sehingga lokasinya dapat dinilai, alih-alih hanya mengandalkan pesan stale_sensors.

Konsistensi 15 run dan optimasi vertikal dari rencana 40 masih tahap berikutnya. Validasi hardware belum dilakukan. Jangan memperpanjang timeout untuk menyembunyikan jeda nyata.
