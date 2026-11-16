# 73 — Konsistensi setelah perbaikan antrean kamera

16 November 2026. Permintaan: melanjutkan progres software/simulator, dengan pengujian kendaraan fisik tetap dikecualikan.

## Cakupan

Mengulang **13 kasus non-GUI yang sudah dipakai pada laporan 71** pada revisi antrean laporan 72. Tidak menambah tingkat kekeruhan, layout, batas kelulusan atau parameter baru. Tidak ada perubahan source produksi.

- Sembilan kualifikasi: jalur 1/2/3 × seed 7/42/91, atenuasi sintetis 0,10/m. Jalur 2 memakai yaw 0,08 rad dan jalur 3 offset lateral 0,15 m.
- Dua kualifikasi tantangan yang sama: arus 0,02 m/s dengan hold, dan prior posisi `[0.1, -0.1]` m.
- Dua ARENA 0,05/m: extended seed 7 dan blue drum seed 91.

Demo GUI tidak diulang pada batch ini; tiga pengulangan GUI dan satu ARENA extended seed 42 pada revisi yang sama sudah disimpan pada laporan 72. Bukti lama dan baru tidak ditimpa. Suite 195 tes pada laporan 72 tetap berlaku pada source yang sama; tidak dijumlahkan sebagai tes baru.

Runner memakai `tools/check_reliability.py`, matriks 13 kasus diambil dari manifest lama. Source/aset dibekukan berdasarkan manifest 98 file dari laporan 72. Tiap hasil menyimpan kondisi, alasan kegagalan bila ada, hasil pemeriksa, akurasi estimator, command/gaya akhir serta shutdown. Eksekusi serial memakai ROS domain 230 dan partition simulator tersendiri, tanpa MAVLink atau kendaraan nyata.

## Hasil akhir — selesai

[Summary dan matriks](../ros2_ws/evidence/consistency-paired-20261116/acceptance/summary.json) · [Runner](../ros2_ws/evidence/consistency-paired-20261116/run.py) · [Manifest source/aset](../ros2_ws/evidence/consistency-paired-20261116/source-sha256.json).

**13/13 run diterima**, seluruhnya DONE, akurasi dalam batas pemeriksa, command/gaya akhir sesuai kontrak stop dan shutdown bersih. Tidak ada perubahan source produksi pada tahap ini. Manifest 98 file sama persis dengan laporan 72; definisi kasus, kondisi dan argumen sama dengan 13 kasus non-GUI laporan 71.

| Kelompok | Hasil | Bukti utama |
|---|---|---|
| Jalur 1 × tiga seed | 3/3 diterima | Pelintasan penuh pergi/balik, U-turn, surface, stop |
| Jalur 2 × tiga seed, yaw 0,08 rad | 3/3 diterima | Pelintasan penuh dan estimator lulus |
| Jalur 3 × tiga seed, offset lateral 0,15 m | 3/3 diterima | Pelintasan penuh dan estimator lulus |
| Arus/hold | 1/1 diterima | Hold 29,988 s; drift XY maksimum 4,95 mm; abort uji menonaktifkan hold dan thruster |
| Prior posisi | 1/1 diterima | Galat XY maksimum 14,765 cm, masih di bawah batas 20 cm |
| ARENA extended seed 7 | 1/1 diterima | 290,7396 poin; thrust–surface 208,680 s; penalti nol |
| ARENA blue drum seed 91 | 1/1 diterima | 210,16066 poin; thrust–surface 227,978 s; penalti nol |

Sembilan kualifikasi reguler, seluruh waktu dalam detik simulasi:

| Metrik | Minimum–maksimum |
|---|---|
| Thrust sampai seluruh badan melewati gate kedua kali | 23,632–24,674 s |
| Thrust–surface | 26,726–27,768 s |
| Thrust–stop | 31,322–32,598 s |
| Galat XY maksimum per run | 1,738–2,614 cm |

ARENA extended tetap membuktikan tiga flare sesuai urutan Y–B–R, drop ke drum pinger, keluar zona, pickup bola yang sama, retensi hingga surface dan Square. Galat XY maksimum extended 16,295 cm dan blue drum 6,252 cm. Kamera tidak diberi koordinat ground truth untuk kontrol.

Log `stale_sensors` pada penutupan tetap disimpan. Pemeriksaan log mendapati seluruh pesan tersebut sesudah DONE, dengan world dipause sebelum shutdown. Ini konsisten dengan penutupan produsen sensor, bukan bukti abort misi pada batch ini. Tidak ada klaim log sepenuhnya tanpa ERROR.

[Verifikasi akhir](../ros2_ws/evidence/consistency-paired-20261116/verification.json) · [Pemeriksaan log shutdown](../ros2_ws/evidence/consistency-paired-20261116/shutdown-log-review.json). Ulangi verifier dari `ros2_ws`: `bash tools/ros.sh python evidence/consistency-paired-20261116/verify.py`.

Batch ini menilai penerimaan misi. Bukti khusus kamera tanpa stale setelah gambar pertama tetap berasal dari tiga GUI berinstrumen pada laporan 72; headless lulus tidak dipakai untuk mengklaim seluruh frame kamera bebas jeda. Suite 195 tes tidak diulang karena source sama; angka tersebut tetap bukti laporan 72.

## Batas

Ini penerimaan ulang matriks terpilih pada perubahan antrean kamera, bukan optimasi kecepatan baru atau bukti keandalan seluruh kondisi kolam. Parameter air sintetis bukan NTU. Tidak menguji kendaraan fisik dan tidak mengidentifikasi semua penyebab stale historis.
