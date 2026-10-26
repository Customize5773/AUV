# Pembaruan rulebook SAUVC 2027 dan dampak simulator

> Pembaruan implementasi: profil default sudah dimigrasikan ke 2027; lihat [laporan 24](24-migrasi-dan-uji-arena-2027.md). Status belum migrasi di bawah adalah snapshot saat audit awal.

Pemeriksaan: **26 Oktober 2026, Asia/Jakarta**. Lingkup pekerjaan ini adalah memverifikasi pembaruan, mengarsipkan sumber dan menilai dampaknya. **Kode, geometri dan hasil penerimaan simulator belum dimigrasikan ke 2027.**

## Publikasi sudah berubah

[Halaman resmi](https://sauvc.org/rulebook/) sekarang menampilkan **SAUVC 2027, versi 2027.2.1**, diperbarui 26 Oktober 2026. Source [commit dd6a05c](https://github.com/sauvc/rulebook/blob/dd6a05cbf147212ddd14c4994b746a45b0bf91fd/rulebook.md) cocok dengan metadata tersebut. API GitHub menyatakan PR #25 merged pada **26 Oktober 2026 09:36:26 WIB**. Jadi pernyataan pemeriksaan 25 Oktober bahwa edisi publik masih 2026/PR masih terbuka adalah snapshot historis dan tidak berlaku sebagai status sekarang.

Sumber halaman, teks, source dengan commit tetap, metadata API, diff terhadap baseline 2026/usulan 2027.1.1 dan gambar tersedia dalam [arsip terbit 2027](../doc/sources/rulebook-2027-published/README.md). Diagram pengguna cocok dengan diagram resmi. Ketiga gambar yang diarsipkan identik dengan gambar usulan sebelumnya; pembaruan ini merupakan publikasi aturan 2027 yang sudah direvisi, bukan bukti bahwa gambarnya baru dibuat hari ini.

## Perubahan terhadap baseline simulator 2026

| Bagian | Baseline 2026 / simulator | Publikasi 2027.2.1 | Dampak |
| --- | --- | --- | --- |
| Kolam | 25 × 16 m, profil dasar latihan dangkal simetris | 50 × 25 m; diagram memberi kedalaman 1,28 m dan 2 m dengan profil berbeda | Bangun ulang dasar, dinding, zona dan batas referee; jangan sekadar menggandakan ukuran |
| Layout | Starting zone di ujung panjang; gate pada bidang X tetap | Starting zone utama di sisi panjang; tiga jalur kualifikasi di sisi arena pada gambar | Ubah spawn, arah start, rute pencarian dan orientasi properti |
| Gate kualifikasi | Sekitar 10 m dari start, lebar 1,5 m, dari dasar sampai permukaan | Sekitar 10 m; lebar 1,5 m dan kedalaman tiang sekitar 1 m menggantung dari permukaan | Bukaan valid tidak boleh dianggap sama dengan seluruh kedalaman kolam; tiga jalur perlu fixture/pemeriksaan |
| Gate utama | Sekitar 16 m dari starting zone; bukaan 1,5 × 1 m | Sekitar 12 m; bukaan 1,5 × 1,5 m | Revisi pendekatan, proyeksi kamera, envelope dan pemeriksa pelintasan |
| Orange flare | Diameter sekitar 15 cm, dari dasar sampai permukaan | Tinggi 1,5 m, diameter sekitar 15 cm | Revisi obstacle; kontak tetap immediate abort |
| Target zone | Drum dekat ujung; mat hijau dapat tidak tersedia | Mat hijau 8 × 2 m mendefinisikan target zone; seluruh drum berada di atasnya | Modelkan batas zona yang eksplisit, bukan hanya koordinat drum |
| Reacquisition | Harus melintasi gate lagi setelah acquisition | Harus keluar target zone setelah acquisition; seluruh bagian AUV harus keluar, kemudian kembali mengambil bola yang sama dan membawanya sampai akhir | Ganti syarat referee/ledger serta state controller; perjalanan ke gate bukan lagi syarat |
| Surface | Bonus normal 5 | Bonus normal 5; tambahan 20 jika sudah Navigation dan surface di Surfacing Square tanpa kontak | Tambah properti, persepsi/rute, bukti inside/no-contact dan perhitungan bonus |
| Timer ARENA | Ledger simulator dimulai pada penempatan/START referee sehingga preflight ikut tercatat | Run time didefinisikan sejak mulai thrust dari starting zone sampai akhir attempt | Awal timer harus diamati dari aktuasi, bukan penempatan atau startup node |
| Video | Maksimum 30 s, underwater minimal 10 s | 40–45 s; underwater tanpa tether minimal 20 s: dive, lurus, 180° clockwise, kembali; kill switch dioperasikan underwater | Siapkan demonstrasi dan desain kill switch yang akan digunakan saat lomba |
| Deadline video | Tenggat edisi 2026 | 20 Desember 2026 pukul 23:59 AoE | Setara **21 Desember 2026 pukul 18:59 WIB** (konversi UTC−12 ke UTC+7) |

Sumber ketentuan: bagian Qualification, The Arena, Navigation, Target Acquisition, Target Reacquisition, Surfacing, Key terms/Timing Bonus dan Video Submission pada halaman resmi. Angka 1,28/2 m dan tiga jalur berasal dari label diagram, bukan ukuran piksel. Gambar juga memuat label 1,8 m, 17,5 m dan 28 m; pemetaan koordinat absolut/breakpoint dasar harus ditetapkan dari makna dimensinya secara hati-hati, bukan direkonstruksi dari proporsi gambar yang tidak berskala. Ilustrasi gate generik tidak boleh mengalahkan spesifikasi tertulis sekitar 1 m kedalaman gate kualifikasi.

Jika X dipilih sepanjang sisi 50 m dan Y sepanjang 25 m seperti top view, gate utama berada melintang berbeda arah dari gate kualifikasi. Kode saat ini membentuk gate pada X tetap dan proyeksi kamera ARENA memakai asumsi normal bidang gate sepanjang X. Orientasi perlu diparameterkan; mengganti ukuran kolam saja tidak cukup.

## Yang tetap berlaku

Kualifikasi masih mengharuskan start menyentuh dinding, seluruh badan lewat gate, U-turn lalu seluruh badan lewat kembali, tanpa surface/kontak gate/dasar/dinding selama lintasan. Waktu resminya tetap berakhir pada pelintasan kedua; waktu menjadi tie-breaker setelah poin. Clockwise disebut khusus demonstrasi video, bukan kewajiban arah putar pada klausul kualifikasi. Surface–stop setelah lintasan tetap sasaran tambahan proyek.

Navigation tetap wajib sebelum tugas lain. Poin dasar tetap: Navigation 15; blue drum 30, red berpinger 50, red lain 10; flare 20 per bola serta bonus urutan 60; reacquisition 60; surface 5. Gate pada ARENA memberi penalti 2, bukan otomatis menggagalkan Navigation. Dasar/dinding 5; automatic abort pada kumulatif >10 s atau lima kontak terpisah. Penalti tetap dihitung pada abort. Ini berbeda dari latihan kita yang sengaja lebih ketat.

Surfacing Square adalah frame PVC 2 × 2 m dengan marker biru sekitar 30 cm di bawahnya. Kontak frame atau surface di luar berarti tidak memperoleh tambahan 20; bonus surface normal tetap berlaku. Navigation harus sudah selesai. Properti ini untuk ARENA, bukan penutup kualifikasi.

Bonus ukuran dan berat masing-masing 10 memerlukan inspeksi dan hanya dihitung jika tim lolos kualifikasi. Tidak boleh otomatis diberikan karena ukuran/massa model simulator. Rumus bonus waktu tetap `(900−RUN_TIME)*0.03` setelah Navigation dan sedikitnya satu tugas lain berhasil. Contoh 4 kini berjumlah 85, memperbaiki total lama 105. Contoh abort 5/6 kini memasukkan penalti dasar. Contoh 3/5/6 tetap tidak merinci bonus waktu; ikuti klausul rumus tertulis dan catat ketidakjelasan contoh, jangan menebak runtime yang tidak diberikan.

AUV dalam video boleh dikembangkan tetapi tidak diubah signifikan; kill switch yang ditunjukkan tidak boleh dimodifikasi. Penyelam berada di kolam saat permainan; simulator belum memodelkan penyelam dan hal ini tidak dengan sendirinya menjadi spesifikasi wajib detektor manusia otomatis.

## Status bukti lama dan urutan migrasi

Hasil 84 tes, kualifikasi empat skenario dan dua ARENA tambahan tetap bukti baseline **2026**. Itu bukan hasil gagal, tetapi belum merupakan penerimaan **2027.2.1**. Angka waktu dan skor lama tidak boleh dipindahkan sebagai benchmark arena baru tanpa pengujian ulang.

1. Tambahkan profil aturan/fixture 2027 terpisah agar baseline 2026 dan artefaknya tetap dapat direproduksi.
2. Modelkan kolam/dasar, tiga jalur kualifikasi, gate utama, target mat, starting zone serta Surfacing Square; dokumentasikan koordinat latihan yang tidak ditentukan persis.
3. Perbarui proyeksi gate dan perencana agar tidak mengasumsikan satu orientasi gate untuk kedua arena.
4. Ubah eligibility pickup dari gate tambahan menjadi seluruh envelope AUV keluar target zone setelah acquisition. Keluar zona berpotensi menghemat perjalanan dibanding kembali ke gate; besarnya penghematan perlu diukur setelah implementasi.
5. Tambahkan bonus square dan timer sejak thrust; bedakan kebijakan skor resmi dari strict training abort.
6. Jalankan ulang geometri/SDF, persepsi, tiga jalur kualifikasi, misi blue/pinger/pickup, square berhasil/kontak/di luar, kehilangan retensi, abort dan shutdown.

Pekerjaan pada sesi pemeriksaan ini hanya memperbarui arsip dan dokumentasi status. Tidak menjalankan ulang misi atau mengubah simulator secara diam-diam. Konfirmasi spesifikasi servo/catu daya/driver/kanal tetap belum tersedia; perubahan rulebook tidak dianggap sebagai konfirmasi perangkat.
