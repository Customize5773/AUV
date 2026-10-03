# Riset teknis dan eksperimen lanjutan

Bagian sumber di bawah adalah temuan publik. Agenda eksperimen adalah **usulan internal**, bukan persyaratan SAUVC 2027.

| Bidang | Bukti/sumber | Pertanyaan yang perlu dijawab tim |
| --- | --- | --- |
| Persepsi | [Catatan UWU](https://aryanaut.github.io/blog/uwu/) membahas kesulitan rentang warna yang ditetapkan tetap | Apakah detektor tetap bekerja ketika white balance, cahaya, sudut, dan latar kolam berubah? |
| Odometri visual | [Eksperimen DSO AUV Society](https://github.com/auvsociety/sauvc-simulations/blob/master/docs/Using-DSO.md) mencatat gangguan objek dinamis, cahaya dasar kolam, lintasan tidak stabil, dan persoalan sumbu; tim saat itu memilih melanjutkan tanpa SLAM | Apakah estimasi posisi meningkatkan keberhasilan dibanding kontrol kedalaman/heading dengan koreksi visual sederhana? |
| Simulasi fisik | [Dokumentasi resmi Gazebo Sim 8](https://gazebosim.org/api/sim/8/underwater_vehicles.html) menjelaskan buoyancy, thruster, dan hydrodynamics, termasuk damping serta added mass | Parameter mana yang diukur dari robot nyata dan mana yang hanya perkiraan? |
| Buoyancy | [Mahbub & Shaharear, 2025](https://arxiv.org/abs/2509.03804) mengusulkan perhitungan volume terendam berbasis convex hull dan evaluasi pada rancangan AUV SAUVC 2025 | Apakah pemodelan buoyancy dinamis membantu skenario launch/surfacing kita? |
| Akustik | [Manual produsen RJE ULB-362](https://www.rjeint.com/wp-content/uploads/2017/01/ULB-362-ULB-362PL-Manual.pdf), tabel spesifikasi halaman PDF 8, memuat varian 27/37,5/45 kHz dan durasi pulsa ≥9 ms | Apakah hydrophone, analog front-end, dan akuisisi data kompatibel dengan sinyal panitia nanti? |
| Kendali | [NYCU](https://github.com/BenTzuHsien/nycu-auv-control) mendokumentasikan kendali tertanam terpisah dari komputer tingkat tinggi | Apakah loop kedalaman dan heading tetap stabil saat detektor melambat atau komputer misi gagal? |

Artikel buoyancy tersebut adalah publikasi riset dengan abstrak dan metadata yang diperiksa; angka kinerja rinci belum direproduksi. Pernyataan abstrak tentang keterbatasan Isaac Sim berlaku pada konteks penelitian penulis, bukan verifikasi terhadap semua versi produk saat ini.

**Usulan eksperimen minimum:**

1. **Kendali:** ukur respons kedalaman, heading, dan manuver balik. Simpan error, overshoot, waktu stabil, tegangan baterai, serta konfigurasi thruster.
2. **Persepsi:** rekam dataset di beberapa sesi kolam. Pisahkan train/test berdasarkan sesi, agar frame berdekatan tidak memberikan hasil evaluasi terlalu optimistis.
3. **Misi:** uji transisi saat target hilang, gerbang baru terlewati sebagian, aktuator gagal, dan waktu pencarian habis. Definisikan bukti selesai tiap tugas.
4. **Akustik:** uji deteksi sinyal dahulu, kemudian estimasi arah. Bandingkan thruster mati/hidup dan beberapa posisi kolam; jangan menilai dari satu posisi terbaik.
5. **Komunikasi:** ukur keberhasilan penerimaan pesan, latensi, pengulangan, dan penolakan pesan rusak. Pisahkan eksperimen komunikasi dari lokalisasi pinger.
6. **Manipulasi:** uji pelepasan dan pengambilan saat robot tidak tepat di pusat target. Rekam jumlah percobaan berhasil, bukan hanya video terbaik.
7. **Simulasi:** variasikan gaya apung, drag, noise, latensi, dan lokasi properti; gunakan hasil untuk mencari kegagalan sebelum uji kolam.

Belum ada alasan berbasis data tim untuk menetapkan merek komputer, kamera, autopilot, hydrophone, atau jumlah thruster. Pilihan tersebut memerlukan inventaris, target misi, anggaran, dan hasil uji.
