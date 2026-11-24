# Akses Jetson langsung dari laptop — AUV-Link

Laptop membuat hotspot **AUV-Link**, Jetson menyambung ke laptop. Tidak memerlukan router, hotspot HP, atau internet untuk SSH.

| Perangkat | Alamat |
| --- | --- |
| Laptop (hotspot) | `10.42.77.1` |
| Jetson (Wi-Fi) | `10.42.77.2` |
| Jetson (Ethernet cadangan) | `192.168.2.2` |

Profil sudah disiapkan. Akun Jetson: `aero`; alias SSH laptop: `auv-wifi`.

## Cara praktis: Hubungkan Jetson (24 November 2026)

Cari **Hubungkan Jetson** di menu aplikasi laptop, atau jalankan:

```bash
python3 /home/rasya/AUV/tools/connect_jetson.py
```

Launcher mengaktifkan AUV-Link hanya jika belum aktif, menunggu SSH hingga sekitar dua menit, memeriksa folder proyek, lalu membuka VS Code. Hotspot tidak otomatis aktif setiap laptop boot agar Wi-Fi internet tidak diambil alih tanpa diminta. Simpan instruksi sebelum klik: chat dapat offline saat hotspot aktif. Jika key SSH memakai passphrase, muat ke ssh-agent terlebih dahulu; launcher tidak meminta password SSH interaktif.

**Profil boot sudah diterapkan dan diverifikasi lewat Ethernet pada 24 November 2026.** Perintah instalasi yang telah dijalankan (tidak perlu diulang):

```bash
ssh -t aero@192.168.2.2 'sudo bash /home/aero/configure-jetson.sh'
```

Hasil pemeriksaan langsung: autoconnect AUV-Link `yes`, priority `100`, retries `0` (tanpa batas), power saving `2` (nonaktif), IP `10.42.77.2/24`. Semua lima profil Wi-Fi lain memiliki autoconnect `no` (profil/password tidak dihapus). Koneksi aktif tidak diputus oleh script; Jetson masih memakai Wi-Fi lab saat verifikasi. Untuk transisi pertama, gunakan langkah Ethernet pada bagian 3 setelah hotspot laptop aktif; pada boot berikutnya Jetson diharapkan menunggu AUV-Link.

Rollback pengaturan profil Jetson ke nilai sebelum perubahan:

```bash
ssh -t aero@192.168.2.2 'sudo bash /home/aero/rollback-jetson.sh'
```

Salinan setup/rollback ada di laptop pada `~/.local/state/auv-link/`. Uji logika launcher: `python3 tools/test_connect_jetson.py` (5 tes lulus; tidak menyentuh jaringan). Uji jaringan dan boot ulang setelah penerapan masih perlu dilakukan.

Untuk penerimaan: setelah akses pertama berhasil, cabut Ethernet dan periksa SSH serta folder melalui VS Code. Kemudian simpan pekerjaan dan uji beberapa nyala ulang terkontrol dengan AUV-Link tetap aktif. Catat hasil SSH tiap percobaan; jangan menyimpulkan andal hanya dari status Wi-Fi connected.

## 1. Aktifkan koneksi

**Matikan hotspot HP "Realme" selama pengujian/akses.** Jangan sambungkan Wi-Fi laptop ke jaringan lain: itu menghentikan AUV-Link. Chat internet dapat offline selama akses berlangsung.

Jalankan dari terminal **laptop**:

```bash
nmcli --wait 20 connection up AUV-Link
```

Nyalakan Jetson setelah hotspot siap, lalu tunggu koneksi otomatis. Jika Jetson sudah menyala dan masih memakai jaringan lain, gunakan langkah Ethernet di bawah.

Uji sebelum membuka VS Code:

```bash
ssh -o ConnectTimeout=10 auv-wifi 'hostname; ls -ld /home/aero/AUV'
```

Lanjut hanya jika muncul `aero` dan informasi folder `/home/aero/AUV`.

## 2. Buka VS Code

Pasang extension **Remote - SSH** dari Microsoft, lalu jalankan di laptop:

```bash
code --new-window --remote ssh-remote+auv-wifi /home/aero/AUV
```

Indikator kiri bawah harus **SSH: auv-wifi**. Jika folder belum terbuka: **File → Open Folder…** → `/home/aero/AUV`.

**Terminal → New Terminal** menjalankan perintah di Jetson. File yang diedit berada di Jetson; salinan laptop tidak otomatis berubah. Pertahankan AUV-Link selama bekerja.

Untuk terminal saja:

```bash
ssh auv-wifi
cd /home/aero/AUV
```

### Jika muncul `Failed to download VS Code Server`

SSH dapat sudah berhasil, tetapi komponen VS Code untuk versi laptop belum lengkap di Jetson. Persiapkan komponen tersebut saat laptop memiliki internet dan Jetson terhubung melalui Ethernet; jangan mengubah profil Wi-Fi untuk memperbaiki error unduhan ini. Buka proyek melalui Ethernet terlebih dahulu:

```bash
code --new-window --remote ssh-remote+192.168.2.2 /home/aero/AUV
```

Remote-SSH biasanya mencoba unduhan di Jetson lalu beralih mengunduh di laptop dan menyalinnya. Setelah instalasi lengkap, akses AUV-Link dapat memakai server yang sama tanpa mengunduh ulang. Pembaruan versi VS Code laptop dapat memerlukan komponen versi baru; extension tertentu juga memerlukan internet. [Dokumentasi resmi](https://code.visualstudio.com/docs/remote/ssh).

**Perbaikan 24 November 2026:** server ARM64 `1.147.0`, commit `8a14f0cc1b08d531eb83255ea3764ae22aa932b5`, sudah tersedia di Jetson, tetapi CLI untuk commit itu belum ada. CLI resmi diunduh di laptop dan dipasang sebagai `~/.vscode-server/code-8a14f0cc1b08d531eb83255ea3764ae22aa932b5`; SHA-256 salinan cocok. Log uji VS Code melalui Ethernet menemukan instalasi yang ada dan berhasil membuat sesi remote tanpa unduhan ulang. Pengujian ulang melalui AUV-Link setelah perbaikan masih menunggu pengguna.

## 3. Jika Jetson belum tersambung

Pasang Ethernet laptop–Jetson sementara. Pastikan hotspot HP mati, lalu jalankan berurutan dari laptop:

```bash
nmcli --wait 20 connection up AUV-Link
ssh -t aero@192.168.2.2 'sudo nmcli --wait 60 connection up AUV-Link'
ssh -o ConnectTimeout=10 auv-wifi 'hostname; ls -ld /home/aero/AUV'
```

Masukkan password `sudo` akun `aero`. Pesan `Connection to 192.168.2.2 closed` setelah aktivasi berhasil adalah normal.

Setelah SSH wireless berhasil, cabut Ethernet dan ulangi tes SSH sebelum membuka VS Code. Jangan mengaktifkan ulang hotspot laptop di antara aktivasi Jetson dan tes SSH.

Jika masih gagal, periksa:

```bash
nmcli device status
ip route get 10.42.77.2
ssh aero@192.168.2.2 'nmcli device status; ip -4 addr show wlP1p1s0'
```

Kedua perangkat harus memakai `AUV-Link`. Rute laptop ke Jetson harus langsung melalui `wlp0s20f3` dari `10.42.77.1`, bukan melalui gateway Realme atau Wi-Fi lab.

## Konfigurasi alias laptop

Blok yang sudah disiapkan di `~/.ssh/config`:

```sshconfig
Host auv-wifi
    HostName 10.42.77.2
    HostKeyAlias 192.168.2.2
    User aero
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes
    ServerAliveInterval 15
    ServerAliveCountMax 3
```

`HostKeyAlias` memakai identitas Jetson yang sudah dikenal melalui Ethernet pada laptop ini. Jika ada peringatan perubahan host key, verifikasi identitas Jetson; jangan menonaktifkan pemeriksaannya.

## Selesai bekerja

Ketik `exit` untuk menutup SSH, atau pilih **Remote: Close Remote Connection** di VS Code. Untuk kembali ke internet melalui hotspot HP, hidupkan hotspot HP lalu jalankan:

```bash
nmcli connection up "realme Note 60"
```

Ini menghentikan AUV-Link dan memutus SSH. Jika perlu internet bersamaan dengan AUV-Link, gunakan jalur internet lain, misalnya USB tethering HP ke laptop; pengaturan tersebut belum diuji di sini.

**Status 20 November 2026:** pengguna mengonfirmasi alur AUV-Link berhasil setelah hotspot HP dimatikan. Pemulihan otomatis setelah reboot dan keberhasilan tanpa Ethernet belum dikonfirmasi secara terpisah.

Panduan operasi: [CARA-OPERASI-SSH.md](CARA-OPERASI-SSH.md).
