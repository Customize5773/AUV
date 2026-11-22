# Pickup live, retensi mekanis dan perjalanan ke Square

23 November 2026. Uji Gazebo ini dimulai di atas drum. Model menggunakan tujuh thruster, badan kompak, batang tetap 8 cm, penahan kecil di depan dan belakang kedua rahang, serta kamera bawah yang dimiringkan 0,72 rad ke arah gripper. Simulasi memakai estimasi tekanan, IMU/magnetometer dan DVL, dengan kalibrasi dari titik awal tertahan. Tinggi dasar drum dan posisi awal kendaraan diketahui. Penilaian memakai lintasan fisika bola yang sama setelah release.

| Uji | Hasil |
|---|---|
| Kamera vertikal, pendekatan dengan tujuh thruster | Posisi bola hilang sebelum pickup. Dalam uji tracking, bola berakhir sekitar 26 cm dari pusat drum. Pengaman menahan perintah tutup. |
| Kamera dimiringkan, penahan depan–belakang, offset perintah +20 dan −20 mm | Kedua run mengangkat bola sekitar 1,63 m dan mempertahankannya sampai permukaan tanpa fixed joint pascarelease. |
| Posisi akhir bola dari empat rekaman ARENA sebelumnya | Kasus 2 dan 4 lulus. Kasus 1 dan 3 timeout sebelum grip. Offset historisnya 54,8 dan 48,0 mm. Pada 3.600 sampel yaw per posisi, badan mendatar yang terpusat pada bola bertabrakan dengan rim di kedua kasus. |
| Pelepasan rendah, kasus 1 dan 3 | Dari ketinggian awal sekitar 1,43 m, AUV turun sebelum melepas bola sekitar 33 cm di atas tinggi pusat bola yang sudah mengendap. Pada dua uji keluar–kembali, seluruh kendaraan keluar dari zona, kembali dan mengambil bola yang sama. Saat muncul di atas drum, bola tetap dekat gripper selama 2,05 detik. |
| Membawa bola ke koordinat Square latihan | Dua run dengan keluar–kembali menempuh perjalanan ke Square selama 51,70 dan 51,75 detik. Jarak horizontal maksimum gripper ke pusat Square selama penahanan akhir 7,62 dan 7,29 cm. Bola tetap terpegang. |
| Menaksir pusat Square dari rentang dua marker pada pendekatan serong | Pada kasus 3, bola masih terpegang. Gripper berakhir sekitar 74 cm dari pusat Square sehingga melebihi batas latihan 65 cm. |

**Penerimaan akhir segmen dengan dua kamera.** AUV menghadap satu sisi Square agar kamera depan dapat menghitung jarak ke marker dan mengoreksi perpindahan dari sisi ke pusat. Perintah jepit menunggu gerak vertikal di bawah 4 mm/s dan galat tinggi estimasi ≤1,2 mm selama sedikitnya 0,4 s. Pada kasus 1 dan 3, galat tinggi aktual saat menjepit 0,54 dan 0,53 mm. Kamera bawah memandu akuisisi ulang. Kamera depan memberi 54 dan 51 pengamatan Square. Transfer berlangsung 54,15 dan 54,10 s. Gripper berada paling jauh 6,94 dan 7,22 cm dari pusat Square selama hold akhir. Pada replay terpisah, odometri yang direkam oleh observer dan paket fisika mengonfirmasi keluar zona, pengangkatan bola, kontinuitas retensi serta kemunculan seluruh proyeksi badan di dalam Square. Replay mengasumsikan tahap navigasi telah lulus, sesuai titik mulai fixture. Uji ini tidak menghasilkan skor total misi dari starting zone.

[Run kasus 1](../ros2_ws/evidence/pickup-hull-25cm/unlatched/lip/pocket/firm/approach-offset-20mm/pose-corrected/live-camera-estimator/calibrated/surface-dynamic-tilted/face-square-drum1/settled-close/native_result.json) · [Run kasus 3](../ros2_ws/evidence/pickup-hull-25cm/unlatched/lip/pocket/firm/approach-offset-20mm/pose-corrected/live-camera-estimator/calibrated/surface-dynamic-tilted/face-square-drum3/settled-close/native_result.json) · [Replay pemeriksa](../ros2_ws/evidence/pickup-hull-25cm/unlatched/lip/pocket/firm/approach-offset-20mm/pose-corrected/live-camera-estimator/calibrated/surface-dynamic-tilted/face-square-drum3/settled-close/retrieval-referee.json) · [Grafik lintasan](../ros2_ws/evidence/pickup-hull-25cm/unlatched/lip/pocket/firm/approach-offset-20mm/pose-corrected/live-camera-estimator/calibrated/surface-dynamic-tilted/face-square-drum3/settled-close/lintasan.png).

Nomor kasus 1–4 merujuk pada posisi relatif bola dari empat rekaman historis. Fixture menempatkan perpindahan tersebut pada drum uji yang sama. Uji dengan pelepasan rendah memakai posisi XY saat release historis. Uji geometri memakai posisi akhir bola historis. Masing-masing hasil merupakan percobaan pada konfigurasi yang disebutkan.

Pemeriksa ARENA kini dapat menggunakan bukti fisika bilateral tanpa joint. Untuk mendapat kredit, bola yang sudah diakuisisi harus dipegang setelah keluar zona, tetap dekat titik jepit dan terangkat melewati bibir drum. Pemisahan bola mencabut kredit. Mode fixture dipilih melalui parameter SDF `use_pickup_joint=false`. Pengujian regresi mencakup attachment lama serta syarat pengangkatan dan hilangnya retensi pada mode kontak.

[Bukti runtime](../ros2_ws/evidence/pickup-hull-25cm/live-comparison.json) · [Geometri empat posisi](../ros2_ws/evidence/pickup-hull-25cm/historical-clearance.json) · [205 tes simulator](../ros2_ws/evidence/pickup-hull-25cm/unit-20261123-final.log) · [Build](../ros2_ws/evidence/pickup-hull-25cm/build-20261123.log) · [Cara menjalankan](../ros2_ws/CARA-RUNNING.md)

### Uji dari starting zone dan pemeriksaan retensi akhir

Pada run ARENA extended dinamis dengan drum pinger 3, konfigurasi default berhenti pada 26,626 s dengan alasan `fixed_gripper_unreachable`. Perintah gerak dan thrust kembali nol, lalu Gazebo ditutup bersih. Uji ini memakai badan default. Hasil pickup badan kompak di atas drum tetap merupakan bukti segmen.

Runner penerimaan sekarang memeriksa kredit retrieval dari referee, identitas payload yang sudah dilepas, bukti jepitan bilateral atau attachment, serta jarak akhir bola ke gripper di bawah 7,5 cm. Pemeriksaan akhir menerima dua rekaman pickup tanpa joint pada kasus 1 dan 3. Langkah terbuka adalah mengintegrasikan badan kompak dan pengendali pickup ke launch dari starting zone, termasuk pencatatan kontak kedua bagian badan, lalu menguji misi lengkap.

[Run dari starting zone](../ros2_ws/evidence/extended-start-rQ8gJC/mission.json) · [206 tes lulus](../ros2_ws/evidence/extended-start-rQ8gJC/tests.log)

Monitor kontak dan pemicu jatuh bola flare kini membaca kedua collision badan (`hull` dan `hull_upper`). Pada uji Gazebo terisolasi, badan dibalik agar hanya bagian atas yang menyentuh platform. Topik kontak mencatat pasangan `sauvc_auv::base_link::hull_upper` dan `stand::base::platform`. Uji ini memeriksa pelaporan kontak. Pelepasan bola oleh benturan bagian atas dan misi lengkap badan kompak masih perlu diuji.

[World uji](../ros2_ws/evidence/compact-upper-contact/probe.sdf) · [Pesan kontak Gazebo](../ros2_ws/evidence/compact-upper-contact/contact.txt) · [Regresi](../ros2_ws/evidence/compact-upper-contact/unit.log)

### ARENA extended dari starting zone dengan badan kompak

Profil opt-in `compact:=true` memasang mesh dan dua collision hasil fixture. World menonaktifkan fixed joint pickup dan pengendali memeriksa celah profil kompak. Pada drum pinger 3, referee mengonfirmasi pelintasan penuh, bola flare biru–merah–kuning jatuh, payload masuk drum pinger dan seluruh badan keluar zona. Saat kembali, pengendali masuk DESCEND_PICKUP lalu berhenti dengan `pickup_not_proven`. Thruster nol dan shutdown bersih.

Pada frame akhir, pusat bola di (25,2418; 21,9044) m dan gripper di (24,9902; 21,9827) m. Selisih horizontal 26,3 cm. Kontrol pendekatan saat ini masih mengarah ke posisi akuisisi drum. Bagian fixture yang perlu dipindahkan berikutnya ialah pelepasan rendah dan koreksi posisi terhadap bola dari kamera sebelum menjepit.

[Hasil misi](../ros2_ws/evidence/compact-start/drum3/mission.json) · [207 tes lulus](../ros2_ws/evidence/compact-start/tests.log)

### Pelepasan rendah dan koreksi pickup dari kamera bawah

Pada satu ulangan drum 3 dari starting zone, profil kompak melepas bola pada z −1,620 m. Kamera bawah mendeteksi kandidat bola putih tunggal dan pengendali memakai proyeksi piksel ke bidang pusat bola untuk turun. Referee mengonfirmasi akuisisi dan keluar zona. Sesaat sebelum abort, galat horizontal aktual gripper terhadap bola 1,64 cm (run sebelumnya 27,15 cm pada tahap yang sama). Namun titik jepit bertahan pada z −1,856 m sejak sekitar detik 204 sementara pusat bola berada di −1,960 m. Jarak vertikal 10,35 cm masih melampaui sasaran 4 cm. Bola juga terus bergeser di dasar. Pengendali mengakhiri misi dengan pickup_not_proven dan grip_requested=false. Penyebab berhentinya penurunan perlu dibedakan melalui kontak badan/rim, sikap kendaraan dan perintah thrust pada interval tersebut.

[Hasil misi](../ros2_ws/evidence/compact-start/low-release/mission.json) · [Status pengendali](../ros2_ws/evidence/compact-start/low-release/mission-controller.json) · [Regresi](../ros2_ws/evidence/compact-start/low-release/tests.log)

### Diagnosis penurunan dan retensi dari starting zone

- Pada rekaman pelepasan rendah sebelumnya, dari detik 210 sampai 240, posisi badan hampir tetap dan tiga thruster vertikal terus memberi gaya ke bawah. Rekaman itu tidak memuat nama pasangan collision sehingga penyebab mekanis kejadian lama belum dapat dipastikan.
- Pada ulangan dengan pembatasan kecepatan turun dekat dasar dan pengaman kemiringan, referee mencatat `PAYLOAD_GRASPED` di 207,65 s. Observer tidak mencatat benturan hull selama pickup. Kontak kedua rahang terlepas saat pengangkatan dan bola tetap di dasar. Referee mengakhiri percobaan dengan `premature_surface`. [Rekaman](../ros2_ws/evidence/compact-start/descent-contact/mission.json)
- Pada ulangan dengan rahang berkantong dan kamera bawah dimiringkan 0,72 rad, pengendali menghentikan penurunan saat pelacakan bola hilang. Citra memperlihatkan bola terpotong di tepi atas ketika badan masih sekitar 1,10 m di bawah permukaan. [Rekaman](../ros2_ws/evidence/compact-start/tilted-contact/mission.json) · [POV saat kehilangan target](../ros2_ws/evidence/compact-start/tilted-contact/pov/DESCEND_PICKUP-201.10.ppm)

Pengendali kini menunggu kedalaman pengamatan sebelum turun, menahan jepitan dua detik sebelum mengangkat dan memeriksa retensi sebelum menuju Square. Run pertama terhenti pada `stale_sensors` sebelum pickup. Pengulangan dengan pengaman yang sama memperoleh 469 estimasi posisi bola dari kamera hingga 245,1 s. Kontak aktual pertama antara hull bawah dan bibir drum 3 tercatat pada 203,346 s. Dua segmen bibir masih menyentuh hull pada 245,204 s. AUV mengakhiri percobaan dengan `pickup_not_proven` dan rahang belum diperintahkan menjepit.

Pada awal penurunan, bola berjarak 4,92 cm dari pusat drum. Untuk badan mendatar dan gripper terpusat tepat di atas bola, pemeriksaan 3.600 heading dengan langkah 0,1° tidak menemukan celah positif. Overlap terkecil pada 200,2 s sebesar 2,09 mm, pada 203,35 s sebesar 5,27 mm dan menjelang abort sebesar 43,28 mm. Batas ini berlaku untuk pose dan lintasan bola pada ulangan tersebut. Untuk menyelesaikan kasus ini dengan batang tetap 8 cm, pendekatan berikut perlu mengubah lokasi akhir bola atau geometri penampang masuk drum.

[Run terhenti saat sensor stale](../ros2_ws/evidence/compact-start/settled-lift/mission.json) · [Run dengan kontak bibir drum](../ros2_ws/evidence/compact-start/settled-lift-repeat/mission.json) · [Pemeriksaan celah](../ros2_ws/evidence/compact-start/settled-lift-repeat/clearance.json) · [212 tes](../ros2_ws/evidence/compact-start/settled-lift/tests.log)
