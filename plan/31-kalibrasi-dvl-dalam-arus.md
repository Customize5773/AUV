# 31 — Kalibrasi DVL dalam arus dengan penahan preflight

29 Oktober 2026. Lingkup hanya koreksi kalibrasi DVL dalam arus dari [laporan 30](30-pengujian-keandalan-berulang.md). **Selesai untuk prosedur preflight tertahan di simulator:** keempat kasus arus dan satu regresi nominal memenuhi referensi akurasi. Kalibrasi kendaraan yang sudah bebas hanyut belum tercakup.

## Penyebab dan perbaikan

Kalibrasi lama merata-ratakan DVL selama preflight ketika kecepatan terukur di bawah 0,02 m/s dan gyro rendah. Drift lambat dalam arus memenuhi syarat tersebut, sehingga gerakan dianggap bias. Kecepatan konstan dan bias tidak dapat dipisahkan hanya dari DVL serta gyro/akselerometer yang tenang.

Simulator sekarang memodelkan prosedur kendaraan **ditahan pada titik penempatan selama kalibrasi**, menggunakan fixed joint ke penopang statis tanpa geometri collision. Ini perubahan kondisi penempatan yang eksplisit. Bukan algoritme kalibrasi kendaraan bebas hanyut. Penopang menyeimbangkan beban selama tertahan; gaya tidak diantrekan pada badan terkunci agar tidak menghasilkan impuls saat pelepasan. Penahan dilepas pada perintah thrust pertama dan tidak dipasang kembali ketika STOP/DONE. Arus tetap dikonfigurasi sepanjang run, dan kendaraan bebas mengalami drag arus setelah dilepas.

Packet sensor menambahkan boolean `deployment_held` dari keberadaan sambungan penahan. Estimator hanya mempelajari bias jika sinyal ini benar, selain pemeriksaan kecepatan/gyro yang sudah ada. Sinyal hilang/tidak tersedia tidak mengizinkan sampel kalibrasi baru. Pelepasan penahan setelah pengambilan sampel, aktivasi misi, atau perintah gerak membekukan bias. Posisi ground truth dan nilai bias buatan sensor tidak diberikan sebagai koreksi estimator.

Penggunaan di kendaraan nyata memerlukan prosedur penahan serta konfirmasi independen yang sesuai. Jangan mengirim `deployment_held=true` hanya berdasarkan kecepatan DVL kecil. Kalibrasi pada kendaraan yang sudah bebas hanyut tetap memerlukan referensi tambahan dan belum diselesaikan oleh perubahan ini.

## Verifikasi

Build native/ROS berhasil. **121 tes unit lulus**, termasuk penolakan drift lambat tanpa konfirmasi penahan dan pembekuan bias setelah penahan dilepas. Uji runtime mencatat pose fisik selama ditahan untuk membuktikan bahwa referensi diam benar-benar terwujud; ground truth hanya digunakan dalam evaluasi.

Percobaan awal `evidence/dvl-restraint-q7/` tidak mencapai simulasi karena socket ROS/Gazebo diblokir sandbox. Percobaan `evidence/dvl-restraint-q7-runtime/` menemukan lonjakan saat penahan dilepas akibat antrean gaya pada badan terkunci; hasil gagal dipertahankan. Perbaikan menahan penerapan wrench selama penopang masih aktif, lalu menjalankan fisika gaya normal setelah pelepasan. Hasil versi akhir disimpan dalam folder `evidence/dvl-restraint-final-*` yang terpisah.

## Batas lingkup

Station keeping setelah surface, toleransi prior posisi, optimasi waktu, persepsi, dan hardware tidak diubah. Kriteria diam akhir dan batas galat tetap sama; kasus arus dapat gagal pemeriksaan diam walaupun masalah kalibrasi sudah diperbaiki. Kelulusan akurasi dilaporkan terpisah dari penerimaan misi keseluruhan.

## Hasil versi akhir

Semua run memakai source yang sama, menyelesaikan misi, menghasilkan perintah/gaya akhir nol, kontrol sensor-only dan shutdown bersih. Referensi akurasi tetap XY 0,20 m, kedalaman 0,03 m dan heading 0,03 rad; semuanya lulus. Perbandingan berikut mengubah prosedur preflight menjadi tertahan, dengan seed dan arus yang sama seperti kasus laporan 30.

| Kasus | Galat XY maksimum sebelum | Sesudah | Penerimaan keseluruhan |
| --- | ---: | ---: | --- |
| Kualifikasi arus +Y 0,02 m/s, seed 7 | 0,3969 m | 0,0275 m | Gagal diam akhir; akurasi lulus |
| Kualifikasi arus +Y 0,02 m/s, seed 42 | 0,3680 m | 0,0187 m | Gagal diam akhir; akurasi lulus |
| Kualifikasi arus +Y 0,02 m/s, seed 91 | 0,3254 m | 0,0431 m | Gagal diam akhir; akurasi lulus |
| Kualifikasi tanpa arus, seed 7 | 0,0285 m | 0,0210 m | Lulus |
| ARENA arus +X 0,02 m/s, seed 42 | 1,0594 m | 0,0651 m | Lulus |

Jadi **5/5 misi dan referensi akurasi lulus, 2/5 penerimaan keseluruhan lulus**. Tiga kegagalan diam tetap dicatat; kriteria tidak dilonggarkan. Kelulusan diam pada satu run ARENA hanya berlaku untuk jendela pengamatan harness dan bukan bukti station keeping aktif atau diam selamanya dalam arus.

Ground truth evaluator menunjukkan perpindahan badan 0 m selama penahan aktif pada seluruh lima run. Pelepasan terjadi bersamaan dengan thrust pertama dan tidak ada relatch. Rata-rata DVL horizontal selama tertahan mendekati bias instrumen; pada ARENA, bias yang dipelajari adalah (+0,000880; −0,000998) m/s dari 72 sampel, dibanding bias virtual (+0,001; −0,001) m/s. Nilai bias virtual tersebut hanya dipakai untuk evaluasi setelah run. Sebelumnya komponen lateral ARENA dipelajari menjadi −0,01115 m/s akibat drift preflight.

Bukti lokal: [verification.json](../ros2_ws/evidence/dvl-restraint-verification/verification.json), [build](../ros2_ws/evidence/dvl-restraint-verification/build.log), [121 tes unit](../ros2_ws/evidence/dvl-restraint-verification/unit-tests.log). JSON mencatat hash source/library native, kondisi, bukti penahan, referensi report setiap run dan hasil sebelum/sesudah. Artefak `evidence/` diabaikan Git; laporan tidak menyatakan seluruh matriks 19 kasus telah diulang.

## Mengulang pengujian

Perintah launch biasa tetap sama. Untuk satu kasus, gunakan folder output baru:

```bash
cd /home/rasya/AUV/ros2_ws
bash tools/ros.sh build --symlink-install
bash tools/ros.sh python tools/check_reliability.py --case a-current --output evidence/dvl-current-recheck-01
```

Kasus lain yang diuji: `q-current-7`, `q-current-42`, `q-current-91`, dan `q-nominal-7`. Exit code 1 pada tiga kualifikasi arus mencerminkan kegagalan diam akhir, bukan kegagalan akurasi DVL pada hasil versi ini.
