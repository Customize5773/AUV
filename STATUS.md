# Posisi kita — simulasi ROS SAUVC

Diperbarui **17 November 2026**. Ini ringkasan utama untuk mengikuti progres; laporan bernomor menyimpan rincian dan bukti historis.

**Tujuan:** menguji misi autonomous berdasarkan rulebook sebelum dipindahkan ke AUV nyata. Kualifikasi mengejar waktu tercepat dengan pelintasan yang sah; ARENA menyelesaikan tugas dan skor. Bukti saat ini masih pada simulator.

![Peta progres simulasi SAUVC](doc/diagrams/status-simulasi-sauvc.png)

[Unduh PNG](doc/diagrams/status-simulasi-sauvc.png) · [SVG untuk diperbesar](doc/diagrams/status-simulasi-sauvc.svg) · [Sumber diagram](doc/diagrams/status-simulasi-sauvc.dot)

## Pegangan saat ini

- **Berfungsi dan punya bukti:** kualifikasi otomatis, ARENA blue drum/extended, kamera dan deteksi, dinamika tujuh thruster, estimator serta pengaman. Hasil berlaku pada skenario yang diuji.
- **Penerimaan terbaru:** gripper di tengah body, pendek saat membawa; bola awal terpasang pada carrier yang sama. Build, **197 tes** serta **tiga misi dinamis** (extended GUI/POV, blue drum dan kualifikasi) lulus dengan shutdown bersih. [Laporan 74](plan/74-gripper-tengah-pendek-dan-bola-awal.md).
- **Penerimaan sebelum perubahan gripper:** 13/13 pengulangan non-GUI lulus pada revisi antrean kamera: sembilan kualifikasi, arus/hold, prior posisi serta ARENA extended dan blue drum. Semua shutdown bersih; manifest 98 file cocok dengan laporan 72. Tiga GUI tanpa stale setelah gambar pertama serta respons kehilangan depth tetap merujuk bukti laporan 72.
- **Tes unit terbaru:** 197 lulus setelah revisi gripper. Hasil 195 tes dan replay pada laporan 70/72 merupakan bukti sebelumnya. Penerimaan misi revisi gripper juga lulus pada tiga fixture yang diuji.
- **Perbaikan kamera terbaru:** kehilangan pasangan RGB–depth pada antrean satu frame direproduksi. Masukan optik kini mempertahankan tiga capture; keluaran tetap satu frame terbaru. Tiga pengulangan GUI lulus tanpa stale setelah gambar pertama masuk. Ini belum jaminan semua beban komputer bebas jeda.
- **Kasus yang baru ditutup:** kualifikasi pada atenuasi sintetis 0,10/m yang sebelumnya `gate_lost` kini lulus di tiga jalur terpilih. Ini uji tambahan, bukan syarat rulebook. Perbaikannya memakai median warna pada fallback; kecepatan dan pengaman tetap.
- **Belum dibuktikan:** seluruh kondisi kolam dan misi pada AUV fisik. Kapal belum selesai. Refraksi, partikel dan gelombang bukan pekerjaan wajib proyek saat ini.

Bukti terbaru: [laporan 74](plan/74-gripper-tengah-pendek-dan-bola-awal.md) dan [verifikasi gripper](ros2_ws/evidence/gripper-centered-20261116/verification.json). Penerimaan 13 run sebelum perubahan gripper ada di [laporan 73](plan/73-konsistensi-setelah-perbaikan-antrean-kamera.md). Diagnosis kamera, tiga GUI dan depth fault ada di [laporan 72](plan/72-antrean-pasangan-rgb-depth-dan-pov.md). Riwayat demonstrasi dan batch 15 run ada pada [laporan 71](plan/71-demonstrasi-dan-konsistensi-revisi-optik.md). Perbaikan detektor ada pada [laporan 70](plan/70-kualifikasi-optik-010-dan-median-warna.md) dan [69](plan/69-rulebook-dan-perbaikan-halo-biru-arena.md). Acuan aktif 2027.3.2, terakhir dicek 16 November: [bukti rulebook](doc/sources/rulebook-check-20261116.json).

## Fokus terakhir — gripper tengah dan bola awal selesai pada simulator

Titik gripper kini `(0, 0, −0,18) m`: pusat bola hanya **8 cm di bawah hull**, dibanding 30 cm sebelumnya. Slider memanjang 22 cm hanya saat pickup dan retract lagi bersama bola; kualifikasi mengunci posisi pendek tanpa payload. Spawn payload, joint pemuatan dan alignment drop memakai titik yang sama. Kamera bawah bergeser 16 cm ke depan dan proyeksinya diselaraskan.

Release pertama gagal karena bukaan 34 mm menahan bola 40 mm. Bukaan kini 42 mm; probe release serta tiga misi final lulus dengan collision tetap aktif. Pose bola dan carrier berimpit pada 110 snapshot awal. Pickup mempertahankan bola melalui joint kontak sampai stop, dengan batas retensi 7,5 cm tetap. [Render inspeksi model baru](ros2_ws/evidence/gripper-centered-20261116/initial.png) · [Video POV extended](ros2_ws/evidence/gripper-centered-20261116/extended-2/pov.mp4).

Perubahan ini model simulator; ruang rod, servo dan mekanik nyata belum tervalidasi. Pengujian kendaraan fisik tetap dikecualikan. Hasil 13 run sebelumnya tetap riwayat sebelum perubahan gripper, bukan penerimaan ulang model terbaru.

## Penerimaan konsistensi sebelumnya

**13/13 run diterima pada source yang sama dengan laporan 72.** Matriks dan batas kelulusan sama dengan 13 kasus non-GUI laporan 71. Tidak ada perubahan source produksi pada tahap ini.

Sembilan kualifikasi: pelintasan kedua 23,632–24,674 detik, start–surface 26,726–27,768 detik, start–stop 31,322–32,598 detik simulasi. Hold arus 0,02 m/s selama sekitar 30 detik lulus dengan drift XY maksimum 4,95 mm; prior posisi ±10 cm juga lulus. ARENA extended mencapai 290,7396 poin dalam 208,680 detik dan blue drum 210,16066 poin dalam 227,978 detik; penalti keduanya nol.

Ini menutup pengulangan matriks yang sudah dipilih, bukan optimasi kecepatan atau jaminan seluruh kondisi. Tidak menambah tingkat uji baru secara otomatis. **Pengujian kendaraan fisik tetap dikecualikan.** [Laporan 73](plan/73-konsistensi-setelah-perbaikan-antrean-kamera.md).

## Diagnosis dan perbaikan antrean kamera sebelumnya

Antrean masukan RGB/depth dinaikkan dari satu menjadi tiga capture agar pasangan bertimestamp sama tidak hilang ketika pesan datang terpisah. Public raw tetap satu frame terbaru, tanpa perubahan batas stale. Pada tiga pengulangan GUI tidak ada stale setelah gambar pertama sampai DONE; sela raw bawah maksimum 0,363–0,470 detik, dibanding 1,112 detik pada reproduksi sebelum perubahan. [Rekaman terbaru](ros2_ws/evidence/camera-pairing-20261116/after-3/pov.mp4).

Kehilangan depth tetap menghasilkan abort aman tanpa replay. ARENA extended lulus: 290,7468 poin, penalti nol, thrust–surface 208,440 detik dan retensi bola sampai surface. Hasil ini menutup mekanisme antrean yang direproduksi; belum menjamin semua beban komputer atau penyebab stale historis. **Pengujian kendaraan fisik dikecualikan sesuai permintaan Anda.**

## Demonstrasi dan konsistensi sebelumnya

**Permintaan Anda sudah dikerjakan pada matriks yang disepakati:** demo terlihat dan seluruh 15 run diterima. Kasus arus 0,02 m/s dengan hold sekitar 30 detik mencatat drift maksimum 5,46 mm; kasus prior posisi ±10 cm juga lulus. Tiga ARENA termasuk demo: dua extended/pinger/pickup dan satu blue drum. Semua hasil tetap disimpan; ini bukti skenario terpilih, bukan seluruh kondisi.

Catatan penutupan: tiap run memiliki satu log `stale_sensors` sesudah `DONE`, dengan world dipause sebelum shutdown. Urutan ini konsisten dengan penghentian produsen sensor saat penutupan; tidak terjadi abort misi pada batch ini. Jeda POV bawah saat demo kualifikasi ditindaklanjuti secara terpisah pada laporan 72. Batch 15 run ini mendahului perubahan antrean.

Perbaikan kualifikasi 0,10/m pada tahap sebelumnya sudah selesai pada kasus yang diuji, dengan bukti di laporan 70.

## Langkah untuk menyamakan pemahaman

**Demonstrasi kualifikasi dan ARENA sudah dijalankan; Anda mengonfirmasi Gazebo serta kedua POV terlihat.** Cocokkan perilaku yang terlihat dengan alur pada diagram. Kedua POV direkam sebagai video untuk ditinjau ulang; konfirmasi terlihat tidak menggantikan pemeriksaan hasil misi. Perintah tersedia di [cara running](ros2_ws/CARA-RUNNING.md).

[Video kualifikasi](ros2_ws/evidence/demo-consistency-20261116/demo-qualification/pov.mp4) · [Video ARENA extended](ros2_ws/evidence/demo-consistency-20261116/demo-arena/pov.mp4). Video hanya merekam kamera simulasi, bukan desktop; bagian awal mencakup preflight. Bab waktu tersedia pada laporan 71.

Setiap sesi teknis berikutnya perlu menyebut satu fokus, hasil yang hendak dibuktikan, lalu hasil nyata dan batasnya. Ringkasan ini diperbarui bila ada bukti baru; pekerjaan opsional diberi label opsional. Persentase kemajuan tidak dipakai karena belum ada ukuran penyelesaian seluruh proyek yang disepakati.
