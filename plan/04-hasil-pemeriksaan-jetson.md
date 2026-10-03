# Hasil pemeriksaan awal Jetson

Diperiksa langsung pada perangkat: 1 Oktober 2026. [Bukti perintah dan keluarannya](evidence/jetson-inventory-2026-10-01.json). Pemeriksaan bersifat baca-saja; perubahan hanya pada dokumentasi workspace. Instalasi BlueOS belum dilakukan.

## Perangkat dan lingkungan

| Komponen | Hasil | Dasar pemeriksaan |
| --- | --- | --- |
| Model menurut sistem | NVIDIA Jetson Orin NX Engineering Reference Developer Kit | `/proc/device-tree/model` |
| Identitas konfigurasi board | `p3768-0000+p3767-0000`, Tegra234 | Device tree; identitas fisik carrier belum diperiksa |
| RAM | Kelas 16 GB; Linux melaporkan sekitar 15 GiB | `free -h`; bersama identitas P3767-0000 konsisten dengan Orin NX 16GB |
| OS | Ubuntu 22.04.5 LTS, Jammy | `/etc/os-release` |
| Arsitektur | aarch64 / ARM64 | Sistem dan klien Docker |
| Jetson Linux / L4T | 36.4.7 | `/etc/nv_tegra_release`, paket `nvidia-l4t-core` |
| Kernel | 5.15.148-tegra | Kernel aktif |
| CUDA runtime | 12.6.68 | Paket `cuda-cudart-12-6` |
| TensorRT | 10.3.0.30 | Paket `libnvinfer10` |
| Penyimpanan root | NVMe, partisi sekitar 116 GiB, tersedia sekitar 56 GiB saat diperiksa | `df -h /`; bukan kapasitas keseluruhan disk |
| Docker | Paket/klien 29.8.1; layanan aktif | Paket, `docker version`, systemd |
| Docker Compose | Paket plugin 5.5.1 | Database paket |
| NVIDIA Container Toolkit | 1.16.2 terpasang | Database paket; runtime GPU dalam container belum diuji |
| Jaringan host | NetworkManager aktif | systemd |
| Port TCP 80/443 | Tidak ada listener pada snapshot pemeriksaan | `ss`; tidak membuktikan BlueOS tidak terpasang pada port lain |

**Versi JetPack:** meta-package `nvidia-jetpack` tidak ditemukan terpasang. Jangan menyimpulkan seluruh SDK tidak tersedia: komponen CUDA/TensorRT ditemukan. NVIDIA menjelaskan JetPack 6.2.1 dengan CUDA 12.6/TensorRT 10.3 dan BSP awal 36.4.4; pengumuman NVIDIA menyebut 36.4.7 sebagai pembaruan BSP cabang JetPack 6. Catatan paling pasti untuk instalasi ini adalah **L4T 36.4.7 beserta versi komponennya**, bukan label minor JetPack yang ditebak. [JetPack 6.2.1](https://developer.nvidia.com/embedded/jetpack-sdk-621), [pengumuman NVIDIA](https://forums.developer.nvidia.com/t/jetpack-releases-with-security-fixes-cve-2025-33182-cve-2025-33177/347678).

Pemetaan P3767-0000 ke Orin NX 16GB juga dicantumkan dalam [release notes NVIDIA](https://developer.nvidia.com/downloads/embedded/l4t/r36_release_v2.0/docs/jetson_linux_release_notes_r36.2.0.pdf). Identifikasi melalui sistem tetap perlu dicocokkan dengan perangkat fisik sebelum pekerjaan flashing/carrier-specific.

## Kamera dan autopilot

**Klarifikasi pengguna:** saat pemeriksaan hanya Jetson yang tersedia; kamera dan Pixhawk belum ada di tempat pengujian. Karena itu, tidak terdeteksinya periferal sesuai kondisi yang dijelaskan, bukan temuan kegagalan driver. Kepemilikan perangkat yang disebut sebelumnya tidak berarti perangkat tersedia pada sesi ini.

- USB yang terlihat: hub Realtek, keyboard, dan mouse. Tidak ada kamera DWE atau Pixhawk yang teridentifikasi pada daftar tersebut.
- Tidak ditemukan `/dev/video*`, `/dev/ttyACM*`, `/dev/ttyUSB*`, atau identitas dalam `/dev/serial/by-id/` dan `/dev/v4l/by-id/`.
- V4L2 mendeteksi pengendali video Tegra `/dev/media0`, tetapi tidak menemukan perangkat capture `/dev/video0`. Ini bukan bukti kamera DWE siap digunakan.
- Ada UART host `/dev/ttyTHS1` dan `/dev/ttyTHS2`. Keberadaannya tidak membuktikan Pixhawk tersambung; UART tidak diprobe dalam pemeriksaan ini.
- Model Pixhawk dan ketiga kamera tetap belum teridentifikasi. Kesimpulan terbatas pada perangkat yang terdeteksi saat pemeriksaan, bukan status inventaris kepemilikan tim.

## Hambatan akses Docker

**Pembaruan setelah inventaris:** pengguna telah memberikan ACL Docker kepada `aero`. Hambatan di bawah adalah kondisi awal dan sudah teratasi; hasil peluncuran BlueOS tersedia pada [laporan berikutnya](05-blueos-tanpa-periferal.md).

`docker ps` dan akses informasi server gagal dengan `permission denied`. Socket dimiliki `root:docker`, sementara grup sesi akun `aero` tidak memuat `docker`. Pemeriksaan baca-saja melalui `sudo -n` juga gagal karena memerlukan kata sandi.

Akibatnya, daftar container, versi server Docker, runtime NVIDIA aktif, dan kemungkinan instalasi BlueOS sebelumnya belum diketahui. Tidak ada perubahan izin socket, keanggotaan grup, konfigurasi layanan, atau jaringan.

## Langkah kerja berikutnya

1. Sediakan akses administratif lokal yang sesuai untuk pemeriksaan/operasi Docker; kata sandi tidak perlu dikirim lewat percakapan. Sesudah tersedia, periksa container yang sudah ada sebelum menambah instalasi.
2. Tentukan konfigurasi BlueOS ARM64 yang sesuai dengan host Ubuntu/NetworkManager serta kebutuhan port dan perangkat. Tinjau installer/konfigurasi sebelum dijalankan pada Jetson yang sedang digunakan ini.
3. Uji antarmuka dan layanan BlueOS yang tidak memerlukan periferal; pisahkan indikator perangkat belum tersambung dari kegagalan platform.
4. Saat perangkat tersedia, sambungkan satu kamera DWE untuk pengujian capture; identifikasi Pixhawk dan firmware, lalu uji pembacaan telemetri.
5. Setelah satu kamera stabil, lanjutkan uji dua/tiga kamera sesuai [rencana kamera](03-opsi-kamera.md).

P0 selesai untuk identifikasi lingkungan Jetson; P0 perangkat periferal masih menunggu deteksi/akses perangkat. Hasil ini belum menyatakan BlueOS kompatibel atau telah berjalan.
