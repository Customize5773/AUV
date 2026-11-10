# 56 — Wi-Fi, reboot dan kesiapan Pixhawk

4 November 2026. Pengguna meminta penyelesaian gangguan Wi-Fi, uji reboot dan validasi fisik. Kondisi yang dikonfirmasi: **Pixhawk hanya USB, tanpa daya thruster**. Karena itu tahap fisik dibatasi pada komunikasi dan pembacaan konfigurasi, bukan gerak kendaraan.

## Diagnosis dan perubahan

Boot Jetson sebelumnya tercatat pada 03:02:32 WIB, berdekatan dengan hilangnya koneksi pada tahap 53. NetworkManager mengaktifkan Wi-Fi sekitar 03:03:02. Ini mendukung reboot sebagai penjelasan untuk sebagian jeda, tetapi tidak membuktikan penyebab semua timeout historis. Journal boot sebelumnya tidak tersedia untuk audit lengkap.

Sebelum perubahan: profil `Lab Robotika AI` memakai powersave default dan perangkat melaporkan power save on; sinyal sekitar −75 dBm. Sepuluh koneksi baseline tetap lulus seluruhnya. Tidak ada bukti eksperimen bahwa power saving adalah akar tunggal atau bahwa perubahan ini meningkatkan kecepatan.

Profil UUID `47027092-9924-42eb-b697-1931fd9a0cc1` diubah menjadi:

- `connection.autoconnect=yes` (tetap).
- `connection.autoconnect-retries=0` untuk terus mencoba koneksi otomatis.
- `802-11-wireless.powersave=2` untuk menonaktifkan power saving.

Konfigurasi mengikuti [referensi resmi NetworkManager](https://www.networkmanager.dev/docs/api/latest/nm-settings-nmcli.html). Nilai sebelumnya disimpan pada `/var/lib/auv-network-backup/20261104T030820/profile-before.json` di Jetson. Power saving aktif juga dinonaktifkan melalui `iw`. IP tetap DHCP; tidak ada perubahan router, firmware, failsafe atau parameter Pixhawk.

## Hasil pengujian

| Pengujian | Hasil |
|---|---|
| Reboot terkontrol | Boot ID berubah; Ethernet dan Wi-Fi kembali mengeksekusi perintah SSH sekitar 47,5 detik sejak penjadwalan reboot |
| Persistensi konfigurasi | Profil tetap autoconnect yes, retries 0, powersave disable; power save off dikonfirmasi setelah Wi-Fi terhubung |
| Koneksi SSH Wi-Fi setelah reboot | 30/30 berhasil; waktu koneksi terlama 2,469 detik |
| Radio Wi-Fi off 2 detik lalu on | 3/3 tersambung otomatis; SSH siap 5,473 / 6,461 / 5,426 detik sejak perintah radio on selesai |
| Layanan GUI | Tetap not-found/inactive setelah reboot |
| Operasi terminal | Empat tes lulus kembali pada Jetson setelah reboot |
| Pixhawk USB | Perangkat terenumerasi; 17 parameter terbaca, 15 parameter profil propulsi cocok |
| Status kendaraan | Tetap disarmed; system_status 5 (CRITICAL), tidak diberi input pilot untuk menyamarkan status |

Pengukuran waktu memakai clock monotonic laptop dan polling SSH. Angka pemulihan adalah waktu deteksi keberhasilan perintah, memiliki ketelitian sesuai interval polling; bukan waktu boot internal atau benchmark 50 siklus. Siklus radio menguji pemulihan setelah radio perangkat dimatikan/dinyalakan, bukan uji jarak, air atau gangguan AP.

Pada snapshot awal setelah reboot, perangkat masih belum terasosiasi dan power save sempat dilaporkan on; setelah NetworkManager mengaktifkan profil, pemeriksaan akhir menunjukkan off. Snapshot awal disimpan, tidak dibuang.

Pembacaan Pixhawk hanya mengirim `PARAM_REQUEST_READ`. Tidak ada `PARAM_SET`, arm, perubahan mode, manual control atau uji motor. Profil yang cocok belum memverifikasi arah thrust, geometri mixer fisik atau kalibrasi sensor. Ketiadaan daya thruster membuat uji gerak/misi fisik belum dapat diselesaikan pada setup sekarang.

## Bukti dan cara memulihkan konfigurasi

Bukti lokal: [verification.json](../evidence/ssh-reboot-20261104/verification.json), [reboot](../evidence/ssh-reboot-20261104/reboot.json), [koneksi ulang](../evidence/ssh-reboot-20261104/reconnect.json), [parameter Pixhawk](../evidence/ssh-reboot-20261104/pixhawk-readiness.json), [pemeriksaan akhir](../evidence/ssh-reboot-20261104/final-check.log).

Rollback hanya bila memang ingin mengembalikan nilai awal:

```bash
sudo nmcli connection modify 47027092-9924-42eb-b697-1931fd9a0cc1 \
  connection.autoconnect-retries -1 802-11-wireless.powersave 0
sudo iw dev wlP1p1s0 set power_save on
```

Wi-Fi dan reboot lulus pada cakupan terbatas di atas. Kendali misi fisik tetap terbuka: perlu jalur ROS–Pixhawk yang tervalidasi, sensor/aktuator terpasang, kalibrasi dan lokasi uji basah dengan operator. Jangan menyamakan keberhasilan komunikasi USB dengan kesiapan menjalankan misi AUV.
