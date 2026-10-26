# Tahapan pekerjaan Program

Ini usulan urutan kerja berdasarkan kondisi awal, bukan jadwal resmi. Durasi ditentukan setelah akses hardware dan waktu kerja mingguan diketahui. Untuk satu pengembang utama, selesaikan satu integrasi sampai dapat diulang sebelum memperluas lingkup.

| Tahap | Pekerjaan Program | Ketergantungan | Bukti selesai yang diusulkan |
| --- | --- | --- | --- |
| P0 — Inventaris | Identifikasi perangkat, firmware, port, lingkungan kerja, dan konfigurasi awal | Akses perangkat/label spesifikasi | Catatan inventaris dan cara pemulihan konfigurasi tersedia |
| P1 — Jetson dan BlueOS | Pilih lingkungan sesuai model, uji instalasi BlueOS, akses antarmuka, restart, dan penyimpanan konfigurasi | P0; daya dan jaringan meja | Langkah instalasi tercatat; layanan yang diperlukan kembali berjalan setelah reboot |
| P2 — Pixhawk | Hubungkan autopilot, baca telemetri, petakan aliran data dan kendali, catat perilaku putus sambungan | P1; model/firmware diketahui | Status autopilot terbaca; data direkam; putus/sambung terdeteksi tanpa perintah tak disengaja |
| P3 — Kamera | Identifikasi tiga unit, uji satu per satu, tambah dua/tiga kamera, lalu akses frame dari program | Jetson dan kamera; dapat diuji sebagian sebelum BlueOS selesai | Rekaman tiap kamera jelas asalnya; identitas konsisten; hasil uji beban tersedia |
| P4 — Gerak dasar | Validasi pemetaan thruster, kendali manual untuk pengujian, sensor dan kendali kedalaman/arah | Thruster, ESC, sensor, daya, mekanik dan tempat uji siap | Gerak sesuai perintah, respons terukur, prosedur penghentian diuji bersama tim |
| P5 — Navigasi | Buat deteksi gerbang dan urutan misi dengan batas waktu/pemulihan | P3, P4; properti dan kolam | Percobaan navigasi berulang dengan log keberhasilan/kegagalan |
| P6 — Tugas tambahan | Pilih tugas berdasarkan kesiapan mekanisme dan data pengujian; usulan awal: penjatuhan bola | Navigasi andal; mekanisme dan kamera yang sesuai | Satu tugas tambahan selesai sebagai bagian alur misi |
| P7 — Integrasi lomba | Latihan launch, misi tanpa kendali operator, recovery, pencatatan, dan persiapan demonstrasi | Aturan edisi berlaku; seluruh subsistem terkait | Konfigurasi yang dapat dipulihkan dan bukti percobaan menyeluruh |

## Jobdesk yang perlu tercakup

| Bidang | Hasil pekerjaan |
| --- | --- |
| Platform | Instalasi yang terdokumentasi, daftar versi, startup layanan, backup konfigurasi |
| Komunikasi | Peta sambungan Jetson–Pixhawk, pembacaan status, jalur perintah, penanganan kehilangan koneksi |
| Kamera | Konfigurasi per unit, kalibrasi sesuai pemasangan, perekaman, distribusi frame ke pemrosesan |
| Persepsi | Dataset lokal, evaluasi deteksi, confidence dan kondisi kegagalan |
| Kendali/misi | Transisi yang jelas, timeout, bukti selesai tugas, serta respons saat sensor/target hilang |
| Pengujian | Catatan setiap percobaan, versi kode/config, video, penyebab kegagalan, dan tindak lanjut |

**Batas integrasi dengan tim lain:** Program membutuhkan diagram daya dan sambungan, posisi/arah thruster, pemasangan kamera, serta mekanisme penghentian fisik dari pekerjaan elektrikal/mekanik. Simulasi atau perintah perangkat lunak tidak menggantikan verifikasi fisik tersebut.

## Fokus sesi pertama

- Lengkapi P0 tanpa terlebih dahulu mengganti OS atau firmware yang belum diidentifikasi.
- Periksa satu kamera secara mandiri untuk mengetahui format dan jalur aksesnya.
- Catat kondisi awal dan kendala yang nyata; dari situ pilih eksperimen P1/P2 berikutnya.

Jika adaptasi BlueOS tersendat, catat layanan yang gagal dan penyebabnya. Eksperimen kamera/persepsi dapat diteruskan secara terpisah sambil menilai perbaikan platform. Pemilihan platform tetap mengikuti arah pengguna; perubahan arah perlu dibahas berdasarkan hasil pengujian.

Format log sederhana: `tanggal, tahap, perangkat, versi, konfigurasi, tujuan, hasil, bukti, kendala, langkah_berikutnya`.
