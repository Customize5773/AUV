# Cara akses Jetson dari laptop lewat Wi-Fi (SSH)

Alur: **laptop → Wi-Fi/router → Jetson**. Jalankan perintah di laptop, kecuali ditandai **di Jetson**.

## 1. Siapkan koneksi

- Nyalakan Jetson dan hubungkan laptop serta Jetson ke jaringan Wi-Fi yang sama. Jaringan harus mengizinkan komunikasi antarperangkat (bukan guest Wi-Fi dengan client isolation).
- Akun Jetson proyek ini: `aero`; folder proyek: `/home/aero/AUV`.
- Alias SSH laptop: `auv-wifi`. Konfigurasi laptop saat panduan dibuat menunjuk ke `192.168.67.167`. Ini alamat DHCP, sehingga dapat berubah; bukan jaminan IP Jetson saat ini.

Jika IP berubah, lihat daftar perangkat/DHCP pada router. Alternatif melalui terminal lokal Jetson atau koneksi yang masih tersedia, jalankan **di Jetson**:

```bash
ip -4 addr
```

Gunakan alamat `inet` pada antarmuka Wi-Fi, bukan `127.0.0.1` atau alamat Docker.

## 2. Masuk dari terminal laptop

Pada laptop yang sudah dikonfigurasi:

```bash
ssh auv-wifi
```

Tanpa alias, gunakan perintah berikut dengan IP Wi-Fi Jetson yang benar:

```bash
ssh aero@192.168.67.167
```

Pada koneksi pertama, cocokkan fingerprint host key dengan Jetson sebelum menerima. Fingerprint dapat dilihat melalui terminal tepercaya **di Jetson**:

```bash
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

Masukkan password akun `aero` jika diminta. Karakter password memang tidak terlihat saat diketik. Jika memakai SSH key, yang mungkin diminta adalah passphrase key laptop.

Setelah berhasil masuk, jalankan **di Jetson**:

```bash
whoami
hostname
cd /home/aero/AUV
pwd
```

`whoami` harus menghasilkan `aero`, dan `pwd` harus `/home/aero/AUV`. Untuk keluar:

```bash
exit
```

## 3. Siapkan alias pada laptop baru

Edit `~/.ssh/config` di laptop. Tambahkan blok berikut jika belum ada; jika sudah ada, perbarui blok yang sama. Sesuaikan `HostName` dengan IP Wi-Fi Jetson:

```sshconfig
Host auv-wifi
    HostName 192.168.67.167
    User aero
    ServerAliveInterval 15
    ServerAliveCountMax 3
```

Laptop proyek yang sudah disiapkan juga memakai pengaturan berikut di dalam blok tersebut:

```sshconfig
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes
```

Tambahkan dua baris itu hanya jika key tersebut tersedia dan public key-nya sudah terdaftar di `~/.ssh/authorized_keys` akun `aero` pada Jetson. Private key tetap di laptop, jangan disalin ke repository.

## 4. Buka proyek melalui VS Code

Jalankan langkah berikut di **VS Code laptop**. Tidak perlu masuk lewat `ssh` di terminal terlebih dahulu.

1. Buka Extensions (`Ctrl+Shift+X`), cari **Remote - SSH** dari **Microsoft**, lalu klik **Install**.
2. Tekan `Ctrl+Shift+P`, pilih **Remote-SSH: Connect to Host…**.
3. Pilih `auv-wifi`; pilih platform **Linux** jika diminta.
4. Masukkan password akun `aero` atau passphrase SSH key jika diminta, lalu tunggu koneksi selesai.
5. Pilih **Open Folder…**, masukkan `/home/aero/AUV`, lalu klik **OK**.
6. Pilih menu **Terminal → New Terminal** untuk menjalankan perintah langsung di Jetson.

Jika `auv-wifi` belum muncul, pilih **Remote-SSH: Open SSH Configuration File…** dari `Ctrl+Shift+P`, buka `~/.ssh/config`, lalu tambahkan alias pada bagian 3. Ulangi langkah koneksi.

Alternatif dari terminal laptop jika perintah `code` tersedia:

```bash
code --remote ssh-remote+auv-wifi /home/aero/AUV
```

Pastikan indikator koneksi di pojok kiri bawah VS Code menunjukkan `SSH: auv-wifi`. File yang diedit adalah file di Jetson; folder `/home/rasya/AUV` di laptop tidak otomatis ikut berubah.

Untuk memutus koneksi, pilih **Remote: Close Remote Connection** dari `Ctrl+Shift+P` atau tutup jendela VS Code remote.

## 5. Jika gagal tersambung

| Gejala | Pemeriksaan |
| --- | --- |
| `Connection timed out` / `No route to host` | Periksa daya Jetson, jaringan Wi-Fi, IP terbaru, dan client isolation pada router. |
| `Connection refused` | Periksa layanan SSH **di Jetson** dengan `sudo systemctl status ssh`. Jika sudah terpasang tetapi berhenti, jalankan `sudo systemctl enable --now ssh`. |
| `Permission denied` | Pastikan user `aero`, password benar, atau public key laptop sudah terdaftar di Jetson. |
| `REMOTE HOST IDENTIFICATION HAS CHANGED` | Verifikasi IP dan fingerprint Jetson melalui akses tepercaya. Jangan menonaktifkan pemeriksaan host key atau menghapus key lama tanpa verifikasi. |
| Terputus setelah Wi-Fi hilang/reboot | Tunggu Jetson kembali ke Wi-Fi, periksa IP, lalu ulangi `ssh auv-wifi` atau sambungkan kembali Remote-SSH. |

Untuk diagnosis dari laptop:

```bash
ssh -v -o ConnectTimeout=10 auv-wifi
```

Keberhasilan login SSH adalah bukti akses; balasan ping saja belum memastikan SSH siap.

Panduan operasi setelah tersambung: [CARA-OPERASI-SSH.md](CARA-OPERASI-SSH.md).
