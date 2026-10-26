# 25 — POV kamera dan pengaman stale_front

26 Oktober 2026. Keluhan: ARENA masuk `TO_SQUARE`, kemudian guard memutus misi dengan `stale_front`.

Guard berhenti karena tidak menerima hasil kamera depan yang valid dengan timestamp baru selama lebih dari 2 detik wall clock. Baris keluarnya proses GUI Gazebo pada log terjadi setelah abort; menutup GUI memang menutup seluruh launch karena GUI merupakan proses wajib. Itu bukan bukti penyebab kamera sebelumnya macet.

## Perbaikan

- Callback persepsi sebelumnya membuat/mengirim gambar anotasi setiap input kamera ketika viewer aktif. Kini POV dibatasi maksimal 5 FPS wall clock; deteksi/tracking dan JSON tetap diproses untuk setiap frame input.
- Antrean raw/annotated image memakai BEST_EFFORT depth 1 sehingga frame lama diganti frame terbaru ketika desktop sibuk. Antrean JSON persepsi dan konsumen controller/guard juga depth 1, dengan reliabilitas tetap.
- Buffer gambar ROS memakai `array('B')`. Frame anotasi mempertahankan stamp/frame ID sumber.
- Jika guard benar-benar menerima kamera stale, log tambahan menyebut jeda sejak frame valid terakhir dan selisih timestamp gambar terhadap waktu simulasi.
- Batas kamera 2 detik, stop/abort terminal, dan larangan memperpanjang freshness dengan timestamp duplikat tetap berlaku.

Ini mitigasi beban dan antrean yang dapat diperbaiki di kode. Penyebab tunggal stall pada run pengguna belum terbukti. Pada run pembanding, error tidak terulang; detektor sekitar 10–30 ms, sedangkan interval frame depan sempat sekitar 0,7 detik. Beban rendering/penjadwalan masih dapat menghentikan kamera sungguhan dan harus tetap memicu stop aman.

## Validasi

Build lulus. 98 tes unit lulus, termasuk deteksi tetap menerima tiga frame ketika POV hanya mengirim dua, timestamp anotasi tetap benar, serta kehilangan kamera masih menghapus deteksi.

Bukti lokal: [`evidence/camera-viewers/`](../ros2_ws/evidence/camera-viewers/). Run pembanding `reproduce.json` memakai Gazebo GUI dan kedua rqt POV aktif, selesai Navigation → flare → blue drum → Square → surface → stop, dan shutdown bersih. Ini tidak membuktikan stall intermiten sudah hilang pada semua kondisi laptop.

Run setelah perbaikan (`acceptance.json`) lulus sampai Square +20 → surface → stop, shutdown bersih. Kedua viewer sempat ditutup lalu dibuka kembali sebelum tahap Square; endpoint masing-masing tersimpan pada `front-viewer-endpoint.txt` dan `bottom-viewer-endpoint.txt`. Klaim kedua viewer aktif dibatasi pada tahap menuju Square, bukan seluruh durasi misi.

Injeksi nyata `SIGSTOP` pada proses persepsi (`actual-camera-loss.json`) menghentikan kedua kamera sekaligus. Controller lebih dahulu abort karena `stale_bottom` dalam 1,879 detik; perintah nol, kendaraan stationary, dan shutdown bersih. Guard tidak menjadi pemicu pertama pada uji ini. Runner bawaan `camera-loss.json` tetap mencatat `passed=false/fault_verified=false` karena fixture itu mengharapkan front loss, sedangkan injeksi ini memutus kedua kamera dan bottom stale lebih dahulu. Bukti penghentian nyata dievaluasi terpisah, tidak mengganti label runner menjadi lulus. Uji software front-loss sebelumnya ada pada `software-camera-loss.json`.

[verification.json](../ros2_ws/evidence/camera-viewers/verification.json) merangkum bukti dan batasnya. Error intermiten asli belum berhasil direproduksi; perbaikan mengurangi sumber beban/antrean, bukan jaminan kamera tidak akan pernah macet. Jika terulang, log baru membedakan wall gap dan image timestamp lag tanpa melonggarkan batas penghentian.
