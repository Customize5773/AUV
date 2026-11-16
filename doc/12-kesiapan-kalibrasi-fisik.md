# Kesiapan kalibrasi fisik AUV

Status dikonfirmasi pengguna pada **13 November 2026**: Raspberry Pi, Jetson dan kamera DWE tersedia; **kapal belum selesai**. Keberadaan perangkat tidak berarti perangkat sudah terhubung atau siap menjalankan misi. Tidak ada uji motor/aktuator dalam tahap ini.

| Bagian | Bukti tersedia | Pekerjaan yang menunggu |
|---|---|---|
| Komputer dan kamera | Raspberry Pi, Jetson, DWE menurut pengguna | Verifikasi ulang koneksi dan konfigurasi pada sesi perangkat berikutnya |
| Intrinsik DWE | [Fitting di udara](../vision-test/reports/dwe-calibration-fit-20261029-v2/README.md), RMS 0,590 px, masih provisional | Sesi validasi terpisah, cakupan bawah/kanan, target dengan ukuran diketahui, serta konfigurasi air/housing akhir |
| Dimensi dan massa | Normalisasi mesh latihan; massa simulator adalah asumsi | Ukur panjang/lebar/tinggi dan massa kapal lengkap, termasuk baterai dan payload |
| Tujuh thruster | Profil latihan T1–T4 horizontal, T5–T7 vertikal | Ukur posisi relatif pusat massa, arah sumbu dan tanda dorong setiap thruster; verifikasi mixer fisik |
| PWM–thrust dan respons | Koefisien model latihan | Rekam PWM, tegangan berbeban, gaya, waktu respons, arah, deadband dan konfigurasi ESC pada rig yang sesuai |
| Buoyancy dan drag | Model gaya simulator | Ukur kendaraan lengkap dalam kondisi air penggunaan; rekam kondisi ballast/payload, kecepatan, arus dan peluruhan gerak |
| Ekstrinsik kamera/sensor | Transformasi virtual simulator | Ukur posisi/orientasi setelah dudukan mekanik final, termasuk housing |
| Payload/pickup/hidrofon | Rancangan dan bukti simulator | Konfirmasi aktuator, catu daya/driver, fabrikasi dan uji perangkat nyata |

## Yang bisa dilakukan sebelum kapal selesai

Gunakan [tool kalibrasi yang sudah ada](../vision-test/calibration/README.md); tidak menambah collector atau fitter baru. Simpan sesi baru terpisah dari 30 pose fitting lama. Prioritaskan cakupan bawah/kanan, pose miring dan jarak berbeda, papan datar serta gambar tajam. Pertahankan identitas kamera, resolusi, fokus/lensa dan ukuran kotak cetakan terukur pada manifest. Jangan mencampur beberapa kamera atau konfigurasi stream dalam satu kalibrasi.

Parameter lama hanya untuk exploreHD SN00009 pada 1920×1080 dalam sesi udara tersebut. `calibration.json` belum disahkan untuk kendali/pengukuran metrik; belum diterapkan ke simulator atau kontrol fisik. Kalibrasi udara tidak menjadi bukti akurasi bawah air, dan ekstrinsik tetap menunggu pemasangan mekanik.

Data propulsi/hidrodinamika yang belum diukur tetap ditandai **belum tersedia**, bukan diganti angka perkiraan baru. Profil simulator tidak diubah menjadi profil kendaraan nyata sebelum data dan satuannya dapat diperiksa. Uji kolam dan penilaian lomba tetap memerlukan kapal yang sudah lengkap.
