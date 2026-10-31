# 41 — Audit dan migrasi rulebook 2027.3.2

1 November 2026. Pelaksanaan tahap pertama rencana 40 setelah konfirmasi pengguna. Status: audit/migrasi acuan versi selesai; lima run runtime diterima. 148 tes unit lulus dan build berhasil.

## Acuan

Halaman publik dan source resmi menyatakan 2027.3.2 (30 Oktober 2026). Source commit `b7194b4c3efa542fd19b1efa15bc6ddc8f9ebbb1`, dibanding arsip 2027.2.1 pada `dd6a05cbf147212ddd14c4994b746a45b0bf91fd`. Byte arsip baru cocok dengan Git blob resmi. [Arsip/checksum/diff](../doc/sources/rulebook-2027.3.2/README.md).

Audit memakai heading bertingkat agar bagian Points dan Specification of props yang berulang tidak tertimpa. Dari 59 bagian: 56 identik setelah normalisasi whitespace, satu penekanan Markdown, dua berubah (metadata dan keanggotaan tim). Perbandingan commit mencatat empat file berubah; aset gambar tidak berubah.

## Matriks dampak

| Bagian | Hasil audit | Tindakan implementasi/penerimaan |
|---|---|---|
| Keanggotaan tim | Syarat minimal separuh mahasiswa penuh waktu; kategori student/open dihapus | Catat sebagai kewajiban administratif, bukan simulasi tim/pendaftaran |
| Video | Penekanan pada kewajiban lama; isi sama | Dokumentasikan; tidak menyamakan video simulator dengan bukti kendaraan nyata |
| Kualifikasi/gate | Isi dan diagram sama | Pertahankan geometri dan U-turn 0,7 rad/s yang diterima; ulang tiga jalur |
| Tugas ARENA, reacquisition, Square, timer, penalti | Isi sama | Pertahankan perilaku; ulang blue drum dan pinger/pickup |
| Ukuran/daya/safety/komunikasi/prosedur | Isi sama | Pertahankan batas dan keterbatasan model yang didokumentasikan; inspeksi fisik belum terbukti |
| Metadata | 2027.2.1 → 2027.3.2 | Satu `rules2027.VERSION` dipakai referee, score, runtime dan penguji |
| Build source rulebook | Stylesheet lokal untuk publikasi/PDF | Arsipkan perubahan upstream; tidak memerlukan upgrade ROS/Gazebo |

Audit hanya menetapkan perbedaan versi. Kekurangan pemodelan yang telah ada sebelumnya tetap kekurangan; perubahan label bukan bukti semua aturan lomba telah diimplementasikan.

## Implementasi

Versi pusat `rules2027.VERSION` kini 2027.3.2. Laporan referee ARENA, score ARENA, runtime kualifikasi dan penguji kualifikasi mengambil konstanta tersebut. Edisi 2026 tetap menghasilkan label 2026 v6.1.0. Tes menegakkan konsistensi label versi dan pemisahan legacy. Tidak ada perubahan gain, dinamika, sensor, geometri, atau logika penilaian karena audit tidak menemukan perubahan aturan pada bagian itu.

## Pengujian

Build dan 148 tes unit lulus. Percobaan pertama di sandbox gagal setup: DDS ditolak membuat socket (`getifaddrs`/UDP Operation not permitted) dan direktori log Gazebo read-only. Ini bukan kegagalan misi atau bukti stale_sensors historis. Log disimpan di `evidence/rulebook-2027-3-2`. Auto-review mengizinkan pengulangan runtime lokal dengan akses socket/log yang diperlukan, pada domain 95/partition terpisah. Tidak mengubah guard untuk mengatasi pembatasan sandbox.

Penerimaan serial disimpan di `evidence/rulebook-2027-3-2-runtime`: tiga jalur kualifikasi dengan fixture laporan 39, lalu ARENA blue drum dan pinger/pickup. Semua upaya dipertahankan. Versi pada output diverifikasi terpisah dari keberhasilan fisika misi.

## Kelanjutan rencana 40

Tahap diagnosis jeda produsen/native/ROS, uji pengaruh GUI + dua POV, batch konsistensi 15 run dan optimasi vertikal belum dikerjakan pada fase migrasi ini. Penyebab stale_sensors spontan masih terbuka. Kalibrasi hardware dan inspeksi tim/kendaraan tetap memerlukan bukti nyata.

## Hasil akhir penerimaan

| Run | Hasil | Waktu/skor |
|---|---|---|
| Kualifikasi lane 1 | Pelintasan penuh, surface/stop lulus | Pelintasan kedua 22,668 s; start–surface 25,728 s |
| Kualifikasi lane 2, yaw awal 0,08 rad | Lulus | 22,814 s; 25,874 s |
| Kualifikasi lane 3, offset 0,15 m | Lulus | 23,830 s; 26,890 s |
| ARENA blue drum | Misi lengkap lulus | 210,2065 poin simulator; thrust–surface 226,450 s |
| ARENA pinger drum 2 + pickup | Misi lengkap lulus | 289,9542 poin simulator; thrust–surface 234,860 s |

Seluruh run berlabel 2027.3.2, lulus kualitas kalibrasi sebelum thrust, kontrol tanpa ground truth, gaya akhir nol dan shutdown bersih. Pinger lulus keluar target zone, mengambil bola yang sama, dan retensi fisik hingga akhir; penalti kedua ARENA nol. Bonus inspeksi ukuran/berat tidak dimasukkan. Ini satu run per fixture dan pengujian headless; GUI/hardware belum divalidasi ulang.

U-turn kualifikasi tetap 4,8 s pada ketiga jalur. Lane 3 membutuhkan tambahan alignment kembali 1,0 s; rentang waktu pada batch ini tidak identik dengan laporan 39 meski parameter gerak sama. Perlu pengulangan konsistensi sebelum menyimpulkan performa statistik.

Bukti: [verification.json](../ros2_ws/evidence/rulebook-2027-3-2-runtime/verification.json), berisi hash source/library dan laporan, perintah, versi sumber serta semua lima run. SHA-256 dan Git blob arsip diperiksa ulang. Kasus setup terblokir sandbox tetap dipertahankan terpisah; bukan run misi yang diterima. 148 tes unit dan build lulus.

Tahap pertama rencana 40 selesai. Audit ini membuktikan penerapan delta versi; tidak mengubah status kewajiban yang belum dimodelkan, validasi hardware, atau penyebab stale_sensors spontan yang masih terbuka.
