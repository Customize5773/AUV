# Kualifikasi beberapa seed dan retensi bola

20 November 2026. Kondisi kualifikasi memakai model dinamis, atenuasi air 0,10/m, dan dua posisi awal. Posisi nominal memiliki offset dan yaw nol. Posisi kedua memiliki offset lateral +0,15 m dan yaw +0,10 rad. Setiap kombinasi jalur, pose, dan seed dijalankan satu kali. Empat hasil seed 42 menggunakan batch jalur 1–2 sebelumnya. Seed 7 dan 91 menggunakan batch baru. Run GUI dicatat terpisah dari statistik headless.

## GUI dan POV

Pada jalur 2 nominal seed 42, pemeriksa menemukan jendela dan subscriber POV depan serta bawah. Gate kedua 22,836 s, surface 25,422 s dan stop 29,842 s. Shutdown bersih, exit 0 dan daftar grup viewer yang perlu dibunuh paksa kosong. Log mencatat stale_sensors 2,920 s setelah DONE. Hasil ini memenuhi pemeriksaan penutupan, dengan peringatan setelah misi yang masih terlihat di GUI. [Laporan](../ros2_ws/evidence/qualification-seeds-pov-20261120/gui/mission.json) · [log](../ros2_ws/evidence/qualification-seeds-pov-20261120/gui/mission.log).

## Retensi pada dudukan latihan

Salinan plugin untuk eksperimen meniadakan pembuatan fixed joint setelah pickup. Bola awal tetap dimuat lalu dilepas, mengendap pada dua rel, dan dijepit. Rekaman setiap langkah pengamatan setelah release diperiksa agar payload tidak terikat kembali. Controller misi dan plugin produksi tetap memakai model pada laporan 81.

| Perintah setelah menjepit | Perpindahan titik grip | Jarak maksimum bola–grip |
|---|---:|---:|
| Maju dan naik | 46,4 cm | 47,4 cm |
| Pembanding rahang terbuka, maju dan naik | 46,4 cm | 47,5 cm |
| Thruster vertikal saja | 38,6 cm | 38,8 cm |

Kontak teramati saat menutup pada percobaan maju dan naik. Bola kemudian tertinggal di dudukan. Kedua percobaan jepit melampaui ambang retensi 7,5 cm. Perpindahan di tabel adalah jarak lurus 3D. Dua percobaan awal dengan perpindahan di bawah 10 cm tidak memenuhi syarat uji angkut. Hasil berlaku untuk geometri, gain dan kontak simulator pada dudukan latihan ini. Belum ada validasi gaya gesek atau servo aktual.

[Trace jepit](../ros2_ws/evidence/gripper-unlatched-20261120/lift/physics.json) · [kontrol terbuka](../ros2_ws/evidence/gripper-unlatched-20261120/lift-open/result.json) · [angkat](../ros2_ws/evidence/gripper-unlatched-20261120/vertical/result.json). Pickup dasar drum masih terkendala clearance −17 cm pada pendekatan mendatar dengan batang tetap 8 cm, sesuai [pemeriksaan geometri](81-aktuasi-rahang-dan-release-terukur.md).

## Matriks headless

| Jalur dan pose | Median gate kedua sah | Lulus sampai shutdown |
|---|---:|---:|
| 1 nominal | 21,536 s | 3/3 |
| 1 offset | 23,138 s | 2/3 |
| 2 nominal | 22,058 s | 3/3 |
| 2 offset | 22,030 s | 3/3 |

12/12 misi selesai dan 11/12 diterima. Tercepat 21,370 s (jalur 1 nominal, seed 91). Median memakai seluruh pelintasan sah. Untuk jalur 1 offset, median dari dua run dengan shutdown bersih saja adalah 23,178 s. Pada seed 91 untuk pose tersebut, proses qualification keluar −11 setelah DONE. Satu pengulangan di luar matriks juga DONE tetapi Gazebo keluar −9. Penyebab kedua terminasi belum diketahui. [Ringkasan dan hasil per run](../ros2_ws/evidence/qualification-seeds-pov-20261120/summary.json).
