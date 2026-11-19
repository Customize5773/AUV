# Lanjutan gripper tetap: diagnosis reach dan fixture tambahan

18 November 2026. Melanjutkan [penerimaan revisi fixed](75-penerimaan-gripper-pendek-tetap.md), tanpa pengujian kendaraan fisik. Gripper tetap pendek dan di tengah; source produksi, ukuran hull/drum, collision, kecepatan dan pengaman tetap sama.

## Penerimaan tambahan

**Tiga run tambahan diterima** oleh pemeriksa yang sudah ada: dua jalur kualifikasi yang belum diuji pada penerimaan fixed pertama, serta ARENA layout alternatif. Manifest 98 file source/binary/aset tetap cocok dengan laporan 75. Hasil build dan 197 tes dari laporan tersebut tetap berlaku pada source yang sama; sesi ini menambah bukti runtime dan diagnosis geometri.

| Kualifikasi tambahan | Gate kedua (s) | Thrust–surface (s) | Thrust–stop (s) |
|---|---:|---:|---:|
| Jalur 1; seed 7, nominal | 23.546 | 26.640 | 31.060 |
| Jalur 2; seed 42, prior ±10 cm, offset 15 cm, yaw 0,1 rad | 22.804 | 25.932 | 30.794 |

Kedua run tambahan memakai atenuasi 0/m. Bersama jalur 3 pada laporan 75 (atenuasi 0,10/m), revisi fixed kini memiliki **satu run lulus pada setiap jalur**. Kondisinya berbeda; ini belum pengulangan kondisi identik untuk menilai konsistensi waktu. Rentang ketiga fixture adalah gate 22,804–24,948 s, surface 25,932–28,076 s, stop 30,794–33,006 s.

ARENA tambahan: **varian 1, blue drum 2, urutan R–Y–B, seed 42, prior ±10 cm**, atenuasi 0/m. Hasil **210.37852 poin**, thrust–surface **220.716 s**, penalti **0**, galat XY maksimum **17.06 cm**. Gate, jatuhnya bola ketiga flare, payload masuk blue drum, Square, surface–stop dan shutdown diperiksa. Run ini tanpa GUI; bukti GUI/dua POV tetap berasal dari fixture blue drum laporan 75.

Total revisi fixed sekarang: **tiga kualifikasi dan dua ARENA blue drum lengkap** pada fixture berbeda, plus satu penolakan extended yang diuji sebelum thrust. Semua misi lengkap diterima dengan gaya akhir nol, stationary dan shutdown bersih. Ini perluasan bukti, bukan optimasi kecepatan atau kelulusan semua kondisi.

## Diagnosis pickup dengan gripper tetap pendek

![Diagnosis collision gripper tetap dan drum](../ros2_ws/evidence/gripper-fixed-reach-20261118/reach.png)

Hull collision yang dipakai simulator adalah box **51,85 × 38,69 × 20 cm**. Diagonal mendatarnya **64,69 cm**, melebihi bukaan dalam drum sekitar **56 cm**. Untuk bola settled dengan pusat floor + 4 cm, offset grip −18 cm menempatkan bawah hull pada floor + 12 cm; bibir drum floor + 32 cm. Kekurangan clearance mendatar **20 cm** berasal dari geometri, sehingga mengubah timeout/alignment saja belum menyelesaikan benturannya.

Pencarian statis memakai box hull dan **32 box dinding drum yang diekstrak dari SDF**, dengan Separating Axis Theorem. Empat self-check sederhana memeriksa box berimpit, terpisah, rotasi yang bersentuhan dan box rotasi yang terpisah meskipun AABB tumpang tindih.

Diperiksa **395,304 orientasi per posisi bola**: roll −180…180° dan pitch −90…90° bertahap 2°, yaw 0…345° bertahap 15°. Enam posisi bola mencakup pusat, offset dekat pusat 2,4 cm, serta offset 20 cm pada empat arah. Pose yang menembus lantai kolam ditolak. Dari pose sisanya, **tidak ditemukan hull bebas benturan dinding** dengan titik grip berimpit pusat bola.

Ini **pencarian diskret**, bukan pembuktian untuk semua orientasi kontinu, lokasi bola, lintasan, titik kontak, bentuk visual atau AUV fisik. Lantai dasar drum dan collision gripper bahkan belum ditambahkan ke filter, sehingga hasil tidak diklaim sebagai simulasi pickup runtime. Pada pendekatan mendatar yang menjaga hull di atas bibir drum, offset grip memerlukan sedikitnya 38 cm dari pusat body; angka ini diagnosis, **bukan perubahan desain yang diterapkan**.

**Pickup tetap terbuka.** Belum ada solusi teruji yang memenuhi gripper pendek tetap dan collision sekarang; controller tetap menolak extended sebelum thrust. Profil pinger/pickup lengkap tidak dinyatakan lulus. Collision AABB adalah model konservatif dari batas visual, bukan geometri detail kendaraan fisik; perubahan bentuk collision memerlukan bukti kesesuaian dengan body, bukan pengurangan ukuran untuk meloloskan drum.

Pemeriksaan lanjutan memakai titik mesh asli, bukan hanya AABB, tersedia pada [laporan 77](77-diagnosis-pickup-dengan-titik-mesh-asli.md).

## Bukti dan pengulangan

- [Verifikasi tambahan](../ros2_ws/evidence/gripper-fixed-followup-20261118/verification.json) · [skrip pemeriksa bukti](../ros2_ws/evidence/gripper-fixed-followup-20261118/verify.py).
- [Jalur 1](../ros2_ws/evidence/gripper-fixed-followup-20261118/q-nominal-7/q-nominal-7.json) · [jalur 2/prior](../ros2_ws/evidence/gripper-fixed-followup-20261118/q-prior-42/q-prior-42.json) · [ARENA alternatif](../ros2_ws/evidence/gripper-fixed-followup-20261118/a-prior/a-prior.json).
- [Data diagnosis reach](../ros2_ws/evidence/gripper-fixed-reach-20261118/reach.json) · [perhitungan](../ros2_ws/evidence/gripper-fixed-reach-20261118/check_reach.py) · [SVG](../ros2_ws/evidence/gripper-fixed-reach-20261118/reach.svg).

```bash
cd /home/rasya/AUV/ros2_ws
bash tools/ros.sh python evidence/gripper-fixed-followup-20261118/verify.py
bash tools/ros.sh python evidence/gripper-fixed-reach-20261118/check_reach.py
```

Perintah pertama memeriksa bukti tersimpan dan manifest; kedua hanya menghitung geometri statis. Keduanya tidak mengaktifkan motor/hardware. Pengujian fisik tetap dikecualikan.


Catatan revisi 19 November: controller kualifikasi kemudian dioptimalkan pada [laporan 78](78-optimasi-awal-kualifikasi-dinamis.md). Manifest dalam laporan ini merujuk source sebelum optimasi; verifikasi source aktif tersedia pada laporan 78.
