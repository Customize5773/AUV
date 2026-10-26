# 24 — Migrasi dan uji arena SAUVC 2027

Tanggal: 26 Oktober 2026. Acuan aktif: [rulebook resmi SAUVC 2027.2.1](https://sauvc.org/rulebook/), diperiksa kembali langsung pada sesi ini; [arsip source/diagram](../doc/sources/rulebook-2027-published/README.md). Menggantikan status “simulator masih baseline 2026” pada laporan 21/23. Bukti lama tetap diberi edisi lama.

## Perubahan yang diterapkan

- Default launch, generator SDF dan harness misi adalah `2027`. Profil 2026 hanya dipilih eksplisit untuk regresi historis.
- Kolam 50 × 25 m, shelf −1,28 m dan dasar dalam −2 m; tiga jalur kualifikasi dengan gate menggantung sekitar 1 m dari permukaan.
- Start utama menghadap sisi kolam yang berbeda dari kualifikasi; transformasi dunia ↔ lokal ARENA menjaga proyeksi kamera, pinger, kontak dan referee konsisten.
- Gate utama 1,5 × 1,5 m, sekitar 12 m dari start; orange flare setinggi 1,5 m, mat target zone 8 × 2 m, empat drum dan Surfacing Square 2 × 2 m dengan marker biru 0,3 m bawah permukaan.
- Navigation wajib sebelum flare/acquisition. Tidak ada syarat kembali melalui gate untuk reacquisition 2027: seluruh envelope AUV harus keluar target zone sesudah acquisition, kemudian mengambil bola yang sama dan mempertahankannya hingga akhir.
- Timer ARENA dimulai dari Twist nonzero yang diterapkan ke simulator, bukan penempatan/START. Bonus Square 20 hanya sesudah Navigation, surface seluruh badan di dalam bukaan dan tanpa kontak frame. Bonus surface normal tetap 5.
- Kontak gate utama mengurangi 2 poin; bottom/wall 5 poin dengan ketentuan automatic abort. Kontak gate kualifikasi tetap menggagalkan kualifikasi. Orange tetap immediate abort.
- Pencarian flare menjangkau zona baru yang lebih luas. Asosiasi gate kualifikasi menolak gate tetangga berdasarkan posisi visual sebelumnya; pemilihan pasangan post juga memeriksa rasio lebar/tinggi proyeksi.
- Square dicari dari kamera; peta Square hanya menerima observasi mendekati arah normal frame untuk menghindari pasangan sudut yang memendek saat dilihat miring.

## Geometri latihan dan batas klaim

Ukuran yang disebut aturan diikuti. Posisi tepat start, flare, gate, drum, Square, ketebalan PVC dan breakpoint dasar adalah pilihan fixture latihan. Diagram resmi tidak berskala. Interpretasi shelf 1,8 m diikuti slope sepanjang 17,5 m dipakai untuk model, bukan ukuran kolam yang sudah disurvei.

Koordinat dunia X=0…50, Y=0…25; lokal ARENA U=Y, V=42−X. Mat lokal U=21…23, V=14…22. Square dunia (11,1; 7). Kualifikasi bergerak sepanjang +X, ARENA sepanjang +Y. Telemetri trajectory harness tetap dunia; posisi bola dan envelope pada referee ARENA adalah lokal U/V, ditandai `coordinate_frame=arena_UV`.

Konfigurasi tujuh thruster bersama HydroShips tetap T1–T4 horizontal, T5–T7 vertikal. Kualifikasi memakai model gaya dan estimasi tekanan/IMU/magnetometer/DVL virtual. **ARENA masih gerak ideal dan odometri ground truth**; misi lengkap bukan bukti thrust atau lokalisasi fisik. Pinger TDOA, servo/latch dan retensi adalah simulator. Servo, wiring, mixer fisik dan pengujian kolam tetap belum divalidasi.

## Bukti penerimaan

Ringkasan yang diperiksa ulang: [verification.json](../ros2_ws/evidence/rulebook-2027/verification.json). `mission_acceptance_passed=true` berlaku pada misi/fixture yang disebut; pengujian ketahanan sintetis dilaporkan terpisah dan belum seluruhnya lulus.

Artefak lokal: [`evidence/rulebook-2027/`](../ros2_ws/evidence/rulebook-2027/). Artefak diabaikan Git; laporan ini tetap tersedia pada clone baru, artefak tidak otomatis ikut.

Build package lulus; 96 tes unit lulus. SDF kualifikasi dan finals dinyatakan `Valid` oleh `ign sdf -k`. Pengujian mempertahankan fixture unit 2026 secara eksplisit dan menambahkan pemeriksaan perilaku 2027, bukan mengganti label hasil lama.

Run final blue drum dengan GUI (`blue-drum-gui-accept.json`) lulus, total 210,14458 poin, thrust–surface 228,514 s, Square +20 dan penalti 0. Run pinger/pickup (`pinger-pickup-accept.json`) lulus, total 290,69712 poin, thrust–surface 210,096 s, retensi bola dan Square +20, penalti 0. Keduanya stop aktual dan shutdown bersih. Angka ini untuk fixture yang diuji, bukan benchmark kendaraan nyata.

Uji kamera 2027 (`perception.json`) lulus pada 19 sudut pandang: gate, flare, drum, Square, jarak/sudut, crop, camera_info, overlay dan penolakan data stale. Dua pandangan blue flare segaris dengan blue drum pada run awal tidak terdeteksi; `perception-aligned-occlusion.json` disimpan sebagai keterbatasan yang belum diselesaikan. Run penerimaan menggunakan pandangan dengan target tidak bertumpuk. Uji perturbasi pada frame 2027 lulus 97 dari 98 pemeriksaan (`perturbations.json`); `blue-flare-far` gagal pada blur horizontal 3 piksel. Ini bukan klaim ketahanan semua sudut/occlusion/pencahayaan. Marker Square yang biru juga dapat menghasilkan kandidat `blue_flare`; controller membatasi asosiasi target/stage, tetapi classifier visual belum membedakan seluruh marker dari flare pada semua kondisi.

Uji fisika terisolasi (`physics.json`) lulus: bola flare jatuh setelah kontak, payload benar-benar menetap dalam drum, release berulang tidak mengisi ulang, close tanpa kontak tidak melekatkan, pickup kontak mengikat bola yang sama, lift mempertahankannya dan open melepasnya. Harness boleh memindah model untuk pengujian komponen; controller misi tidak melakukan teleport.

Percobaan gagal dipertahankan: `qualification-lane3.json` (asosiasi gate tetangga), `qualification-lane1.json` (gate hilang), `blue-drum-gui.json` (pencarian flare terlalu sempit), serta `pinger-pickup-final.json` (abort `stale_bottom` saat beberapa simulator berjalan bersamaan). Run awal `pinger-pickup.json` menyelesaikan pickup/retensi tetapi tidak mendapat bonus Square; bukan penerimaan bonus Square. Jangan menggantinya dengan klaim lulus menyeluruh.

| Run | Lulus | Hasil simulator |
| --- | --- | --- |
| Kualifikasi lane 1, build akhir | True | Start–surface 27.536 s; stop 32.466 s |
| Kualifikasi lane 2, build akhir | True | Start–surface 27.652 s; stop 32.616 s |
| Kualifikasi lane 3, build akhir | True | Start–surface 27.426 s; stop 32.560 s |
| ARENA pinger/pickup, varian 1 | True | 290.69712 poin; thrust–surface 210.096 s; Square +20, penalti 0 |

Semua run lulus di atas memiliki shutdown bersih. Waktu kualifikasi resmi berakhir pada pelintasan penuh kedua; start–surface dan stop adalah metrik proyek tambahan. Skor ARENA tidak memasukkan bonus inspeksi ukuran/berat.

## Menjalankan

```bash
cd /home/rasya/AUV/ros2_ws
bash tools/ros.sh build --symlink-install
# Kualifikasi: lane:=1/2/3
bash tools/ros.sh launch sauvc_sim arena.launch.py edition:=2027 autonomous:=true lane:=1
# ARENA blue drum, lalu Surfacing Square
bash tools/ros.sh launch sauvc_sim arena.launch.py edition:=2027 arena:=finals autonomous:=true
# Pinger, acquisition, keluar zona, pickup, retensi, Square
bash tools/ros.sh launch sauvc_sim arena.launch.py edition:=2027 arena:=finals autonomous:=true extended:=true
```

Hentikan satu mode sebelum memulai yang lain pada domain/partition yang sama. Tidak ada koneksi MAVLink atau output motor/servo hardware dalam run ini.
