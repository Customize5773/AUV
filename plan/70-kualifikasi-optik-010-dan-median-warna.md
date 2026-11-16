# 70 — Kualifikasi optik 0,10/m dan median warna

16 November 2026, Asia/Jakarta. Fokus yang diminta pengguna: menindaklanjuti `gate_lost` pada kualifikasi 0,10/m. Ini skenario latihan sintetis tambahan, bukan syarat rulebook.

## Diagnosis yang direkam

Kasus jalur 3 dengan offset lateral 0,15 m direproduksi pada source sebelum perubahan. Misi kembali ABORT `gate_lost`; proses berhenti aman dan shutdown bersih. Observer menyimpan enam capture RGB jernih, depth dan RGB berpengaruh air pada timestamp yang sama. [Hasil diagnosis](../ros2_ws/evidence/qualification-dense-20261116/diagnosis/capture.json), [contoh gambar](../ros2_ws/evidence/qualification-dense-20261116/diagnosis/gate-00-water.png).

Detektor memakai estimasi warna rata-rata seluruh frame untuk fallback keseimbangan warna. Lantai dekat yang lebih terang membias estimasi relatif terhadap gate jauh yang lebih terpengaruh haze. Pada frame pertama, rata-rata sampel RGB sekitar [77,96; 120,47; 135,18], menghasilkan gain merah 1,545. Deteksi tetap kosong. Median [49; 99; 117] menghasilkan gain merah 2,0, masih pada batas gain lama, dan gate kembali terdeteksi. Hal yang sama terlihat pada keenam capture. [Analisis per frame](../ros2_ws/evidence/qualification-dense-20261116/diagnosis/balance-analysis.json).

## Perubahan terkecil

[gate_detection.py](../ros2_ws/src/sauvc_sim/sauvc_sim/gate_detection.py) memakai median sampel RGB sebagai pengganti rata-rata pada fallback yang sudah ada. Deteksi asli tetap dicoba dahulu. Batas gain 0,5…2, syarat cast warna, mask warna, geometri pasangan tiang, proyeksi arah/jarak dan pengaman tidak dilonggarkan. Controller tidak menerima koefisien air, depth atau posisi gate ground truth.

Satu pasangan frame diagnosis jernih/berpengaruh air dijadikan fixture NumPy terkompresi untuk tes regresi. Tes memeriksa deteksi, span dan bearing terhadap frame jernih. Fixture tersebut hanya dibaca tes, bukan runtime controller.

## Bukti sebelum penerimaan

- **195 tes unit lulus**, termasuk regresi dari capture yang benar-benar gagal sebelum perubahan.
- **Enam replay positif** kembali mendeteksi gate, dengan span/center dekat frame jernih; **12 replay negatif** tidak menghasilkan gate palsu. [Replay](../ros2_ws/evidence/qualification-dense-20261116/replay.json).
- Build package selesai. Source/aset/fixture untuk penerimaan dibekukan pada [manifest](../ros2_ws/evidence/qualification-dense-20261116/acceptance/source-sha256.json).

## Penerimaan misi

**Lima pengujian headless diterima**, seluruhnya DONE, command/gaya akhir nol, kendaraan stationary dan shutdown bersih. Referee membuktikan pelintasan penuh pergi/balik, U-turn, surface dan stop pada semua kualifikasi.

| Kasus | Pelintasan kedua resmi | Thrust–surface | Thrust–stop | Galat XY maksimum |
|---|---:|---:|---:|---:|
| 0,10/m, jalur 3, offset 0,15 m — kasus gagal semula | 23,944 s | 27,072 s | 31,662 s | 1,77 cm |
| 0,10/m, jalur 1 | 23,274 s | 26,402 s | 31,026 s | 1,75 cm |
| 0,10/m, jalur 2, yaw 0,08 rad | 24,002 s | 27,098 s | 31,620 s | 1,75 cm |
| Baseline jernih, jalur 3, offset 0,15 m | 22,726 s | 25,820 s | 30,784 s | 3,39 cm |

ARENA blue drum 0,05/m juga lulus: **210,15304 poin**, thrust–surface **228,232 s**, galat XY maksimum **6,48 cm**, bonus Square +20 dan penalti 0. Ini regresi pemakai kode bersama; bukan optimasi kecepatan baru.

[Summary runner](../ros2_ws/evidence/qualification-dense-20261116/acceptance/runner.json), [verifikasi lengkap](../ros2_ws/evidence/qualification-dense-20261116/acceptance/verification.json) dan [log verifier](../ros2_ws/evidence/qualification-dense-20261116/acceptance/verifier.log). Semua PID launch sudah berakhir. Manifest dan fixture cocok; dibanding source laporan 69, hanya detektor gate, tesnya dan fixture regresi yang berubah. Bukti gagal sebelum perubahan tetap disimpan.

**Fokus yang diminta selesai:** tiga jalur 0,10/m pada kasus terpilih lulus setelah perbaikan, tanpa mengubah pengaman. Ini satu run per jalur, bukan estimasi probabilitas keandalan atau pengulangan seluruh matriks 18 kasus.

## Batas

Tidak ada perubahan kecepatan, model gaya atau aturan lomba. Angka 0,10/m adalah koefisien optik sintetis, bukan NTU atau ukuran kejernihan resmi SAUVC. Kelulusan kasus terpilih tidak mewakili seluruh kondisi kolam atau AUV nyata. Tidak menaikkan level uji baru secara otomatis setelah kasus ini selesai. Ringkasan utama tetap [STATUS.md](../STATUS.md).
