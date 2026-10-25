# Konsep pelepas payload satu bola dengan servo

Status: rancangan awal, belum difabrikasi atau diuji. Model parametrik: [dropper.scad](dropper.scad). Unit mm. Tidak ada PWM atau output hardware yang diaktifkan oleh pekerjaan simulator.

Bola ditahan rak putar di bawah tabung vertikal. Servo memutar rak menjauh sehingga bola turun melalui gravitasi. Sumbu putar sejajar tabung, berjarak 40 mm dari pusat bola. Dudukan terpisah menanggung berat rak/bola melalui bearing; poros servo hanya memberikan torsi. Bola tidak didorong servo dan tidak boleh dijepit linkage.

| Komponen | Dimensi konsep |
| --- | --- |
| Bola | 35–45 mm, massa maksimum 200 g menurut rulebook; simulator 40 mm/100 g |
| Tabung | ID 48 mm, OD 54 mm, tinggi 58 mm |
| Rak putar | 62×62×3 mm dengan lengan ke pivot |
| Bukaan | 48 mm, tanpa baut/linkage menjorok ke jalur bola |
| Sudut rak | 0° tertutup; sekitar 120° terbuka, perlu uji envelope aktual |
| Telinga pemasangan | Dua lubang 4,5 mm; bracket AUV dan bracket servo diukur terpisah |

Di OpenSCAD, `open_angle=0` untuk posisi tertutup atau `120` untuk terbuka. Render tabung dan rak sebagai bagian terpisah sebelum mengekspor STL; model gabungan ini untuk pemeriksaan susunan, bukan satu benda cetak. Bearing, stopper, spline horn dan bracket servo belum dimodelkan karena dimensinya mengikuti perangkat yang dipilih. Periksa lintasan sapuan rak terhadap thruster, kamera, kabel dan badan. Sisakan ruang di bawah bola; tabung tidak boleh menutup lensa bawah.

Penentuan servo mengikuti pengukuran torsi rak basah. Perkiraan awal: massa 0,2 kg, normal 1,96 N, koefisien gesek asumsi 0,3 dan lengan 0,04 m memberi torsi gesek sekitar 0,024 Nm (0,24 kgf·cm), sebelum bearing, pegas dan kontaminasi. Ini bukan rating servo akhir. Ukur gaya pembukaan saat terendam lalu pilih margin torsi dan arus sesuai hasil. Rating waterproof servo, kedalaman, konektor, korosi, tegangan serta arus stall harus cocok dengan lingkungan dan BEC yang dipakai. Jangan menyuplai servo dari pin logika Jetson.

Kontrol: sumber daya servo terpisah dengan common ground sesuai antarmuka, fuse/current limit, stopper mekanis dan kondisi boot tertutup. Tentukan pin/PWM setelah mengetahui flight controller/driver serta kanal yang benar-benar kosong. Kanal gripper atau thruster yang sudah terpakai tidak boleh dialihkan. Posisi 0°/120° CAD tidak sama dengan angka PWM universal. Kalibrasi endpoint tanpa bola terlebih dahulu agar servo tidak stall.

Interlock yang diperlukan saat implementasi hardware: release hanya saat armed untuk misi dan alignment stabil; satu release per attempt; sensor posisi tertutup/terbuka atau feedback aktuator untuk mendeteksi macet. Perintah release hanya membuktikan permintaan, bukan bola telah keluar atau masuk drum. Tambahkan sensor bola/rekaman kamera untuk pembuktian. Servo biasa tidak otomatis kembali tertutup saat listrik mati; bila wajib fail-closed, gunakan latch berpegas dengan geometri yang telah diuji, jangan mengandalkan firmware saja.

Uji meja: periksa bola 35/40/45 mm; kalibrasi endpoint tanpa beban; lakukan minimal 30 siklus basah per ukuran; ukur arus, waktu release, retensi saat miring dan kecenderungan macet. Uji mati daya, reboot, perintah berulang dan alignment salah tanpa menghubungkan thruster. Lanjutkan uji kolam dengan kamera bawah dan drum setelah retensi/release konsisten. Sebelum dipasang ke AUV, ukur ulang titik pusat bola terhadap badan; simulator memakai offset (+0,20, 0, −0,18) m dan harus disesuaikan dengan pemasangan nyata.

Mekanisme flare merupakan properti penyelenggara: AUV menabrak/mendekati flare sehingga bola terlepas. Servo ini untuk payload kendaraan, bukan untuk mengendalikan pelepasan bola flare penyelenggara.
