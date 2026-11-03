# 50 — Akar kehilangan frame besar: kapasitas shared memory Fast DDS

Tanggal: 4 November 2026. Status: reproduksi kapasitas dan pembalikan terverifikasi; tiga kualifikasi GUI, ARENA standar dan pengaman kehilangan kamera diterima.

## Pendekatan isolasi

Pengujian baru menghilangkan renderer, fisika, detektor, controller dan misi. Dua publisher sintetis mengirim Image RGB8 10 Hz, melalui ROS langsung atau Gazebo Transport → parameter_bridge → ROS. Isi piksel tidak diproses. Subscriber yang sama mencatat sequence dari timestamp, ukuran payload dan waktu kedatangan. QoS sensor tetap BEST_EFFORT.

Publisher mengirim 200 frame per kamera. Pengukuran menggunakan sequence 10–189, yaitu 180 frame per kamera, agar discovery awal dan penutupan tidak tercampur. Uji mengubah resolusi/payload, lalu kapasitas shared-memory segment pada publisher saja; receiver tetap memakai konfigurasi sebelumnya.

## Reproduksi tanpa Gazebo

| Jalur / profil | Payload | Depan diterima | Bawah diterima | Gap maksimum depan / bawah |
| --- | --- | --- | --- | --- |
| ROS langsung, konfigurasi awal | 640×480 RGB | 48/180 | 70/180 | 2,200 / 1,101 s |
| Bridge, konfigurasi awal | 640×480 RGB | 111/180 | 94/180 | 0,900 / 1,601 s |
| ROS langsung, konfigurasi awal | 320×240 RGB | 180/180 | 180/180 | 0,100 / 0,100 s |
| Bridge, konfigurasi awal | 320×240 RGB | 180/180 | 180/180 | 0,101 / 0,101 s |
| ROS langsung, SHM eksplisit 512 KiB | 640×480 RGB | 56/180 | 101/180 | 3,000 / 2,099 s |
| ROS langsung, SHM 16 MiB | 640×480 RGB | 180/180 | 180/180 | 0,101 / 0,101 s |
| Bridge, SHM 16 MiB | 640×480 RGB | 180/180 | 180/180 | 0,101 / 0,102 s |
| Kembali ke SHM 512 KiB | 640×480 RGB | 43/180 | 57/180 | 2,000 / 2,201 s |

Log publisher ROS pada kontrol default, kecil, besar dan pembalikan masing-masing mencatat seluruh 200 sequence; durasi publish maksimum sekitar 1,0–1,3 ms. Kehilangan yang dihitung tidak berasal dari timer publisher yang hanya mengirim sebagian sequence.

Kontrol kecil–besar–kecil mereproduksi, menghilangkan, lalu memunculkan kembali kehilangan frame. Dua XML kontrol memiliki transport SHM/UDP yang sama dan berbeda hanya pada segment_size. Ini memperkuat hubungan kausal kapasitas segment dan kehilangan pesan besar; masalah dapat terjadi tanpa renderer, algoritma vision atau bridge.

## Penjelasan

Satu frame RGB 640×480 memiliki payload 921.600 byte (900 KiB), belum termasuk header. Ukuran itu lebih besar dari segment 512 KiB. [Dokumentasi Fast DDS 2.6](https://fast-dds.docs.eprosima.com/en/v2.6.10/fastdds/transport/shared_memory/shared_memory.html) menyebut default segment 512 KiB dan memperingatkan kehilangan data ketika segment terlalu dekat dengan atau lebih kecil dari ukuran data.

Dengan 16 MiB pada publisher, kedua kamera kembali menerima seluruh frame terukur tanpa mengubah receiver. Masalah yang berhasil direproduksi ini menjelaskan jalur menuju `stale_camera`: kehilangan pesan berturut-turut dapat melewati deadline kamera. Ini bukti akar masalah untuk mode kegagalan yang diuji; tidak menyatakan setiap insiden historis pasti memiliki satu sebab yang sama.

## Perbaikan repositori

- `config/fastdds-images.xml` menyediakan SHM 16 MiB dan tetap menyertakan UDPv4 untuk discovery/peer jaringan. Tidak mengubah sysctl, tidak membersihkan shared memory milik proses lain, dan tidak memasang dependensi baru.
- Launch memberi profil hanya pada proses bridge yang menerbitkan Image dan proses persepsi yang menerbitkan overlay RGB besar. Pada default isolated, bridge sensor/kendali tidak mendapat override. Pada layout single, profil berlaku pada participant bridge yang juga memuat gambar.
- QoS kamera dari laporan 49 tetap BEST_EFFORT depth 1. Resolusi 640×480, FPS, intrinsics, controller, estimator, gaya tujuh thruster dan semua timeout dipertahankan.
- Setup memasang XML bersama konfigurasi package. Hash matriks reliability sekarang mencakup XML, agar perubahan transport tidak lolos dari pemeriksaan source berubah.

Audit `/proc` mengonfirmasi env profil pada camera bridge/perception dan file SHM terpetakan berukuran sekitar 16 MiB; bridge kritis tidak diberi env profil. Mapping yang dibaca participant lain tidak dianggap bukti participant itu mengalokasikan segment besar sendiri. Instalasi XML melalui ament dan build berhasil.

## Penerimaan misi

178 tes unit lulus. Tes baru menolak segment yang tidak cukup untuk dua frame RGB default dan memastikan UDP tetap dikonfigurasi.

Tiga run kualifikasi GUI lane 1 seed 7, dengan dua POV dan tiga observer independen, sudah diterima: start–surface 25,902 / 25,872 / 25,818 detik. Gap frame segar persepsi depan maksimum 0,152 / 0,162 / 0,161 detik; ROS raw depan 0,136 / 0,140 / 0,144 detik, mendekati native 0,133 / 0,137 / 0,126 detik. Seluruh pelintasan penuh, surface, stop, gaya nol dan shutdown bersih terverifikasi.

ARENA standar GUI dengan dua POV pada snapshot source yang sama **lulus**: thrust–surface 227,004 detik, skor simulator 210,18988, penalti 0. Kontak flare, payload masuk drum, Surfacing Square dan stop terverifikasi. Gap maksimum native depan/bawah 0,265/0,275 s; raw ROS 0,295/0,293 s; frame segar persepsi 0,287/0,465 s. Checker dan ketiga probe exit 0, tanpa cleanup paksa.

Uji `camera_loss` sesudah thrust juga lulus sebagai respons fault yang diharapkan: state ABORT, perintah/gaya thruster nol, stationary dan shutdown bersih. Tidak ada timeout yang dilonggarkan. Hasil pengiriman sintetis dan hasil misi disimpan serta diperiksa terpisah.

## Bukti

Folder lokal: `ros2_ws/evidence/camera-isolation-20261104/`. `summary.json` memuat empat kontrol resolusi/jalur; `shm-summary.json` dan `reversal-summary.json` menyimpan eksperimen kapasitas serta pembalikan. `acceptance/summary.json`, raw native/ROS metadata, `profile-audit.json`, build dan log tes mempertahankan bukti masing-masing tahap.

Pada uji throughput mandiri, wrapper `ros2 run` bridge tercatat exit -15 karena cleanup harness mengirim SIGINT ke induk dahulu lalu SIGTERM ke grup. Ini dicatat terpisah dari hasil penerimaan frame dan tidak dianggap bukti shutdown misi bersih. Penerimaan misi memakai checker shutdown penuh tersendiri.

## Batas

Bukti berlaku pada Fast DDS dan transport lokal host ini. QoS BEST_EFFORT tetap merupakan kontrak subscriber kamera, bukan penjelasan utama kehilangan payload besar. Belum memvalidasi kamera nyata/driver Jetson atau transfer gambar antarmesin. Tidak ada perubahan parameter atau perintah Pixhawk.

Ringkasan verifikasi dengan assert, hash source termasuk XML, kesamaan XML kontrol kecuali kapasitas, audit instalasi profil, metrik frame dan bukti misi: [verification.json](../ros2_ws/evidence/camera-isolation-20261104/verification.json). Extended pinger/pickup belum diulang pada profil ini.
