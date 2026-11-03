# 51 — Regresi pinger extended dan transport sintetis Jetson

Tanggal: 4 November 2026. Status: dua regresi extended final dan transport sintetis Jetson terverifikasi; satu kegagalan shutdown awal tetap dipertahankan.

## Ruang lingkup

Source runtime, model gaya, estimator, guard, viewer, QoS serta profil SHM 16 MiB dipertahankan dari laporan 50. Pengujian menggunakan model dinamis tujuh thruster, extended=true, scene_variant=1, blue_drum=3, pinger_drum=4, urutan Y-B-R, seed 91, Gazebo GUI dan dua POV. Tiga pengulangan awal memakai native/ROS sensor observer dan native image observer independen. Acuan fixture tetap 2027.3.2; [rulebook resmi](https://sauvc.org/rulebook/) yang diperiksa 4 November masih menampilkan versi 2027.3.2, pembaruan 30 Oktober 2026.

Tidak ada perubahan kode produksi pada tahap ini. Hasil 178 tes unit laporan 50 menjadi baseline hanya jika hash source sesuai; tidak diklaim tes unit dijalankan ulang di tahap ini.

## Regresi extended awal

Ketiga misi menyelesaikan tugas. Run 1 dan 3 diterima; run 2 gagal penerimaan karena server Gazebo memerlukan SIGKILL saat shutdown. Status DONE, pickup/retensi atau skor tidak menggantikan syarat shutdown bersih. Hasil gagal dipertahankan.

Waktu thrust–surface run 1/2/3: 206,242 / 206,192 / 206,326 detik. Pada window misi aktif, gap frame segar depan maksimum 0,257 / 0,204 / 0,190 detik; bawah 0,359 / 0,351 / 0,379 detik. Diagnosis sensor tidak menemukan stale saat misi aktif.

Observer pada harness awal masih hidup selama GUI/server dihentikan. Pembandingan berikutnya menghentikan observer sesudah controller DONE + 0,25 detik, sebelum teardown normal checker. Dua run final **diterima** dengan waktu thrust–surface 206,248 / 206,474 detik, skor simulator 290,81256 / 290,80578 dan penalti 0. Ketiga observer serta checker exit 0, GUI dan kedua POV terverifikasi, dan shutdown bersih tanpa cleanup paksa.

Verifier memeriksa event keluar target zone, acquisition/retrieval dengan ball_id yang sama, physical_retention, extended_proof, surface dan stopped. Timestamp terakhir observer native sensor, ROS sensor dan native kamera tetap melewati event STOPPED pada kedua run; penghentian observer tidak memangkas fase aktif. Gap frame segar depan 0,223 / 0,195 s; bawah 0,384 / 0,343 s.

Ini perbaikan lifecycle harness diagnostik, bukan perubahan controller atau klaim bahwa observer adalah satu-satunya penyebab shutdown historis. Semua syarat penerimaan misi dan shutdown tetap. Total yang disimpan: lima misi selesai, empat diterima, satu ditolak karena shutdown. Dua run terakhir memenuhi seluruh syarat pada prosedur yang diperbarui.

## Jetson: transport sintetis terisolasi

SSH ke aero@192.168.2.2 berhasil. Jetson melaporkan aarch64, ROS Humble dan middleware rmw_fastrtps_cpp. Dua aliran RGB 640×480 10 Hz diuji pada domain 118/localhost, dalam direktori sementara `/tmp/sauvc-dds-check-*`; tidak mengubah workspace, unit layanan, profil DDS global atau perangkat USB.

Setiap publisher mengirim 100 frame per aliran. Penilaian sequence 10–89 berarti 80 frame per aliran, terpisah dari discovery/penutupan. Receiver tidak diberi profil baru; hanya publisher pada kasus SHM 16 MiB yang diberi XML.

| Profil Jetson | Depan | Bawah | Gap maksimum depan/bawah |
| --- | --- | --- | --- |
| Default | 16/80 | 30/80 | 2,800 / 1,497 s |
| SHM 16 MiB | 80/80 | 80/80 | 0,100 / 0,102 s |
| Kembali ke default | 17/80 | 37/80 | 1,200 / 0,500 s |

Semua publisher/subscriber uji exit 0 dan audit tidak menemukan client sintetis tersisa. Ini memvalidasi transport sintetis lokal Jetson, bukan transfer DDS antarmesin, input kamera nyata, inferensi vision, CUDA atau misi fisik. Data yang dipindah ke laptop adalah metadata/log, bukan stream kamera.

## Inventaris kamera dan layanan: baca saja

Jetson menampilkan satu perangkat USB exploreHD dengan serial yang dilaporkan SN00009, bukan empat kamera terpisah:

- /dev/video0: capture MJPEG/YUYV, termasuk 640×480; MJPEG juga melaporkan resolusi lebih besar.
- /dev/video2: capture H.264 dari perangkat USB yang sama.
- /dev/video1 dan /dev/video3: metadata capture.

Tidak ada pemilik device terdeteksi oleh fuser saat inventarisasi. Peran depan/bawah belum dipetakan. Format hanya di-query; tidak menjalankan stream, mengubah kontrol kamera atau menyimpan foto.

Pixhawk USB masih terenumerasi, tetapi firmware/status MAVLink tidak dibaca ulang dan tidak ada perintah arm, mode, motor atau parameter.

Audit layanan menunjukkan HydroShips belum siap: snapshot is-active awal melaporkan active, tetapi inspeksi rinci kemudian menunjukkan auto-restart, MainPID=0 dan restart counter 1221. WorkingDirectory/ExecStart masih menunjuk `/home/aero/AUV2027/hydroships` yang tidak ada; repo `/home/aero/AUV/hydroships` ada. Interpreter `.venv/bin/python` di repo baru juga tautan rusak (resolved path mengandung `unsupported reparse tag 0xa000000c`). HTTP 8081 menolak koneksi. Journal user tidak tersedia, sehingga tidak diklaim ada diagnosis log traceback layanan.

Unit dan venv tidak diubah. Sebelum integrasi driver fisik, perlu menyiapkan venv Linux Jetson yang valid, memvalidasi dependensi/entry point, lalu memasang ulang unit lewat installer repo pada lokasi yang benar. Jangan hanya mengganti WorkingDirectory dan menganggap layanan siap.

## Bukti

Folder `ros2_ws/evidence/pinger-shm-20261104/`: batch `acceptance/`, pembandingan `observer-close-first/`, inventory kamera/format, status/path layanan, serta `jetson-synthetic-summary.json` dan log/frame metadata per kasus. Kredensial tidak disimpan dalam helper yang dipertahankan; helper replay meminta password interaktif.

## Batas

Pengulangan memakai fixture/seed yang sama. Belum ada validasi hardware payload/pickup, hidrofon, driver kamera nyata atau kalibrasi kendaraan. Kegagalan shutdown awal tidak dihapus dan tidak dihitung lulus.

Ringkasan assert bukti/hash, kesamaan source dengan laporan 50, penolakan shutdown awal dan coverage observer melalui STOPPED: [verification.json](../ros2_ws/evidence/pinger-shm-20261104/verification.json). Hasil akhir [observer-close-first/summary.json](../ros2_ws/evidence/pinger-shm-20261104/observer-close-first/summary.json), transport [Jetson sintetis](../ros2_ws/evidence/pinger-shm-20261104/jetson-synthetic-summary.json).
