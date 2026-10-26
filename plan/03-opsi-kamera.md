# Opsi penggunaan tiga kamera DWE

**Inventaris terkonfirmasi: 3 kamera DWE sudah tersedia.** Model dan antarmukanya belum diketahui. Penempatan dan pola pemrosesan berikut merupakan usulan untuk dibahas bersama tim mekanik.

## Rekomendasi awal

Mulai pengembangan dengan kamera **depan**, kemudian tambah kamera **bawah**. Tentukan manfaat kamera ketiga melalui uji cakupan pandang. Ketiga unit bisa disiapkan untuk eksperimen tanpa mengharuskan tiga detektor berjalan bersamaan sepanjang misi.

| Opsi pemasangan | Fungsi yang diusulkan | Cara menilai |
| --- | --- | --- |
| Depan | Gerbang, rintangan, dan flare | Target terlihat pada jarak pendekatan dan manuver yang diuji |
| Depan + bawah | Menambah pengamatan drum serta posisi pelepasan bola | Pengamatan bawah membantu penempatan; pandangan tidak tertutup frame/aktuator |
| Depan + bawah + kamera mekanisme | Mengamati area kerja dropper/gripper dari sudut tambahan | Memberikan informasi yang tidak tersedia pada kamera bawah; posisi menunggu rancangan aktuator |
| Depan + bawah + samping/belakang | Memeriksa area yang tidak terlihat pada manuver tertentu | Ada kegagalan nyata yang terbantu sudut ini; bukan penambahan hanya untuk memakai semua unit |

Untuk tahap frame sekarang, usulkan dudukan yang dapat disesuaikan saat pengujian. Jika kamera ketiga belum menambah keberhasilan tugas, pertahankan sebagai cadangan atau alat eksperimen. Ini keputusan yang akan ditinjau, bukan kesimpulan bahwa unit ketiga tidak berguna.

## Dipasang, mengirim video, dan dianalisis adalah keputusan terpisah

1. **Terpasang:** kamera berada pada robot dan tersambung.
2. **Akuisisi/rekam/stream:** video diambil, disimpan, atau ditampilkan untuk pengujian.
3. **Pemrosesan misi:** frame dianalisis untuk menghasilkan keputusan robot.

Usulan awal: pilih pemrosesan menurut tahap misi, misalnya depan untuk navigasi dan bawah untuk pendekatan drum. Dua atau tiga jalur pemrosesan bersamaan baru diaktifkan bila diperlukan dan hasil uji Jetson memadai. Pengembangan harus mendukung konfigurasi kamera, bukan mengunci asumsi bahwa semuanya selalu aktif.

BlueOS mendokumentasikan kemampuan konfigurasi dan streaming beberapa kamera bersamaan. Kemampuan streaming itu belum membuktikan performa analisis visi tiga kamera pada Jetson milik tim. [Getting Started resmi](https://blueos.cloud/docs/stable/usage/getting-started/), diperiksa 1 Oktober 2026.

Dokumentasi kamera mencantumkan DWE exploreHD sebagai kamera USB yang sudah diuji. Model unit tim perlu dipastikan sebelum memakai contoh tersebut sebagai acuan kompatibilitas. [Dokumentasi kamera resmi](https://blueos.cloud/docs/stable/integrations/hardware/required/camera/), diperiksa 1 Oktober 2026.

## Rencana pengujian

| Pengujian | Data yang dicatat | Keputusan |
| --- | --- | --- |
| Tiap unit sendiri | Identitas, format, resolusi, FPS aktual, daya, hasil rekam | Kondisi dasar tiga unit dan konfigurasi yang tersedia |
| Dua unit | FPS, frame hilang, beban CPU/GPU, suhu, latensi, topologi sambungan | Kelayakan depan + bawah |
| Tiga unit | Metrik yang sama, tambah rekaman dan beban pemrosesan | Batas penggunaan bersamaan |
| Restart dan sambung ulang | Pemetaan identitas ke fungsi, deteksi kehilangan video | Kamera depan/bawah tidak tertukar diam-diam |
| Pemasangan nyata | Area pandang, pantulan enclosure, frame/aktuator yang menghalangi | Sudut dan posisi kamera ketiga |
| Uji misi | Keberhasilan pendekatan/penempatan dengan dan tanpa kamera ketiga | Manfaat unit tambahan dibanding kompleksitasnya |

Konfigurasi yang perlu dapat diatur: nama fungsi (`front`, `down`, `aux`), identitas perangkat, profil video, lokasi kalibrasi, orientasi pemasangan, kebijakan rekaman, dan tugas yang menggunakannya. Kalibrasi dilakukan sesuai konfigurasi optik yang dipakai, termasuk pengujian bawah air.

Belum diputuskan: resolusi/FPS target, cara pembagian frame antar-aplikasi, kebutuhan hub, pemakaian GPU, dan sinkronisasi antarkamera. Tiga kamera tidak otomatis merupakan sistem stereo; kebutuhan itu harus datang dari tugas dan didukung pengujian.
