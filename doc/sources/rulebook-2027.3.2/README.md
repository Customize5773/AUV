# Arsip rulebook resmi SAUVC 2027.3.2

Diperiksa 1 November 2026, Asia/Jakarta. [Halaman publik](https://sauvc.org/rulebook/) menyatakan versi 2027.3.2, diperbarui 30 Oktober. Source dikunci ke [commit b7194b4](https://github.com/sauvc/rulebook/blob/b7194b4c3efa542fd19b1efa15bc6ddc8f9ebbb1/rulebook.md); checksum Git blob cocok dengan metadata commit resmi.

| Berkas | Isi |
|---|---|
| [rulebook.md](rulebook.md) | Source resmi pada commit tetap, byte cocok dengan Git blob |
| [source.json](source.json) | Commit, URL, tanggal, ukuran, SHA-256 dan Git blob SHA |
| [diff-2027.2.1.patch](diff-2027.2.1.patch) | Diff source lengkap terhadap arsip lama |
| [section-audit.json](section-audit.json) | Audit 59 bagian memakai path heading bertingkat, termasuk Points/props yang berulang |
| [compare-commits.json](compare-commits.json) | Perbandingan GitHub: dua commit, empat file berubah; tidak ada aset gambar berubah |

Normalisasi whitespace menghasilkan 56 bagian identik, satu hanya penekanan Markdown, dan dua berbeda (metadata serta keanggotaan tim). Perubahan isi aturan: minimal separuh anggota harus mahasiswa penuh waktu; klasifikasi student/open dari arsip lama dihapus. Penekanan pada larangan perubahan signifikan kendaraan setelah video tidak mengubah isi kewajiban. Build/PDF mendapatkan stylesheet lokal.

Aturan tugas/skor, kualifikasi dan geometri yang dinyatakan dalam source tidak berubah. Matriks dampak dan penerimaan simulator ada pada [laporan 41](../../../plan/41-audit-dan-migrasi-rulebook-2027-3-2.md). Ini audit perbedaan versi; bukan klaim bahwa seluruh kewajiban lomba sudah dimodelkan atau kendaraan memenuhi inspeksi fisik.

Source diarsipkan tanpa mengubah teks. Gambar identik dengan arsip lama dan tidak diduplikasi; tautan gambar relatif pada source mengikuti tata letak repo upstream. Hak sumber tetap pada penyelenggara. [Arsip 2027.2.1](../rulebook-2027-published/README.md) dipertahankan sebagai riwayat.

## Pemeriksaan ulang 4 November 2026

Halaman resmi masih menyatakan **2027.3.2**, diperbarui **30 Oktober 2026**. Source `master/rulebook.md` upstream identik byte demi byte dengan arsip ini (SHA-256 sama); tidak ditemukan perubahan teks aturan yang memerlukan migrasi simulator. Bukti pemeriksaan: [rulebook-check-20261104.json](../rulebook-check-20261104.json). Pemeriksaan ini tidak membuktikan tidak adanya pengumuman lain di luar halaman/source tersebut.

## Pemeriksaan ulang 13 November 2026

Halaman resmi tetap **2027.3.2**, diperbarui **30 Oktober 2026**. GitHub compare terhadap commit arsip `b7194b4c3efa542fd19b1efa15bc6ddc8f9ebbb1` menghasilkan `identical`, nol commit dan nol file berubah pada `master`; daftar PR terbuka kosong saat diperiksa. Jadi source aturan dan aset dalam repo resmi belum berubah dari arsip, dan migrasi simulator tidak diperlukan. [Bukti pemeriksaan](../rulebook-check-20261113.json). Label beranda v6.1.0 masih tertinggal meskipun tautannya menuju rulebook 2027. Tidak ditemukan guidebook 2027 terpisah pada halaman resmi/pencarian yang diperiksa; kanal privat panitia tidak diperiksa.

## Pemeriksaan ulang 14 November 2026

Versi publik tetap **2027.3.2**, diperbarui 30 Oktober. GitHub compare terhadap commit arsip menunjukkan `master` identik, tanpa commit/file berubah. [Bukti pemeriksaan](../rulebook-check-20261114.json). Tidak diperlukan migrasi aturan simulator; pemeriksaan ini tidak mencakup kanal privat panitia.

## Pemeriksaan ulang 16 November 2026

Halaman resmi masih 2027.3.2 (30 Oktober); GitHub compare `master` terhadap commit arsip identik, nol commit/file berubah. Tidak diperlukan migrasi simulator. [Bukti pemeriksaan](../rulebook-check-20261116.json). Kanal privat panitia tidak diperiksa.

## Pemeriksaan ulang 18 November 2026

Halaman publik masih **2027.3.2**, diperbarui **30 Oktober 2026**. Perbandingan `master` dengan commit arsip tetap `identical`, nol commit dan nol file berubah, termasuk aset dalam repo. [Bukti pemeriksaan](../rulebook-check-20261118.json). Tidak diperlukan migrasi rulebook baru; ini tidak menyatakan revisi gripper fixed sudah lulus penerimaan simulator.

Aturan reacquisition tetap mensyaratkan seluruh bagian AUV keluar target zone sebelum kembali mengambil bola yang sama, lalu mempertahankannya sampai akhir attempt. Bagian tersebut tidak menentukan gripper harus memanjang. Drum berdiameter 60 cm dan kedalaman 30 cm; bola tim berdiameter 3,5–4,5 cm dengan massa maksimal 200 g. Kontak aktuator pada bagian dalam drum saat deploy/retrieve tidak dipenalti; kontak bagian luar drum atau body kendaraan dapat terkena penalti yang sama dengan menyentuh dasar kolam. [Aturan resmi, bagian 9.2, 9.3 dan 9.9](https://sauvc.org/rulebook/).

Cakupan pemeriksaan hanya halaman publik dan source repo resmi; pengumuman privat panitia tidak diperiksa.
