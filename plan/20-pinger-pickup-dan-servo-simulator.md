# Pinger, pickup dan servo pada simulator

Tanggal: **25 Oktober 2026, Asia/Jakarta**. Implementasi berada di `/home/rasya/AUV/ros2_ws`. Mode tambahan diaktifkan dengan `extended:=true`; mode blue drum biasa tetap tersedia. Ini pengembangan simulator dan rancangan mekanik, tanpa mengirim PWM atau mengaktifkan perangkat fisik.

## Acuan tugas

[Rulebook resmi](https://sauvc.org/rulebook/) yang diperiksa masih 2026 v6.1.0. Red drum dengan pinger bernilai 50 poin. Reacquisition memerlukan acquisition yang berhasil, pelintasan penuh gate tambahan setelah acquisition, pengambilan bola yang sama dan retensi sampai akhir. Mode tambahan mengikuti urutan ini setelah tugas Navigation dan flare.

## Pinger virtual

Plugin native menempatkan sumber pada salah satu red drum yang dipilih fixture. Empat hidrofon virtual berada pada body `(±0,1,0,0)` dan `(0,±0,1,0)` m. Paket `/sauvc/acoustics` hanya berisi `time`, `frequency_hz=45000` dan empat `tdoa_s` terhadap hidrofon pertama; tidak ada koordinat sumber, indeks drum atau range ground truth.

Asumsi kecepatan suara 1500 m/s dan noise Gaussian TDOA 0,2 µs. [acoustics.py](../ros2_ws/src/sauvc_sim/sauvc_sim/acoustics.py) menghitung bearing far-field dan perpotongan least-squares sinar pada XY menggunakan pose bertimestamp. Geometri yang kurang terobservasi/stasioner, data invalid, frekuensi salah atau timestamp mundur ditolak. Controller memakai estimasi tersebut untuk alignment ke drum, sementara referee mengetahui fixture secara terpisah untuk menilai drum yang benar.

Ini model geometrik waktu tiba, bukan simulasi propagasi gelombang, pantulan/multipath, attenuation atau hydrophone/ADC nyata. Pose ARENA masih ground truth; belum estimator sensor seperti kualifikasi dinamis. Badan diasumsikan hampir datar untuk estimator bearing XY.

## Pelepasan dan pickup

Pelepas satu bola kini mempunyai slew sudut virtual 0→120° selama 0,4 s; bola baru dibebaskan setelah bukaan tercapai. Setelah pelepasan, gravitasi/collision menggerakkan bola. Request release berulang tidak membuat bola baru atau mengembalikan bola ke kendaraan. Penyangga dan sudut ini adalah aktuator ideal, bukan simulasi linkage atau torsi servo fisik.

Alat pickup memakai dua jari dan atap dengan collision di belakang badan. Close saja tidak menangkap bola: plugin harus mengamati kontak dengan `payload_ball` yang sudah dilepas, kemudian membuat fixed `DetachableJoint` antara link kendaraan dan link bola yang sama. Tidak ada set-pose bola saat pickup/lift. Open menghapus sambungan sehingga gravitasi kembali menjatuhkan bola. Sambungan fixed merepresentasikan latch ideal, bukan gaya gesek jepitan.

Titik drop **(+0,20, 0, −0,18) m** dan titik pickup **(−0,20, 0, −0,45) m** dipisahkan agar alat tidak menahan bola saat drop. Alat permanen diperhitungkan dalam envelope referee untuk dasar/dinding/gate. Kedalaman mode tambahan lebih dangkal dekat ujung kolam dan sekitar −0,8 m di lintasan gate. Koreksi roll/pitch dari odometri menjaga level setelah interaksi collision; pembatas dan timeout command guard tetap berlaku. Koreksi ini khusus ARENA ideal; kualifikasi dinamis tidak mendapat kendali roll/pitch baru.

## Pelintasan dan retensi independen

Controller kembali ke gate setelah acquisition, melintasinya penuh, lalu kembali melalui gate menuju drum. Referee memeriksa bukaan gate dan perubahan sisi seluruh envelope; perpindahan di bagian lain kolam tidak memberi kredit pelintasan. Kontak gate tetap menggagalkan latihan.

Bukti pickup memerlukan sambungan native dan bola dekat titik alat dalam posisi world aktual. Retensi harus konsisten >0,5 s dan tetap valid saat surface. Jika sambungan hilang atau bola menjauh, kredit reacquisition dicabut. Controller tidak menerima koordinat bola native; hanya status acquisition/pelintasan/grasp/retensi. Pada pickup, alignment kembali menggunakan estimasi posisi target yang disimpan saat drop. Ini asumsi bola menetap dalam drum, bukan detektor visual bola kecil.

## Rancangan mekanik dan batas fisik

[Dropper](../mechanical/payload-servo/dropper.scad), [pickup](../mechanical/payload-servo/pickup.scad) dan [catatan mekanik](../mechanical/payload-servo/README.md) adalah konsep parametrik. Fabrikasi, render OpenSCAD, pemilihan servo, linkage, bearing, housing waterproof, endpoint PWM, catu daya serta uji meja/basah belum dilakukan. Belum ada perangkat servo/driver yang ditentukan. Uji simulator tidak membuktikan kemampuan hardware tersebut.

## Menjalankan

```bash
cd /home/rasya/AUV/ros2_ws
bash tools/ros.sh build --symlink-install
# Mode tambahan: pinger otomatis dipilih pada red drum pertama
bash tools/ros.sh launch sauvc_sim arena.launch.py arena:=finals autonomous:=true extended:=true
# Fixture lain
bash tools/ros.sh launch sauvc_sim arena.launch.py arena:=finals autonomous:=true extended:=true scene_variant:=1 blue_drum:=3 pinger_drum:=4 flare_order:=Y-B-R
# Misi blue drum sebelumnya
bash tools/ros.sh launch sauvc_sim arena.launch.py arena:=finals autonomous:=true
```

Diagnostik: `/sauvc/arena/physics` memuat sudut servo, kontak pickup, status sambungan dan posisi bola untuk referee/logger. `/sauvc/arena/result` memuat status tugas dan rincian skor. Bukti lokal berada di `evidence/arena-extended/`; percobaan gagal dipertahankan.


## Penerimaan akhir

**Selesai pada simulator untuk dua fixture yang diuji.** Build final dan validasi SDF lulus. **84 tes unit** lulus, termasuk triangulasi, geometri tidak terobservasi, input invalid/stale, batas tool, pelintasan aperture, kehilangan retensi dan koreksi level. Bukti: [verification.json](../ros2_ws/evidence/arena-extended/verification.json).

| Skenario | Sumber pinger | Hasil | Skor attempt | Penutupan |
| --- | --- | --- | --- | --- |
| Nominal; B-R-Y | Drum 2 (red) | DONE / COMPLETE | 270.13132 | Bersih |
| Alternatif; Y-B-R | Drum 4 (red) | DONE / COMPLETE | 270.74440 | Bersih |

Keduanya memperoleh 50 poin acquisition pinger dan 60 poin reacquisition, tanpa penalti. Harness tambahan menghitung ulang total dari event START/SURFACE, memeriksa urutan acquisition → gate tambahan → grasp → surface, serta memastikan sambungan dan posisi bola tetap mengikuti alat sampai surface. Galat akhir estimasi pinger pada dua run ini dihitung oleh harness terhadap fixture, tidak dikirim balik ke controller. Angka per run dan jumlah sampel retensi tercatat dalam JSON; bukan jaminan akurasi hardware.

[Uji mekanisme akhir](../ros2_ws/evidence/arena-extended/physics-final.json) lulus: bola tertahan, sudut servo bergerak sebelum drop, flare jatuh, payload menetap >0,5 s, release berulang tidak rearm, close saat meleset tidak attach, kontak memungkinkan pickup, lift membawa bola yang sama, open melepas sambungan dan bola benar-benar jatuh. Harness mekanisme ini mengatur pose untuk mengisolasi perilaku; misi penuh tidak memakai teleport.

[Regresi default](../ros2_ws/evidence/arena-extended/default-regression.json) juga lulus, skor 190,31486 dan shutdown bersih. Beberapa percobaan awal gagal karena alat memotong jalur drop/dasar kolam, pembacaan bidang gate yang terlalu membatasi lintasan setelah Navigation, serta kontak crossbar akibat perubahan sikap. Posisi alat, kedalaman dan koreksi level diperbaiki; kriteria kontak/pelintasan tidak dilonggarkan. Run `mission5` membuktikan tugas lengkap tetapi gagal shutdown sehingga tidak dihitung sebagai penerimaan akhir. Ulangan nominal-final menggunakan pause setelah penilaian, drain callback, lalu stop server dan lulus. Semua percobaan awal dipertahankan.

Batas yang tersisa adalah fabrikasi/kalibrasi servo serta sensor akustik nyata, model torsi/jepitan/air yang terkalibrasi, dan pengujian kolam. Belum ada wiring/PWM aktif atau pengukuran DWE/hidrofon nyata.


## Catatan konfirmasi perangkat

**Konfirmasi pengguna — 25 Oktober 2026:** model servo, tegangan/catu daya, driver dan kanal flight controller belum dapat dikonfirmasi. Statusnya **belum dikonfirmasi**, bukan dipastikan belum tersedia. Rancangan tetap parametrik; wiring, pemilihan pin/kanal, endpoint PWM dan kalibrasi servo fisik menunggu spesifikasi perangkat. Tidak ada output hardware yang diaktifkan.
