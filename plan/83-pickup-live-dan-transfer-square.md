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

### Peletakan bola dekat dasar dan keluar vertikal

Pada profil kompak, pengendali menargetkan pusat bola 11 cm di atas lantai kolam, menunggu kestabilan posisi dan kecepatan estimasi, kemudian naik vertikal sampai kedalaman badan 1,20 m sebelum keluar zona. Percobaan pertama timeout saat alignment. Setelah koreksi posisi dipertahankan sepanjang waktu tunggu dan kecepatan DVL disaring, referee mencatat akuisisi drum 3 dan keluar zona penuh.

| Pengukuran dunia Gazebo | Run sebelumnya | Pelepasan dekat dasar |
|---|---:|---:|
| Ketinggian pusat bola di atas posisi istirahat saat paket fisika pertama sesudah release | 34,23 cm | 5,86 cm |
| Jarak horizontal bola dari pusat drum saat release | 1,57 cm | 1,93 cm |
| Jarak saat mulai alignment kembali | 3,40 cm | 4,29 cm |
| Jarak saat mulai turun untuk pickup | 4,92 cm | 5,75 cm |

Selama penarikan vertikal dan perjalanan kembali, posisi horizontal bola bergeser sekitar 1,36–1,37 mm/s. Kontak pertama hull dengan rim tercatat pada 213,596 s. Pickup berakhir dengan `pickup_not_proven`, tanpa kredit retrieval. Satu pasangan run ini tidak menunjukkan perbaikan posisi akhir. Uji terpisah dengan rahang yang dibuka saat AUV diam di atas drum diperlukan untuk membedakan gerak yang diwariskan saat release, impuls kontak rahang, dan perilaku kontak dasar drum.

[Perbandingan fase](../ros2_ws/evidence/compact-start/placement-settle-O5s0/placement-comparison.json) · [Rekaman misi](../ros2_ws/evidence/compact-start/placement-settle-O5s0/mission.json) · [212 tes lulus](../ros2_ws/evidence/compact-start/placement-settle-O5s0/tests.log)

### Isolasi penyebab bola terus bergeser setelah release

Fixture menempatkan gripper kompak di atas drum 3, pada heading 2,2645 rad dan pusat bola awal z −1,90141 m. AUV memakai pengendali kecepatan ideal agar gerak lateral dapat diatur terpisah dari pelepasan. Percobaan awal memakai anchor dinamis tidak membuka rahang dan dikeluarkan dari hasil. Pada delapan uji lengkap, servo dan loading joint mengikuti urutan pelepasan biasa. Pada kontrol tanpa kontak rahang, hanya collision jari yang dilepas. Gravitasi bola dan collision drum tetap aktif. Untuk kondisi bergerak, perintah kecepatan dunia mendekati (−0,7; −1,8) mm/s sampai pengamat pertama kali melihat bola lepas. Setiap kondisi diulang dua kali.

| Kondisi release | Perpindahan horizontal bola dari 1 sampai 30 detik setelah release |
|---|---:|
| AUV diam, rahang biasa | 0 mm terukur pada kedua run |
| AUV diam, collision jari dilepas | 0 mm terukur pada kedua run |
| AUV bergerak, rahang biasa | 13,68 dan 13,67 mm |
| AUV bergerak, collision jari dilepas | 40,02 dan 40,02 mm |
| Pembanding misi dinamis sebelumnya | 39,57 mm |

Gerak lateral sebelum release cukup untuk menghasilkan drift. Geometri jari memengaruhi hasil pada fixture bergerak. Data 20 Hz dengan pembulatan koordinat sekitar 0,1 mm tidak cukup untuk mengukur impuls sesaat atau menyimpulkan koefisien gesek fisik. [Data per fase](../ros2_ws/evidence/compact-start/release-isolation/comparison.json) · [Fixture](../ros2_ws/evidence/compact-start/release-isolation/probe.py)

Pada uji dinamis berikutnya, tahap `BRAKE_RELEASE` menahan perintah gerak nol sebelum pembukaan rahang. Pengendali memeriksa perpindahan horizontal estimasi ≤3 mm selama 2 s dan syarat kecepatan estimasi yang sudah ada. Pada satu ulangan, jarak bola dari pusat drum saat AUV kembali untuk alignment berubah dari 4,29 menjadi 2,82 cm. Saat mulai turun, jarak berubah dari 5,75 menjadi 3,42 cm. Referee mengonfirmasi akuisisi serta keluar zona. Collision hull bawah dengan rim_27 mulai 215,926 s. Misi berakhir dengan pickup_not_proven, tanpa perintah jepit. Pada koordinat bola awal penurunan, 1.280 dari 3.600 arah badan mendatar memiliki celah positif dengan asumsi gripper tepat di atas bola. Celah terbaik 8,40 mm; hasil untuk satu pose statis tidak membuktikan lintasan bebas benturan. [Perbandingan misi](../ros2_ws/evidence/compact-start/brake-release-JukK/placement-comparison.json) · [Sapuan yaw](../ros2_ws/evidence/compact-start/brake-release-JukK/clearance.json) · [213 tes](../ros2_ws/evidence/compact-start/brake-release-JukK/tests.log)

### Penerimaan dari starting zone dengan pemilihan heading pickup

Pada drum pinger 3, pengendali memilih arah hadap sebelum turun memakai offset estimasi bola terhadap pusat drum. Run pertama menggunakan estimasi pusat akustik dan kamera bawah untuk bola. Referee mencatat gerbang, ketiga flare sesuai urutan, payload di drum, keluar zona penuh, jepitan pada 222,250 s, kredit retrieval pada 228,400 s, surface pada 287,878 s lalu stop pada 293,284 s. Skor simulator 289,16604 termasuk Square +20 dan penalti nol. Waktu thrust–surface 261,132 s. Pada 1.347 frame fisika dari kredit retrieval hingga akhir rekaman, sensor jari mencatat kontak dengan bola, jarak gripper–bola maksimum 4,02 cm, dan payload_attached selalu false. Shutdown bersih. Sudut badan pada percobaan ini masih menyimpang dari tangen aktual. Kelulusan satu run tidak mengukur konsistensi pemilihan heading. [Misi lengkap](../ros2_ws/evidence/compact-start/yaw-OUUB/mission.json) · [Geometri saat pickup](../ros2_ws/evidence/compact-start/yaw-OUUB/pickup-summary.json)

Untuk memperkirakan arah tangen dari kamera, detektor mengambil piksel perbatasan dasar drum merah dengan dinding dalamnya. Pengendali memproyeksikan busur ke bidang dasar drum dan pusat bola ke bidang yang 2 cm lebih tinggi. Estimasi pusat diterima bila busur memiliki kelengkungan yang cukup dan sesuai dengan radius dalam drum. Pada dua frame survei arsip yang memenuhi kriteria, galat posisi relatif bola–pusat drum 3,86 dan 2,18 mm. Pada sapuan geometri mendatar dengan offset bola 34 mm, semua 360 arah offset memberi celah 8,31–8,68 mm jika badan tepat pada arah tangen. Pada offset 50 mm seluruh arah yang disampel berpotongan dengan dinding. [Replay kamera](../ros2_ws/evidence/compact-start/yaw-OUUB/camera-replay.json) · [Sapuan geometri](../ros2_ws/evidence/compact-start/visual-yaw-aCjx/heading-envelope.json)

Pada varian kamera bawah dengan koreksi lengan gripper terhadap roll/pitch, seed 42 mencapai DONE. Saat mulai turun, offset bola aktual 39,72 mm, galat heading terhadap tangen aktual 3,08° dan galat horizontal gripper–bola 1,43 mm. Saat mulai angkat, galat heading 0,78°, galat horizontal 1,33 mm, dan titik jepit 40,87 mm di atas pusat bola. Observer tidak mencatat kontak hull–drum pada tahap pickup. Skor 289,05858 dengan thrust–surface 264,714 s. Pada 1.389 frame setelah kredit retrieval tercatat kontak jari dan bola, tanpa fixed joint. Thruster nol dan shutdown bersih. Kedua varian diuji dengan seed sensor yang sama, tetapi lintasan pelepasan bola aktual berbeda. [Rekaman lengkap](../ros2_ws/evidence/compact-start/visual-yaw-aCjx/mission.json) · [Perbandingan penerimaan](../ros2_ws/evidence/compact-start/visual-yaw-aCjx/verification.json) · [Grafik misi lengkap](../ros2_ws/evidence/compact-start/visual-yaw-aCjx/misi-lengkap.png) · [Uji regresi](../ros2_ws/evidence/compact-start/visual-yaw-aCjx/tests.log)

Ulangan seed sensor 91 juga mencapai DONE, dengan skor 289,19604, waktu thrust–surface 260,132 s dan penalti 0. Kedua run dengan kode kamera bawah yang sama lulus pada drum pinger 3. [Bukti seed 91](../ros2_ws/evidence/compact-start/heading-seed91-6L3j/mission.json) · [Rekap](../ros2_ws/evidence/compact-start/visual-yaw-aCjx/verification.json)

### Drum pinger 4 dan batas pickup dekat dinding, 24 November

Satu run dari starting zone dengan profil kompak, tujuh thruster dan seed 42 mencapai DONE di drum pinger 4. Skor 289,34658, waktu thrust–surface 255,114 s, penalti nol. Saat kembali untuk alignment, pusat bola berjarak 18,44 mm dari pusat drum. Saat mulai turun jaraknya 28,23 mm, dan saat mulai angkat 35,56 mm. Tidak tercatat kontak hull dengan rim selama pickup. Seluruh 1.399 frame dari kredit retrieval sampai akhir merekam kontak jari tanpa fixed joint. Thruster kembali nol dan Gazebo ditutup bersih. [Misi](../ros2_ws/evidence/compact-start/pinger4-0TUZ/mission.json)

Pada uji penurunan terpisah, bola ditempatkan di dasar pada offset yang ditentukan. Uji pembanding mengaktifkan collision kedua bagian hull dan menghilangkan collision alat agar mengukur hambatan badan secara terpisah. Dengan arah panjang badan tangensial dan offset 20 mm, titik jepit mencapai 40,1 mm di atas pusat bola tanpa kontak hull–rim. Pada offset 250 mm, hull menabrak rim saat titik jepit masih 171 mm di atas pusat bola. Percobaan pendahuluan dengan seluruh collision juga merekam benturan pada offset 250 mm, sedangkan percobaan 20 mm dengan seluruh collision berakhir timeout tanpa bukti jepitan. Pada sapuan statis sepanjang arah +X drum, 410 dari 3.600 heading bebas pada offset 40 mm, 54 pada 45 mm dan nol pada 50 mm. Hasil penurunan terpisah mengukur akses badan, bukan kelulusan misi pickup pada posisi paksa. [Celah geometri](../ros2_ws/evidence/compact-start/pinger4-0TUZ/clearance.json) · [Penurunan 20 mm](../ros2_ws/evidence/compact-start/pinger4-0TUZ/hull-descent-20mm/result.json) · [Penurunan 250 mm](../ros2_ws/evidence/compact-start/pinger4-0TUZ/hull-descent-250mm/result.json)

### Pemeriksaan sebelum turun, 24 November

Pengendali kompak kini memeriksa seluruh sudut penampang badan bawah terhadap radius dalam drum sebelum beralih dari ALIGN_PICKUP ke DESCEND_PICKUP. Margin horizontal 5 mm dipilih sebagai asumsi latihan di atas galat replay kamera 2,2–3,9 mm. Jika pusat drum visual tidak tersedia atau celah tidak positif, AUV menahan posisi untuk pengamatan ulang. Setelah tiga detik tanpa celah yang memenuhi margin, pengendali abort dengan pickup_clearance_unverified. Uji pengendali dengan bola 25 cm dari pusat mempertahankan perintah nol dan tidak mengirim perintah jepit. Suite 219 tes lulus. Regresi misi lengkap Gazebo dengan pemeriksaan baru masih perlu dijalankan. Margin 5 mm belum merupakan batas ketidakpastian kamera fisik. [Hasil tes](../ros2_ws/evidence/pickup-clearance/tests.log)

### Regresi Gazebo setelah pengaman celah pickup, 24 November

Pada misi lengkap profil kompak dengan tujuh thruster, drum 3 seed 42 mencapai DONE (289,15752 poin, thrust–surface 261,416 s). Drum 4 seed 91 juga mencapai DONE (289,25526 poin, 258,158 s). Referee mengonfirmasi akuisisi dan retrieval payload yang sama, surface di Square serta stop. Sejak kredit retrieval, 1.333/1.333 dan 1.420/1.420 sampel masing-masing menunjukkan jepitan bilateral tanpa fixed joint. Kedua misi mencatat penalti nol, thruster akhir nol dan shutdown bersih.

Dua percobaan drum 4 seed 42 berakhir di ALIGN_PICKUP dengan pickup_clearance_unverified. Saat abort, jarak bola dari pusat drum adalah 4,52 dan 6,55 cm. Sapuan 3.600 heading dengan posisi aktual dari observer menunjukkan celah terbaik setelah margin masing-masing −4,40 dan −18,95 mm. Pengendali tidak memerintahkan jepit dan observer tidak merekam kontak hull dengan rim selama pickup. Satu peluncuran tambahan bertumpang tindih dengan shutdown ulangan seed 42 sehingga hasil akhir referee ulangan itu dan peluncuran tambahan tidak digunakan untuk penilaian skor. Run seed 91 kemudian dijalankan di domain ROS dan partisi Gazebo tersendiri.

Pada fixture Gazebo terpisah dengan bola 25 cm dari pusat drum 4, posisi bola dan pusat drum diberikan ke pengendali; pose kendaraan dibaca dari Gazebo. Seluruh collision kendaraan dipertahankan. Selama 90 sampel (3,026 s simulasi), posisi vertikal tetap, seluruh perintah gerak nol, tidak ada perintah jepit atau kontak rim, dan pengendali abort dengan pickup_clearance_unverified. Bukti persepsi kamera langsung berasal dari misi lengkap. Pengujian berikutnya yang relevan untuk konsistensi adalah mengurangi pergeseran bola sesudah release pada drum 4, dengan margin 5 mm tetap aktif. [Ringkasan semua run](../ros2_ws/evidence/compact-start/guard-wLKo/verification.json) · [Trace fixture](../ros2_ws/evidence/compact-start/guard-wLKo/near-wall/result.json)
