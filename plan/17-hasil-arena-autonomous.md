# Hasil ketahanan persepsi dan ARENA autonomous

Tanggal: **25 Oktober 2026, Asia/Jakarta**. Lingkup: menyelesaikan ketahanan deteksi, tracking, proyeksi kamera dan integrasi misi Navigation → flare → blue drum pada **simulator** `/home/rasya/AUV/ros2_ws`.

**Status jeda atas permintaan pengguna: implementasi tersedia, tetapi ARENA belum dinyatakan selesai/stabil.** Tidak ada proses uji sesi ini yang masih berjalan saat pemeriksaan jeda. Pada kode terakhir, `nominal-synced.json` (layout 0, B-R-Y, drum 1) dan `blue-four-fixed.json` (layout 1, R-Y-B, drum 4) lulus `COMPLETE`. Namun `alternate-synced.json` (layout 1, Y-B-R, drum 3) gagal saat Navigation dengan `mission_or_state_timeout`; hasil positif `alternate.json` di bawah berasal dari revisi sebelumnya.

Temuan terakhir: peta mengestimasi gate pada x≈15,033 m, sedangkan gate sebenarnya x=16 m. AUV berhenti pada x≈16,233 m sehingga belakang badan belum lewat sepenuhnya. Dugaan yang perlu diperbaiki adalah proyeksi gate pada pandangan miring dan penerimaan pembaruan landmark yang mengunci estimasi pendek. Penutupan simulator pada run gagal itu juga belum bersih. **Belum ada perbaikan gate tersebut yang diterapkan setelah permintaan jeda.**

Pekerjaan tersisa: perbaiki pendekatan/estimasi gate, ulangi regresi layout/urutan yang terdampak, selesaikan build serta ringkasan bukti akhir. `evidence/arena-autonomous/verification.json` belum dibuat; tautan ringkasan pada bagian bawah adalah keluaran yang masih harus diselesaikan. Bukti lain yang sudah lulus: 54 tes logika/geometri, 18 skenario kamera, 94 perturbasi, lima uji gangguan, uji fisika bola dan regresi kualifikasi (9,316 s start sampai surface).

## Acuan dan batas hasil

[Rulebook resmi](https://sauvc.org/rulebook/) diperiksa kembali: edisi terbit **2026 v6.1.0**, diperbarui 27 November 2025. [PR 2027 #25](https://github.com/sauvc/rulebook/pull/25) masih terbuka, sehingga hasil ini tidak dinyatakan sebagai kepatuhan final edisi 2027.

Navigation wajib selesai sebelum tugas lain. AUV harus menghindari orange flare dan tidak menjatuhkan bola flare selama Navigation. Urutan flare disampaikan setelah Navigation; perintah menyentuh flare atau melepas payload tidak membuktikan bola jatuh atau masuk drum. Implementasi mengikuti urutan tersebut. Pinger, reacquisition/pengambilan kembali bola dan sistem skor lomba lengkap tidak termasuk tugas yang diminta.

## Empat bagian yang diimplementasikan

| Bagian | Implementasi |
| --- | --- |
| Ketahanan deteksi | Masker warna/bentuk diperbaiki untuk pencahayaan rendah dan blur ringan; stripe gate dipisahkan dari red drum di latar. Gate satu tiang, citra kosong dan drum terpotong ditolak. Fragmen flare <30 px tidak diberi estimasi jarak. |
| Tracking | ID per kamera, konfirmasi tiga pengamatan, asosiasi kelas/prediksi pusat citra, expiry 0,7 s timestamp gambar. Deteksi yang hilang tidak diterbitkan sebagai prediksi terkini. |
| Kalibrasi/proyeksi simulator | `CameraInfo`, pinhole K, distorsi nol, ekstrinsik kamera depan/bawah dan posisi metrik dari ukuran properti. Pose pada timestamp gambar diinterpolasi sebelum target dipetakan ke world. |
| Kontrol ARENA | Dive dalam starting zone, hindari orange, lewat gate penuh, jalankan urutan flare setelah Navigation, cari blue drum, alignment titik payload, drop, tunggu bukti masuk, surface dan stop. |

Kalibrasi simulator berasal dari geometri pembangkitan kamera, bukan pengukuran DWE. Intrinsik memakai HFOV 1,22173 rad, principal point `(319.5,239.5)` untuk 640×480, piksel persegi. Kamera depan berada di `(0.32,0,0)` badan; kamera bawah di `(0,0,-0.12)` dan menghadap bawah. Model proyeksi ini mengasumsikan badan mendekati datar; pipeline kendaraan fisik memerlukan kalibrasi serta transformasi sikap lengkap yang terukur.

Landmark statis baru memerlukan tiga posisi yang konsisten selain konfirmasi track citra. Pembaruan posisi yang melompat >0,75 m ditolak; jika satu warna terpecah menjadi beberapa komponen, kandidat terdekat dengan landmark dipilih. Ini memperbaiki kasus flare kuning tipis yang sempat menghasilkan jarak terlalu jauh saat urutan `R-Y-B`. Posisi kendaraan dipasangkan dengan timestamp gambar; frame di luar buffer pose/toleransi tidak dipakai untuk memperbarui peta.

```mermaid
flowchart LR
  C[Kamera Gazebo] --> P[Deteksi dan tracking]
  P --> M[Peta dari proyeksi kamera]
  O[Odometri bertimestamp] --> M
  M --> A[Controller ARENA]
  A --> G[Pengawas perintah]
  G --> S[Fisika Gazebo]
  S --> R[Referee kontak dan bola]
  R -- Status tugas tanpa koordinat target --> A
```

Controller tidak menerima layout properti atau berlangganan `/sauvc/arena/physics`. Koordinat pada event referee juga dibuang sebelum status diberikan ke controller. Dimensi kolam/zona dipakai untuk rute pencarian, sedangkan target flare/drum berasal dari kamera. Jika target keluar FOV pada pendekatan terakhir, controller memakai landmark statis dan odometri; ini bukan navigasi visual tanpa lokalisasi.

## Bola fisik dan pembuktian independen

Bola flare dan payload adalah model dinamis dengan collision. Mekanisme latihan menahan bola flare sampai kontak hull–tiang yang nyata, melepas penyangga, lalu memberi dorongan awal kecil; setelah itu gravitasi/collision menggerakkan bola. Tiang masih kaku, dan drag/buoyancy bola di air belum dimodelkan. Pada Fortress, komponen perintah kecepatan perlu dibuang setelah pelepasan agar perintah nol lama tidak membatalkan gerak jatuh.

Payload berdiameter 4 cm dan bermassa contoh 100 g. Titik payload berada **20 cm di depan, 18 cm di bawah** pusat badan agar tidak menutup lensa bawah. Alignment memperhitungkan offset tersebut. Setelah bagian akhir drum terpotong FOV, alignment menyelesaikan pergeseran pendek terhadap pusat hasil kamera yang sudah dipetakan.

Referee terpisah memeriksa seluruh envelope AUV saat lewat gate, kontak orange/flare, urutan bola yang turun >12 cm dari posisi tertahan, lalu payload pertama berada di dalam radius drum dan dekat dasar selama >0,5 s. `DONE` controller, flag release atau kontak saja tidak cukup. Referee menunggu surface dan perintah nol serta posisi stabil selama satu detik sebelum `COMPLETE`. Hasil terminal tidak berubah saat penutupan simulator.

Preset latihan menggagalkan kontak gate, dasar, dinding atau drum oleh hull; ini **lebih ketat** daripada penalti pada rulebook terbit. Keberhasilan yang dicatat adalah rangkaian tugas yang diminta, bukan perhitungan skor kompetisi menyeluruh.

## Bukti pengujian

- **54 tes logika/geometri lulus**, termasuk decode RGB/BGR/stride, deteksi warna/bentuk, clutter red drum di belakang gate, konfirmasi/expiry track, interpolasi yaw pada batas ±π, penolakan landmark melompat, alignment offset payload, penerimaan bola dan hasil terminal.
- **18 skenario kamera Gazebo lulus**, mencakup gate depan/balik, jauh/miring, empat warna flare, red/blue drum, posisi offset, satu tiang, citra kosong dan objek terpotong. JSON, raw image, anotasi dan `CameraInfo` dicocokkan melalui timestamp/header.
- **94 pemeriksaan perturbasi frame lulus**: intensitas 55% dan 125%, gain kanal biru 85%, noise ±8, blur horizontal tiga piksel, serta penolakan gate/drum yang dioklusi/dipotong. Ini batas perturbasi yang diuji, bukan jaminan untuk semua pencahayaan/occlusion.
- Pada sampel posisi terkontrol, galat proyeksi terbesar sekitar **0,118 m** pada gate miring. Range gate tetap mengasumsikan orientasi mendekati tegak lurus; angka tersebut bukan akurasi kamera nyata atau galat lokalisasi saat bergerak.
- Uji fisika terpisah membuktikan bola tertahan stabil, bola flare jatuh setelah kontak dan payload menetap di dasar drum. Posisi AUV hanya diatur oleh harness pada uji fisika/kamera terpisah, bukan pada misi penuh.
- Regresi kualifikasi `vision`, lane 1, `speed_scale=8` lulus `DONE`: **9,316 s** start sampai surface, **10,438 s** sampai stop pada satu run. Ini bukan median benchmark baru.

Misi penuh dimulai dari starting zone tanpa teleport atau waypoint properti yang disuntikkan ke controller. Fixture alternatif menggeser gate, orange dan ketiga flare; warna drum biru juga ditukar.

| Misi | Layout | Drum biru | Urutan | Kriteria |
| --- | --- | --- | --- | --- |
| Nominal | 0 | 1 | B-R-Y | Full gate, tiga bola jatuh, payload dalam blue drum, surface dan stop |
| Alternatif | 1 | 3 | Y-B-R | Kriteria yang sama; red drum dilewati tanpa drop |
| Regresi fragmen flare | 1 | 4 | R-Y-B | Kasus yang sempat gagal kini mencapai `COMPLETE` setelah perbaikan landmark/timestamp |

Lima skenario gangguan kamera, perintah, odometri, kontak dan clock membuktikan `ABORT`, perintah nol dan posisi diam. Kehilangan perintah ditangani pengawas independen dengan timeout 0,5 s; data wajib macet ditangani dalam 2 s wall clock. Pengujian kamera terpisah juga memastikan JSON lama serta gambar anotasi dibersihkan ketika kamera berhenti. Alat uji menutup server melalui API sebelum cleanup untuk menghindari hang SIGINT Gazebo yang ditemukan pada salah satu percobaan awal.

Ringkasan akhir, hash sumber dan tautan bukti **belum difinalisasi**; target keluaran adalah `ros2_ws/evidence/arena-autonomous/verification.json`. Bukti lokal berada di `ros2_ws/evidence/`, diabaikan Git; kode dan alat uji disimpan dalam repositori. Percobaan gagal awal tetap disimpan agar tidak tercampur dengan hasil penerimaan akhir.

## Menjalankan dan status

```bash
cd /home/rasya/AUV/ros2_ws
bash tools/ros.sh build --symlink-install
bash tools/ros.sh launch sauvc_sim arena.launch.py arena:=finals autonomous:=true flare_order:=B-R-Y
```

Status: `/sauvc/arena/state`. Hasil independen: `/sauvc/arena/result`. Gambar inspeksi: `/sauvc/perception/front/image_annotated` dan `/sauvc/perception/bottom/image_annotated`. Perintah pengulangan uji ada dalam [README workspace](../ros2_ws/README.md).

Seluruh hasil merupakan simulasi dengan gerak ideal dan odometri ground truth. Kalibrasi DWE fisik, kolam nyata, air keruh/refleksi berat, dinamika thruster, pinger dan pengambilan kembali payload belum divalidasi. GUI/rqt untuk misi ARENA penuh belum diperiksa secara langsung; pengujian runtime dilakukan headless dengan kamera rendering aktif.
