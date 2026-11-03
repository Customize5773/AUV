# Rencana Program — SAUVC 2027

Status: **draf pengantar untuk diskusi**, 1 Oktober 2026. Belum menjadi arsitektur final atau jadwal komitmen. Disusun dari percakapan dengan penanggung jawab Program.

Tujuan pekerjaan Program adalah mengintegrasikan Jetson, Pixhawk–ArduSub, dan kamera, kemudian membangun kemampuan robot menjalankan misi otonom secara bertahap. Fokus pertama: integrasi perangkat di meja dengan bukti pengujian yang dapat diulang.

| Dokumen | Isi |
| --- | --- |
| [Kondisi dan keputusan](01-kondisi-dan-keputusan.md) | Fakta dari pengguna, usulan, dan informasi yang belum diketahui |
| [Tahapan pekerjaan](02-tahapan-program.md) | Jobdesk, urutan kerja, ketergantungan, dan bukti selesai |
| [Opsi tiga kamera](03-opsi-kamera.md) | Alternatif penempatan dan cara memilih konfigurasi |
| [Pemeriksaan langsung Jetson](04-hasil-pemeriksaan-jetson.md) | Inventaris aktual, bukti perintah, status Docker, dan periferal |
| [Pelaksanaan BlueOS](05-blueos-tanpa-periferal.md) | Konfigurasi pengujian tanpa periferal dan status verifikasi |
| [Adaptasi BlueOS–Jetson](06-adaptasi-blueos-jetson.md) | Perapian antarmuka, suhu/platform, dan persistensi HydroShips |
| [Aplikasi mandiri HydroShips](07-hydroships.md) | Implementasi yang disetujui: Jetson–Pixhawk, dashboard, parameter, telemetri, dan pengujian SITL |
| [Validasi HydroShips langsung di Jetson](08-validasi-jetson-hydroships.md) | Pencocokan metrik host, startup, restart, pemulihan proses, dan integritas konfigurasi |
| [Platform autonomous ROS 2](09-platform-autonomous-ros2.md) | Editor misi, executor ROS 2, kontrak modul tugas, riwayat, dan pengujian software di Jetson |
| [Validasi Pixhawk fisik dan ROS 2](10-validasi-pixhawk-ros2.md) | Pembacaan ArduSub melalui USB, cadangan parameter, dan penerusan telemetri ke ROS 2 |
| [Simulasi arena SAUVC](12-simulasi-sauvc-ros2.md) | Workspace ROS 2/Gazebo terpisah, geometri kualifikasi/final dan bukti uji kamera/gerak |
| [Rencana kualifikasi autonomous](13-rencana-kualifikasi-autonomous.md) | Gate pergi/balik, U-turn, surface sesudah finish dan stop; selesai pada model latihan ideal |
| [Tinjauan rulebook terbaru dan rencana ARENA](14-tinjauan-rulebook-dan-rencana-arena.md) | Perbedaan aturan terbit/draf 2027, koreksi urutan misi dan penerimaan flare/payload; implementasi dilanjutkan pada laporan 17 |
| [Hasil kualifikasi autonomous](15-hasil-kualifikasi-autonomous.md) | Implementasi controller visual/odometri, pemeriksa independen, pengawas dan bukti pengujian |
| [Hasil deteksi kamera](16-hasil-deteksi-kamera.md) | Gate, flare berwarna dan blue/red drum dari citra, topic persepsi, uji frame simulator dan batas hasil |
| [Hasil ARENA autonomous](17-hasil-arena-autonomous.md) | Ketahanan persepsi, tracking, proyeksi kamera, misi visual, bola flare dinamis, payload masuk blue drum dan pemeriksa independen |
| [Dinamika dan estimasi sensor](18-dinamika-dan-estimasi-sensor.md) | Kualifikasi dengan gaya enam thruster, drag/buoyancy, AHRS/tekanan/DVL, pemisahan ground truth dan bukti uji fisika/sensor |

**Perkembangan berikutnya:** pengguna menyetujui aplikasi mandiri dengan BlueOS sebagai acuan, lalu meminta seluruh source digabung dalam Git AUV2027. Aplikasi tersedia di [`hydroships/`](../hydroships/README.md), port lokal **8081**. Laporan 07 menjadi acuan implementasi baru; catatan BlueOS di bawah merekam tahap sebelumnya.

**Koreksi inventaris:** sudah tersedia **3 kamera DWE**. Pembahasan 1–3 kamera adalah opsi penggunaan dari tiga unit tersebut, bukan rencana membeli kamera tambahan.

**Ketersediaan 12 Oktober 2026:** Pixhawk1 sudah tersedia melalui USB Jetson, memakai ArduSub 4.1.0. Pengguna mengonfirmasi catu daya hanya USB. Validasi baca telemetri/parameter dan relay ROS 2 dicatat di laporan 10; kamera belum divalidasi pada sesi ini. Catatan layanan BlueOS sebelumnya tersedia pada [laporan pelaksanaan](05-blueos-tanpa-periferal.md).

Arah awal platform adalah menjalankan/menyesuaikan **BlueOS pada Jetson**, kemudian berkembang menjadi aplikasi mandiri HydroShips. Pemeriksaan langsung mengidentifikasi Jetson Orin NX kelas 16 GB, Ubuntu 22.04.5, dan L4T 36.4.7. Akses Docker telah diberikan dan pengujian tanpa periferal berhasil dengan keterbatasan yang tercatat; ini belum validasi robot lengkap. Pixhawk1 teridentifikasi pada 12 Oktober 2026; model DWE, jumlah thruster, ESC, dan sensor kedalaman belum dikonfirmasi pada sesi ini.

Sumber aturan dan gambar arena tersedia dalam [riset SAUVC](../doc/README.md) dan [indeks gambar rulebook](../doc/sources/rulebook-images/README.md). Acuan aktif adalah edisi 2027.2.1; laporan 21 dan 24 mencatat perubahan serta migrasi simulator.

Urutan kerja yang diusulkan: **identifikasi perangkat → BlueOS dan komunikasi → kamera → kendali dasar → navigasi → tugas tambahan → latihan terintegrasi**. Beberapa eksperimen persepsi dapat berjalan memakai rekaman saat hardware gerak belum siap.

[19 — Penilaian ARENA dan rancangan servo payload](19-penilaian-arena-dan-rancangan-servo.md): ledger skor, bukti fisika bola dan rancangan mekanik awal; tanpa aktivasi hardware.

[20 — Pinger, pickup dan servo simulator](20-pinger-pickup-dan-servo-simulator.md): mode ARENA tambahan, TDOA hidrofon virtual, pickup berbasis kontak dan retensi bola; mekanisme hardware masih rancangan.

[21 — Pembaruan rulebook 2027.2.1](21-update-rulebook-2027.md): publikasi resmi 26 Oktober, perubahan geometri/reacquisition/square/timer dan kebutuhan migrasi; simulator tetap baseline 2026 sampai implementasi diuji ulang.

[22 — Pixhawk dan rencana 7 thruster](22-pixhawk-konfigurasi-7-thruster.md): pembacaan USB langsung, CUSTOM_7T, backup parameter dan pemetaan output; geometri serta koefisien mixer masih perlu dikonfirmasi, tanpa motor test.

[23 — Sinkronisasi 7 thruster](23-sinkronisasi-7-thruster.md): profil bersama 4 horizontal + 3 vertikal, allocator/plant tujuh kanal, panel HydroShips dan relay ROS; asumsi geometri tetap terpisah dari mixer hardware yang belum terverifikasi.

[24 — Migrasi dan uji arena 2027](24-migrasi-dan-uji-arena-2027.md): profil default 2027.2.1, geometri baru, target-zone exit, Surfacing Square dan penerimaan runtime.

[25 — Perbaikan POV dan stale kamera](25-perbaikan-pov-dan-stale-camera.md): antrean frame terbaru, batas FPS anotasi dan verifikasi guard kamera.

[26 — ARENA dinamis dan estimasi sensor](26-arena-dinamika-dan-estimasi-sensor.md): plant tujuh thruster bersama kualifikasi, kendali tanpa pose ground truth dan penerimaan ulang.

[27 — Kalibrasi DVL dan penerimaan GUI/POV](27-kalibrasi-dvl-dan-penerimaan-gui.md): bias preflight tanpa ground truth, kedua misi GUI, tiga jalur kualifikasi dan batas referensi galat tetap.

[28 — Snapshot jeda pengujian keandalan](28-pengujian-keandalan-berjalan.md): enam kualifikasi lulus, regresi flare dan titik lanjut yang disimpan saat rehat.

[29 — Validasi flare dan penerimaan ulang](29-validasi-flare-dan-penerimaan-ulang.md): perbaikan geometri landmark, akustik hampir vertikal dan retensi dengan orientasi penuh; 113 tes unit, 98/98 uji label dan bukti lulus lima fixture ARENA dinamis.

[30 — Pengujian keandalan berulang](30-pengujian-keandalan-berulang.md): 18 run dengan variasi seed, prior, cahaya dan arus; 14 diterima, empat kasus arus gagal diam/akurasi; satu pengulangan tambahan prior gagal akurasi. Integrasi DVL diperbaiki dan 120 tes unit lulus.

[31 — Kalibrasi DVL dalam arus](31-kalibrasi-dvl-dalam-arus.md): penahan preflight virtual dan konfirmasi kalibrasi; 121 tes unit, empat kasus arus + satu nominal lulus akurasi. Tiga kualifikasi berarus tetap gagal diam akhir.

[32 — Surface hold dan koreksi prior](32-surface-hold-dan-koreksi-prior.md): hold opt-in setelah surface, disarm terkunci saat fault, koreksi visual gate survei dan inisialisasi sensor parsial; 130 tes unit, 8 kualifikasi + rerun ARENA lulus.

[33 — Sinkronisasi kamera dan estimator](33-sinkronisasi-kamera-dan-estimator.md): observasi gate menunggu timestamp instrumen, penolakan duplikat/stale tetap berlaku, dan pengulangan kasus prior posisi; 132 tes unit serta tujuh kualifikasi lulus.

[34 — Hold panjang dan variasi arus](34-uji-hold-panjang-dan-variasi-arus.md): 134 tes unit; 3/4 run diterima, satu hold 180 detik gagal drift; arus konstan berbeda antar-run dan batas bias DVL.

[35 — Kualitas kalibrasi DVL sebelum start](35-kualitas-kalibrasi-dvl-sebelum-start.md): pemeriksaan ketidakpastian bias, kesiapan sebelum thrust, dan pengulangan hold 180 detik.

[36 — Investigasi stale_sensors](36-investigasi-stale-sensors.md): waktu penerimaan, umur sensor, dua pengulangan dan fault setelah DIVE; penyebab gangguan lama masih terbuka.

[37 — Fault setelah start](37-fault-setelah-start.md): 142 tes unit, empat fault native terikat thrust, lima respons fault dan satu kualifikasi normal lulus.

[38 — Fault runtime setelah gerak](38-fault-runtime-setelah-gerak.md): 146 tes, delapan respons fault saat misi aktif dan satu kualifikasi normal lulus.

[39 — Benchmark dan percepatan U-turn](39-benchmark-dan-percepatan-uturn.md): tiga pasangan lulus, waktu pelintasan kedua lebih cepat 1,562–1,938 s, 147 tes unit.

[40 — Rencana solusi dan validasi berikutnya](40-rencana-solusi-dan-validasi-berikutnya.md): audit rulebook, diagnosis jeda sensor, opsi transport, konsistensi U-turn dan optimasi vertikal; pelaksanaan dikonfirmasi; audit/migrasi tercatat pada laporan 41.

[41 — Audit dan migrasi rulebook 2027.3.2](41-audit-dan-migrasi-rulebook-2027-3-2.md): audit source lengkap, 148 tes unit, tiga kualifikasi dan dua ARENA lulus.

[42 — Diagnosis lokasi stale_sensors](42-diagnosis-lokasi-stale-sensors.md): dua observer independen, 157 tes, empat lokasi fault terbedakan, matriks 11 run diterima; batas investigasi historis dinyatakan.

[43 — Isolasi bridge kamera dan sensor](43-isolasi-bridge-kamera-dan-sensor.md): 160 tes; enam eksperimen A/B/fault dan empat penerimaan default (termasuk hold 180 s berarus) diterima, sensor tetap segar saat proses kamera jeda; penyebab historis tetap belum terbukti.

[44 — Konsistensi kualifikasi dan waktu preflight](44-konsistensi-kualifikasi-dan-preflight.md): 169 tes unit lulus, startup tertunda lulus; batch 18 kasus source baru berjalan. Pixhawk USB Jetson terverifikasi melalui capture pasif; tetap disarmed, status CRITICAL belum didiagnosis.

[45 — Diagnosis Pixhawk USB Jetson](45-diagnosis-pixhawk-usb-jetson.md): profil tujuh thruster cocok, disarmed; CRITICAL terbukti akibat kehilangan input pilot: input netral terbatas memulihkan STANDBY, lalu timeout mengembalikan CRITICAL. Sensor kedalaman eksternal belum terverifikasi.

[46 — Penerimaan kualifikasi dan regresi pinger](46-penerimaan-kualifikasi-dan-regresi-pinger.md): 170 tes unit lulus; 15 run jalur serta tiga kasus lanjutan diterima dalam dua tahap. Arus memakai hold aktif dengan bukti emergency stop; drift motor-off tetap tercatat. Regresi pinger/pickup dinamis lulus, 205,798 detik dan skor 290,82606 tanpa penalti.

[47 — Shutdown POV kamera](47-shutdown-pov-kamera.md): penampil Qt satu proses dan penutupan GUI Gazebo sebelum server; kualifikasi dan ARENA dengan dua POV lulus tanpa SIGKILL, 174 tes unit lulus. `gate_lost` intermiten pada percobaan awal tetap terbuka.

[48 — Pemulihan gate hilang](48-pemulihan-gate-hilang.md): koreksi skala yaw pencarian dinamis, 175 tes unit lulus; 4/5 percobaan misi selesai dan satu abort stale_camera. Pengaman kehilangan kamera sengaja terverifikasi; penerimaan GUI masih parsial.

[49 — Diagnosis transport kamera dan QoS](49-diagnosis-transport-kamera.md): observer native/raw ROS, uji bridge gap, QoS kamera BEST_EFFORT depth 1; 177 tes unit, tiga kualifikasi dan satu ARENA GUI final serta respons camera_loss diterima. Percobaan asinkron dibatalkan; akar unik gangguan historis belum ditutup.

[50 — Akar kehilangan frame besar](50-akar-kehilangan-frame-shared-memory.md): isolasi tanpa renderer, kontrol kapasitas SHM kecil–besar–kecil; profil 16 MiB khusus penerbit gambar. 178 tes unit, tiga kualifikasi GUI, ARENA standar dan respons camera_loss diterima.

[51 — Regresi pinger dan Jetson](51-regresi-pinger-dan-transport-jetson.md): dua run extended final diterima, satu kegagalan shutdown awal dipertahankan; coverage observer hingga STOPPED. Jetson menerima 80/80 frame sintetis pada profil 16 MiB. Unit HydroShips lama dan venv rusak menjadi prasyarat integrasi fisik berikutnya.

[52 — Pemulihan HydroShips Jetson](52-pemulihan-hydroships-jetson.md): environment Linux baru dan unit path aktif; staging, tujuh sampel API/frontend serta bridge ROS ready terverifikasi. Tidak ada koneksi atau perintah kendaraan.
