# Posisi kita — simulasi ROS SAUVC

Diperbarui **24 November 2026**. Ini ringkasan utama untuk mengikuti progres; laporan bernomor menyimpan rincian dan bukti historis.

**Tujuan:** menguji misi autonomous berdasarkan rulebook sebelum dipindahkan ke AUV nyata. Kualifikasi mengejar waktu tercepat dengan pelintasan yang sah; ARENA menyelesaikan tugas dan skor. Bukti saat ini masih pada simulator.

![Peta progres simulasi SAUVC](doc/diagrams/status-simulasi-sauvc.png)

[Unduh PNG](doc/diagrams/status-simulasi-sauvc.png) · [SVG untuk diperbesar](doc/diagrams/status-simulasi-sauvc.svg) · [Sumber diagram](doc/diagrams/status-simulasi-sauvc.dot)

**Rulebook: halaman resmi dicek 19 November tetap 2027.3.2.** Pemeriksaan repo/arsip pada 18 November: versi publik tetap 2027.3.2 (30 Oktober), repo resmi identik dengan arsip; tidak ada migrasi aturan baru. [Bukti](doc/sources/rulebook-check-20261118.json).

**Regresi setelah pengaman pickup, 24 November.** Drum 3 seed 42 dan drum 4 seed 91 lulus hingga surface dan stop. Pada drum 4 seed 42, dua percobaan berhenti sebelum turun setelah bola bergeser keluar dari posisi yang memenuhi margin. Fixture offset 25 cm juga berhenti sebelum benturan. Konsistensi posisi bola sesudah release di drum 4 masih terbuka. [Bukti pascapengaman](ros2_ws/evidence/compact-start/guard-wLKo/verification.json).

## Penerimaan ARENA extended dari starting zone, drum pinger 3

ARENA extended telah mencapai DONE dari starting zone dengan badan kompak dan gripper tetap 8 cm. Pada seed 42, varian kamera bawah memperkirakan posisi relatif bola dan pusat drum, mengatur arah hadap, mengambil kembali bola yang sama, lalu membawanya ke Surfacing Square. Skor simulator 289,05858, waktu thrust–surface 264,714 s dan penalti nol. Setelah kredit retrieval, 1.389 frame fisika berturut-turut mencatat kontak jari tanpa fixed joint. Ulangan seed sensor 91 juga mencapai DONE, dengan skor 289,19604, waktu thrust–surface 260,132 s dan penalti 0. Kedua run dengan kode kamera bawah yang sama lulus pada drum pinger 3. Varian sebelumnya berbasis pusat akustik juga lulus satu run. [Grafik lintasan dan pengangkatan bola](ros2_ws/evidence/compact-start/visual-yaw-aCjx/misi-lengkap.png) · [Ringkasan penerimaan](ros2_ws/evidence/compact-start/visual-yaw-aCjx/verification.json) · [Cara mengulang](ros2_ws/CARA-RUNNING.md) · [Laporan 83](plan/83-pickup-live-dan-transfer-square.md).

Pada drum pinger 4, satu run seed 42 juga lulus dengan skor 289,34658, thrust–surface 255,114 s dan penalti nol. Bola berada 2,82 cm dari pusat drum saat AUV mulai turun. Uji terpisah pada offset 25 cm mengonfirmasi benturan badan dengan bibir drum sebelum mencapai tinggi pickup. [Penerimaan drum 4](ros2_ws/evidence/compact-start/pinger4-0TUZ/mission.json) · [Uji dekat dinding](ros2_ws/evidence/compact-start/pinger4-0TUZ/hull-descent-250mm/result.json).

## Pickup dengan kamera live dan tujuh thruster, 23 November

Pada fixture lokal, gripper tetap 8 cm sudah membawa bola yang sama tanpa pengunci hingga koordinat Surfacing Square. Dua run akhir mencakup pelepasan rendah, keluar zona, kembali, pickup dari kamera bawah, perjalanan sekitar 54 detik dan muncul di dalam Square yang dilokalisasi dengan kamera depan. Pemeriksa independen memverifikasi retensi hingga permukaan. Dua posisi bola dekat dinding drum masih menghalangi pendekatan mendatar. [Laporan pickup live](plan/83-pickup-live-dan-transfer-square.md) · [Cara mengulang](ros2_ws/CARA-RUNNING.md).

## ARENA dengan gripper tetap 8 cm, 21 November

Pada pose pickup mendatar tepat di tengah drum, 944 vertex OBJ dari grup `part_57` berada di dalam dinding. Usulan CAD membatasi radius bagian badan yang masuk drum menjadi 27 cm dari sumbu gripper, dengan kelonggaran nominal 1 cm. Radius terluar mesh kini 30,64 cm dan sudut box collision 32,35 cm. Dimensi masih ukuran latihan. [Potongan atas dan samping](doc/diagrams/pickup-potongan-badan.png) · [Pengukuran](ros2_ws/evidence/pickup-body-sections-20261121/measurement.json).

Pemetaan ke FBX menemukan empat komponen sumber terdekat, yaitu `Body40`, `Body42`, `Body44` dan `Body46`, masing-masing untuk 236 vertex yang masuk dinding. Saat turun vertikal dengan badan mendatar, radius sapuan mencapai 30,64 cm. Untuk menyisakan kelonggaran radial 1 cm dengan galat posisi hingga 2 cm ke arah mana pun, target radius bagian yang masuk drum adalah 25 cm. Selisih maksimum 5,64 cm berlaku pada titik terluar. Perubahan CAD dan pembuktian pickup di Gazebo masih terbuka. [Pengukuran dan pemetaan komponen](ros2_ws/evidence/pickup-cad-map-20261121/measurements.json).


Varian uji dengan bagian bawah dipersempit dan dua box collision lolos validasi SDF. Pada penurunan mendatar, celah radial minimum badan 3,00 cm di tengah dan 1,00 cm pada offset 2 cm. Bagian atas badan masih 5 mm di atas bibir. Pada target titik jepit tepat di pusat bola, ujung jari akan menembus dasar drum sekurangnya 28,95 mm. Uji ini berupa pemeriksaan geometri kontinu. Penerimaan misi extended belum dijalankan pada varian ini. Berikutnya uji kontak kedua rahang pada ketinggian lebih tinggi sebelum mengubah bentuk telapak atau kontrol kedalaman. [Generator varian](ros2_ws/evidence/pickup-hull-25cm/check.py) · [Hasil dua lintasan](ros2_ws/evidence/pickup-hull-25cm/results.json).

**Pickup lebih tinggi, hasil geometri.** Dengan pusat dudukan rahang 40 mm di atas pusat bola yang sejajar, kedua rahang mulai menyentuh bola pada posisi sendi ±0,2438 rad. Celah terendah terhadap dasar selama penutupan hingga kontak adalah 6,5 mm. Langkah berikutnya adalah fixture kontak dinamis di Gazebo pada pose ini untuk mengukur pergeseran bola dan menguji pengangkatan. [Hasil sweep kedua rahang](ros2_ws/evidence/pickup-hull-25cm/raised_grip.json).

**23 November, uji pickup di Gazebo.** Pada fixture badan kompak dengan kontrol kecepatan dan bola di pusat drum, jarak vertikal aktual saat perintah tutup adalah 39,73 mm. Pada run produksi, pengunci yang mensyaratkan kontak kedua rahang aktif dan bola naik 239,55 mm. Pada run pembanding dengan pengunci pascarelease dinonaktifkan, kontak teramati dan dudukan naik 239,83 mm, tetapi bola tetap di dasar. Pergeseran horizontal selama penutupan berada di bawah resolusi posisi log. Berikutnya uji revisi bibir rahang yang menopang bola dari bawah pada fixture tanpa pengunci. [Run dengan pengunci](ros2_ws/evidence/pickup-hull-25cm/native_result.json) · [Run tanpa pengunci](ros2_ws/evidence/pickup-hull-25cm/unlatched/native_result.json).

**23 November, angkat tanpa pengunci.** Dengan batang 8 cm dan pengendali sendi P=0,3 serta D=0,008, bola tengah bertahan selama 2,05 s setelah diangkat. Tinggi minimum selama hold mencapai 23,36 cm dengan telapak lama dan 23,48 cm dengan bibir tambahan. Pada uji pendekatan berbibir dengan perintah offset 20 mm, saat menutup dudukan masih 67,57 mm di atas pusat bola, dan bola tertinggal. Tindak lanjut adalah menguji koreksi posisi dan syarat penutupan berbasis pose sebelum misi extended. [Perbandingan fixture Gazebo](ros2_ws/evidence/pickup-hull-25cm/hold-comparison.json).

**23 November, koreksi posisi sebelum menutup rahang.** Pada fixture Gazebo tanpa pengunci, galat lateral awal 19 mm dikoreksi memakai posisi bola dari simulator. Perintah tutup menunggu galat lateral ≤3 mm dan galat tinggi ≤2 mm selama 0,20 detik. Tinggi saat menutup 40,56 mm. Bola bertahan 2,05 detik pada kenaikan minimum 23,34 cm dengan telapak lama dan 23,47 cm dengan bibir tambahan. Masing-masing satu run. Tahap berikutnya menguji estimasi posisi bola dari kamera bawah pada pendekatan yang sama. [Telapak lama](ros2_ws/evidence/pickup-hull-25cm/unlatched/firm/approach-offset-20mm/pose-corrected/native_result.json) · [Bibir tambahan](ros2_ws/evidence/pickup-hull-25cm/unlatched/lip/firm/approach-offset-20mm/pose-corrected/native_result.json).

**23 November, kamera bawah dan pickup.** Render Gazebo memakai kalibrasi sensor aktif pada drum berisi dan kosong, tanpa badan AUV pada fixture optik. Saat dudukan 35 cm di atas bola, estimasi lateral satu frame −19,74 mm untuk offset −19 mm memakai tinggi diketahui. Pada 11 dan 4 cm seluruh bola sudah keluar bidang pandang. Replay estimasi lateral ke fixture angkat tanpa pengunci memberi galat aktual 0,8 mm saat menutup dan kenaikan minimum 23,34 cm selama hold 2,05 detik. Replay memakai posisi dudukan simulator, sumbu longitudinal sejajar, dan tinggi dasar diketahui. Integrasi frame langsung pada AUV bergerak serta estimator navigasi masih terbuka. [Bukti kamera](ros2_ws/evidence/pickup-hull-25cm/camera-visibility/result.json) · [Replay pickup](ros2_ws/evidence/pickup-hull-25cm/unlatched/firm/approach-offset-20mm/pose-corrected/survey-replay/native_result.json).

Strategi pilihan pinger tanpa pickup lulus di Gazebo dengan pinger pada drum merah nomor 3. Referee memberi 50 poin acquisition. Rute default dan rute cadangan saat topik akustik diputus memperoleh 30 poin untuk drum biru. Ketiga run mencapai DONE, Square +20 dan shutdown bersih. Pengujian unit berjumlah 204. [Hasil per strategi](ros2_ws/evidence/pinger-drop-tNaJ7A/verification.json) · [Cara menjalankan](ros2_ws/CARA-RUNNING.md).

Tiga run tambahan menguji pinger di posisi 1, 2 dan 4. Bersama hasil posisi 3 sebelumnya, referee memverifikasi bola masuk drum berpinger pada keempat posisi yang diuji, masing-masing satu run dengan bonus Square dan penalti nol. [Perbandingan per posisi](ros2_ws/evidence/pinger-layouts-A70RG7/verification.json).

Uji geometri terpisah menempatkan titik jepit 2 cm lebih rendah untuk merepresentasikan batang 10 cm. Pada enam posisi bola dan 395.304 orientasi per posisi, tidak ditemukan pose tanpa benturan badan dengan drum yang juga lolos batas lantai. Batang aktif tetap 8 cm. [Hasil grid 10 cm](ros2_ws/evidence/pinger-layouts-A70RG7/reach-10cm/reach.json).

## Shutdown kualifikasi Gazebo, 21 November

Plugin kamera lokal Fortress 6.18.0 menserialkan penghentian thread render. Uji dua pemanggil stop mencapai timeout pada kode asli dan selesai dalam 50 pengulangan setelah perbaikan. Lima run kualifikasi headless pada jalur 1 dan 2 dengan seed 91 mencapai finish, stop, dan shutdown bersih. Build akhir dan 202 tes simulator lulus. [Ringkasan verifikasi](ros2_ws/evidence/fortress-stop-fix-YDWpIC/verification.json).

Kualifikasi GUI jalur 2 dan ARENA blue drum juga lulus dengan kedua POV dan shutdown bersih. Gate kedua 23,770 s; blue drum 210,1429 poin tanpa penalti. Kedua run GUI mencatat `stale_sensors` setelah DONE, masing-masing +2,922 s dan +3,081 s. Extended dengan gripper pendek menghasilkan `ABORT: fixed_gripper_unreachable` dan nol perintah gerak nonzero. [Verifikasi GUI dan ARENA](ros2_ws/evidence/fortress-gui-arena-mZSxvx/verification.json).

Pada pengujian GUI berikutnya, checker membiarkan sensor tetap menerbitkan data saat jendela Gazebo ditutup. Kualifikasi dan ARENA blue drum mencapai DONE dengan kedua POV dan shutdown bersih tanpa `stale_sensors`. Injeksi kehilangan IMU tetap memicu `ABORT: stale_gyro` dengan thrust nol. [Verifikasi](ros2_ws/evidence/gui-live-shutdown-qeyDoN/verification.json).

## Uji meja Jetson dan Pixhawk, 20 November

Uji bersama DWE 320 × 240 dan telemetri Pixhawk lulus selama 300,08 detik dalam kondisi disarmed. Kamera menerbitkan 2.832 frame, persepsi memproses 1.919, dan umur frame p95 sejak pembacaan host mencapai 260 ms. Subscriber ROS menerima 580 pesan status selama kamera aktif dan 40 sesudah kamera berhenti. Pixhawk melaporkan CRITICAL sepanjang uji baca-saja. Gate fisik dan sensor kedalaman eksternal masih menunggu perangkat. [Ringkasan uji](evidence/pixhawk-ethernet-20261120/combined-eFwgib/summary.json).

Pada koneksi Ethernet ke Jetson dan USB ke Pixhawk, 23 input pilot netral terbatas saat disarmed menghasilkan transisi CRITICAL → STANDBY. Setelah pengiriman dihentikan, Pixhawk melaporkan `Lost manual control` 3,02 detik setelah input terakhir lalu heartbeat kembali CRITICAL. Peringatan kehilangan heartbeat GCS juga tercatat. Tidak ada pengubahan parameter atau arming. [Rekaman MAVLink](evidence/pixhawk-ethernet-20261120/integration-jG0Ybw/readback.json).

Subscriber terpisah menerima enam frame orientasi segar dari relay uji serial pada topik ROS 2 `/auv2027/vehicle/state` di Jetson. Satu barometer dilaporkan (BARO1_DEVID 721674, BARO2/3 nol), rentang 1012,45–1012,49 hPa, bit health tekanan absolut mati. Kedalaman eksternal belum terverifikasi. Pada pemeriksaan awal kamera belum terdeteksi. Setelah tersambung, DWE exploreHD SN00009 lulus uji ROS/persepsi 30 detik pada 320×240 (239 hasil dari 278 frame terbit, tanpa kegagalan baca, umur frame p95 226 ms, deteksi kedaluwarsa setelah stream berhenti). Pada percobaan format default, 18 hasil dari 281 frame terbit dan pemeriksaan kehilangan kamera gagal. [Hasil 320×240](evidence/pixhawk-ethernet-20261120/dwe-RGKpmi/qvga.json) · [Percobaan default](evidence/pixhawk-ethernet-20261120/dwe-RGKpmi/accepted.json). Sensor tekanan eksternal belum dipasang menurut pengguna. [Hasil subscriber](evidence/pixhawk-ethernet-20261120/integration-jG0Ybw/dds.json).

## Revisi aktif — rahang bergerak, batang tetap 8 cm

**20 November.** Pengunci pickup kini memerlukan kontak bola dengan kedua rahang pada langkah fisika yang sama saat ada perintah grip. Pada dudukan latihan di Gazebo, bola terpasang saat dijepit dua rahang. Dengan collision satu rahang dinonaktifkan khusus untuk injeksi gangguan, satu rahang menyentuh bola dan pengunci tetap terbuka. Saat menutup dalam kondisi kosong, pengunci juga tetap terbuka. [Uji dua rahang](ros2_ws/evidence/gripper-contact-20261120/rails/physics.json) · [Uji satu rahang](ros2_ws/evidence/gripper-contact-20261120/rail-one/physics.json). Retensi setelah jepitan masih memakai fixed joint. Pickup dasar drum tetap terhalang jangkauan. Uji ulang pada revisi dua rahang selesai. Blue drum mencapai **210,13492 poin** tanpa penalti dan surface dalam **228,836 s**. Kualifikasi jalur 3 mencatat gate kedua **22,052 s**, surface **24,670 s** dan stop **29,056 s**. Kedua run dinamis headless selesai dengan exit 0 dan shutdown bersih. [Bukti dua misi 20 November](ros2_ws/evidence/gripper-regression-20261120/acceptance.json).

Dua pengulangan tambahan kualifikasi jalur 3 lulus. Bersama run pertama pada revisi yang sama, **3/3** selesai dengan exit 0 dan shutdown bersih. Pada seed 42, offset lateral 0,15 m dan atenuasi 0,10/m, waktu pelintasan penuh kedua berkisar **22,052–22,918 s** dengan median **22,760 s**. Median surface **25,378 s**, median stop **29,832 s**. [Hasil per run](ros2_ws/evidence/qualification-repeat-20261120/summary.json).

Jalur 1 dan 2 juga lulus pada posisi nominal dan pada offset lateral +0,15 m dengan yaw awal +0,10 rad. Keempat run dinamis memakai seed 42 dan atenuasi 0,10/m, mencapai DONE dan keluar dengan kode 0. Finish gate kedua nominal/offset masing-masing 22,890/23,218 s pada jalur 1 dan 22,058/22,030 s pada jalur 2. Log jalur 2 nominal mencatat stale_sensors setelah DONE. [Bukti empat run](ros2_ws/evidence/qualification-lanes12-20261120/summary.json).

Pada jalur 2 nominal, peringatan lama muncul 2,717 s setelah DONE. Checker headless sebelumnya ikut menjeda fisika saat shutdown. Jeda render kini hanya dilakukan untuk GUI. Satu pengulangan headless pada kondisi yang sama mencapai finish 21,664 s, DONE, thruster nol dan shutdown bersih tanpa stale_sensors. Urutan pause terhadap fault lama tidak memiliki timestamp yang cukup untuk memastikan sebab tunggal. [Laporan pengulangan](ros2_ws/evidence/qualification-shutdown-20261120/mission.json).

Batch seed 7, 42 dan 91 menghasilkan 12/12 finish kualifikasi sah dan 11/12 run headless lulus sampai shutdown. GUI jalur 2 dan kedua POV ditutup bersih. Pada uji dudukan tanpa pengunci, bola terlepas ketika AUV bergerak. [Hasil multiseed, GUI dan retensi](plan/82-kualifikasi-multiseed-dan-retensi.md).

**Pembanding 19 November.**

Dua rahang kini memakai sendi revolute dengan controller posisi berbasis torsi. Payload awal dibawa dalam rahang tertutup; release menunggu bukaan aktual. Uji normal dan rahang macet lulus, termasuk render buka–lepas–tutup. Build dan **202 tes** lulus. Regresi dinamis diterima: blue drum **210,14494 poin / 228,502 s** tanpa penalti; kualifikasi jalur 3 mencatat gate kedua **22,994 s**, surface **25,578 s** dan stop **30,542 s**, keduanya stationary dan shutdown bersih. ARENA diulang dengan exit code **0**; [verifikasi akhir](ros2_ws/evidence/gripper-completion-20261119/verification.json) menutup celah exit code sebelumnya. Kualifikasi dan 202 tes memakai bukti pada 98 hash source/aset yang sama, tidak diulang pada penutupan ini. Retensi masih latch ideal dan pickup dasar drum tetap belum didukung. [Video](ros2_ws/evidence/gripper-joints-20261119/preview/jaw-motion.mp4) · [Laporan 81](plan/81-aktuasi-rahang-dan-release-terukur.md).

## Riwayat bentuk — laporan 80

Sesuai revisi pengguna, batang gripper dipendekkan menjadi **8 cm dari bawah hull ke atas telapak**. Kepala bergaya Newton memakai dua rahang capit berongga, gigi kecil, rumah aktuator hitam dan pin biru; posisi tetap di tengah, tanpa slider. Titik grip kini `(0, 0, −0,21) m`.

Build serta **201 tes lulus**. Release native dengan collision aktif, ARENA blue drum dan kualifikasi jalur 3 diterima; semua stop dan shutdown bersih. Blue drum **210,1426 poin / 228,580 s**, penalti nol. Kualifikasi: gate kedua **22,792 s**, surface **25,376 s**, stop **29,796 s**. [Laporan 80](plan/80-gripper-ringkas-bergaya-newton.md) · [Tampilan keseluruhan](ros2_ws/evidence/gripper-newton-20261119/initial.png) · [Detail telapak](ros2_ws/evidence/gripper-newton-20261119/empty/initial.png).

Pada laporan 80, rahang masih terbuka dan rigid. Aktuasi berikutnya ada pada laporan 81; keduanya tidak mengemulasikan mekanisme/performa Newton asli.

**Konsekuensi jangkauan:** clearance pickup dasar drum menjadi −17 cm pada pendekatan mendatar sekarang. Pengaman extended tetap menolak konfigurasi ini; keberhasilan pickup laporan 79 berlaku pada batang panjang sebelumnya.

## Riwayat gripper panjang — laporan 79

### Penerimaan versi panjang sebelumnya

Perubahan panjang **disetujui pengguna dan selesai diuji**: gripper di tengah `(0, 0, −0,40) m`, 30 cm di bawah hull, tanpa slider. Build selesai, **200 tes lulus**, dan tiga fixture 2027 diterima:

| Misi | Hasil terkini |
|---|---|
| Extended/pinger/pickup, Gazebo dan dua POV | **290,8026 poin**, thrust–surface **206,580 s**, penalti nol; bola yang sama dipertahankan sampai stop |
| ARENA blue drum | **210,15928 poin**, thrust–surface **228,024 s**, penalti nol |
| Kualifikasi jalur 3, air 0,10/m | Gate kedua **22,234 s**, surface **24,818 s**, stop **29,272 s** |

Semua stop dan shutdown bersih. Target kedalaman kualifikasi 2027 kini **−0,50 m** agar alat tetap berada dalam bukaan gate. Regresi pertama pada kedalaman lama gagal dan disimpan; pengulangan setelah koreksi lulus. ARENA memakai geometri/controller yang sama dengan revisi sekarang; patch kedalaman terakhir hanya mengenai kualifikasi.

Bola awal berada pada gripper. Retensi pickup terverifikasi pada 1.340 snapshot native, dengan jarak maksimum 4,71 cm terhadap titik grip, di bawah batas 7,5 cm. **Pickup selesai pada fixture simulator ini**; mekanisme jepit masih latch ideal dengan syarat collision, bukan pembuktian jari/servo nyata. Seluruh kondisi dan kendaraan fisik belum terbukti; pengujian fisik tetap dikecualikan.

[Laporan 79 dan bukti](plan/79-gripper-fixed-panjang-dan-pickup-selesai.md) · [Render alat dan bola awal](ros2_ws/evidence/gripper-fixed-040-20261119/initial.png) · [Video extended](ros2_ws/evidence/gripper-fixed-040-20261119/extended-1/pov.mp4) · [Cara running](ros2_ws/CARA-RUNNING.md).

## Riwayat sebelum penambahan panjang yang disetujui

## Status revisi fixed — 19 November 2026

Pilihan pengguna: **gripper pendek dan tetap, tanpa mekanisme memanjang**. Kode geometri kini memakai dudukan fixed pada `(0, 0, −0,18) m`; payload awal ARENA memakai titik yang sama. Pemeriksaan statis mengonfirmasi tidak ada joint slider dan extended ditolak dengan `fixed_gripper_unreachable` karena clearance pickup −20 cm.

**Kualifikasi sebelum penambahan panjang — optimasi 19 November:** pendekatan gate dimulai setelah estimasi kedalaman −0,25 m sambil melanjutkan penyelaman menuju −0,60 m. **198 tes lulus dan lima run controller baru diterima**, mencakup tiga jalur. Batas thrust/kecepatan, referee, U-turn dan pengaman tetap sama.

Pada tiga run nominal identik per revisi, median gate kedua **23,678 → 21,802 s**, surface **26,772 → 24,896 s**, stop **32,280 → 29,554 s**. Seluruh tiga baseline dan lima run baru stop/shutdown bersih. Ini hasil simulator pada fixture terpilih, bukan jaminan semua kondisi. [Laporan 78 dan grafik perbandingan](plan/78-optimasi-awal-kualifikasi-dinamis.md).

**ARENA:** dua layout blue drum lulus pada run 18 November: baseline **210,14872 poin / 228,376 s**, alternatif **210,37852 poin / 220,716 s**, penalti nol. Satu memiliki bukti Gazebo/dua POV. Controller ARENA tidak diubah pada optimasi ini dan run ARENA belum diulang. [Penerimaan fixed awal](plan/75-penerimaan-gripper-pendek-tetap.md) · [Fixture tambahan](plan/76-diagnosis-reach-fixed-dan-fixture-tambahan.md).

**Yang masih kurang:** pickup dasar drum dengan gripper pendek tetap belum didukung. Diagnosis box collision mendatar menunjukkan kekurangan clearance 20 cm; pencarian pose statis diskret pada enam posisi bola juga belum menemukan pose bebas benturan. Ini belum bukti untuk semua lintasan atau geometri fisik. Extended tetap ditolak sebelum thrust; penolakannya bukan kelulusan misi pickup. [Gambar diagnosis](ros2_ws/evidence/gripper-fixed-reach-20261118/reach.png). Validasi seluruh kondisi dan AUV nyata belum dilakukan; pengujian fisik tetap dikecualikan. [Cara running](ros2_ws/CARA-RUNNING.md).

**Diagnosis tambahan 19 November:** titik mesh asli juga berbenturan dengan lantai/dinding pada seluruh grid pose yang diuji di enam posisi bola. Contoh vertex asli berada sekitar 9,99 mm di dalam salah satu solid dinding drum. Ini menutup dugaan bahwa hasil grid sebelumnya semata-mata berasal dari ruang kosong dalam AABB; belum membuktikan seluruh kemungkinan lintasan. Diagnosis tersebut tidak mengubah geometri; optimasi dan misi kualifikasi sesudahnya dicatat pada laporan 78. [Laporan 77 dan gambar](plan/77-diagnosis-pickup-dengan-titik-mesh-asli.md).

Hasil tiga misi pada bagian riwayat di bawah adalah **versi slider 17 November**. Revisi fixed memiliki hasil 197 tes dan penerimaan sendiri pada laporan 75. Pengujian kendaraan fisik tetap dikecualikan.

## Riwayat sampai versi slider — 17 November 2026

- **Berfungsi dan punya bukti:** kualifikasi otomatis, ARENA blue drum/extended, kamera dan deteksi, dinamika tujuh thruster, estimator serta pengaman. Hasil berlaku pada skenario yang diuji.
- **Penerimaan versi slider:** gripper di tengah body, pendek saat membawa; bola awal terpasang pada carrier yang sama. Build, **197 tes** serta **tiga misi dinamis** (extended GUI/POV, blue drum dan kualifikasi) lulus dengan shutdown bersih. [Laporan 74](plan/74-gripper-tengah-pendek-dan-bola-awal.md).
- **Penerimaan sebelum perubahan gripper:** 13/13 pengulangan non-GUI lulus pada revisi antrean kamera: sembilan kualifikasi, arus/hold, prior posisi serta ARENA extended dan blue drum. Semua shutdown bersih; manifest 98 file cocok dengan laporan 72. Tiga GUI tanpa stale setelah gambar pertama serta respons kehilangan depth tetap merujuk bukti laporan 72.
- **Tes unit versi slider:** 197 lulus setelah revisi gripper. Hasil 195 tes dan replay pada laporan 70/72 merupakan bukti sebelumnya. Penerimaan misi revisi gripper juga lulus pada tiga fixture yang diuji.
- **Perbaikan kamera terbaru:** kehilangan pasangan RGB–depth pada antrean satu frame direproduksi. Masukan optik kini mempertahankan tiga capture; keluaran tetap satu frame terbaru. Tiga pengulangan GUI lulus tanpa stale setelah gambar pertama masuk. Ini belum jaminan semua beban komputer bebas jeda.
- **Kasus yang baru ditutup:** kualifikasi pada atenuasi sintetis 0,10/m yang sebelumnya `gate_lost` kini lulus di tiga jalur terpilih. Ini uji tambahan, bukan syarat rulebook. Perbaikannya memakai median warna pada fallback; kecepatan dan pengaman tetap.
- **Belum dibuktikan:** seluruh kondisi kolam dan misi pada AUV fisik. Kapal belum selesai. Refraksi, partikel dan gelombang bukan pekerjaan wajib proyek saat ini.

Bukti versi slider: [laporan 74](plan/74-gripper-tengah-pendek-dan-bola-awal.md) dan [verifikasi gripper](ros2_ws/evidence/gripper-centered-20261116/verification.json). Penerimaan 13 run sebelum perubahan gripper ada di [laporan 73](plan/73-konsistensi-setelah-perbaikan-antrean-kamera.md). Diagnosis kamera, tiga GUI dan depth fault ada di [laporan 72](plan/72-antrean-pasangan-rgb-depth-dan-pov.md). Riwayat demonstrasi dan batch 15 run ada pada [laporan 71](plan/71-demonstrasi-dan-konsistensi-revisi-optik.md). Perbaikan detektor ada pada [laporan 70](plan/70-kualifikasi-optik-010-dan-median-warna.md) dan [69](plan/69-rulebook-dan-perbaikan-halo-biru-arena.md). Acuan aktif 2027.3.2, terakhir dicek 18 November: [bukti rulebook](doc/sources/rulebook-check-20261118.json).

## Riwayat gripper dengan slider — digantikan pilihan fixed

Titik gripper kini `(0, 0, −0,18) m`: pusat bola hanya **8 cm di bawah hull**, dibanding 30 cm sebelumnya. Slider memanjang 22 cm hanya saat pickup dan retract lagi bersama bola; kualifikasi mengunci posisi pendek tanpa payload. Spawn payload, joint pemuatan dan alignment drop memakai titik yang sama. Kamera bawah bergeser 16 cm ke depan dan proyeksinya diselaraskan.

Release pertama gagal karena bukaan 34 mm menahan bola 40 mm. Bukaan kini 42 mm; probe release serta tiga misi final lulus dengan collision tetap aktif. Pose bola dan carrier berimpit pada 110 snapshot awal. Pickup mempertahankan bola melalui joint kontak sampai stop, dengan batas retensi 7,5 cm tetap. [Render inspeksi model baru](ros2_ws/evidence/gripper-centered-20261116/initial.png) · [Video POV extended](ros2_ws/evidence/gripper-centered-20261116/extended-2/pov.mp4).

Perubahan ini model simulator; ruang rod, servo dan mekanik nyata belum tervalidasi. Pengujian kendaraan fisik tetap dikecualikan. Hasil 13 run sebelumnya tetap riwayat sebelum perubahan gripper, bukan penerimaan ulang model terbaru.

## Penerimaan konsistensi sebelumnya

**13/13 run diterima pada source yang sama dengan laporan 72.** Matriks dan batas kelulusan sama dengan 13 kasus non-GUI laporan 71. Tidak ada perubahan source produksi pada tahap ini.

Sembilan kualifikasi: pelintasan kedua 23,632–24,674 detik, start–surface 26,726–27,768 detik, start–stop 31,322–32,598 detik simulasi. Hold arus 0,02 m/s selama sekitar 30 detik lulus dengan drift XY maksimum 4,95 mm; prior posisi ±10 cm juga lulus. ARENA extended mencapai 290,7396 poin dalam 208,680 detik dan blue drum 210,16066 poin dalam 227,978 detik; penalti keduanya nol.

Ini menutup pengulangan matriks yang sudah dipilih, bukan optimasi kecepatan atau jaminan seluruh kondisi. Tidak menambah tingkat uji baru secara otomatis. **Pengujian kendaraan fisik tetap dikecualikan.** [Laporan 73](plan/73-konsistensi-setelah-perbaikan-antrean-kamera.md).

## Diagnosis dan perbaikan antrean kamera sebelumnya

Antrean masukan RGB/depth dinaikkan dari satu menjadi tiga capture agar pasangan bertimestamp sama tidak hilang ketika pesan datang terpisah. Public raw tetap satu frame terbaru, tanpa perubahan batas stale. Pada tiga pengulangan GUI tidak ada stale setelah gambar pertama sampai DONE; sela raw bawah maksimum 0,363–0,470 detik, dibanding 1,112 detik pada reproduksi sebelum perubahan. [Rekaman terbaru](ros2_ws/evidence/camera-pairing-20261116/after-3/pov.mp4).

Kehilangan depth tetap menghasilkan abort aman tanpa replay. ARENA extended lulus: 290,7468 poin, penalti nol, thrust–surface 208,440 detik dan retensi bola sampai surface. Hasil ini menutup mekanisme antrean yang direproduksi; belum menjamin semua beban komputer atau penyebab stale historis. **Pengujian kendaraan fisik dikecualikan sesuai permintaan Anda.**

## Demonstrasi dan konsistensi sebelumnya

**Permintaan Anda sudah dikerjakan pada matriks yang disepakati:** demo terlihat dan seluruh 15 run diterima. Kasus arus 0,02 m/s dengan hold sekitar 30 detik mencatat drift maksimum 5,46 mm; kasus prior posisi ±10 cm juga lulus. Tiga ARENA termasuk demo: dua extended/pinger/pickup dan satu blue drum. Semua hasil tetap disimpan; ini bukti skenario terpilih, bukan seluruh kondisi.

Catatan penutupan: tiap run memiliki satu log `stale_sensors` sesudah `DONE`, dengan world dipause sebelum shutdown. Urutan ini konsisten dengan penghentian produsen sensor saat penutupan; tidak terjadi abort misi pada batch ini. Jeda POV bawah saat demo kualifikasi ditindaklanjuti secara terpisah pada laporan 72. Batch 15 run ini mendahului perubahan antrean.

Perbaikan kualifikasi 0,10/m pada tahap sebelumnya sudah selesai pada kasus yang diuji, dengan bukti di laporan 70.

## Langkah untuk menyamakan pemahaman

**Demonstrasi kualifikasi dan ARENA sudah dijalankan; Anda mengonfirmasi Gazebo serta kedua POV terlihat.** Cocokkan perilaku yang terlihat dengan alur pada diagram. Kedua POV direkam sebagai video untuk ditinjau ulang; konfirmasi terlihat tidak menggantikan pemeriksaan hasil misi. Perintah tersedia di [cara running](ros2_ws/CARA-RUNNING.md).

[Video kualifikasi](ros2_ws/evidence/demo-consistency-20261116/demo-qualification/pov.mp4) · [Video ARENA extended](ros2_ws/evidence/demo-consistency-20261116/demo-arena/pov.mp4). Video hanya merekam kamera simulasi, bukan desktop; bagian awal mencakup preflight. Bab waktu tersedia pada laporan 71.

Setiap sesi teknis berikutnya perlu menyebut satu fokus, hasil yang hendak dibuktikan, lalu hasil nyata dan batasnya. Ringkasan ini diperbarui bila ada bukti baru; pekerjaan opsional diberi label opsional. Persentase kemajuan tidak dipakai karena belum ada ukuran penyelesaian seluruh proyek yang disepakati.
