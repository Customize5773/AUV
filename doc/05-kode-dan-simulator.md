# Kode, dataset, dan simulator yang relevan

Telaah dokumentasi publik: 1 Oktober 2026. Belum dilakukan instalasi, audit kode, reproduksi eksperimen, atau pengujian hardware.

| Proyek | Isi yang ditemukan | Nilai bagi persiapan | Batasan |
| --- | --- | --- | --- |
| [OpenMantaClaus](https://github.com/kushagra77/OpenMantaClaus) | Lima thruster; persepsi monokular, bearing-only EKF SLAM, pemilih misi, model/dataset YOLO; tautan BOM dan dokumentasi | Contoh alur persepsi → estimasi → eksekusi yang dikembangkan untuk SAUVC 2026 | Klaim biaya sekitar AUD 2.500 berasal dari pembuat, bukan penawaran harga bagi tim kita; ketersediaan setiap aset belum diaudit |
| [Nautilus-One](https://github.com/Offset-official/Nautilus-One) | Paket ROS 2, ArduSub, MAVROS, Gazebo Garden, ardupilot_gazebo, dan BehaviorTree; target SAUVC 2025/rulebook 5.1.4 | Pembanding arsitektur autopilot dan komputer pendamping | Arena, dependensi, dan asumsi misi lama perlu diperiksa |
| [AUV Society uwv-simulator](https://github.com/auvsociety/uwv-simulator) | ROS Noetic + Gazebo 11; lingkungan kolam SAUVC; model vec6; paket control, description, env; README menampilkan BSD-3-Clause | Referensi model thruster dan pengacakan properti arena | Berbasis ROS 1; bukan paket siap pakai untuk ROS 2 |
| [NYCU auv-control](https://github.com/BenTzuHsien/nycu-auv-control) | Kendali STM32F407 dengan IMU, DVL, sensor tekanan; pembagian lapisan tingkat tinggi dan kendali real-time | Referensi firmware dan pemisahan tanggung jawab kendali | Pembuat menyatakan lapisan ROS/perencanaan/visi tidak disertakan karena berkas hilang |
| [AUV Society — eksperimen DSO](https://github.com/auvsociety/sauvc-simulations/blob/master/docs/Using-DSO.md) | Dokumentasi dataset kamera, eksperimen odometri, masalah lintasan dan arah sumbu | Bacaan tentang eksperimen yang gagal dan keputusan mengurangi ketergantungan SLAM | Catatan lama; berkas dataset tertaut belum diunduh atau diperiksa |
| [SAUVC props](https://github.com/sauvc/props) | Dokumen properti 2022 dan foto gerbang, flare, area awal, serta lintasan | Referensi membuat properti latihan | Dimensi/warna historis tidak otomatis berlaku 2027 |
| [SAUVC GitHub](https://github.com/sauvc) | Repositori situs, rulebook, briefing, arsip, dan streaming | Jalur pemantauan perubahan dari penyelenggara | Commit baru belum tentu perubahan aturan yang berlaku |

**Usulan evaluasi sebelum memilih stack:** buat proyek uji terpisah, catat commit, baca lisensi kode dan dataset masing-masing, petakan versi OS/middleware/firmware, lalu uji satu sensor dan satu aktuator. Ukur waktu integrasi serta kualitas dokumentasi sebelum memutuskan migrasi seluruh sistem. Hindari menganggap README sebagai bukti keberhasilan reproduksi.
