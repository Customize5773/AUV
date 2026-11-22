# Akses Jetson langsung dari laptop — AUV-Link

Laptop membuat hotspot **AUV-Link**, Jetson menyambung ke laptop. Tidak memerlukan router, hotspot HP, atau internet untuk SSH.

| Perangkat | Alamat |
| --- | --- |
| Laptop (hotspot) | `10.42.77.1` |
| Jetson (Wi-Fi) | `10.42.77.2` |
| Jetson (Ethernet cadangan) | `192.168.2.2` |

Profil sudah disiapkan. Akun Jetson: `aero`; alias SSH laptop: `auv-wifi`.

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
