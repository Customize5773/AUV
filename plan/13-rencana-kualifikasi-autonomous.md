# Rencana lanjutan simulasi SAUVC: kualifikasi autonomous

**Status 25 Oktober 2026: implementasi kualifikasi telah disetujui pengguna dan sedang divalidasi.** Rancangan di bawah dipertahankan sebagai kriteria penerimaan; hasil aktual dicatat dalam [laporan implementasi](15-hasil-kualifikasi-autonomous.md).

**Revisi 25 Oktober 2026:** acuan utama adalah rulebook penyelenggara yang diverifikasi daring. Situs masih menerbitkan edisi 2026 v6.1.0, tetapi repositori resmi sudah memiliki usulan 2027.1.1 pada PR #25 yang belum digabung. Perbedaan versi, diagram terbaru dan koreksi urutan ARENA tercatat di [tinjauan rulebook dan rencana ARENA](14-tinjauan-rulebook-dan-rencana-arena.md). Sumber versi harus diperiksa lagi sebelum implementasi; diagram 2026 tidak dianggap sebagai arena 2027.

## Target dan dasar keputusan

Melanjutkan simulasi di `/home/rasya/AUV/ros2_ws` sampai AUV latihan dapat menyelam, melewati gerbang kualifikasi dengan seluruh badan, melakukan U-turn, lalu melewati gerbang yang sama kembali secara otomatis. Setelah pelintasan balik lengkap diverifikasi, AUV langsung naik secara vertikal ke permukaan dan berhenti otomatis. Hasil lintasan dan penyelesaian surfacing harus dibuktikan oleh pemeriksa simulasi yang terpisah dari controller.

[Rulebook resmi](https://sauvc.org/rulebook/) yang diperiksa pada sesi perencanaan ini masih berjudul **SAUVC 2026, v6.1.0**. Bagian Qualification mensyaratkan lintasan pergi, U-turn, lintasan balik, seluruh badan melintas, serta tidak menyentuh gerbang/dasar/dinding atau muncul ke permukaan selama lintasan. Bagian Qualification Arena(s) menentukan start menyentuh dinding dan gerbang sekitar 10 m dari start dengan lebar 1,5 m. Rencana memakai acuan tersebut sebagai latihan; belum menetapkan kepatuhan terhadap aturan 2027.

Ketentuan lintasan pergi/U-turn/balik juga terdapat dalam [usulan 2027 pada commit 746357d](https://github.com/sauvc/rulebook/blob/746357dcfe2e0fe89364aaad6ef8a2d60c5f5f8d/rulebook.md#qualification). Waktu resmi berhenti ketika seluruh badan selesai melewati gate untuk kedua kali. Karena itu `SURFACE` merupakan urutan penutup simulasi **setelah** keberhasilan kualifikasi tercatat, bukan persyaratan tambahan untuk memperoleh poin kualifikasi. Naik sebelum pelintasan kedua lengkap tetap merupakan pelanggaran. Bagian Qualification tidak menetapkan arah putar clockwise; ketentuan tersebut muncul pada video submission dalam usulan 2027 dan tidak otomatis diterapkan pada kualifikasi.

Pemeriksaan source saat menyusun rencana menemukan dua arena, kontrol kecepatan ideal, kamera depan/bawah dan odometri ground truth. Artefak pengujian sebelumnya mencatat kedua arena lulus uji gerak singkat; lintasan kualifikasi penuh belum terbukti. Pengujian simulator tidak dijalankan ulang pada tahap perencanaan ini.

## Ruang lingkup pekerjaan setelah dikonfirmasi

Fokus implementasi pertama adalah **kualifikasi lengkap pada model latihan yang sudah ada, diikuti surface dan berhenti otomatis**. Jumlah jalur serta bentuk gerbang mengikuti versi arena yang dipilih: arena 2026 saat ini memiliki dua jalur; diagram usulan 2027 menggambarkan tiga jalur dan gerbang menggantung sekitar 1 m dari permukaan. Launch arena manual tetap tersedia; controller autonomous hanya aktif melalui peluncuran yang memang memilih misi kualifikasi. Workspace KKI dan platform autonomous HydroShips tetap terpisah. Rencana ARENA dilaksanakan sesudah kualifikasi dan menunggu konfirmasi yang sama.

Model kotak dan kendali kecepatan ideal dipakai dahulu. Uji lintasan berbasis odometri menjadi pembanding untuk memeriksa controller dan pemeriksa lomba. Setelah itu kamera depan menjadi sumber deteksi dan alignment gerbang. Kedua hasil diberi label berbeda; lintasan berdasarkan koordinat gerbang tidak dilaporkan sebagai navigasi visual.

## Urutan pekerjaan dan syarat selesai

| Tahap | Pekerjaan | Bukti selesai |
| --- | --- | --- |
| 1. Dasar runtime dan penghentian | Periksa ulang build, SDF, sensor dan gerak; tambah pembatas kecepatan serta pengawas perintah; rapikan penghentian proses yang dimiliki launch | Uji lama kedua arena tetap lulus; perintah nol diterapkan saat controller berhenti/crash atau sumber data putus; tidak ada simulator milik pengujian yang tertinggal |
| 2. Pemeriksa kualifikasi | Tambah data kontak, peristiwa pelintasan gerbang, U-turn, batas kolam dan permukaan; pisahkan akhir lintasan resmi dari surface penutup | Uji membedakan surfacing terlalu dini, pelintasan kedua lengkap, serta surface yang diizinkan setelah lintasan selesai |
| 3. Controller dengan umpan balik odometri | Buat urutan menyelam, approach, lintasan pergi, menjauh secukupnya, U-turn, lintasan balik, langsung surface dan berhenti; semua transisi memakai kondisi terukur dan deadline | Kualifikasi dua arah sah, waktu selesai tercatat sebelum ascent, kemudian permukaan tercapai dan perintah nol; dilabeli uji berbasis ground truth |
| 4. Deteksi dan alignment kamera | Deteksi pasangan tiang berpenanda oranye dari kamera depan; kendalikan alignment dan approach; cari gerbang kembali setelah U-turn | Deteksi berasal dari frame aktual; koreksi terlihat saat posisi/yaw awal bergeser; kehilangan deteksi menghentikan approach dan memicu pencarian terbatas atau abort |
| 5. Pembuktian dan dokumentasi | Jalankan uji berulang, gangguan terkontrol, serta demonstrasi GUI; simpan log, lintasan dan hasil pemeriksa | Tersedia laporan JSON, jejak state, bukti dua pelintasan penuh, U-turn, ascent setelah selesai, berhenti di permukaan, hasil skenario gagal, serta rekaman demonstrasi visual |

Tahap 3 tidak menggantikan tahap 4. Penyelesaian pekerjaan yang direncanakan mencakup keduanya beserta bukti pada tahap 5.

## Rancangan kendali yang diusulkan

Urutan normal:

```text
WAIT_READY -> DIVE -> FIND_GATE -> ALIGN -> PASS_OUT
           -> CLEAR_GATE -> TURN -> FIND_RETURN_GATE
           -> ALIGN_RETURN -> PASS_BACK -> QUALIFIED
           -> SURFACE -> STOP -> DONE
```

Setiap state aktif dapat berakhir di `ABORT`. Misi tidak mulai sebelum clock, odometri, pemeriksa kontak dan, untuk navigasi visual, kamera tersedia serta masih segar. `QUALIFIED` memerlukan putusan pemeriksa bahwa lintasan lengkap sah; sesudah itu gerak horizontal dihentikan dan ascent dimulai tanpa kembali ke dinding start atau mengambil lintasan tambahan. `DONE` baru tercapai setelah badan mencapai posisi permukaan yang ditetapkan dan perintah kecepatan nol terverifikasi. Hasil `qualification_passed`, waktu akhir lintasan, `surface_completed` dan kendaraan berhenti dicatat terpisah. Kegagalan ascent tidak boleh mengubah waktu akhir lintasan atau dilaporkan sebagai penutup misi berhasil. Abort bersifat terminal, tanpa resume otomatis.

Controller memakai odometri untuk kedalaman dan heading pada model latihan ini. Pada tahap visual, arah menuju gerbang dan alignment ditentukan dari kamera; koordinat pasti gerbang yang dipakai pemeriksa tidak disalurkan sebagai pengganti hasil deteksi. Saat gerbang keluar dari bidang pandang karena sudah sangat dekat atau sedang melintas, pergerakan terbatas dengan odometri hanya boleh terjadi setelah alignment visual terkunci dan harus dicatat. Jika deteksi gagal sebelum kondisi tersebut, controller tidak diam-diam beralih ke waypoint.

Deteksi awal menggunakan segmentasi warna dan bentuk tiang, tanpa pelatihan YOLO. Dua tiang harus membentuk pasangan gerbang yang masuk akal; satu objek oranye saja tidak cukup. Keluaran minimum adalah terdeteksi/tidak, error pusat citra, lebar bukaan dalam piksel dan timestamp. OpenCV Python 3.10 akan diperiksa ketersediaannya dan hanya ditambahkan ke lingkungan lokal bila diperlukan; modul `cv2` sistem yang ditemukan saat perencanaan ber-ABI Python 3.12.

Nilai awal berikut merupakan usulan rekayasa, bukan ketentuan kompetisi: pusat badan pada kedalaman sekitar 0,6 m, kecepatan maju maksimum 0,3 m/s, yaw maksimum 0,5 rad/s, timeout perintah 0,5 s, dan batas total percobaan 180 s waktu simulasi. Nilai akan disesuaikan berdasarkan clearance serta hasil pengukuran. U-turn harus dilakukan setelah seluruh badan bebas dari gerbang, lalu maju dalam arah badan yang sudah berbalik; bergerak mundur melewati gerbang tanpa berputar tidak memenuhi syarat.

## Penghentian dan pembuktian independen

- Pengawas perintah menjadi satu-satunya penulis ke topic kecepatan Gazebo saat misi autonomous aktif. Controller mengirim perintah ke topic masukan terpisah. Pengawas membatasi nilai, menolak NaN/Infinity dan mengirim nol ketika perintah kedaluwarsa. Ini dibutuhkan karena plugin saat ini mempertahankan perintah terakhir meskipun publisher berhenti.
- Deadline lintasan memakai waktu simulasi. Kesegaran penerimaan perintah/data dan deteksi clock macet memakai monotonic wall clock, sehingga pause atau putusnya simulator tidak menyisakan perintah lama untuk diputar ulang. Menghilangkan seluruh proses pengawas diuji melalui penghentian simulator, tanpa mengklaim perlindungan controller kendaraan fisik.
- Pemeriksa membaca ground truth dan kontak simulator secara langsung. Pemeriksa tidak menerima klaim berhasil dari controller dan tidak mengendalikan arah gerak kendaraan.
- Pelintasan dihitung memakai seluruh envelope badan model beserta bagian yang menonjol, orientasi aktual dan ketebalan gerbang. Titik pusat melewati x=10 saja tidak cukup. Lintasan harus melalui bukaan gerbang yang dipilih, dengan urutan pergi -> U-turn -> balik yang sah.
- Instrumentasi kontak harus terbukti bekerja melalui skenario benturan sengaja. Tidak adanya pesan benturan saja tidak cukup untuk menganggap jalur bebas benturan apabila sumber kontak belum siap atau terputus.
- Posisi awal memang menyentuh dinding dan badan dapat berada sebagian di permukaan. Pemeriksa membedakan kondisi peluncuran, lintasan underwater, dan ascent sesudah `QUALIFIED`. Pengecualian awal dibatasi state dan deadline; izin ascent akhir hanya diberikan sesudah seluruh badan bebas dari gerbang pada lintasan balik. Selain dua kondisi tersebut, surfacing selama lintasan dinilai gagal.
- Tidak ada perintah gerak setelah `DONE`/`ABORT`. Gejala `Errno::ESRCH` saat shutdown GUI ditangani dan diuji terpisah; keberhasilan lintasan tidak dipakai untuk menyatakan shutdown sudah bersih.

## Bagian kode yang diperkirakan berubah

Nama modul berikut adalah usulan penempatan, bukan file yang sudah diimplementasikan.

| Lokasi | Perubahan yang direncanakan |
| --- | --- |
| `ros2_ws/src/sauvc_sim/sauvc_sim/arena.py` | Instrumentasi kontak serta pilihan jalur/offset spawn yang diperlukan untuk uji kualifikasi |
| `ros2_ws/src/sauvc_sim/sauvc_sim/qualification.py` | FSM dan kendali dengan umpan balik; log state dan alasan abort |
| `ros2_ws/src/sauvc_sim/sauvc_sim/gate_detection.py` | Fungsi deteksi citra yang dapat diuji tanpa menjalankan ROS |
| `ros2_ws/src/sauvc_sim/sauvc_sim/referee.py` | Pemeriksaan lintasan, putaran, kontak dan permukaan; hasil independen |
| `ros2_ws/src/sauvc_sim/sauvc_sim/command_guard.py` | Pengawas perintah dan keluaran nol saat timeout |
| `ros2_ws/src/sauvc_sim/config/bridge.yaml` | Aliran data kontak simulator yang dibutuhkan pemeriksa |
| `ros2_ws/src/sauvc_sim/launch/` | Peluncuran misi kualifikasi serta lifecycle simulator/node; arena manual tetap menjadi pilihan tersendiri |
| `ros2_ws/src/sauvc_sim/setup.py`, `setup.cfg`, `package.xml` | Registrasi executable dan dependensi runtime yang benar-benar dipakai |
| `ros2_ws/src/sauvc_sim/test/`, `ros2_ws/tools/` | Uji logika, skenario kegagalan dan pemeriksaan kualifikasi lengkap |
| `ros2_ws/README.md`, `plan/` | Cara menjalankan, label sumber kendali, bukti dan keterbatasan |

Tetap gunakan package yang sudah ada, topic standar yang tersedia, dan wrapper `bash tools/ros.sh`. Tidak menambah framework navigasi, custom ROS message, atau package baru tanpa kebutuhan yang terbukti selama implementasi.

## Skenario penerimaan

| Skenario | Hasil yang harus terlihat |
| --- | --- |
| Semua jalur pada versi arena yang dipilih, posisi nominal | Masing-masing tiga percobaan berurutan dengan dua pelintasan penuh, U-turn, tanpa pelanggaran, lalu langsung surface dan berhenti |
| Offset lateral awal ±0,2 m dan yaw ±10° | Mode visual mengoreksi arah dari gambar; laporan menyimpan offset, hasil deteksi dan putusan akhir |
| Pusat kendaraan sudah melintasi bidang gerbang tetapi belakang belum lewat | Belum mendapat pelintasan penuh; U-turn pada kondisi ini belum diizinkan |
| Bergerak di luar bukaan, salah gerbang, atau mundur tanpa U-turn | Tidak dinilai sebagai kualifikasi lengkap |
| Gerbang, lantai atau dinding tersentuh setelah fase start | Percobaan gagal dengan alasan dan kontak yang teridentifikasi |
| Badan menembus permukaan sebelum pelintasan balik lengkap | Percobaan kualifikasi gagal |
| Ascent setelah pelintasan balik lengkap | Waktu kualifikasi sudah tercatat; AUV naik vertikal tanpa kembali ke start, mencapai permukaan, kemudian perintah nol |
| Ascent selesai tetapi perintah naik masih aktif | Penutup misi belum dianggap berhasil |
| Kamera/odom/kontak terputus, clock berhenti, atau controller dimatikan | Perintah dihentikan; percobaan tidak dianggap berhasil dan tidak otomatis dilanjutkan |
| Gerbang tidak ditemukan atau hanya satu tiang terlihat | Pencarian terbatas lalu abort, tanpa keberhasilan sintetis |
| Penghentian normal, abort dan penutupan GUI | Node/simulator milik peluncuran ini berhenti tanpa mengganggu proses workspace lain |
| Regresi arena final | Build, SDF dan uji kamera/gerak yang sudah ada tetap lulus |

Artefak disimpan pada subfolder baru di `ros2_ws/evidence/` agar bukti awal tidak tertimpa. Laporan menyertakan parameter, mode kendali, timestamps, state, posisi/heading saat peristiwa penting, hasil kontak, alasan gagal dan hasil akhir. Status controller, putusan pemeriksa serta hasil penghentian proses dilaporkan terpisah.

## Batas tahap ini dan kelanjutan

Tahap kualifikasi belum mencakup dinamika thruster/buoyancy/drag, tuning ArduSub, kendali hardware, SLAM, akustik pinger, pengambilan kembali bola, integrasi UI/executor HydroShips, atau pengacakan arena secara umum. Rencana lanjutan [ARENA](14-tinjauan-rulebook-dan-rencana-arena.md) mencakup Navigation dahulu, tugas flare sesuai urutan panitia, dan payload ke blue drum. Geometri dan kriteria keberhasilan harus mengikuti sumber versi yang dicatat, bukan diagram lama atau urutan yang bertentangan dengan rulebook.

**Persetujuan berikutnya:** pengguna meminta “Implementasi kualifikasi terlebih dahulu” pada 25 Oktober 2026. Batas menunggu konfirmasi untuk kualifikasi telah terpenuhi; implementasi dan pengujiannya dilanjutkan. Misi ARENA belum dikerjakan.
