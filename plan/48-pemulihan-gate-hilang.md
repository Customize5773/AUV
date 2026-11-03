# 48 — Pemulihan deteksi gate yang hilang sementara

Tanggal: 3 November 2026. Status: koreksi skala terverifikasi; penerimaan GUI masih parsial karena satu abort kamera spontan.

## Temuan

Laporan 47 menyimpan satu abort `gate_lost` pada ALIGN. Rekaman menunjukkan kendaraan berhenti sekitar x=7,7 m dan melakukan pencarian yaw; diagnosis transport pada window aktif tidak menemukan stale sensor. Raw image serta keluaran detektor controller pada run gagal belum direkam, sehingga penyebab unik kegagalan historis tidak diklaim diketahui.

Ada cacat skala yang dapat diuji langsung: cabang pencarian outbound ketika deteksi tidak tersedia menghitung yaw 0,18*cos(...), lalu mengalikannya dengan speed_scale=8. Pada model dinamis, hasil dibatasi menjadi 0,7 rad/s. Cabang pencarian return sebelumnya sudah membagi speed_scale; cabang outbound belum. Rotasi pencarian yang terlalu cepat berpotensi membawa gate keluar FOV dan memperburuk kehilangan sementara.

## Perbaikan minimal

Hanya perintah yaw pencarian dinamis outbound dibagi speed_scale sebelum penskalaan akhir, sehingga laju fisiknya tetap 0,18*cos(...) rad/s. Mode ideal, approach, PASS, U-turn, surface, gaya tujuh thruster, estimator serta pengaman tidak diubah. Kehilangan deteksi tetap menghentikan maju dan abort setelah delapan detik; kebaruan kamera dan batas aktuator tetap.

Replay membandingkan implementasi sebelum/sesudah pada pose/observasi sama: perintah yaw awal 0,7 → 0,18 rad/s, maju tetap nol; keduanya abort `gate_lost` setelah deadline. Ini bukti koreksi cabang, bukan reproduksi penuh insiden Gazebo lama.

## Verifikasi

175 tes unit lulus. Tes baru memastikan kecepatan yaw fisik tidak berubah antara speed_scale 1/8 dan timeout delapan detik tetap mematikan perintah. Empat percobaan GUI lane 1 seed 7 dan satu headless dijalankan serial dengan source dibekukan serta observer native/ROS independen. Tiga GUI dan satu headless lulus; percobaan GUI ketiga abort `stale_camera`. Batch awal berhenti pada kegagalan tersebut; satu GUI dan headless dilanjutkan pada folder bukti baru. Hasil gagal tidak diganti atau dihitung sebagai lulus.

| Kasus | Hasil | Start–surface |
| --- | --- | --- |
| q-gui7-1 | Lulus | 26.178 detik |
| q-gui7-2 | Lulus | 27.186 detik |
| q-gui7-3 | Abort stale_camera | — |
| q-gui7-4 | Lulus | 26.786 detik |
| q-headless7 | Lulus | 26.600 detik |

Seluruh misi yang diterima memenuhi pelintasan penuh, surface, stop, akurasi, gaya akhir nol, diagnosis aktif tanpa stale sensor dan shutdown bersih; GUI juga memverifikasi dua POV tanpa cleanup paksa. Kasus gagal kamera tetap menghasilkan perintah/gaya nol dan shutdown bersih. Ini bukan bukti transport kamera selalu andal.

Uji tambahan `camera_loss` sengaja diinjeksikan sesudah thrust: checker exit 0, state ABORT, fault_verified, zero_command, thrusters_zero, stationary dan shutdown_clean semuanya benar. Ini membuktikan pengaman tetap aktif, bukan penyelesaian gangguan kamera spontan.

Bukti lokal: `ros2_ws/evidence/gate-search-2027/`, terutama `replay.json`, `unit-tests.log` dan `acceptance/summary.json`.

## Batas

Hasil simulator tidak membuktikan performa fisik. Belum mengoptimalkan thrust/kecepatan atau mengubah tuning approach; tidak mengubah konfigurasi Pixhawk. Penerimaan yang lulus tidak cukup untuk menganggap semua penyebab `gate_lost` sudah selesai.

Ringkasan akhir dengan assert bukti/hash dan status `partial_gui_acceptance`: [verification.json](../ros2_ws/evidence/gate-search-2027/verification.json). Hanya controller kualifikasi dan tesnya berbeda dari snapshot laporan 47; estimator, gaya, guard dan viewer identik. Langkah berikutnya adalah menentukan lokasi jeda kamera (produsen, bridge atau callback), bukan melonggarkan batas kamera.
