# 47 — Shutdown POV kamera

Tanggal: 3 November 2026. Status: penerimaan kualifikasi dan ARENA GUI lulus; dua percobaan gagal sebelumnya dipertahankan.

## Masalah dan pilihan

Penampil RQt sebelumnya memerlukan cleanup paksa. Pemeriksa menghentikan grup dengan SIGTERM, menunggu launcher saja, lalu langsung SIGKILL jika grup masih ada. Probe alternatif `image_tools/showimage` menerima kedua aliran tetapi tidak memberi shutdown andal di host ini: uji SIGINT menghasilkan crash satu proses dan proses lainnya masih hidup saat pemeriksaan. Bukti alternatif dipertahankan, tidak digunakan sebagai penerimaan.

## Perubahan

`tools/pov_viewer.py` memakai Qt binding yang sudah terpasang dan decoder RGB/BGR yang sudah ada, dalam satu proses ROS/Qt per kamera. Tidak menambah library eksternal. Subscriber memakai sensor-data QoS; tombol tutup, SIGINT dan SIGTERM keluar melalui event loop Qt, lalu node/context ROS dihentikan pada finally. Penampil tidak membuka kamera langsung dan tidak ikut mengendalikan kendaraan.

Kedua checker menggunakan perintah viewer bersama. Verifikasi subscriber memakai nama node kamera yang tepat, dan pemeriksa jendela tetap membatasi pada PID milik proses uji. ARENA kini juga mewajibkan dua jendela terdeteksi. Cleanup paksa pada viewer menyebabkan penerimaan gagal, bukan hanya dicatat. `package.xml` menyatakan dependensi `python_qt_binding`; panduan running diperbarui ke penampil baru.

Pada penerimaan kedua, proses GUI Gazebo masih memerlukan SIGKILL meski kedua POV berhenti bersih. Checker kini meminta penutupan jendela Gazebo melalui X11 sebelum menghentikan server; pemilihan jendela dibatasi pada PID turunan launch milik pengujian. Jika jendela tidak tersedia atau penutupan belum selesai, jalur penghentian server dan fallback sebelumnya tetap tersedia.

## Verifikasi

- 174 tes unit lulus, termasuk penolakan kamera yang tidak dikenal, pembatasan jendela pada proses milik uji, serta penutupan GUI ketika jendela tersedia/tidak tersedia atau wait timeout.
- Probe dua aliran sintetis: masing-masing satu subscriber, dua jendela terdeteksi/diatur, kedua viewer exit 0 dan daftar cleanup paksa kosong.
- Kualifikasi dinamis lane 1 seed 7, GUI + dua POV: lulus; pelintasan kedua 26,392 detik, start–surface 29,452 detik, start–stop 33,838 detik; galat XY maksimum 2,76 cm.
- ARENA blue drum dinamis seed 7, GUI + dua POV: lulus; thrust–surface 226,374 detik, skor 210,20878, penalti 0; galat XY maksimum 4,53 cm. Kontak flare, payload masuk drum, Square dan stop terverifikasi.
- Kedua penerimaan memakai snapshot source yang sama, dua jendela dan nama subscriber front/bottom tepat, `gui_close_requested=true`, `pov_cleanup_forced_groups=[]`, `shutdown_forced=false`, dan `shutdown_clean=true`. Checker serta kedua probe exit 0; diagnosis window aktif tidak menemukan stale sensor. File controller/estimator/fisika sama dengan penerimaan laporan 46.

Percobaan awal kualifikasi GUI abort `gate_lost` saat alignment. Percobaan kedua menyelesaikan misi tetapi GUI Gazebo memerlukan SIGKILL, sehingga keduanya **tidak diterima**. Sesudah perbaikan urutan penutupan, dua misi GUI diterima. `gate_lost` belum ditetapkan penyebabnya dan tidak diklaim diperbaiki. Diagnosis offline window thrust–ABORT pada percobaan pertama mengklasifikasikan `no_stale_sensor_event`.

Bukti: `ros2_ws/evidence/pov-shutdown-2027/`, terutama `direct-qt/probe.json`, `unit-tests-final3.log` dan `gui-close-first/summary.json`. Probe sintetis membuktikan lifecycle viewer, bukan penyelesaian misi.

## Batas

Pengaturan posisi jendela diuji pada X11. Wayland dan Jetson GUI belum diuji. Uji ini tidak mengubah controller, estimator, fisika atau konfigurasi Pixhawk.

Verifier akhir dengan assert dan SHA-256: [verification.json](../ros2_ws/evidence/pov-shutdown-2027/verification.json). Ringkasan penerimaan: [GUI close-first](../ros2_ws/evidence/pov-shutdown-2027/gui-close-first/summary.json). Capture seluruh desktop tidak digunakan sebagai bukti viewer.
