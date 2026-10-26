# Tinjauan rulebook terbaru dan rencana misi ARENA

**Pembaruan 26 Oktober 2026:** rulebook **2027.2.1 sudah dipublikasikan** dan PR #25 telah merged. Isi berikut dipertahankan sebagai snapshot 25 Oktober; status sumber serta rencana terbaru ada pada [laporan 21](21-update-rulebook-2027.md). Implementasi kualifikasi/ARENA juga sudah berkembang setelah rencana awal ini; hasilnya tercatat pada laporan 15–20.

Pemeriksaan: **25 Oktober 2026, Asia/Jakarta**. **Pengguna telah menyetujui implementasi kualifikasi terlebih dahulu; implementasi ARENA belum dimulai.** Rulebook penyelenggara menjadi acuan utama; pemahaman atau usulan alur dalam percakapan dikoreksi apabila bertentangan dengan aturan.

## Sumber dan status versi

| Sumber yang diperiksa daring | Hasil | Penggunaan |
| --- | --- | --- |
| [Beranda SAUVC 2027](https://sauvc.org/#competition) | Masih menautkan Rulebook v6.1.0 | Branding 2027 tidak menjadikan isi rulebook yang ditautkan edisi 2027 |
| [Rulebook yang dipublikasikan](https://sauvc.org/rulebook/) | Berjudul 2026, v6.1.0; menampilkan 27 November 2025 | Acuan terbit yang tersedia saat pemeriksaan |
| [Source master](https://github.com/sauvc/rulebook/blob/master/rulebook.md) | Edisi 2026 v6.1.0; metadata tanggal 15 Mei 2026 | Catat perbedaan tanggal terhadap halaman web; jangan menyimpulkan isinya 2027 |
| [PR resmi #25](https://github.com/sauvc/rulebook/pull/25) | Usulan rulebook 2027, masih **open**, **belum merged**, tidak dideploy | Persiapan perubahan, belum ketentuan terbit |
| [Isi usulan pada commit 746357d](https://github.com/sauvc/rulebook/blob/746357dcfe2e0fe89364aaad6ef8a2d60c5f5f8d/rulebook.md) | Versi **2027.1.1**; metadata dokumen 10 Oktober 2026; commit terakhir 23 Oktober 2026 | Snapshot tetap untuk perbandingan dan perencanaan |
| [Participant manual](https://sauvc.org/manual) | Isi masih manual 2026 di bawah branding situs 2027 | Tidak dipakai sebagai konfirmasi arena/jadwal teknis 2027 |

Metadata PR diperiksa melalui API GitHub: head `746357dcfe2e0fe89364aaad6ef8a2d60c5f5f8d`, base `1caf29cf132318b9b5fc81b7a73ac772db9fbca0`, `merged=false`; commit head bertanggal 23 Oktober 2026 pukul 12:12:16 UTC. PR telah siap ditinjau (`draft=false` pada GitHub), tetapi **isi usulan berjudul draft dan belum disahkan melalui merge/publikasi**. PR diperbarui 24 Oktober 2026. Tenggat video dalam isinya masih `[TBD]`.

Tidak tepat lagi menyatakan "belum ada dokumen 2027" tanpa penjelasan: usulan resmi 2027 sudah ada di repositori, sementara situs publik masih menyajikan edisi 2026. Pemeriksaan ini tidak membuktikan ada keputusan final lain di kanal yang tidak dapat diakses.

## Perubahan penting yang memengaruhi simulator

Perbandingan berikut berasal dari teks dan label diagram, bukan pengukuran piksel. Kolom 2027 seluruhnya masih **usulan** dari commit tersebut.

| Unsur | Edisi 2026 terbit / simulator saat ini | Usulan 2027.1.1 | Implikasi rencana |
| --- | --- | --- | --- |
| Kolam | 25 × 16 m | 50 × 25 m | Arena sekarang tetap berlabel 2026; belum sesuai geometri usulan 2027 |
| Profil dasar pada diagram | Ujung 1,2 m, tengah 1,6 m | Label kedalaman 1,28 m dan 2 m; profil dasar berbeda | Jangan sekadar memperbesar kolam lama; periksa bidang dasar dari diagram yang dipilih |
| Gerbang utama | Sekitar 16 m dari start; 1,5 × 1 m | Sekitar 12 m dari start; 1,5 × 1,5 m | Clearance dan pendekatan harus mengikuti versi |
| Orange flare | Diameter sekitar 15 cm, dasar sampai permukaan | Tinggi 1,5 m, diameter sekitar 15 cm | Tinggi obstacle berubah, penghindaran tetap wajib |
| Gerbang kualifikasi | Dua jalur pada diagram; dari dasar sampai permukaan | Diagram menunjukkan tiga jalur di sisi arena; gerbang lebar 1,5 m, menggantung sekitar 1 m dari permukaan | Jumlah jalur dan batas bukaan tidak dihardcode mengikuti arena lama |
| Zona drum | Empat drum dekat ujung arena; mat hijau dapat tidak tersedia | Empat drum di mat hijau 8 × 2 m | Cari warna, bukan indeks/posisi drum biru yang selalu sama |
| Tata letak | Diagram 2026 yang sebelumnya dikirim pengguna | Diagram `arena-2027.png` baru; area operasi dan zona flare berpindah | Jalur pergerakan harus direncanakan ulang |
| Surfacing Square | Tidak tersedia | Bingkai 2 × 2 m; marker biru sekitar 30 cm di bawahnya | Usulan bonus 20 poin setelah Navigation, di luar bonus surface 5 poin; bukan bonus kualifikasi |
| Video submission | Maksimum 30 s; underwater minimal 10 s | 40–45 s; underwater minimal 20 s; dive, lurus, putar 180° clockwise, kembali; kill switch diuji underwater | Ini persyaratan video, bukan dasar menyatakan putaran kualifikasi wajib clockwise |

[Diagram usulan arena](https://github.com/sauvc/rulebook/blob/746357dcfe2e0fe89364aaad6ef8a2d60c5f5f8d/img/arena-2027.png), [gerbang kualifikasi](https://github.com/sauvc/rulebook/blob/746357dcfe2e0fe89364aaad6ef8a2d60c5f5f8d/img/qualification-gate.jpg), dan [Surfacing Square](https://github.com/sauvc/rulebook/blob/746357dcfe2e0fe89364aaad6ef8a2d60c5f5f8d/img/surfacing-square-2027.png) telah diperiksa secara visual. Salinan analisis berada di [folder sumber usulan 2027](../doc/sources/rulebook-2027-proposal/README.md), terpisah dari arsip 2026.

Usulan 2027 menyebut gerbang kualifikasi menggantung sekitar 1 m; ilustrasi depan lama menggambarkan dasar di bawah tiang sedangkan diagram arena baru memperlihatkan lantai lebih dalam. Implementasi tidak boleh menganggap kedalaman kolam sama dengan tinggi gerbang hanya dari ilustrasi depan generik. Gunakan ukuran tertulis, catat ketidakpastian dan periksa kembali apabila sumber final memberi penjelasan.

## Koreksi pemahaman urutan misi

Bagian Tasks pada kedua sumber mewajibkan **Navigation selesai sebelum task lain**. Gambar hanya menunjukkan zona penempatan benda; urutan posisi pada gambar bukan urutan pengerjaan. Karena itu rencana tidak menggunakan skenario flare dahulu sebagai pengganti ketentuan resmi.

| Pemahaman sebelumnya | Acuan rulebook dan keputusan rencana |
| --- | --- |
| Menabrak blue, red, yellow lalu melewati gate | Lewati gate terlebih dahulu sambil menghindari orange flare; sesudah Navigation baru kerjakan task flare/drum |
| Urutan flare selalu B-R-Y | Urutan diberikan panitia setelah Navigation dan dapat berubah setiap percobaan; B-R-Y hanya salah satu contoh input latihan |
| Tiang flare tersentuh berarti task selesai | Bola golf di atas flare harus benar-benar jatuh; kontak saja dicatat sebagai kontak, bukan keberhasilan task |
| Selalu mengejar blue drum | Memilih blue drum adalah strategi visual yang sah, bukan satu-satunya target aturan; bernilai 30 poin, sedangkan red drum berpinger menawarkan 50 poin |
| Drop command berhasil berarti bola masuk | Hanya bola yang benar-benar masuk drum yang dinilai; aturan mempertimbangkan bola pertama |
| Setiap kontak menyebabkan abort seperti kualifikasi | Kualifikasi dan arena memiliki ketentuan berbeda: gate/dasar/dinding dilarang selama kualifikasi; pada arena gate/dasar/dinding memiliki penalti, dengan batas kontak dasar/dinding untuk automatic abort; kontak orange flare menyebabkan abort langsung |

Pada arena, kontak gate bernilai penalti 2 poin; dasar/dinding 5 poin. Automatic abort berlaku setelah kontak dasar/dinding kumulatif lebih dari 10 s atau lima sentuhan terpisah. Pemeriksa harus mencatat skor/penalti sesuai sumber; target latihan tanpa benturan boleh lebih ketat tetapi tidak diberi label sebagai aturan abort lomba. Surfacing menutup attempt dan perolehan task yang sudah selesai tetap dilaporkan; itu berbeda dari menyatakan semua task sebelumnya batal.

## Alur kualifikasi yang direvisi

```text
Start menyentuh dinding -> menyelam
-> gate pergi, seluruh badan lewat -> U-turn
-> gate balik, seluruh badan lewat -> catat hasil dan waktu kualifikasi
-> langsung surface vertikal -> berhenti otomatis
```

Kenaikan terakhir merupakan penutup otomatis simulasi setelah lintasan kualifikasi selesai, sesuai permintaan pengguna. Rulebook mengakhiri pengukuran kualifikasi pada pelintasan kedua lengkap; tidak mewajibkan tambahan perjalanan ke start atau ke Surfacing Square. Jangan menyamakan surface sesudah selesai dengan pelanggaran surface ketika lintasan masih berlangsung. Rincian controller dan penerimaan ada pada [rencana kualifikasi](13-rencana-kualifikasi-autonomous.md).

## Alur ARENA yang diusulkan berdasarkan aturan

Satu strategi yang sah untuk task yang ingin dikembangkan pengguna:

```text
Starting zone di permukaan -> menyelam di dalam starting zone
-> cari jalur dan hindari orange flare
-> lewati gate utama dengan seluruh badan (Navigation)
-> terima urutan flare dari panitia
-> dekati flare sesuai urutan dan sebabkan bola masing-masing jatuh
-> cari blue drum, red drum tidak dijadikan target pelepasan
-> alignment kamera bawah -> lepaskan satu payload
-> verifikasi bola masuk blue drum -> hentikan gerak horizontal
-> surface untuk menutup attempt -> berhenti otomatis
```

Setelah Navigation, Acquisition dan Communication & Localization dapat dipilih urutannya; menempatkan flare sebelum blue drum dalam strategi di atas adalah pilihan rute, bukan kewajiban rulebook. Jika urutan yang disampaikan B-R-Y, AUV menargetkan blue lalu red lalu yellow; jika input lain, AUV mengikutinya. Jalur perpindahan setelah gate menyesuaikan geometri versi arena, tanpa menganggap koordinat atau arah hadap gambar lama berlaku pada diagram baru.

Red drum tetap dipersepsi sebagai penghalang untuk menghindari tabrakan. Lokasi blue drum tidak diasumsikan selalu pada urutan pertama, sebab panitia dapat mengacak susunan drum. Payload yang direncanakan berupa bola sesuai batas rulebook, bukan objek ukuran bebas. Penutupan normal yang diusulkan adalah surface setelah bola masuk terverifikasi, agar attempt resmi berakhir; berhenti terendam sesudah release saja tidak disamakan dengan penutupan attempt. Posisi ascent aman dipilih mengikuti geometri arena. Jika usulan Surfacing Square kelak disahkan, rute bonus perlu direncanakan dan diuji sebelum dijadikan target; kotak ini tidak diwajibkan pada rute 2026.

Strategi ini mencakup Navigation, Communication & Localization dan visual Target Acquisition. **Target Reacquisition belum termasuk**: task itu memerlukan keberhasilan Acquisition, melewati gate lagi, lalu mengambil kembali bola sendiri dan menahannya hingga akhir. Karena itu penyelesaian strategi ini tidak dilaporkan sebagai seluruh empat task SAUVC selesai.

## Urutan implementasi setelah konfirmasi

| Tahap | Hasil yang dituju |
| --- | --- |
| 0. Verifikasi sumber | Cek ulang halaman terbit, head master dan PR #25; catat versi/commit. Edisi 2026 menjadi acuan terbit saat ini; penggunaan usulan 2027 harus berlabel usulan dan tercakup dalam konfirmasi rencana |
| 1. Kualifikasi | Jalankan rencana 13: pengawas perintah, pemeriksa independen, lintasan dua arah, U-turn, surface sesudah finish, stop; buktikan pada kamera dan odometri |
| 2. Navigation arena | Pilih geometri versi yang benar; AUV menyelam sebelum keluar start, menghindari orange flare dan melintas penuh melalui gate sebelum task lain |
| 3. Flare berurutan | Tambah input urutan sesudah Navigation, deteksi warna, approach terkendali, bola flare dinamis dan pemeriksa jatuhnya bola |
| 4. Payload ke blue drum | Deteksi drum dari kamera bawah, abaikan red sebagai target, alignment, pelepasan payload fisik dan pemeriksa bola masuk |
| 5. Uji terintegrasi | Jalankan rangkaian Navigation -> flare -> drum; simpan rekaman, log state, bukti peristiwa fisik, skor/penalti dan keterbatasan versi |

Perubahan teknis ARENA diperkirakan menyentuh generator world/model, bridge pose/kontak, controller misi, deteksi warna/drum, model serta pelepas payload, model bola flare, pemeriksa independen, launch, executable/dependensi, uji dan panduan. Tetap gunakan package serta wrapper yang ada. Kode kualifikasi dipakai ulang untuk kendali dasar dan pengawas perintah; pemeriksa arena harus memiliki aturan yang sesuai arena.

## Bukti penerimaan ARENA

- Sebelum Navigation selesai, tidak ada task flare atau pelepasan payload yang dapat dinyatakan berhasil; sentuhan orange flare menghentikan attempt sesuai aturan.
- Pelintasan gate memakai seluruh envelope kendaraan, bukan pusat odometri saja; kontak tetap terukur dan tercatat sebagai penalti sesuai ketentuan arena.
- Uji setidaknya B-R-Y dan satu urutan berbeda; keberhasilan tiap flare memerlukan bola jatuh aktual, bukan hanya pesan controller atau kedekatan geometris.
- Payload terlihat dibawa AUV lalu dilepas dari mekanismenya; tidak diteleport atau dimunculkan langsung di drum. Model awal dapat memakai gravitasi/collision sederhana, dengan keterbatasan hidrodinamika dinyatakan.
- Uji blue drum pada lebih dari satu posisi susunan; pelepasan ke red drum, bola jatuh di luar drum dan drop tanpa alignment tidak dilaporkan sebagai Target Acquisition biru berhasil.
- Pemeriksa membaca pose/kontak bola dan drum secara independen. Perintah release, ack mekanisme, bola masuk dan bola menetap dicatat sebagai peristiwa yang berbeda.
- Bola payload berada seluruhnya di dalam bukaan blue drum dan hasil akhirnya terukur; toleransi alignment/stabilitas adalah parameter rekayasa, bukan angka resmi yang dikarang dari rulebook.
- Saat gambar/odom/komunikasi urutan hilang, misi berhenti atau abort terkontrol tanpa melanjutkan task berdasarkan keberhasilan sintetis. Hasil parsial yang memang sah tetap dicatat.

## Pemantauan pembaruan

Sebelum implementasi, perubahan dimensi/scoring, dan demonstrasi akhir: buka lagi link rulebook dari beranda, periksa versi/tanggal isinya, status merge PR #25 dan head commit repositori. Jika sumber terbit berubah, bandingkan aturan/diagram dan revisi parameter serta tes sebelum menyatakan simulator sesuai versi baru. Simpan tahun, versi, commit, URL, tanggal pemeriksaan, serta status published/proposed pada bukti pengujian. Tidak ada monitoring latar belakang atau pembaruan otomatis yang dipasang pada tahap ini.

**Perkembangan setelah perencanaan:** pengguna menyetujui implementasi kualifikasi terlebih dahulu. Hasilnya dicatat dalam [laporan kualifikasi](15-hasil-kualifikasi-autonomous.md). Rencana ARENA dan perubahan geometri usulan 2027 belum diimplementasikan.
