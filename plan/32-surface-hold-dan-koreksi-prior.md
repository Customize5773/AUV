# 32 — Surface hold dalam arus dan koreksi prior kualifikasi

30 Oktober 2026. Lingkup: dua kekurangan laporan 30 setelah [perbaikan kalibrasi DVL](31-kalibrasi-dvl-dalam-arus.md). **Selesai pada penerimaan terarah simulator: 8 run kualifikasi dan 1 rerun ARENA lulus; 130 tes unit lulus.** Ringkasan dengan manifest source per run: [verification.json](../ros2_ws/evidence/surface-hold-acceptance-2027/verification.json).

## Mode surface hold

`surface_hold:=true` menambahkan kontrol posisi aktif setelah surface, untuk kendaraan dinamis autonomous. Default tetap `false`: mode motor-off lama tetap mematikan thruster. Mode baru berlaku untuk kualifikasi dan ARENA.

Saat STOP, node propulsi menyimpan estimasi XY, kedalaman dan heading sebagai target. Selisih posisi diubah menjadi kecepatan body-frame terbatas (setiap sumbu horizontal 0,15 m/s, vertikal 0,08 m/s, yaw 0,2 rad/s). Pengendali gaya tujuh thruster mempertahankan integral kecepatan dekat nol selama hold untuk melawan gangguan konstan. Batas gaya dan saturasi tetap berlaku. Target tidak diambil dari pose ground truth atau nilai arus simulator.

Pada mode ini DONE berarti tugas misi selesai dan hold tetap aktif, **bukan motor mati**. Status `/sauvc/surface_hold/status` memuat `active`, `disarmed` dan target estimasi. Abort, fault dari guard, feedback/perintah yang kedaluwarsa, atau posisi nonfinite menonaktifkan output dan mengunci disarm; stream yang kembali sehat tidak melanjutkan hold otomatis. Guard sekarang tetap memublikasikan fault pertama sesudah DONE; sebelumnya status terminal dapat membungkam publikasi fault.

Motor-off dan station keeping membutuhkan kriteria berbeda. Harness tetap menyimpan `thrusters_zero`; untuk mode hold nilai ini boleh false ketika hold aktif, tetapi penerimaan juga mewajibkan bukti gaya aktif, drift fisik terukur dan penghentian darurat ke nol. Ini bukan pelonggaran kriteria motor-off lama. Referee ARENA menerima parameter hold yang eksplisit: untuk hold, perintah gerak misi harus nol dan pose fisik harus stabil, sedangkan gaya aktif diperbolehkan. Mode motor-off tetap mensyaratkan gaya nol. Result ARENA mencantumkan `stop_mode`. Pengujian 30 detik serta abort tetap merupakan syarat tambahan hold.

## Koreksi posisi awal kualifikasi

Estimator menggunakan **gate kualifikasi yang posisinya diketahui dari survei layout latihan**: bidang X=10 m dan pusat jalur yang dipilih. Kamera memberikan range/bearing dan offset kamera depan 0,32 m. Pengamatan harus berada pada fase pendekatan outbound sebelum PASS_OUT, jarak 1,8–4 m, bearing <0,15 rad, yaw <0,25 rad, roll/pitch <0,06 rad dan umur gambar 0–0,12 s. Posisi kamera dikompensasi terhadap usia frame memakai DVL. Frame kedaluwarsa, duplikat, pandangan kembali, gate salah jalur dan inovasi >0,6 m ditolak.

Tiga pengamatan konsisten diperlukan sebelum koreksi translasi dengan gain 0,2. Koreksi hanya aktif pada kualifikasi; ARENA tidak diasumsikan memiliki peta properti tetap. Pengamatan gambar tidak mengganti kedalaman/heading instrumen. `gate_corrections` pada health mencatat jumlah koreksi yang diterapkan.

Koordinat survei dan ukuran gate harus benar untuk penggunaan nyata. Ini belum pembuktian lokalisasi pada gate yang posisi/orientasinya tidak diketahui, layout acak, atau kamera yang belum dikalibrasi. Ground truth hanya digunakan evaluator.

## Inisialisasi sensor parsial

Regresi nominal pada batch pertama menyelesaikan misi dan motor-off, tetapi galat kedalaman awal mencapai 0,033019 m. Paket pertama belum lengkap, sementara filter menganggap pose sudah diinisialisasi karena timestamp sebelumnya tersedia. Pengukuran tekanan pertama akhirnya dicampur dengan nilai awal nol. Estimator kini membedakan timestamp paket dan status inisialisasi: snapshot instrumen lengkap pertama menginisialisasi kedalaman serta sikap secara langsung; paket selanjutnya memakai filter normal. Tes regresi mengirim gyro/accelerometer/magnetometer lebih dahulu, baru tekanan/DVL. Ambang penerimaan tidak diubah.

Batch awal `evidence/surface-hold-and-gate-2027/` dipertahankan: tujuh run lulus, regresi nominal gagal akurasi depth, ARENA belum dijalankan. Batch berikutnya mengulang kesembilan kasus setelah perbaikan startup: delapan kualifikasi lulus, tetapi ARENA tertahan pada STOP dan timeout karena referee masih mensyaratkan gaya thruster nol. Run ini dipertahankan sebagai kegagalan. Setelah referee diberi mode hold eksplisit, hanya ARENA yang diulang; kode kontrol/estimasi kualifikasi tidak berubah. Perbedaan source terhadap delapan run kualifikasi dibatasi pada `arena_runtime.py`, penambahan parameter khusus node `arena_referee` di launch, dan tes regresinya. Seluruh suite unit diulang menjadi 130 tes. Jadi hasil akhir merupakan gabungan penerimaan terarah, bukan klaim bahwa seluruh sembilan run diulang lagi pada revisi referee terakhir.

## Verifikasi

Build berhasil; **130 tes unit lulus**. Tes tambahan mencakup mode hold opt-in, integral gangguan konstan, fault setelah DONE, feedback hilang, posisi nonfinite, disarm terkunci, koreksi prior dengan usia frame serta penolakan pengamatan tidak sah.

Matriks penerimaan yang ditetapkan:

- Tiga kualifikasi berarus 0,02 m/s, seed 7/42/91, dengan hold aktif.
- Tiga kualifikasi prior XY salah (+0,10; −0,10 m), penempatan lateral +0,15 m dan yaw +0,10 rad, jalur 1/2/3; ditambah satu pengulangan seed 91.
- Satu regresi kualifikasi nominal dengan motor-off.
- Satu ARENA berarus 0,02 m/s dengan hold aktif.

Setiap run hold ditahan hingga setidaknya 35 detik setelah DONE. Evaluator mengukur drift XY/depth pada 30 detik terakhir sebelum injeksi abort: batas XY 0,10 m dan depth 0,03 m. Fase settling awal tidak termasuk jendela ini. Setelah itu fault uji `verification_surface_hold_stop` dikirim melalui topic guard, dan gaya thruster harus turun ke nol serta disarm terkunci. Hasil misi sebelum injeksi disimpan; hasil referee sesudah injeksi dicatat terpisah. Batas akurasi estimasi tetap XY 0,20 m, depth 0,03 m dan yaw 0,03 rad.

Percobaan pertama pada `evidence/surface-hold-diagnostic/` lulus hold/abort, tetapi publisher fault uji memakai QoS yang tidak diterima beberapa subscriber. QoS uji disesuaikan dengan STATUS_QOS sebelum batch final. Output lama dipertahankan sebagai diagnostik, tidak menggantikan hasil final.

## Hasil akhir

Keempat kasus prior posisi lulus: galat maksimum 0,147103 m (jalur 1), 0,144465 m (jalur 2), 0,182372 m (jalur 3), dan 0,150861 m (pengulangan jalur 3). Margin terburuk terhadap ambang 0,20 m adalah 0,017628 m. Koreksi kamera bersifat oportunistik: seed 91 run pertama menerima nol koreksi, sedangkan pengulangannya menerima 16; karena syarat pengamatan ketat, koreksi visual tidak dijamin pada setiap run. Ini bukti pada empat kasus tersebut, bukan jaminan semua kesalahan prior atau timing kamera.

Ketiga hold kualifikasi lulus; drift XY jendela 30 detik adalah 0,019911 / 0,005287 / 0,020086 m untuk seed 7/42/91. Seluruhnya membuktikan gaya aktif sebelum fault dan disarm/gaya nol setelah fault. Regresi nominal motor-off juga lulus.

| Kasus | Galat XY maksimum (cm) | Koreksi gate | Drift hold 30 s (cm) |
| --- | ---: | ---: | ---: |
| nominal-motor-off | 2.58 | 2 | — |
| prior-91 | 18.24 | 0 | — |
| hold-7 | 3.17 | 6 | 1.99 |
| hold-42 | 2.36 | 3 | 0.53 |
| hold-91 | 3.38 | 11 | 2.01 |
| prior-7 | 14.71 | 8 | — |
| prior-42 | 14.45 | 5 | — |
| prior-91-repeat | 15.09 | 16 | — |
| arena-hold | 6.61 | — | 1.19 |

Semua sembilan run terpilih lulus misi, referensi akurasi, pemisahan ground truth dan shutdown bersih. Lima run motor-off mematikan gaya thruster. Empat run hold membuktikan gaya aktif selama hold, lalu disarm terkunci dan gaya nol setelah injeksi fault. ARENA menyelesaikan gate, flare, payload blue drum dan surface dengan `stop_mode=surface_hold`.

Sebagai pembanding yang mencakup fase settling serta sesudah abort, perpindahan XY maksimum dari SURFACE hingga shutdown pada keempat run hold adalah 2,82–4,52 cm. Angka ini tidak menggantikan kriteria jendela hold sebelum abort; kedua fase dicatat terpisah di JSON.

Bukti: [8 kualifikasi dan ARENA yang timeout](../ros2_ws/evidence/surface-hold-and-gate-final-2027/summary.json), [rerun ARENA lulus](../ros2_ws/evidence/surface-hold-arena-final-2027/summary.json), [build terakhir](../ros2_ws/evidence/surface-hold-arena-final-2027/build.log), [130 tes unit](../ros2_ws/evidence/surface-hold-arena-final-2027/unit-tests.log). `evidence/` adalah artefak lokal yang diabaikan Git.

## Menjalankan

```bash
cd /home/rasya/AUV/ros2_ws
# Kualifikasi dengan hold aktif setelah surface
bash tools/ros.sh launch sauvc_sim arena.launch.py autonomous:=true surface_hold:=true
# ARENA dengan hold aktif setelah surface
bash tools/ros.sh launch sauvc_sim arena.launch.py arena:=finals autonomous:=true surface_hold:=true
```

Jalankan satu simulator setiap kali. Untuk motor-off gunakan `surface_hold:=false` (default). Status hold dapat dilihat dengan `bash tools/ros.sh topic echo /sauvc/surface_hold/status`. Ctrl+C menutup simulasi. Ini tidak mengaktifkan hardware nyata.

Harness menerima `--surface-hold`; parameter ini hanya untuk pengujian dinamis tanpa fault awal karena uji abort dilakukan setelah jendela hold. Gunakan folder output baru:

```bash
bash tools/ros.sh python tools/check_qualification.py --vehicle-model dynamic --surface-hold --conditions evidence/dvl-restraint-final-q-current-7/q-current-7-conditions.json --output evidence/hold-recheck-01/result.json
```

Keseluruhan matriks berada dalam `run.py` di folder bukti. Runner memeriksa hash source sebelum setiap kasus dan menolak menimpa hasil lama. GUI/POV, arus yang lebih besar, seluruh matriks historis, gate acak dan kendaraan nyata tidak diuji pada tahap ini.
