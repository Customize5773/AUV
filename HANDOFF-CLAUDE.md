# HANDOFF CLAUDE — panduan awal AUV / SAUVC

**Diperbarui 24 November 2026.** Bahasa kerja pengguna: **Indonesia**. File ini menggabungkan konteks beberapa sesi yang bekerja pada repo yang sama. Baca ringkasan ini dahulu, kemudian bagian sesuai tugas. Judul dan ungkapan “sesi ini” dalam lampiran adalah perspektif sesi asal, bukan prioritas tunggal seluruh proyek.

## Ringkasan untuk langsung melanjutkan

Rasya mengembangkan AUV untuk SAUVC. Tujuan simulasi ROS 2 adalah menguji persepsi, estimasi sensor, kontrol, urutan tugas, skor, kontak fisik dan failsafe sebelum dipindahkan ke kendaraan nyata. Kualifikasi mengejar **waktu tercepat dengan pelintasan sah**; ARENA mengejar penyelesaian tugas yang dapat dibuktikan referee independen. Jangan mengejar waktu dengan mengurangi syarat badan sepenuhnya melewati gate atau melonggarkan pengaman.

**Keputusan operasi:** kendaraan tidak memakai GUI web HydroShips. Laptop memakai VS Code Remote SSH untuk mengedit dan menjalankan kode **di Jetson**, melalui wireless. GUI bukan jalur operasi aktif. Simulator Gazebo dan POV di laptop tetap boleh dipakai; keputusan tanpa GUI onboard tidak berarti menghapus visualisasi simulasi.

**Status saat file diperiksa:** HEAD lokal `fdf8225a` (`Enhance compact pickup and alignment strategies in arena mission`). `HANDOFF-CLAUDE.md` sudah berisi konteks dari sesi lain dan masih untracked; isi sebelumnya dipertahankan di bawah. Penyusunan ringkasan ini hanya membaca repo/laporan, tidak menyambungkan Jetson, menjalankan simulator, memeriksa rulebook online, atau menguji hardware.

## Peta konteks dan urutan membaca

| Kebutuhan Claude | Sumber utama |
|---|---|
| Status simulator terbaru dan prioritas | [STATUS.md](STATUS.md), bagian akhir [laporan 83](plan/83-pickup-live-dan-transfer-square.md) |
| Perintah launch, checker dan POV | [ros2_ws/CARA-RUNNING.md](ros2_ws/CARA-RUNNING.md) |
| Akses wireless langsung laptop–Jetson | [Cara-Akses-Jetson-SSH.md](Cara-Akses-Jetson-SSH.md), lampiran jaringan dalam file ini |
| Operasi tanpa GUI | [tools/auv.sh](tools/auv.sh), [laporan 53](plan/53-operasi-ssh-dan-arsip-gui.md) |
| Riwayat migrasi GUI dan SSH | [laporan 52](plan/52-pemulihan-hydroships-jetson.md), [53](plan/53-operasi-ssh-dan-arsip-gui.md), [56](plan/56-wifi-reboot-dan-kesiapan-pixhawk.md) |
| Kamera fisik ke ROS/persepsi | [laporan 55](plan/55-kamera-fisik-ros-persepsi.md), pembaruan uji meja pada STATUS.md |
| Benchmark model vision | Bagian vision dalam file ini dan `vision-test/reports/jetson-gate-system-20261102-v1/` |
| Riwayat keputusan lengkap | [plan/README.md](plan/README.md) |

**Catatan ketersediaan:** `CARA-OPERASI-SSH.md` masih disebut pada beberapa lampiran historis, tetapi tidak ditemukan dalam checkout saat handoff ini diperiksa. Gunakan `Cara-Akses-Jetson-SSH.md`, `tools/auv.sh` dan laporan 53 sebagai acuan yang tersedia.

## Prioritas simulator saat serah terima

Menurut laporan 83, perubahan terbaru menambah pemeriksaan clearance sebelum `ALIGN_PICKUP → DESCEND_PICKUP` untuk profil badan kompak dan gripper tetap 8 cm. Margin latihan 5 mm; jika celah tidak dapat diverifikasi selama tiga detik, abort `pickup_clearance_unverified`. **219 tes tercatat lulus, tetapi regresi Gazebo misi penuh setelah pengaman ini masih terbuka.**

Penerimaan sebelum pengaman terbaru:

| Extended dari starting zone | Skor | Thrust–surface | Batas |
|---|---:|---:|---|
| Drum pinger 3, seed 42 | 289,05858 | 264,714 s | DONE, retensi bola tanpa fixed joint |
| Drum pinger 3, seed 91 | 289,19604 | 260,132 s | DONE, kode kamera bawah sama |
| Drum pinger 4, seed 42 | 289,34658 | 255,114 s | DONE, penalti nol |

Hasil tersebut belum membuktikan regresi kode terakhir. Bola dekat dinding drum masih mempunyai batas mekanik: offset 25 cm menyebabkan badan membentur bibir sebelum mencapai tinggi pickup. Jika melanjutkan simulator, tugas pertama adalah build dan penerimaan nominal drum 3/4 setelah pengaman baru, lalu uji abort pada fixture dekat dinding. Perintah dan kriteria pemeriksaan ada di lampiran simulator pada akhir file ini. Jangan memperpanjang gripper atau memakai pengunci untuk menyamarkan kegagalan tanpa persetujuan desain pengguna.

Baseline rulebook yang **tercatat** masih 2027.3.2, terakhir disebut dicek resmi 19 November. Ini bukan pemeriksaan online baru pada 24 November. Verifikasi sumber resmi sebelum mengubah aturan, dimensi lomba atau skor. Waktu resmi kualifikasi dan metrik surface–stop harus tetap dibedakan sesuai rulebook yang diverifikasi.

## Konteks sesi panjang ini: HydroShips → SSH dan pemeriksaan Jetson

1. **Simulasi berkembang jauh melampaui world visual.** Kualifikasi dan ARENA memakai model gaya tujuh thruster, estimator sensor virtual, kamera, referee, pengaman kehilangan data dan bukti runtime. T1–T4 horizontal, T5–T7 vertikal. Profil bersama di [config/propulsion.json](config/propulsion.json); simulator tidak bergantung pada folder GUI. Pemetaan parameter yang cocok belum membuktikan posisi, arah gaya dan mixer fisik.
2. **Pemulihan GUI bersifat historis.** Pada 4 November, unit HydroShips yang masih menunjuk `/home/aero/AUV2027/hydroships` dan venv rusak sempat dipulihkan. Itu laporan 52, bukan status aplikasi yang harus diaktifkan lagi.
3. **Pengguna kemudian mengganti keputusan:** AUV memakai SSH saja. Folder GUI dipindah menjadi `GUI-prototype`, unit `hydroships.service` dihentikan/dinonaktifkan/diarsipkan. Pengguna selanjutnya secara eksplisit mengonfirmasi GUI laptop sengaja dihapus; cukup arsip di Jetson `/home/aero/AUV/GUI-prototype`. Jangan memulihkan GUI laptop atau mengaktifkan layanan karena membaca laporan 52.
4. **Terminal menggantikan GUI:** `tools/auv.sh` menyediakan `devices`, `status`, `telemetry`, `camera-check`, `sim-start qualification|arena|pinger`, `sim-stop`, dan `logs`. Perintah simulasi menggunakan systemd user dan tidak membuka MAVLink hardware. `sim-stop` bukan emergency stop AUV fisik. Reader telemetry pasif memakai `.venv-vehicle`; jangan menggunakan venv GUI lama untuk ROS.
5. **Validasi 4 November, jaringan lab lama:** 30/30 koneksi SSH berhasil setelah konfigurasi power saving, tiga siklus radio off/on pulih 5,43–6,46 detik, satu reboot pulih sekitar 47,5 detik. Sebanyak 17 parameter Pixhawk terbaca; 15 parameter propulsi cocok; tetap disarmed dan CRITICAL. Pengguna saat itu menyatakan Pixhawk hanya USB tanpa daya thruster. Tidak dilakukan uji gerak, perubahan parameter, arm atau mode. Bukti ada di laporan 56 dan `evidence/ssh-reboot-20261104/`.
6. **Jangan menerapkan hasil lab lama ke AUV-Link.** IP Wi-Fi `192.168.67.167`, UUID/prosedur rollback profil lab, serta angka reboot/reconnect pada laporan 56 adalah historis. Jaringan kemudian berubah ke hotspot langsung AUV-Link; lihat konfigurasi terbaru di bawah dan lampiran jaringan. Belum ada pembuktian reboot/cable-free AUV-Link yang setara hanya dari pengujian lab lama.
7. **Riwayat hardware lebih baru ada pada STATUS.md:** uji meja kamera DWE dan telemetry 300 detik, relay orientasi ROS, serta input pilot netral terbatas saat disarmed untuk mengisolasi failsafe telah dicatat pada 20 November. CRITICAL dapat terkait kehilangan input pilot, tetapi jangan menganggap semua CRITICAL pasti karena itu. Sensor tekanan eksternal disebut belum terpasang. Itu bukan izin mengirim input pilot terus-menerus, menonaktifkan failsafe atau memulai misi fisik.

## Lokasi dan batas perangkat

- Laptop: `/home/rasya/AUV`; workspace simulator: `/home/rasya/AUV/ros2_ws`. **Jangan tertukar dengan `/home/rasya/ros2_ws`** milik proyek lain.
- Jetson Orin NX: akun `aero`, repo `/home/aero/AUV`. AUV-Link menurut panduan: laptop `10.42.77.1`, Jetson `10.42.77.2`; alias `auv-wifi`. Ethernet cadangan Jetson `192.168.2.2`.
- Satu radio laptop berganti antara klien internet dan hotspot AUV-Link. Mengaktifkan hotspot dapat memutus internet/chat. Siapkan instruksi offline dan ikuti panduan jaringan; jangan mengganti profil diam-diam saat pengguna bergantung pada koneksi itu.
- Kredensial tidak disertakan. Gunakan kunci SSH yang sudah tersedia dan pertahankan pemeriksaan host key. Jika sudo membutuhkan password, pengguna memasukkannya langsung di terminal, bukan chat/source/log.
- Koneksi hardware belum diperiksa ketika handoff ini ditulis. Klaim perangkat terakhir tersambung/terputus di lampiran adalah snapshot sesi asal; periksa ulang sebelum pengujian yang memerlukannya.
- Tidak ada bukti misi kolam lengkap, kalibrasi thrust/PWM/mixer, hidrofon fisik, waterproofing atau gripper/servo di air selesai. Cocoknya parameter dan keberhasilan simulasi tidak menggantikannya.

## Cara melanjutkan tanpa mengulang atau menimpa pekerjaan

1. Baca `AGENTS.md`, `git status --short`, STATUS.md dan laporan terakhir yang relevan. Ikuti aturan Graphify: query sebelum pencarian source, update graph setelah perubahan kode. Repo pernah diedit beberapa sesi bersamaan; jangan reset, clean atau menimpa perubahan yang tidak dibuat sendiri.
2. Tentukan jalur dari permintaan terbaru pengguna: simulator pickup, vision, atau jaringan/hardware. Jangan menganggap kata “prioritas” dari salah satu lampiran otomatis membatalkan jalur lain. Jika diminta meneruskan simulasi, regresi pengaman pickup adalah pekerjaan terbuka terdekat yang telah diidentifikasi.
3. Simpan setiap run baru dalam direktori bukti tersendiri. Bedakan unit test, fixture, misi Gazebo penuh, replay digital, kamera di udara dan misi fisik. Pertahankan run gagal, alasan abort, proses exit dan shutdown; jangan melonggarkan guard demi angka lulus.
4. Bukti dan model besar banyak yang diabaikan Git: `ros2_ws/evidence/`, `evidence/`, seluruh `vision-test/`, serta cache/build. **File handoff atau clone repo saja tidak cukup membawa semua artefak.** Jika Claude tidak memiliki workspace/salinan artefak, tandai bukti tidak tersedia; jangan mengarang isinya.
5. Berbahasa Indonesia, fokus hasil dan batas bukti. Pengguna menyukai solusi sederhana ala Ponytail dan kemajuan konkret. Jangan berhenti pada rencana jika implementasi sudah diminta; tetapi jika pengguna meminta rencana lalu menunggu konfirmasi, patuhi batas itu. Handoff ini sendiri hanya transfer konteks, bukan instruksi untuk otomatis reboot, menjalankan motor, atau mengubah konfigurasi perangkat.

---

# Konteks lengkap dari sesi lain — dipertahankan

Bagian berikut sudah ada dalam file sebelum ringkasan pengarah di atas ditambahkan. Angka vision dan jaringan mempunyai tanggal serta cakupannya masing-masing. Gunakan sumber terbaru yang cocok dengan tugas; jangan menyatukan seluruh hasil menjadi satu penerimaan sistem end-to-end.

# HANDOFF untuk Claude — AUV dan eksperimen arsitektur vision

Disusun **24 November 2026** untuk memindahkan konteks percakapan Codex ke Claude. Bukti vision terakhir dalam sesi ini berasal dari **2 November 2026**, diperiksa kembali dari laporan lokal saat menyusun file ini. Tidak ada benchmark baru, koneksi Jetson baru atau pengujian fisik pada penyusunan handoff.

Dokumen ini mencakup dua jalur pekerjaan:

1. **Vision AUV / `vision-test/`**: konteks utama sesi chat yang diserahterimakan, dijelaskan terlebih dahulu.
2. **Simulasi ROS 2 SAUVC**: catatan handoff yang sudah ada sebelumnya dipertahankan utuh pada bagian akhir. Status dan prioritasnya terpisah dari eksperimen vision; jangan menganggap keduanya sudah terintegrasi.

## 1. Tujuan awal pengguna dan keputusan ruang lingkup

Permintaan awal Rasya: menguji berbagai teknologi/arsitektur vision seperti YOLOv8, YOLO11, OpenCV dan CNN untuk menentukan pendekatan yang pantas digunakan pada AUV. Pekerjaan eksperimen berada di folder **`vision-test/`**, bukan membuat proyek pembanding baru di tempat lain.

Hasil yang dicari adalah keputusan berdasarkan akurasi/lokalisasi, ketahanan terhadap gangguan, alarm keliru, biaya komputasi Jetson, dan kelayakan informasi untuk kendali. Jangan menyamakan pemilihan detektor dengan pengesahan seluruh sistem navigasi.

Keputusan diskusi: **gate kualifikasi terlebih dahulu**, kamera depan, termasuk menemukan kembali gate setelah U-turn. Flare/drum bukan fokus benchmark vision saat ini. Eksperimen awal `opencvtest2` masih coba-coba dan bukan baseline matang.

Pengguna belum menyiapkan gate fisik/arena dan pengujian kolam pada tahap terakhir sesi vision. Kamera DWE fisik sudah pernah digunakan melalui USB Jetson di udara. Pengguna meminta memaksimalkan pekerjaan digital terlebih dahulu. Jangan mengharuskan pengambilan data fisik untuk setiap pekerjaan digital yang masih bisa dilakukan.

## 2. Keputusan arsitektur sementara

**Kandidat integrasi pengembangan pertama:**

```text
DWE/gambar asli
  → satu letterbox ke input model
  → YOLOv8n 160 TensorRT FP16 + torchvision NMS
  → verifier bukaan v2 berbasis warna/geometri OpenCV
  → asosiasi satu target + konfirmasi tiga observasi + freshness
  → observasi target untuk eksperimen integrasi simulator
```

**YOLO11n 160 FP16 tetap pembanding.** Alasannya bukan YOLOv8n selalu paling cepat, melainkan recall lebih kuat pada kondisi redup/noise dalam resep dan dataset yang telah diuji. Kecepatan berubah sesuai workload. OpenCV tetap baseline dan komponen verifier. Ini belum keputusan final untuk deployment bawah air atau izin mengendalikan aktuator.

Sumber utama: [ARCHITECTURE-DECISION](vision-test/ARCHITECTURE-DECISION.md), [README vision](vision-test/README.md), [rencana gate](vision-test/GATE-PLAN.md). Dokumen tersebut menyimpan beberapa snapshot historis; utamakan laporan sistem lengkap di bawah untuk hasil sesi terakhir.

## 3. Inventaris pembanding yang benar-benar diuji

Tujuh pendekatan, dengan sembilan resep utama pada perbandingan Jetson terakhir:

| Resep | Runtime pada Jetson |
|---|---|
| OpenCV HSV/geometri, gambar 640×480 | CPU |
| TinyGateCNN proyek, input 160×120 | CPU |
| YOLOv8n 160 | TensorRT FP16 |
| YOLO11n 160 | TensorRT FP16 |
| YOLOv8n 320, resep putaran kedua | PyTorch CUDA |
| YOLO11n 320, resep putaran kedua | PyTorch CUDA |
| D-FINE-N 320 | PyTorch CUDA |
| SSDLite–MobileNetV3 320 | PyTorch CUDA |
| RTMDet-tiny 320 | TorchScript CUDA |

YOLO 160 PyTorch CUDA juga dipakai dalam audit kesetaraan preprocessing/native, terpisah dari tabel timing sembilan resep utama. Input, training dan backend berbeda: jangan mengklaim ini perbandingan murni seluruh keluarga arsitektur. TinyGateCNN yang lemah tidak membuktikan semua CNN lemah. RT-DETR pernah dibahas sebagai kandidat, bukan bukti bahwa sudah diuji pada batch ini.

RTMDet native MMDetection/MMEngine masih terkendala dependensi (`mmcv`/API distributed Torch NVIDIA). Yang berhasil adalah **jalur inferensi TorchScript** yang diekspor dan diperiksa parity. Jangan mengganti Torch NVIDIA/global agar instalasi MMDetection terlihat berhasil. Rujukan: [ekspor RTMDet](vision-test/reports/rtmdet-torchscript-export-20261102-v2/README.md).

## 4. Bukti terakhir — sistem lengkap di Jetson

Baca dahulu [laporan sistem gate digital](vision-test/reports/jetson-gate-system-20261102-v1/README.md), lalu `summary.json`, `verification.json` dan `system-metrics.csv` di folder yang sama.

- Dua model × enam kondisi × 108 gambar × tiga inferensi = **3.888 sampel pengukuran**.
- Setiap kondisi memakai **48 frame val sintetis**, termasuk **36 gate core**, dan **60 PNG negatif DWE tersimpan**.
- Negatif berasal dari dua stream/sudut dalam **satu ruangan**, bukan lingkungan independen.
- Verifier menolak seluruh alarm negatif pada semua 12 kombinasi model–kondisi. Tidak ada tambahan gate sintetis cocok yang hilang setelah verifier pada set ini.
- **122 langkah ekspektasi temporal lulus**: target hilang, observasi tidak terverifikasi, timestamp berulang/tidak berurutan, stale/future, ambigu, gap dan timeout tanpa kedatangan frame. Ini langkah skenario perangkat lunak, bukan 122 misi fisik.
- **80 tes lulus di laptop dan 80 di Jetson** pada run tersebut. Angka ini historis, bukan klaim suite terbaru per 24 November sudah dijalankan lagi.

| Kondisi | Kandidat negatif v8 /60 | Kandidat negatif v11 /60 | Lolos verifier v8 / v11 | TP sintetis sekaligus bukaan cocok v8 / v11, dari 36 |
|---|---:|---:|---:|---:|
| original | 10 | 23 | 0 / 0 | 36 / 36 |
| dark55 | 2 | 58 | 0 / 0 | 29 / 24 |
| bright125 | 40 | 5 | 0 / 0 | 36 / 36 |
| blur5 | 6 | 11 | 0 / 0 | 36 / 36 |
| noise8 | 31 | 30 | 0 / 0 | 36 / 26 |
| blue_gain | 12 | 8 | 0 / 0 | 36 / 34 |

**Makna:** alarm detektor belum hilang dari model. Yang berhasil pada set ini adalah penolakan oleh verifier. Jangan mengubah hasil ini menjadi klaim detektor tanpa false positive atau keamanan di kolam.

| Model | p95 pipeline lengkap, rentang enam kondisi | Sampel terburuk |
|---|---:|---:|
| YOLOv8n 160 FP16 | 27,25–32,64 ms | 81,37 ms |
| YOLO11n 160 FP16 | 25,79–30,44 ms | 66,74 ms |

Timing mencakup preprocessing/inferensi/NMS/pemetaan box dengan sinkronisasi CUDA, verifier CPU dan selector. Input sudah ada di RAM; kamera/USB, disk dan transformasi diagnostik tidak diukur. Tidak boleh menyimpulkan stabil 30 fps atau latensi sensor-ke-kendali dari angka ini. Urutan semua v8 lalu semua v11 tidak diacak.

Tiga inferensi per gambar adalah **pengulangan gambar diam**. Selector direset untuk setiap gambar, lalu diamati tiga kali. Skenario fault terpisah menyuntikkan observasi di antarmuka verifier–selector. Hasil ini belum membuktikan tracking identitas pada video bergerak.

## 5. Bukti pendukung — canonical preprocessing dan benchmark sembilan resep

[Laporan canonical Jetson](vision-test/reports/jetson-canonical-20261102-v1/README.md) selesai sebelum laporan sistem lengkap:

- **2.592 pemeriksaan pixel** pada CUDA PyTorch/TensorRT; **432 perbandingan prediksi original** terhadap native pada backend yang sama. Selisih box maksimum sekitar 0,0001221 piksel, score nol. Ini tidak berarti output PT identik dengan FP16.
- **9 resep × 6 kondisi = 54 kombinasi stress**; lima warmup dan 144 sampel timing per kondisi.
- **12 run TensorRT** dalam enam blok AB/BA; original mempertahankan 36 TP/0 FP/0 FN pada core sintetis.
- Median p95 run sintetis: **v8 9,90 ms**, **v11 10,48 ms**. Replay campuran tersimpan 120 detik/model justru lebih cepat pada v11: p95 **v8 10,43 ms**, **v11 9,14 ms**.
- Replay memproses **13.014 frame v8**, **13.953 frame v11**; throughput offline ini bukan fps kamera. Jangan menyamakan timing detektor saja dengan timing pipeline lengkap bagian sebelumnya.
- 79 tes/perangkat adalah snapshot tahap ini; bertambah menjadi 80 setelah runner sistem ditambahkan.
- SSH pernah terputus saat replay awal; bukti `.interrupted` dipertahankan dan dikecualikan. Pengulangan berikut dijalankan dengan `nohup` dan selesai. Tidak menimpa bukti lama.

## 6. Kontrak perangkat lunak yang harus dipertahankan

| File di `vision-test/` | Peran |
|---|---|
| `benchmark/vision_preprocessing.py` | Letterbox bersama YOLO 160/320, validasi output dan proyeksi koordinat asli |
| `benchmark/gate_alignment.py` | Pemeriksaan pasangan warna/geometri dasar |
| `benchmark/gate_alignment_v2.py` | Tambahan bukti tiang vertikal; menolak palang/sudut yang menyerupai pasangan tiang |
| `benchmark/target_selection.py` | Target tunggal, asosiasi, konfirmasi dan freshness |
| `benchmark/evaluate.py` | Evaluator box/alignment dengan input ketat |
| `benchmark/run_digital_consistency.py` | Audit CPU/CUDA PT/TRT terhadap native |
| `jetson/replay_gate_system.py` | Runner sistem lengkap dan skenario temporal tanpa kamera |
| `jetson/stress_extended_device.py` | Stress tujuh resep tambahan |
| `jetson/repeat_benchmarks.py` | Benchmark bergantian dua YOLO |
| `jetson/soak_saved_frames.py` | Replay TensorRT berjangka pada gambar tersimpan |
| `jetson/live_camera.py` | Runner kamera; tidak dijalankan dalam tahap digital terakhir |
| `jetson/air_comparison.py` | Pembanding pada sampel kamera tersimpan |
| `tests/test_system_replay.py` | Regresi ekspektasi fault dan rekonfirmasi |

Preprocessing YOLO: **BGR native → satu resize INTER_LINEAR dengan rasio dipertahankan → padding 114 → input model → box ke koordinat gambar asli**. Pinned Ultralytics **8.3.203** dan NMS torchvision. Jangan mengecilkan DWE 1920×1080 ke 640×480 sebelum factory: cara lama itu menyembunyikan banyak alarm dan mengubah arti hasil. `--legacy-common-input` hanya diagnostik historis. Undistortion belum diterapkan.

Selector menerima ukuran gambar eksplisit; default 640×480 tetap didukung. Konfirmasi minimal **tiga observasi**, asosiasi IoU minimum **0,5**, batas lompatan horizontal **0,2 lebar box**, freshness **0,25 detik**. Jangan melonggarkan agar tes tampak lulus. Tidak boleh meneruskan target lama saat observasi ditolak/timeout. Perubahan verifier dapat memengaruhi recall; evaluasi alarm negatif dan kehilangan gate positif bersama.

## 7. Data, kamera, dan batas validitas

- Dataset `datasets/qualification-render-v1/` memiliki 240 frame: train 132 core + 12 challenge = 144; val 44 core + 4 challenge = 48; test 44 core + 4 challenge = 48. Total 220 core dan 20 challenge satu tiang. Challenge tidak dimasukkan sebagai label negatif kosong pada training YOLO. Benchmark di atas memakai 48 val. Fixture/geometri/aset sintetis tetap dibagi lintas split; bukan bukti generalisasi kolam.
- Test lama sudah pernah dibuka/dinilai. Jangan menyebut penilaian ulang sebagai test independen baru atau menyetel threshold memakai test. Bobot/threshold tidak diubah pada tahap digital terakhir.
- Semua kondisi gangguan menggunakan transformasi digital dari gambar yang sama, bukan air keruh/refraksi/arus nyata.
- Video `vision-test/yolov8n_200_epoch.mp4` adalah rekaman bekas deteksi dengan overlay; pengguna tidak mempunyai versi mentah. Jangan memperlakukannya sebagai video mentah independen untuk benchmark model.
- Checkerboard sudah dicetak dan diukur **25 mm**. Kalibrasi DWE v2 di udara: 30 pose stabil, fitting 24 + enam diagnostik, RMS fitting **0,590 px**, residual diagnostik **0,376–1,074 px**. Lihat [kalibrasi v2](vision-test/reports/dwe-calibration-fit-20261029-v2/README.md). Masih provisional: cakupan bawah/kanan dan kestabilan antar-sesi perlu pemeriksaan. Belum diterapkan pada runtime/kontrol; bukan kalibrasi bawah air.
- Uji live historis DWE mencapai sekitar 29,3 fps selama 300 detik/model, nol read failure pada run yang dilaporkan. Ini sesi lain, jangan digabung sebagai bukti bahwa pipeline verifier terbaru sudah live 30 fps.

## 8. Lokasi perangkat, environment dan transfer

- Laptop: `/home/rasya/AUV/vision-test`.
- Jetson: `/home/aero/AUV/vision-test`, akun **`aero`**. Alamat LAN historis **192.168.2.2**, laptop **192.168.2.1**.
- Panduan akses yang sekarang ada di repo juga mencatat alias **`auv-wifi`**, hotspot AUV-Link laptop **10.42.77.1**, Jetson **10.42.77.2**: [Cara-Akses-Jetson-SSH](Cara-Akses-Jetson-SSH.md). Konfirmasi route/alamat/koneksi aktual; jangan menganggap socket SSH `/tmp` dari sesi lama masih hidup. File handoff simulator di bawah menyatakan perangkat terakhir terputus; koneksi tidak diuji saat menulis handoff ini.
- Runtime terukur 2 November: Jetson Orin NX, NVIDIA Torch `2.5.0a0+872d972e41.nv24.08`, CUDA **12.6**, TensorRT **10.3.0**, OpenCV **4.11.0**, power **MAXN**. Konfirmasi versi aktual sebelum perubahan environment. Jangan menebak versi JetPack hanya dari label CUDA.
- Jetson memakai **`.venv-jetson/bin/python`**. Pertahankan user site: torchvision berada di sana; jangan menetapkan `PYTHONNOUSERSITE=1`. Jangan menyalin venv x86 laptop ke ARM, mengganti Torch NVIDIA, atau menganggap engine TensorRT portabel ke perangkat/runtime lain.
- Laptop memakai **`.venv-train/bin/python`** untuk suite lengkap; Python sistem tidak memiliki seluruh Torch/Ultralytics yang dibutuhkan. `.venv-dfine` dan `.venv-rtmdet` juga pernah dipakai untuk jalur khusus.
- Runner, test, laporan dan PNG hasil terakhir sudah disinkronkan ke Jetson pada sesi 2 November dan hash salinan diperiksa. Itu bukti historis, bukan pemeriksaan koneksi hari ini.
- **Penting: seluruh `vision-test/` diabaikan oleh `.gitignore`. Clone/pull repo atau mengirim file handoff ini saja tidak membawa kode, checkpoint, dataset dan laporan vision.** Claude perlu akses workspace yang sama atau salinan folder/artifak tersebut. Jangan mengubah `.gitignore` atau force-add model besar tanpa kebutuhan yang disepakati.
- Jangan menulis password/token ke handoff, source atau log. Jika host key berubah, verifikasi fingerprint melalui perangkat sebelum memperbarui known_hosts; jangan mematikan verifikasi SSH.

## 9. Cara melanjutkan dan memeriksa bukti

Baca laporan sebelum menjalankan eksperimen baru. Semua perintah berikut adalah referensi, **tidak dijalankan saat membuat handoff**.

Suite laptop:

```bash
cd /home/rasya/AUV/vision-test
.venv-train/bin/python -m unittest discover -s tests -q
```

Suite Jetson, setelah koneksi dan path diverifikasi:

```bash
cd /home/aero/AUV/vision-test
.venv-jetson/bin/python -m unittest discover -s tests -q
```

Replay sistem baru di Jetson; setiap run harus memakai output yang belum ada:

```bash
cd /home/aero/AUV/vision-test
out="reports/jetson-gate-system-$(date +%Y%m%d-%H%M%S)"
taskset -c 0 .venv-jetson/bin/python jetson/replay_gate_system.py --output "$out"
```

Untuk job panjang via SSH, gunakan `nohup`/tmux dan simpan log serta exit code; jangan mengandalkan umur koneksi terminal. Jangan menjalankan beberapa benchmark GPU bersamaan. Jangan mengubah mode daya/clock di tengah perbandingan tanpa mencatat protokol.

Audit artefak terakhir dan pembuatan ulang PNG di laptop:

```bash
cd /home/rasya/AUV/vision-test
MPLCONFIGDIR=/tmp/auv-matplotlib python3 \
  reports/jetson-gate-system-20261102-v1/audit_and_report.py
```

Audit mengikat hash kode/citra dan dapat gagal jika source telah berubah sejak snapshot. Selidiki mismatch sebelum menyebut hasil lama lulus terhadap source baru; jangan mengedit prediksi/metrik historis untuk menghilangkan error.

## 10. Urutan pekerjaan digital selanjutnya

1. Baca `git status`, instruksi lokal, laporan terakhir, dan periksa file/venv tersedia. Pastikan apakah Rasya ingin meneruskan **vision** atau **simulator pickup**; keduanya punya tugas terbuka berbeda. Jika permintaan jelas tentang vision, tidak perlu mengalihkan ke pickup.
2. **Prioritas vision yang belum dikerjakan di sesi ini:** adapter pipeline kandidat–verifier–selector ke eksperimen persepsi simulator atau stream simulator. Mulai dari observasi/log tanpa aktuator fisik. Jangan menganggap ROS 2 sekarang sudah memakai YOLO TensorRT dari `vision-test`.
3. Ukur antrean/frame age, frame drop dan deadline pipeline pada replay/stream berurutan. Uji kehilangan target/reacquisition dalam gerakan, target mirip lebih dari satu, dan timestamp; pengulangan gambar statis belum menjawab ini.
4. Bila mempercepat verifier, profilkan terlebih dahulu. Ia memanggil beberapa pemrosesan HSV/pasangan/Sobel; penggunaan ulang hasil atau ROI mungkin membantu, tetapi perlu regresi box/target, recall dan alarm pada kasus kegagalan. Jangan menurunkan pemeriksaan geometri hanya demi fps.
5. Latih/ubah threshold hanya dengan protokol pengembangan yang jelas, bobot baru dan output baru; simpan pembanding beku. Data independen tetap diperlukan sebelum klaim generalisasi.
6. Ketika pengguna siap fisik: kumpulkan negatif dari lingkungan lain dan gate nyata, validasi kalibrasi/mode kamera serta kondisi bawah air, lalu alignment/pelintasan. Jangan menyatakan langkah itu selesai dari skor simulator.

## 11. PNG dan laporan yang perlu diberikan kepada pengguna

Pengguna menyukai gambar **PNG**, semua resep yang telah diuji, label instrumen jelas beserta satuan/backend, dan path file konkret. Nilai yang belum tersedia harus diberi label unavailable, bukan nol.

- [Perbandingan pipeline lengkap](vision-test/reports/jetson-gate-system-20261102-v1/gate-system-comparison.png).
- [Galeri alarm YOLOv8n](vision-test/reports/jetson-gate-system-20261102-v1/yolov8n-false-candidates.png).
- [Galeri alarm YOLO11n](vision-test/reports/jetson-gate-system-20261102-v1/yolo11n-false-candidates.png).
- [Sembilan resep di Jetson](vision-test/reports/jetson-canonical-20261102-v1/jetson-all-recipes.png).
- [Stabilitas timing](vision-test/reports/jetson-canonical-20261102-v1/jetson-canonical-stability.png).
- [Alarm negatif sebelum verifier](vision-test/reports/jetson-canonical-20261102-v1/jetson-negative-alarms.png).
- [Grafik historis semua model 29 Oktober](vision-test/reports/vision-instruments-20261029/README.md).

## 12. Cara bekerja dengan Rasya

Berbahasa Indonesia, singkat dan berdasarkan bukti. Saat diminta “lanjut”, teruskan dari artefak terakhir; jangan mengulang setup atau menanyakan izin untuk langkah reversibel yang sudah menjadi lingkup tugas. Tunjukkan progres dan keterbatasan yang relevan, bukan hanya rencana. Selesaikan pekerjaan digital yang tidak menunggu data fisik.

Jangan mencampur CPU, GPU/TensorRT, data sintetis, negatif ruangan, live camera dan misi fisik. Jangan mengubah angka historis menjadi status terbaru tanpa verifikasi. Hormati file/perubahan dari sesi lain. Tidak ada otorisasi menjalankan thruster, gripper atau gerak kendaraan fisik dari handoff ini.

Ikuti `AGENTS.md`: jika graph ada, gunakan `graphify query` sebelum penelusuran sumber; graph saat ini tidak selalu mencakup folder vision yang di-ignore. Setelah perubahan kode gunakan `graphify update .`. Pertahankan workspace simulator `/home/rasya/AUV/ros2_ws` terpisah dari `/home/rasya/ros2_ws`; untuk yang pertama gunakan `bash tools/ros.sh` sesuai panduannya.

---

## Lampiran — handoff simulator yang sudah ada, dipertahankan utuh

Bagian berikut berasal dari pekerjaan simulator lain. Statusnya tidak diaudit ulang pada penyusunan konteks vision ini. Prioritas “pekerjaan aktif sekarang” di lampiran berlaku untuk jalur simulator tersebut, bukan instruksi otomatis mengganti tugas vision.

# Handoff sesi akses wireless Jetson — untuk Claude

Disusun 24 November 2026 dari percakapan ini. **Baca bagian ini untuk pekerjaan jaringan/SSH.** Handoff simulasi yang sebelumnya ada di file ini dipertahankan di bawah sebagai konteks terpisah; angka dan status simulasinya tidak diperiksa ulang dalam sesi jaringan ini.

## Tujuan dan hasil akhir

Pengguna ingin mengedit `/home/aero/AUV` di Jetson dari VS Code laptop, langsung melalui wireless, tanpa router atau hotspot HP. Solusi yang dipasang: **laptop menjadi hotspot AUV-Link, Jetson menjadi klien Wi-Fi**. Pengguna akhirnya menyatakan **“berhasil”** setelah menjalankan urutan dengan hotspot HP dimatikan. Panduan operasional terbaru: [Cara-Akses-Jetson-SSH.md](Cara-Akses-Jetson-SSH.md).

## Konfigurasi yang perlu dipertahankan

| Komponen | Nilai |
| --- | --- |
| Repo laptop | `/home/rasya/AUV` |
| Akun/hostname Jetson | `aero` |
| Proyek Jetson | `/home/aero/AUV` |
| Profil/SSID langsung | `AUV-Link` |
| Laptop Wi-Fi | `wlp0s20f3`, `10.42.77.1/24`, mode AP 2,4 GHz |
| Jetson Wi-Fi | `wlP1p1s0`, `10.42.77.2/24`, alamat manual |
| Ethernet cadangan | laptop `192.168.2.1`, Jetson `192.168.2.2` |
| Alias SSH laptop | `auv-wifi` → `aero@10.42.77.2` |

Pemeriksaan lokal 24 November: alias masih menunjuk ke `10.42.77.2`, `HostKeyAlias 192.168.2.2`; profil laptop AUV-Link memiliki `ipv4.method shared`, alamat `10.42.77.1/24`, `connection.autoconnect no`. Jadi hotspot laptop diaktifkan secara sengaja dengan nmcli. Konfigurasi awal pernah dibuat manual; jangan menyamakan kondisi awal dengan kondisi lokal terakhir.

Profil Jetson yang dipasang pada sesi ini: autoconnect `true`, priority `100`, IPv4 manual `10.42.77.2/24`, never-default `true`, IPv6 disabled. Lokasi instalasi: `/etc/NetworkManager/system-connections/AUV-Link.nmconnection` (root, mode 600). File persiapan `/home/aero/AUV-Link.nmconnection` juga pernah dibuat; jangan mencetak isinya karena mengandung password. Password acak AUV-Link disimpan dalam profil jaringan, **tidak ditulis di handoff/repo**. Profil Jetson belum dibaca ulang pada 24 November.

`~/.ssh/config` laptop menggunakan key `~/.ssh/id_ed25519`, `IdentitiesOnly yes`, `ServerAliveInterval 15`, `ServerAliveCountMax 3`. HostKeyAlias memakai identitas Jetson yang telah dikenal melalui Ethernet; jangan menonaktifkan pemeriksaan host key. Backup config sebelum perpindahan Realme pernah dibuat sebagai `~/.ssh/config.before-realme`.

## Urutan yang berhasil

Pengguna perlu menjalankan langkah ini sendiri ketika chat kehilangan internet. Simpan instruksi dulu. Matikan hotspot HP Realme, pasang Ethernet sementara untuk pemulihan, lalu dari laptop:

```bash
nmcli --wait 20 connection up AUV-Link
ssh -t aero@192.168.2.2 'sudo nmcli --wait 60 connection up AUV-Link'
ssh -o ConnectTimeout=10 auv-wifi 'hostname; ls -ld /home/aero/AUV'
```

Hanya jika SSH terakhir berhasil, lanjut:

```bash
code --new-window --remote ssh-remote+auv-wifi /home/aero/AUV
```

Pastikan indikator `SSH: auv-wifi`; jika perlu buka **File → Open Folder… → /home/aero/AUV**. Terminal dan file remote berada di Jetson; checkout laptop tidak otomatis ikut berubah.

Untuk penggunaan tanpa kabel: aktifkan hotspot laptop sebelum menyalakan Jetson, tunggu autoconnect, lalu tes SSH. Jika gagal, gunakan Ethernet untuk diagnosis. Setelah tes SSH wireless berhasil, cabut Ethernet dan ulangi tes agar bukti tanpa kabel eksplisit.

## Pelajaran penting — jangan ulangi diagnosis yang sama

- **Satu adaptor Wi-Fi laptop dipakai bergantian sebagai hotspot atau klien Realme/lab.** Saat laptop kembali ke jaringan internet, AUV-Link berhenti dan `10.42.77.2` tidak terjangkau. Ini berkali-kali terlihat langsung pada `nmcli device status` dan `ip route get`.
- Jangan mengaktifkan hotspot melalui tool saat chat bergantung pada Wi-Fi yang sama tanpa menyiapkan langkah offline. Pengguna sudah menjelaskan chat akan offline dan meminta perintah untuk dijalankan sendiri.
- `Connection successfully activated` membuktikan aktivasi profil, bukan keberhasilan SSH. Membuka jendela VS Code juga bukan bukti koneksi remote.
- `Connection to 192.168.2.2 closed` sesudah perintah nmcli selesai adalah normal.
- Autoconnect priority tidak otomatis memindahkan Jetson dari Realme yang masih aktif. Perpindahan eksplisit melalui Ethernet pernah diperlukan. Jangan berulang kali hanya meminta laptop mengaktifkan AUV-Link.
- Jangan aktifkan ulang hotspot laptop setelah Jetson tersambung tanpa alasan; ini dapat memutus klien.
- `sudo -n` di Jetson gagal karena password diperlukan. Pengguna memasukkan password langsung di terminal `ssh -t`; jangan meminta password sudo di chat atau menganggap password hotspot sebagai password sudo.

## Bukti dan batas klaim

Log pengguna pernah menunjukkan laptop `10.42.77.1`, Jetson `10.42.77.2`, SSID AUV-Link, serta `ssh ... hostname` menghasilkan `aero`. Radio Jetson ketika itu terhubung ke BSSID laptop `ec:4c:8c:71:7b:5e`, sinyal -31 dBm. Pengguna kemudian mengonfirmasi alur berhasil setelah hotspot HP dimatikan; panduan diperbarui berdasarkan konfirmasi itu.

**Belum ada konfirmasi terpisah yang lengkap untuk:** SSH/VS Code setelah Ethernet dicabut, cold boot/autoconnect tanpa kabel, pemulihan berulang, dan internet USB tethering bersamaan. Jangan mengklaim semua itu telah lulus. Tidak ada uji actuator/motor atau misi fisik pada sesi ini.

## Riwayat jaringan sebelumnya

- Wi-Fi lab `Lab Robotika AI`: IP historis Jetson `192.168.67.167`. Jetson berasosiasi tetapi DHCP timeout. Capture 60 detik berisi 7 paket Discover/Request keluar tanpa Offer/ACK tertangkap. Ini tidak membuktikan router rusak atau paket sampai ke router. Penyebab akar belum terselesaikan.
- Hotspot HP `realme Note 60`: laptop `10.29.49.14`, Jetson `10.29.49.116` saat diuji; SSH dan VS Code pernah berhasil. Alamat tersebut DHCP/historis, bukan konfigurasi AUV-Link aktif.
- Pengguna memilih AUV-Link untuk menghilangkan ketergantungan pada HP/router. Jangan mengembalikan alias ke IP Realme tanpa kebutuhan yang jelas.

## Jika diminta melanjutkan

Mulai dengan hasil aktual dan kebutuhan pengguna, bukan mengulang setup dari nol. Untuk kegagalan, ambil kondisi kedua perangkat pada waktu yang sama:

```bash
nmcli device status
ip route get 10.42.77.2
ssh aero@192.168.2.2 'nmcli device status; ip -4 addr show wlP1p1s0'
ssh -o ConnectTimeout=10 auv-wifi 'hostname; ls -ld /home/aero/AUV'
```

Jika pengguna ingin pembuktian akhir, prioritaskan tes tanpa Ethernet dan boot ulang terkontrol setelah pekerjaan disimpan. Jangan melakukan reboot otomatis hanya karena handoff menyebut tes ini. Untuk internet bersamaan, USB tethering HP ke laptop merupakan opsi yang dibahas, belum dipasang/diuji.

Pengguna menyukai instruksi Bahasa Indonesia yang ringkas, teknis, bisa disalin; bedakan bukti berhasil dari rencana. Ikuti AGENTS.md saat menelusuri kode, termasuk graphify sebelum pencarian kode. Hindari menimpa perubahan pekerjaan lain. Permintaan terakhir sesi ini hanya menyiapkan handoff, bukan menjalankan tes baru.

---

# Handoff simulasi yang sudah ada sebelumnya

# Serah terima simulasi ROS 2 SAUVC kepada Claude
**Titik lanjut per 24 November 2026.** Rasya mengembangkan dan menguji strategi AUV otonom sebelum kapal siap masuk kolam. Prioritas kualifikasi adalah waktu tercepat dengan dua pelintasan sah. Prioritas ARENA adalah menuntaskan tugas dan membuktikannya dengan pengamatan independen. Pekerjaan aktif sekarang adalah regresi pickup bola setelah penambahan pengaman sebelum turun.

## Konteks yang perlu dipertahankan

- Repo berada di `/home/rasya/AUV`. Simulator SAUVC berada di `ros2_ws/` **di dalam repo ini**. Workspace lain di `/home/rasya/ros2_ws` digunakan untuk proyek berbeda. Ikuti [instruksi repo](AGENTS.md), termasuk memakai Graphify untuk menelusuri kode. Periksa perubahan lokal sebelum mengedit dan simpan hasil run baru di direktori tersendiri.
- Baseline aturan yang tercatat adalah **SAUVC 2027.3.2**. Sebelum mengubah geometri lomba, urutan tugas atau skor, cek versi yang sedang diterbitkan dan catat perbedaannya. Ukuran kendaraan, margin kamera dan posisi pada skenario latihan memiliki asumsi tersendiri. [Rulebook resmi](https://sauvc.org/rulebook/)
- Kualifikasi sudah berjalan di simulator dinamis pada tiga jalur. AUV menyelam, seluruh badan melewati gate, berputar, melewati gate kembali, lalu naik dan berhenti. Catat waktu pelintasan penuh kedua untuk lomba serta waktu surface dan stop untuk proyek.
- ARENA memakai model dinamis tujuh thruster, T1–T4 horizontal dan T5–T7 vertikal, dengan estimator sensor virtual. Alur latihan mencakup menghindari flare oranye, melintasi gate, menyentuh flare sesuai urutan skenario, dan menjatuhkan bola. Varian blue drum menuju drum biru. Varian extended memilih drum pinger, keluar sepenuhnya dari target zone, kembali mengambil **bola yang sama**, lalu membawanya hingga surface di Square dan berhenti.
- Pertahankan keputusan mekanik pengguna. Batang gripper tetap **8 cm** dalam rentang yang diminta 5–10 cm, terpasang di tengah bawah badan, dan panjangnya tetap. Dua rahang bergerak saat melepas dan menjepit. Profil uji pickup memakai opsi **compact** dengan bentuk badan bawah yang direvisi. Kamera bawah membantu mengukur posisi bola terhadap pusat drum untuk memilih arah hadap sebelum turun.
- Seluruh hasil di bawah berasal dari simulasi. Jetson Orin NX, Pixhawk dan kamera DWE pernah tersedia untuk pengujian terpisah. Terakhir pengguna menyatakan perangkat sedang terputus. Kapal lengkap, kalibrasi mixer dan thrust, hidrofon, serta gripper di air masih memerlukan validasi fisik. Pilihan servo, catu dan kanal belum dikonfirmasi.

## Bukti terakhir dan pekerjaan terbuka

| Uji Gazebo extended sebelum pengaman baru | Skor simulator | Thrust sampai surface |
|---|---:|---:|
| Drum 3, seed 42 | 289,05858 | 264,714 s |
| Drum 3, seed 91 | 289,19604 | 260,132 s |
| Drum 4, seed 42 | 289,34658 | 255,114 s |

Ketiganya mencapai DONE. Pada drum 4, semua 1.399 frame dari kredit retrieval sampai akhir merekam kontak jari dengan bola tanpa fixed joint. Bukti ini berlaku untuk posisi bola yang terjadi pada run tersebut. [Rekap drum 3](ros2_ws/evidence/compact-start/visual-yaw-aCjx/verification.json) · [Run drum 4](ros2_ws/evidence/compact-start/pinger4-0TUZ/mission.json)

Batas mekanik yang sudah terukur terjadi saat bola berada **25 cm dari pusat drum**. Dalam uji penurunan terpisah, badan mengenai bibir drum ketika titik jepit masih 17,1 cm di atas pusat bola. Perubahan terakhir memeriksa celah seluruh sudut badan bawah sebelum transisi `ALIGN_PICKUP → DESCEND_PICKUP`. Margin latihan 5 mm. Jika pengamatan ulang selama 3 detik gagal membuktikan celah cukup, pengendali menghentikan upaya dengan `pickup_clearance_unverified`. **219 tes lulus setelah perubahan ini. Penerimaan Gazebo misi penuh setelah perubahan masih terbuka.** [Laporan eksperimen 83](plan/83-pickup-live-dan-transfer-square.md) · [Log tes](ros2_ws/evidence/pickup-clearance/tests.log)

## Tugas pertama untuk sesi baru

1. Build revisi saat ini. Ulang misi extended nominal drum 3 dan 4 secara berurutan. Contoh perintah di bawah memakai direktori bukti baru setiap kali dijalankan.
2. Untuk tiap run, periksa `passed`, `extended_proof`, `physical_retention`, `surfacing_square_verified` dan `shutdown_clean`. Cocokkan dengan peristiwa referee, kontak badan–drum, kontak rahang dengan payload asli sampai surface, status fixed joint dan thruster akhir. Jika kasus nominal abort, periksa estimasi pusat drum dan margin saat ALIGN_PICKUP sebelum mengubah ambang.
3. Ulang kasus bola dekat dinding dengan fixture dan collision yang dicatat di laporan 83. Untuk offset 25 cm, hasil pengaman yang diharapkan adalah menahan posisi kemudian abort sebelum turun atau menjepit. Catat hasil ini terpisah dari keberhasilan mengambil bola.
4. Tambahkan lokasi JSON, seed/kondisi, status shutdown dan hasil aktual ke laporan 83. Laporkan singkat kepada Rasya apa yang lulus, apa yang gagal, serta langkah berikutnya.

```bash
cd /home/rasya/AUV/ros2_ws
bash tools/ros.sh build --symlink-install
```

Setelah build berhasil, jalankan blok berikut. Pemeriksa akan berhenti pada drum pertama yang gagal agar lognya bisa ditinjau.

```bash
for drum in 3 4; do
  out=$(mktemp -d "evidence/compact-start/post-guard-drum${drum}-XXXXXX") || break
  echo "Bukti run: $out"
  bash tools/ros.sh python tools/check_arena.py --edition 2027 --compact --extended \
    --vehicle-model dynamic --pinger-drum "$drum" --output "$out/mission.json" || break
done
```

Untuk demo, tambahkan `--gui --pov` pada satu run. Gazebo menampilkan arena dari luar, sedangkan dua POV menampilkan kamera **depan dan bawah** AUV. Panduan menjalankan kualifikasi, ARENA, serta viewer tersedia di [CARA-RUNNING](ros2_ws/CARA-RUNNING.md). Untuk status proyek yang lebih luas lihat [STATUS](STATUS.md). Untuk pickup kompak gunakan bagian paling akhir laporan 83 karena hasil gripper versi sebelumnya juga masih tersimpan di repo.
