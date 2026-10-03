# Usulan rencana persiapan tim

Ini **rencana internal hasil sintesis**, bukan jadwal atau tenggat resmi panitia. Disusun 1 Oktober 2026. Sesuaikan dengan hardware dan kapasitas tim.

| Periode | Fokus | Bukti selesai yang diusulkan |
| --- | --- | --- |
| Oktober 2026 | Inventaris, target misi, pemeriksaan desain, akses kolam, prototipe kendali | Robot dapat diuji aman; wiring terdokumentasi; kedalaman/heading dapat diukur |
| November 2026 | Integrasi persepsi dan navigasi dasar | Percobaan gerbang/manuver balik berulang dengan log dan pencahayaan berbeda |
| Desember 2026 | Satu misi tambahan yang paling andal; persiapan demonstrasi video | Misi dari launch sampai selesai tanpa intervensi; berkas bukti siap disesuaikan |
| Januari 2027 | Latihan seluruh alur; logistik robot/baterai; review aturan terbaru | Percobaan berulang dengan properti berpindah; jalur perjalanan dan pengiriman jelas |
| Februari 2027 | Bekukan konfigurasi, latihan operator, pengemasan, dokumentasi | Konfigurasi dapat dipulihkan; suku cadang siap; paket dokumen final |

Registrasi dan video mengikuti tenggat resmi ketika ditemukan; jangan menunggu bulan pada tabel jika pengumuman meminta lebih awal.

**Prioritas yang disarankan:** keselamatan dan kedap → kendali dasar → navigasi → satu tugas tambahan → peningkatan tugas kompleks. Pertimbangkan hasil historis dan keterbatasan waktu kolam dalam [pembelajaran tim](04-tim-dan-pembelajaran.md), bukan hanya besarnya poin teoretis.

| Eksperimen | Rekaman yang diperlukan | Keputusan yang ditopang |
| --- | --- | --- |
| Depth/heading hold | Setpoint, pengukuran, output aktuator, waktu, tegangan | Parameter kendali dan kestabilan |
| Deteksi target | Video, label, confidence, latency, kondisi cahaya | Pemilihan detektor dan batas operasinya |
| Navigasi | Posisi awal, konfigurasi arena, hasil setiap percobaan | Keandalan, bukan demonstrasi tunggal |
| Drop/pickup | Error posisi, keberhasilan mekanisme, waktu | Layak/tidaknya mekanisme dibawa |
| Kehilangan sensor | Jenis gangguan, respons robot, log | Perilaku gagal yang dapat diprediksi |
| Operasi operator | Durasi setup, checklist terlewat, recovery | Kesiapan menjalankan robot di slot terbatas |

Format log yang disarankan: `run_id, tanggal, operator, versi_kode, konfigurasi, arena, baterai, target, hasil, penyebab_gagal, tautan_video`.

Tetapkan target numerik pengujian setelah kemampuan dasar terukur. Misalnya, rasio sukses harus selalu menyertakan jumlah percobaan dan kondisi; hasil 1/1 tidak cukup untuk menyatakan keandalan.
