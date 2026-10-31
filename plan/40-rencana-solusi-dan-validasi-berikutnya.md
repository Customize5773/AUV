# 40 — Rencana solusi dan validasi berikutnya

1 November 2026, Asia/Jakarta. **Status: implementasi telah dikonfirmasi pengguna; tahap audit/migrasi dicatat pada laporan 41.** Disusun dari laporan 35–39, bukti benchmark yang tersimpan, paket ROS terpasang, dan sumber primer di bawah. Penyusunan awal rencana dilakukan tanpa menjalankan simulasi atau mengubah controller/configuration. Pelaksanaan berikutnya dicatat pada laporan tahap terkait.

Tujuan bersama: AUV nyata yang autonomous, patuh rulebook dan tercepat. Simulasi dipakai untuk mengembangkan dan membuktikan perilaku sebelum uji kolam. Ukuran kemajuan: pelintasan/tugas sah, waktu, tingkat keberhasilan dan kesiapan hardware. Hold panjang adalah alat diagnosis, bukan sasaran lomba.

## Fakta yang sudah diketahui

- Rulebook resmi yang diperiksa kembali menyatakan **2027.3.2**, diperbarui 30 Oktober 2026. Fixture/metadata simulator masih **2027.2.1**. Baru bagian kualifikasi yang dibandingkan pada laporan 39; migrasi menyeluruh belum terbukti.
- U-turn kandidat 0,7 rad/s sudah diterima pada tiga pasangan fixture: sekitar 6,5 → 4,8 s. Waktu pelintasan kedua kandidat 22,748–22,848 s; start–surface 25,838–25,942 s. Hanya satu run per profil/kondisi, arus nol dan cahaya normal. Angka ini bukan statistik keandalan.
- Riwayat fase kandidat: DIVE sekitar 2,95–3,00 s; ALIGN 8,85–8,90 s; PASS_OUT 2,85–2,95 s; CLEAR_GATE sekitar 0,75 s; TURN 4,80 s; PASS_BACK 2,70–2,80 s; SURFACE sampai STOP 5,20–5,85 s. ALIGN mencakup perjalanan mendekati gate, bukan seluruhnya waktu diam. Waktu surface pertama pada referee berbeda dari akhir fase SURFACE controller.
- Pada kegagalan historis, beberapa aliran memiliki lompatan timestamp simulasi sekitar 4,9–5,8 s. Data tersebut belum menentukan penyebabnya. Dua pengulangan bersih dan uji bridge terkontrol membuktikan respons guard, bukan menghilangkan penyebab spontan.
- Batas stale estimator 0,3 s dan watchdog aktuator 0,5 s. Pertahankan selama eksperimen. Kendaraan harus berhenti pada kehilangan data yang benar-benar melewati batas.
- Paket lokal `ros-humble-ros-gz-bridge` adalah 0.244.26; header `BridgeConfig` yang diperiksa memiliki queue size/lazy/direction dan belum memuat profil QoS. Dokumentasi versi baru tidak boleh langsung dijadikan konfigurasi untuk binary ini.

## Urutan kerja yang direkomendasikan

### 1. Bekukan acuan aturan dan buat matriks perubahan

Ambil snapshot versi 2027.3.2 dari sumber resmi beserta tanggal/hash. Bandingkan dengan arsip 2027.2.1, lalu petakan setiap perubahan: aturan, geometri, referee/skor, persepsi, controller, serta dokumentasi. Tandai bagian yang sama agar tidak ditulis ulang tanpa alasan.

Implementasi nantinya hanya mengubah bagian yang terkena dampak. Metadata versi diperbarui setelah audit dan penerimaan yang relevan selesai. Bukti lama tetap bertanda versi asal. Jika ada geometri yang tidak ditentukan secara pasti oleh aturan, pertahankan label asumsi latihan.

**Keluaran:** snapshot/diff, tabel aturan → file → pengujian, serta daftar penerimaan yang wajib diulang. Tidak menyebut seluruh simulator sudah 2027.3.2 hanya dengan mengganti string versi.

### 2. Tentukan lokasi jeda sebelum memilih perbaikan stale_sensors

Tambahkan observasi paling kecil yang masih membedakan rantai berikut:

`produksi sensor Gazebo → transport Gazebo → bridge → penerimaan ROS → estimator → guard`

Gunakan observer transport Gazebo dan ROS yang independen, dicocokkan melalui timestamp simulasi/nomor urut. Simpan umur paket pada estimator, waktu penerimaan, CPU/RSS/pressure host, serta waktu simulasi dibanding wall-clock. Bila perlu menambahkan timestamp diagnostik produsen atau durasi publish, letakkan pada telemetry evaluasi; jangan memasukkan informasi simulator ke input navigasi. Pastikan basis jam antarpencatat cocok sebelum menghitung latensi lintas proses.

Matriks awal dibatasi: masing-masing tiga misi kualifikasi dengan GUI/POV mati, lalu tiga dengan Gazebo + dua POV. Gunakan seed/layout yang sama, jalankan serial, simpan semua percobaan. Ini uji pengaruh beban, bukan pembuktian statistik lengkap. Jika salah satu gagal, analisis lokasinya sebelum mengulang banyak run. Jika tidak terulang, laporkan belum terulang dan gunakan pencatatan tersebut pada benchmark berikutnya; jangan terus mengulang hold tanpa batas.

| Bukti yang ditemukan | Hipotesis yang diuji | Solusi kandidat |
|---|---|---|
| Produksi/tick Gazebo ikut berhenti, pressure host naik | Beban rendering atau penjadwalan simulator | Uji konfigurasi rendering/headless dan laju kamera yang masih memenuhi deteksi; pisahkan hasil dengan GUI dari benchmark headless |
| Data native terus ada, penerimaan ROS terlambat | Kemacetan bridge/DDS | Pisahkan kamera ke proses bridge sendiri; bandingkan dengan bridge tunggal pada input/beban sama |
| ROS observer lancar, estimator tertinggal | Callback mahal atau antrean estimator | Profilkan callback; gunakan observasi kamera terbaru dan batasi kerja mahal setelah bukti menunjuk jalur tersebut |
| Pencatat tertinggal, estimator tetap menerima paket segar | Beban observer | Ringankan pencatat; jangan menyebutnya kehilangan sensor pada pengendali |

**Batas kesimpulan:** satu interupsi bridge yang disengaja hanya memvalidasi signature dan fail-safe. Itu tidak menetapkan bridge sebagai penyebab kejadian lama.

### 3. Pilih solusi transport berdasarkan hasil tahap 2

Pilihan pertama bila kemacetan gambar terbukti: **pisahkan bridge kamera dari bridge sensor/clock/command**. Ini eksperimen isolasi proses dengan binary yang terpasang, sehingga dapat dibandingkan tanpa upgrade ROS. Pastikan tidak ada topic yang dijembatani dua kali atau publisher clock ganda.

Pilihan berikutnya bila diperlukan: antrean gambar lebih kecil dan QoS yang mengutamakan frame terbaru. Verifikasi dukungan paket lokal dan kompatibilitas seluruh publisher/subscriber terlebih dahulu. Header lokal saja belum membuktikan semua mekanisme override tersedia/tidak tersedia; cek implementasi/parameter sebelum menentukan cara konfigurasi.

Pilihan asynchronous publishing atau perubahan RMW hanya dipertimbangkan bila identitas middleware, mode aktual dan bukti blocking sudah diketahui. Dokumentasi Fast DDS menjelaskan bahwa write RELIABLE dapat memblokir ketika resource/history penuh; itu mendukung hipotesis, bukan membuktikan penyebab di laptop ini. Jangan mengganti seluruh stream menjadi best effort, meng-upgrade stack, atau mengubah banyak parameter sekaligus untuk percobaan pertama.

**Syarat penerimaan perbaikan:** misi/tugas tetap sah; tidak ada abort spontan dalam matriks yang ditetapkan; latensi dan umur paket membaik pada kasus yang direproduksi; kehilangan data disengaja masih memicu stop/gaya nol pada batas lama; shutdown bersih. Jika masalah historis tidak direproduksi, sebut hasil sebagai mitigasi/isolasi teruji, bukan akar masalah yang sudah selesai.

### 4. Buktikan konsistensi profil U-turn cepat

Gunakan profil 0,7 rad/s sebagai kandidat yang sudah ada. Setelah acuan rulebook terkunci, lakukan lima run per jalur (15 run total), dengan variasi seed yang ditetapkan sebelum pengujian. Tambahkan tiga kasus arus/prior yang dipilih dari fixture historis, bukan kombinasi acak tanpa batas.

Catat pelintasan kedua, surface pertama, stop, persiapan sebelum thrust, waktu tiap fase, kontak, galat estimasi, umur paket dan saturasi thruster. Sajikan semua run; bandingkan median/rentang dan keberhasilan. Jangan menghitung p95 sebagai bukti tail latency yang andal dari hanya lima sampel per jalur.

**Gerbang penerimaan batch:** seluruh run yang dipersyaratkan lulus pelintasan penuh dua kali, tanpa kontak terlarang/surface dini; kalibrasi siap sebelum thrust; batas akurasi lama lulus; stop/gaya nol dan shutdown lulus. Satu kegagalan berarti batch belum diterima; investigasi atau rollback kandidat terkait sebelum mempercepat lagi. Angka 100% pada batch tetap tidak berarti andal pada semua kondisi kolam.

### 5. Optimasi satu fase berikutnya

Setelah tahap 1 dan penerimaan dasar, kandidat paling kecil untuk ditelaah adalah **profil vertikal DIVE/SURFACE**, karena permintaan heave saat ini 0,2 m/s sedangkan clamp model mencapai 0,3 m/s. Itu headroom model, belum kemampuan hardware terukur.

Uji satu perubahan per eksperimen: DIVE terlebih dahulu, kemudian SURFACE bila bukti mendukung. Jangan langsung menaikkan keduanya. Periksa overshoot kedalaman, clearance dasar/gate, settling permukaan, waktu stop dan alokasi gaya tujuh thruster. Target performa berasal dari baseline fase dan jarak/akselerasi yang diukur, bukan janji detik tanpa percobaan.

ALIGN yang panjang perlu dianalisis sebagai jarak tempuh, sudut dan kecepatan aktual. Jangan menaikkan gain alignment hanya karena nama fase ini dominan; gain yang terlalu besar berisiko osilasi. Batas kecepatan/thrust/massa/drag tidak diubah untuk sekadar menghasilkan skor waktu lebih baik.

Bandingkan baseline dan kandidat pada kondisi yang sama, dengan hash source dan semua upaya disimpan. Pertahankan perubahan hanya bila waktu membaik dan seluruh kriteria misi lulus. Uji ulang komponen/fault yang jalurnya terkena perubahan; hindari mengulang seluruh suite panjang tanpa alasan baru.

## Keluaran akhir implementasi nanti

- Laporan migrasi aturan beserta batas asumsi fixture.
- Bukti lokasi jeda sensor atau status belum direproduksi yang jujur, dengan kandidat mitigasi yang sudah diuji.
- Profil kualifikasi terpilih dengan tabel waktu, tingkat keberhasilan batch dan batas pengujian.
- `verification.json`, manifest source/kondisi/perintah, log gagal dan log diterima.
- README/CARA-RUNNING/Graphify diperbarui mengikuti perubahan yang benar-benar diterima.

Hardware menjadi tahap berikutnya: kalibrasi PWM–thrust, geometri/mixer tujuh thruster, sensor nyata dan uji kolam. Penentuan servo/catu daya/driver tetap menunggu informasi yang sebelumnya belum dikonfirmasi. Rencana ini tidak mengaktifkan output hardware.

## Sumber dan bukti

- [Rulebook resmi](https://sauvc.org/rulebook/), diperiksa 1 November 2026: versi 2027.3.2, pembaruan 30 Oktober.
- [Dokumentasi ros_gz_bridge cabang Humble](https://github.com/gazebosim/ros_gz/blob/humble/ros_gz_bridge/README.md), dibandingkan dengan header/paket lokal; fitur cabang lain tidak otomatis tersedia.
- [Fast DDS: publishing data dan blocking write](https://fast-dds.docs.eprosima.com/en/2.14.x/fastdds/dds_layer/publisher/dataWriter/publishingData.html). Perilaku generik ini belum menetapkan RMW/mode/penyebab aktual di repo.
- [Investigasi stale](36-investigasi-stale-sensors.md), [fault setelah gerak](38-fault-runtime-setelah-gerak.md), [benchmark U-turn](39-benchmark-dan-percepatan-uturn.md).

**Pelaksanaan:** pengguna mengonfirmasi untuk melanjutkan. Tahap pertama berlangsung pada [laporan 41](41-audit-dan-migrasi-rulebook-2027-3-2.md); tahap berikutnya mengikuti urutan dan gerbang penerimaan di atas.

Pembaruan pelaksanaan: audit/migrasi selesai pada laporan 41. [Diagnosis lokasi dan matriks nominal/GUI](42-diagnosis-lokasi-stale-sensors.md) selesai pada laporan 42; kejadian lama tidak dapat dilokalisasi secara unik dari arsipnya dan tidak terulang pada matriks baru. Solusi bridge/QoS tahap 3 tetap bersyarat bukti; tidak diterapkan berdasarkan dugaan. Batch konsistensi dan optimasi vertikal tetap tahap berikutnya.
