# Platform ROS 2 HydroShips

Package `auv2027_autonomy` berada di Git AUV2027 yang sama. ROS 2 Humble dijalankan dengan Python sistem; backend FastAPI tetap menggunakan virtualenv. Platform mengelola urutan tugas dan riwayat, belum menyediakan algoritme AUV, simulasi fisika, atau kendali Pixhawk.

## Operasi melalui aplikasi

Buka `http://127.0.0.1:8081/#autonomy`. Mulai runtime jika belum aktif, susun rencana, simpan, pilih skenario, lalu **Jalankan uji software**. Skenario sintetis mencakup berhasil, gagal, dan tidak merespons. Respons sintetis dikirim setelah sekitar 1,5 detik; timeout lebih pendek akan menggagalkan tahap.

Setiap tahap menunggu hasil dengan pasangan `run_id` dan `request_id` yang sesuai. Hasil duplikat, hasil tahap lama, dan hasil yang datang pada/setelah deadline tidak menyelesaikan tahap berikutnya. Timeout tahap atau batas total menghentikan misi. **Batalkan** mengakhiri uji aktif. **Hentikan runtime** menghentikan proses ROS; misi aktif ditandai `interrupted`. Restart runtime/aplikasi tidak melanjutkan atau memulai misi otomatis.

Rencana memiliki 1–16 tahap, nama maksimal 80 karakter, timeout tahap 1–600 detik, dan batas total 1–1800 detik. Ini batas aplikasi, bukan aturan kompetisi. Simpan menggunakan nomor revisi agar perubahan dari browser lain tidak tertimpa. SQLite menyimpan maksimal 100 eksekusi; browser menampilkan 20 terbaru. Unduhan JSON memuat snapshot rencana, skenario, status tiap tahap, waktu, dan jejak kejadian.

## Menjalankan dan membangun package

Layanan HydroShips menjalankan source package langsung, sehingga `colcon build` tidak diperlukan untuk UI. Untuk pemakaian sebagai package ROS 2:

```bash
cd /home/aero/AUV2027/hydroships/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select auv2027_autonomy --symlink-install
source install/local_setup.bash
ros2 run auv2027_autonomy platform
```

Jalankan hanya satu executor pada domain yang sama. Perintah standalone di atas tidak terhubung ke browser; hentikan runtime dari browser atau gunakan domain terpisah untuk eksperimen standalone. Jangan menjalankan kembali launch KKI atau workspace AGV untuk menghidupkan platform ini.

Konfigurasi lingkungan backend:

| Variabel | Default | Fungsi |
| --- | --- | --- |
| `HYDROSHIPS_ROS_ENABLED` | `0`, unit systemd memasang `1` | Menyalakan runtime saat layanan mulai; tidak menjalankan misi |
| `HYDROSHIPS_ROS_SETUP` | `/opt/ros/humble/setup.bash` | Setup ROS milik administrator |
| `HYDROSHIPS_ROS_DOMAIN_ID` | `0` | Domain DDS platform, harus sama dengan modul tugas |
| `HYDROSHIPS_ROS_TEST_TASKS` | `1` | `0` menonaktifkan node tugas sintetis untuk uji modul eksternal |

Untuk mengubah layanan terpasang, gunakan `systemctl --user edit hydroships.service`, isi `[Service]` dan `Environment=...`, lalu restart layanan. Runtime terdiri dari `mission_executor`, `console_bridge`, serta `software_test_tasks` jika diaktifkan, semuanya pada namespace `/auv2027`. Backend mengawasi proses, heartbeat, dan konfirmasi perintah. Jika backend mati, proses anak menerima SIGTERM; tidak ada mekanisme resume otomatis. Penghentian proses platform bukan pengganti mekanisme berhenti pada pengendali kendaraan eksternal.

## Kontrak modul tugas

Seluruh topic berikut bertipe `std_msgs/msg/String` berisi object JSON, QoS reliable/volatile, depth 10. Tidak diperlukan custom message atau rosbridge WebSocket.

| Topic | Arah | Isi |
| --- | --- | --- |
| `/auv2027/tasks/request` | Executor → modul tugas | Satu permintaan tahap, contoh di bawah |
| `/auv2027/tasks/result` | Modul tugas → executor | Hasil dengan ID yang sesuai |
| `/auv2027/tasks/cancel` | Executor → modul tugas | `run_id`, `request_id` yang harus dihentikan/dibersihkan |
| `/auv2027/mission/state` | Executor → console | `executor_id`, `mission` (snapshot atau null) |
| `/auv2027/mission/command` | Console → executor | `command_id`, `action` start/abort, payload |
| `/auv2027/mission/ack` | Executor → console | `command_id`, `accepted`, `run_id` atau `error` |

Contoh request:

```json
{"run_id":"UUID-eksekusi","request_id":"UUID-tahap","step_index":0,"task":"navigation","timeout":15,"mode":"software_test","scenario":"success"}
```

Modul mengembalikan salah satu hasil berikut menggunakan **ID persis dari request**, setelah pekerjaan selesai:

```json
{"run_id":"UUID-eksekusi","request_id":"UUID-tahap","status":"succeeded"}
```

```json
{"run_id":"UUID-eksekusi","request_id":"UUID-tahap","status":"failed","detail":"Target tidak ditemukan"}
```

`task` tersedia: `navigation`, `acquisition`, `reacquisition`, `localization`. Ini slot tugas, bukan implementasi deteksi/navigasi. `scenario` hanya mengatur respons driver sintetis; modul eksternal menentukan hasil berdasarkan pekerjaannya sendiri. Seluruh request saat ini tetap berlabel `software_test`.

Untuk memasukkan modul sendiri:

1. Matikan driver sintetis dengan `HYDROSHIPS_ROS_TEST_TASKS=0` dan restart HydroShips, atau gunakan `platform --external-tasks` untuk standalone.
2. Jalankan node modul pada domain yang sama. Subscribe request dan cancel; publish result. Modul harus menangani ID duplikat dan pembatalan, serta memiliki deadline lokal jika komunikasi/executor hilang.
3. Uji dengan data rekaman atau simulator. Tanpa modul yang merespons, misi harus timeout; tidak ada fallback keberhasilan sintetis.
4. Tambahkan adapter persepsi/navigasi/Pixhawk beserta pengujian terpisah sebelum penggunaan fisik. Belum tersedia mode eksekusi kendaraan pada platform ini.

Bridge juga membaca `/hydroships/mission/state` sebagai String dengan QoS best-effort untuk menampilkan state dari proyek ROV lama. Bridge tidak mengirim command ke sistem KKI, tidak menjalankan launch lamanya, dan tidak berlangganan gambar kamera atau mengeluarkan `cmd_vel`.

## Pengujian

Dari folder `hydroships/`:

```bash
env -u PYTHONPATH HYDROSHIPS_TEST_ROS=1 .venv/bin/python -m pytest -q
```

Tes ROS menggunakan domain 78. Pemeriksaan browser memerlukan layanan uji terpisah pada port 8083, domain 77, data sementara, dan driver sintetis aktif:

```bash
env -u PYTHONPATH HYDROSHIPS_PORT=8083 HYDROSHIPS_ROS_ENABLED=1 \
  HYDROSHIPS_ROS_DOMAIN_ID=77 HYDROSHIPS_DATA_DIR=/tmp/hydroships-autonomy-check \
  .venv/bin/python -m hydroships
# Terminal lain:
env -u PYTHONPATH .venv/bin/python scripts/check-autonomy-browser.py
```

Bukti dan batas validasi: [laporan platform autonomous](../../plan/09-platform-autonomous-ros2.md). Email maintainer `example.invalid` pada metadata package adalah placeholder, bukan alamat kontak tim.
