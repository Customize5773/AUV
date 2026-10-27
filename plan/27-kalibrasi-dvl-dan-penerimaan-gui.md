# 27 — Kalibrasi DVL dan penerimaan GUI/POV

28 Oktober 2026. Melanjutkan [laporan 26](26-arena-dinamika-dan-estimasi-sensor.md): mengurangi drift tanpa pose ground truth, kemudian menguji ARENA dinamis dengan Gazebo dan kedua POV aktif.

## Perubahan estimator

DVL sebelumnya mengintegrasikan bias kecepatan horizontal kecil selama seluruh run. Kalibrasi sekarang mengestimasi rata-rata bias XY dari sampel preflight saat kendaraan ditahan diam horizontal pada titik penempatan. Sampel ditolak jika kecepatan horizontal terukur ≥0,02 m/s atau gyro ≥0,03 rad/s. Minimal 20 pengukuran DVL diperlukan sebelum koreksi diterapkan; heave vertikal tidak dianggap bias nol.

Kalibrasi dilatch berhenti ketika state keluar WAIT/WAIT_READY atau perintah gerak nonzero diterima. Gerakan misi tidak boleh dilatih menjadi bias. Tidak ada koreksi posisi dari referee/ground truth, dan koefisien noise/drag/force plant tidak diubah. Jika sampel tidak cukup, koreksi bias tidak diterapkan; diagnostik health menyatakan jumlah sampel dan status kalibrasi.

**Asumsi penting:** kendaraan harus ditahan diam horizontal selama preflight. Bias DVL tidak dapat dibedakan dari gerakan riil yang pelan hanya dengan ambang tersebut; kalibrasi ini tidak boleh dipakai otomatis pada AUV yang hanyut dalam arus tanpa prosedur penahanan/rujukan diam yang sah. Runtime ini tetap simulator, bukan implementasi kalibrasi hardware yang sudah diuji.

Replay kausal atas rekaman laporan 26 membekukan kalibrasi pada waktu DIVE, hanya menggunakan pengukuran sensor sebelum waktu tersebut. Ground truth dipakai oleh evaluator setelah replay, bukan masukan estimator. Bukti `replay.json` membandingkan galat terhadap baseline; pengujian closed-loop baru tetap diperlukan karena lintasan dapat berubah.

## Pengujian GUI

Harness `check_arena.py --gui --pov` membuka Gazebo serta dua rqt image viewer. Harness memeriksa kedua proses tetap hidup selama loop misi dan endpoint subscriber kamera depan/bawah masih tersambung pada akhir. Jika viewer keluar selama misi, penerimaan gagal. Argumen --pov memerlukan --gui. Seluruh proses uji dimiliki harness, tanpa koneksi hardware.

Artefak lokal: [`evidence/arena-gui-calibration/`](../ros2_ws/evidence/arena-gui-calibration/). Screenshot hanya mengambil jendela simulator/viewer yang diuji. Uji perangkat lunak memeriksa pembekuan bias, preflight pendek/bergerak, serta perintah manual yang menghentikan kalibrasi.


## Penutupan viewer

Pada run penuh, launcher `ros2 run` berhenti setelah SIGTERM tetapi proses Qt masih hidup dalam grup yang sama. Harness kini memeriksa dan menghentikan seluruh grup miliknya, bukan hanya menunggu PID launcher. Proses yang tersisa diakhiri paksa; daftar grup dicatat sebagai `pov_cleanup_forced_groups`, terpisah dari status shutdown Gazebo. Ini tidak mengklaim destructor Qt/libproj pada mesin ini sudah diperbaiki.

Tes regresi membuat launcher dan anak yang sengaja mengabaikan SIGTERM, lalu memastikan anak tetap dihentikan meskipun launcher sudah keluar. Screenshot memakai isi drawable jendela viewer, agar jendela aplikasi lain yang menutupinya tidak ikut tersimpan. Bukti gambar yang dipertahankan hanya viewer yang telah diperiksa.


## Hasil run penuh dengan GUI dan kedua POV

| Misi | Status | Poin simulator | Thrust–surface | Galat XY maksimum baru | Run headless sebelumnya |
| --- | --- | ---: | ---: | ---: | ---: |
| Blue drum | Lulus | 210.25942 | 224.686 s | 0.1216 m | 0.2208 m |
| Pinger/pickup varian 1 | Lulus | 290.86800 | 204.400 s | 0.1694 m | 0.1548 m |

Keduanya mencapai DONE/COMPLETE, bonus Square +20, penalti 0, gaya tujuh thruster nol, stop nyata dan shutdown Gazebo bersih. Pinger/pickup mempertahankan bola yang sama hingga akhir. Kedua launcher viewer hidup selama loop pengujian, dan subscriber rqt depan/bawah terkonfirmasi pada akhir. Jendela viewer juga diperiksa langsung. Tidak ada abort stale_front/stale_bottom pada kedua run ini.

**Referensi galat tetap:** XY <0,20 m, kedalaman <0,03 m, heading <0,03 rad, dengan >50 sampel cocok waktu. Kedua run memenuhi referensi tersebut. Blue drum membaik jelas; galat maksimum dan RMS pinger pada run baru sedikit lebih besar daripada run headless lama, walaupun masih memenuhi referensi. Tidak ada klaim setiap metrik atau setiap lintasan membaik. Perbandingan bukan eksperimen arsitektur/benchmark waktu yang terisolasi: GUI, jadwal callback dan lintasan closed-loop dapat berbeda. Replay sensor kausal memisahkan pemeriksaan efek estimator dari run closed-loop baru.

Bias final XY terestimasi sekitar [0,001082; −0,000962] m/s dari 57 sampel preflight pada kedua run. Setelah aktivasi misi jumlah sampel/bias dibekukan. Noise plant tidak diubah dan tidak ada pemasukan koordinat ground truth ke estimator/controller.


## Regresi akhir dan bukti

**107 tes unit lulus.** Kalibrasi tidak mengubah batas validitas/timeout sensor atau menghilangkan pengaman. Empat run `pressure_loss`, `dvl_loss`, `actuator_loss`, `camera_loss` lulus sebagai uji penghentian: ABORT sesuai penyebab, perintah/gaya akhir nol, kendaraan stationary dan shutdown Gazebo bersih. Kamera_loss memutus penerimaan controller, sedangkan tiga lainnya memakai injeksi plant/sensor virtual seperti laporan 26.

Ketiga jalur kualifikasi lulus ulang dengan estimator baru:

| Jalur | Start–surface | Start–stop | Galat XY maksimum |
| --- | ---: | ---: | ---: |
| 1 | 33.242 s | 37.798 s | 0.0818 m |
| 2 | 28.892 s | 32.802 s | 0.0802 m |
| 3 | 28.508 s | 33.098 s | 0.0826 m |

Jalur 1 juga diulang sendirian setelah batch selesai: start–surface 27,328 s, stop 32,462 s, galat XY 0,0816 m. Run batch jalur 1 membutuhkan 33,242 s, terutama lebih lama di ALIGN sebelum pelintasan keluar. Variasi waktu tetap perlu benchmark pengulangan yang terkontrol; belum ada klaim kalibrasi mempercepat seluruh misi atau bahwa penyebab variasi waktunya sudah dipastikan.

Uji pendek `gui-cleanup-fault.json` menjalankan GUI + dua POV dengan injeksi DVL loss, memverifikasi pengaman serta cleanup grup viewer yang baru. Kedua grup Qt tersisa perlu SIGKILL setelah launchernya keluar; daftar grup tercatat terpisah dari shutdown bersih Gazebo. Pemeriksaan proses memastikan tidak ada simulator/viewer uji tertinggal.

[verification.json](../ros2_ws/evidence/arena-gui-calibration/verification.json) mencatat `mission_acceptance_passed=true` dan `all_arena_runs_meet_accuracy_reference=true` untuk dua fixture GUI ini. Ambang tidak diubah untuk meluluskan hasil. Bukti lama tetap tersedia pada laporan 26, bukan ditimpa. `replay.json`, `unit-tests.log`, file GUI/POV dan regresi berada pada folder bukti yang sama; folder evidence diabaikan Git.

Batas yang tetap berlaku: satu seed simulator dan dua fixture ARENA, bukan pembuktian semua gangguan/arus/layout; stall intermiten lama tidak dinyatakan hilang selamanya. Kalibrasi preflight mengasumsikan penempatan hampir level dan diam horizontal. Kamera/sensor DVL, mixer, thruster, servo/gripper, hidrofon serta kolam nyata belum divalidasi.

## Menjalankan verifikasi GUI

```bash
cd /home/rasya/AUV/ros2_ws
bash tools/ros.sh build --symlink-install
# Hentikan launch sebelumnya pada domain/partition yang sama.
bash tools/ros.sh python tools/check_arena.py --vehicle-model dynamic --gui --pov --output evidence/gui-verification/blue.json
# Untuk fixture alternatif pinger/pickup, gunakan output berbeda.
bash tools/ros.sh python tools/check_arena.py --vehicle-model dynamic --gui --pov --extended --scene-variant 1 --blue-drum 3 --pinger-drum 4 --order Y-B-R --output evidence/gui-verification/pickup.json
```

Harness menutup jendela setelah pemeriksaan. Panduan latihan tiga terminal: [CARA-RUNNING.md](../ros2_ws/CARA-RUNNING.md).
