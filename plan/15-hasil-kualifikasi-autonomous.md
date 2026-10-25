# Implementasi kualifikasi autonomous SAUVC

Tanggal: **25 Oktober 2026, Asia/Jakarta**. Pengguna menyetujui implementasi kualifikasi terlebih dahulu. **Status: validasi akhir sedang berjalan.**

## Acuan dan cakupan

[Rulebook terbit](https://sauvc.org/rulebook/) diperiksa ulang: **2026 v6.1.0**. [Usulan 2027 PR #25](https://github.com/sauvc/rulebook/pull/25) masih terbuka pada pemeriksaan sesi ini. Implementasi menggunakan dua jalur dan geometri 2026 yang sudah tersedia, tidak menyatakan kesesuaian terhadap geometri usulan 2027.

Alur: **menyelam -> melintas gate dengan seluruh badan -> menjauh secukupnya -> U-turn -> melintas gate kembali dengan seluruh badan -> langsung surface vertikal -> berhenti otomatis**. Waktu lintasan berhenti pada pelintasan balik lengkap. Surface berikutnya adalah penutup simulasi sesuai permintaan pengguna, bukan syarat tambahan poin kualifikasi.

## Implementasi

- `qualification.py`: FSM dengan umpan balik kedalaman/heading, deadline, pencarian gate terbatas, fase melintas dan urutan surface/stop terminal.
- `gate_detection.py`: deteksi pasangan tiang oranye pada frame kamera sebenarnya menggunakan NumPy, termasuk sisi balik yang lebih gelap; tidak memakai posisi gate ground truth sebagai pengganti citra.
- `referee.py`: pemeriksa independen untuk seluruh envelope termasuk bagian menonjol dan orientasi 3D, bukaan gerbang yang dipilih, U-turn, kontak, batas kolam, permukaan, serta penghentian aktual.
- `runtime.py`: adapter ROS untuk controller, pemeriksa dan pengawas perintah dalam proses berbeda; controller tidak menulis langsung ke Gazebo saat autonomous.
- `contact_monitor.cc`: membaca kontak fisika hull dan menerbitkan heartbeat kosong agar tidak adanya benturan dapat dibedakan dari sumber kontak yang tidak aktif.
- Launch manual tetap tersedia; `autonomous:=true` mengaktifkan kualifikasi. Mode `vision` menjadi default, `odom` adalah pembanding yang diberi label terpisah.

Odometri tetap ground truth untuk kedalaman, heading dan gerakan pendek ketika gate terlalu dekat untuk terlihat lengkap. Pada mode visual, estimasi bidang gate untuk fase tersebut berasal dari range/bearing citra terakhir. Pemeriksa boleh memakai geometri world yang diketahui dan tidak mempercayai klaim keberhasilan controller.

## Validasi

Hasil akhir, jumlah ulangan dan lokasi bukti diisi sesudah seluruh pemeriksaan selesai. Bukti sesi ini disimpan di [`ros2_ws/evidence/qualification-autonomous/`](../ros2_ws/evidence/qualification-autonomous/), terpisah dari bukti simulator dasar 22 Oktober. Hasil `passed` pada skenario gangguan berarti penghentian aman lulus; `mission_passed` tetap false.

## Perbaikan dari pengujian

U-turn pertama terlalu dekat sehingga kedua tiang tidak kembali masuk bidang pandang; kendaraan kini menjauh 1,8 m dari titik pelintasan keluar sebelum berputar. Ambang kecerahan awal tidak mengenali sisi balik gate yang berada dalam bayangan; perbandingan warna kini menerima sisi tersebut. Keduanya diberi pemeriksaan terarah, dan mode visual diuji ulang penuh.

Saat beberapa renderer dijalankan bersamaan, startup dapat membuat clock macet sebelum kendaraan bergerak. Pengawas menghentikan percobaan tersebut; misi kini menunggu clock maju sebelum mengaktifkan gerak. Ini tidak melonggarkan timeout saat lintasan berlangsung.

Proses GUI dan server dipisahkan di launch agar lifecycle dimiliki ROS launch, menghindari jalur fork Ruby yang sebelumnya menghasilkan `Errno::ESRCH`. Hasil shutdown diuji terpisah dari keberhasilan lintasan.

Pada host Ubuntu 24.04 dengan Fortress berbasis 22.04, header Protobuf 3.12 disiapkan di workspace lokal untuk membangun plugin terhadap ABI terpasang; tidak mengganti paket sistem. Perintah persiapan dan menjalankan tersedia dalam [README workspace](../ros2_ws/README.md).

## Batas hasil

Model masih kotak dengan kecepatan ideal; tidak ada thruster, hidrodinamika, ArduSub atau kendali hardware. Pengujian ini tidak membuktikan performa kendaraan fisik. Misi ARENA, bola flare, payload drum, pinger dan Target Reacquisition belum diimplementasikan.
