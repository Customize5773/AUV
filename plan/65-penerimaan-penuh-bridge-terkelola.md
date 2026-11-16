# 65 — Penerimaan penuh bridge terkelola

14 November 2026, Asia/Jakarta. Melanjutkan laporan 64: tutup celah penerimaan bertahap dengan mengulang seluruh matriks kualifikasi pada bridge terkelola, tanpa perubahan tuning atau batas pengaman.

## Lingkup

Lima seed per tiga jalur, ditambah arus/hold dan dua kasus prior posisi: total 18 kasus. Source dibekukan dan dicocokkan dengan source rerun bridge pada laporan 64. Controller tetap kedalaman 0,60 m, gain vertikal 1,5; model gaya tujuh thruster dan estimator sensor virtual. ARENA tidak diulang pada tahap ini karena ketiga regresi GUI/POV source identik telah diterima pada laporan 64.

## Hasil akhir

**18/18 kasus diterima pada source yang sama**, seluruh misi DONE, shutdown bersih dan semua PID launch sudah berakhir. Tidak ada retry dalam batch ini. Hash seluruh source cocok dengan revisi bridge yang diterima pada laporan 64; hash executable bridge juga cocok dengan bukti uji signal.

| Kelompok | Diterima | Start–surface |
|---|---:|---:|
| Jalur 1, lima seed | 5/5 | 25,822–26,718 s |
| Jalur 2, heading awal menyimpang | 5/5 | 25,824–26,872 s |
| Jalur 3, offset lateral | 5/5 | 25,966–26,838 s |
| Arus/hold dan dua prior posisi | 3/3 | 25,900–26,854 s |

Pelintasan kedua resmi **22,696–23,760 s** (median 23,408); surface **25,822–26,872 s** (median 26,536); stop **29,788–32,192 s** (median 30,993). Angka stop mencatat event proyek; mode hold tetap mengendalikan posisi dengan thruster aktif sesudah event tersebut. Galat XY maksimum **0,147650 m**, di bawah ambang 0,20 m yang tidak diubah.

Hold pada arus 0,02 m/s berlangsung **29,988 s** dengan drift maksimum **0,005055 m (0,51 cm)**; injeksi fault berikutnya membuktikan disarm dan gaya nol. Seluruh kasus memiliki event pelintasan keluar penuh, U-turn, pelintasan balik penuh, surface dan stop.

Kasus `q-lane3-123` yang sebelumnya crash shutdown juga lulus dalam matriks penuh ini. Bukti kegagalan awal laporan 64 dipertahankan; hasil baru bukan penulisan ulang summary lama.

[Summary matriks](../ros2_ws/evidence/qualification-managed-bridge-20261114/summary.json) menyimpan kondisi, command dan exit code tiap kasus. [Verifikasi lengkap](../ros2_ws/evidence/qualification-managed-bridge-20261114/verification.json) menyimpan hash dan pemeriksaan tiap run; [output verifier](../ros2_ws/evidence/qualification-managed-bridge-20261114/verifier.log).

Dari `ros2_ws`:

```bash
bash tools/ros.sh python tools/check_reliability.py --profile qualification-speed --suite qualification --output evidence/qualification-managed-bridge-20261114
```

Untuk pengulangan, pilih output baru. Bukti lama tidak ditimpa. Verifier memeriksa seluruh 18 kasus, hash source/binary, dinamika tujuh thruster, sensor-only control, pelintasan penuh, stop/fault hold dan cleanup proses.

Kapal belum selesai; tidak ada uji thruster atau misi fisik pada tahap ini.

## Kesimpulan dan batas

Celah penerimaan bertahap pada laporan 64 sudah ditutup untuk seluruh matriks kualifikasi ini. Penerimaan ARENA GUI/dua POV tetap mengacu pada tiga run source identik laporan 64; tidak dihitung sebagai run baru tahap ini. Suite Python/native tidak dijalankan ulang karena tidak ada perubahan source produk setelah kelulusannya pada laporan 64.

Ini verifikasi konsistensi dan lifecycle, **bukan peningkatan kecepatan**. Median surface batch baru 26,536 s, sementara baseline laporan 64 sebesar 25,854 s; perbedaan revisi dan variasi alignment tidak dipakai untuk menyimpulkan sebab tunggal. Kandidat tuning sebelumnya tetap ditolak. Tahap optimasi berikutnya perlu memisahkan waktu pencarian/alignment balik dari gerak sebelum mengubah parameter.

Pengujian tidak menjamin semua arus/layout atau kondisi air nyata. Kalibrasi AUV fisik menunggu kapal selesai; tidak ada koneksi atau aktuasi hardware pada tahap ini.
