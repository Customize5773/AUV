# 74 — Gripper di tengah, pendek saat membawa, dan bola awal

> Riwayat versi slider. Pada 18 November pengguna memilih gripper pendek dan tetap, tanpa mekanisme memanjang. Hasil di bawah berlaku pada versi slider; status revisi aktif ada di [STATUS](../STATUS.md).

16–17 November 2026. Permintaan pengguna: tempatkan gripper di tengah body, rapatkan ke AUV, dan perbaiki bola awal yang terlihat berada di tempat lain. Pekerjaan dibatasi pada simulator.

## Penyebab posisi bola lama

Sebelumnya, titik pickup berada `(−0,20, 0, −0,40) m`, tetapi payload awal ditahan dropper pada `(+0,20, 0, −0,18) m`. Gripper juga hanya dibuat pada mode extended. Jadi bola dan alat pickup memang merupakan dua titik terpisah; ini tidak sesuai tampilan yang diminta pengguna.

## Geometri sekarang

- Titik gripper tepat di tengah body: **x = 0, y = 0**.
- Posisi tersimpan/loaded **z = −0,18 m**. Karena bawah hull z = −0,10 m, pusat bola berjarak **8 cm dari bawah hull**, dibanding 30 cm sebelumnya.
- Slider memanjang **22 cm** hanya saat pickup, mencapai z = −0,40 m untuk menjangkau dasar drum. Setelah bola terpasang, slider kembali pendek dan membawa bola melalui joint fisika. Di kualifikasi, slider dikunci pada posisi pendek dan tanpa payload.
- Carrier memakai joint prismatic dengan batas posisi, kecepatan 0,18 m/s dan gaya 3 N. Ini parameter aktuator latihan, bukan kalibrasi servo nyata. Rod disimpan ke dalam body saat retract.
- Payload awal memakai fixed joint pemuatan pada carrier hingga release. SDF spawn dan posisi fisika memakai titik yang sama, sehingga tidak ada perpindahan awal dari lokasi dropper lama.
- Kamera bawah bergeser 16 cm ke depan agar bola/gripper tengah tidak menutup lensa. Origin pada proyeksi pixel/ray ikut berubah; kamera depan tetap.
- Controller drop sekarang alignment ke tengah body. Referee memakai extension terukur dari fisika untuk envelope dan retensi. Toleransi jarak retensi tetap 7,5 cm, dengan transform roll/pitch/yaw penuh.

![Render inspeksi gripper tengah dengan payload awal](../ros2_ws/evidence/gripper-centered-20261116/initial.png)

Render berasal dari kamera spectator Gazebo, bukan desktop. Lampu inspeksi ditambahkan hanya pada world capture agar bagian bawah terlihat jelas; arena penerimaan tidak diberi lampu tambahan. Payload awal dan titik gripper berimpit pada **110 snapshot capture final**, dengan joint pemuatan terpasang dan slider tersimpan. Selisih maksimum tercatat 0,000 m pada resolusi telemetri; geometri SDF juga memverifikasi spawn pada titik yang sama sebelum tick pertama.

## Diagnosis release — kegagalan tetap disimpan

Percobaan extended pertama mencapai tiga flare dan release, tetapi gagal memasukkan payload ke drum. Joint terlepas; collision ujung jari menahan bola. Bukaan lama **34 mm**, lebih sempit daripada bola **40 mm**. Uji release singkat dengan collision gripper dibuang *hanya pada salinan diagnostik* membuat bola jatuh; dengan collision lama, bola tetap tertahan. Cara pelepasan joint dicocokkan dengan [implementasi resmi Fortress](https://github.com/gazebosim/gz-sim/blob/ign-gazebo6/src/systems/detachable_joint/DetachableJoint.cc).

Produksi mempertahankan seluruh collision. Ujung jari kini menghasilkan bukaan **42 mm** dan diberi stem penghubung. Atap menjadi bidang kontak saat pickup; pendekatan turun 2 mm melewati titik tangensi memastikan kontak sebelum settling, dengan clearance hull–rim nominal sekitar 1,8 cm. Uji release setelah koreksi membuktikan bola jatuh lewat gravitasi, tanpa teleport atau pengubahan drum/target.

Percobaan gagal: [extended-1](../ros2_ws/evidence/gripper-centered-20261116/extended-1/mission.json). Probe diagnostik: [dengan jari lama](../ros2_ws/evidence/gripper-centered-20261116/release-with-jaws/physics.json), [tanpa collision—diagnostik](../ros2_ws/evidence/gripper-centered-20261116/release-no-jaws/physics.json), [collision produksi terkoreksi](../ros2_ws/evidence/gripper-centered-20261116/release-corrected/physics.json).

## Penerimaan akhir — selesai

Build plugin dan paket selesai. **197 tes lulus**, termasuk pose awal, bukaan bebas bola, proyeksi kamera, retensi selama retract, penolakan stroke invalid dan alignment ke tengah. Tiga misi dinamis pada source final diterima; seluruhnya DONE dan shutdown bersih, tanpa cleanup paksa grup POV.

| Kasus | Hasil |
|---|---|
| ARENA extended GUI/dua POV, varian 1, pinger drum 4, blue drum 3, Y–B–R, air 0,05/m | Lulus; **290,79048 poin**, thrust–surface **206,984 s**, penalti nol |
| ARENA blue drum, seed 91, air 0,05/m | Lulus; **210,13954 poin**, thrust–surface **228,682 s**, penalti nol |
| Kualifikasi jalur 3, offset lateral 0,15 m, air 0,10/m | Lulus pergi → U-turn → kembali → surface → stop; finish gate **23,358 s**, thrust–surface **26,452 s**, thrust–stop **31,042 s** |

Slider mencapai **0,220 m** dan kembali tersimpan (extension akhir sekitar 0,000000109 m). Sebanyak **1.348 snapshot** sesudah pickup membuktikan attachment bertahan sampai stop. Jarak maksimum bola ke titik carrier **4,882 cm**, tetap di bawah batas retensi **7,5 cm**. Joint mempertahankan offset kontak yang sebenarnya; bola tidak diteleport ke pusat saat pickup. Ini bukti latch kontak, bukan pembuktian gaya jepit jari.

Render awal memakai source final. Capture kamera bawah saat navigasi juga menunjukkan lensa tidak tertutup payload/gripper: [POV](../ros2_ws/evidence/gripper-centered-20261116/extended-2/camera-clearance.png). [Video POV extended](../ros2_ws/evidence/gripper-centered-20261116/extended-2/pov.mp4) hanya merekam kamera simulator, tanpa desktop.

[Verifikasi akhir](../ros2_ws/evidence/gripper-centered-20261116/verification.json) mencocokkan **98 file source/aset**, geometri, spawn, release lewat gravitasi, stroke penuh, retract dan tiga pemeriksa misi. [Log tes](../ros2_ws/evidence/gripper-centered-20261116/unit-tests-release.log) · [Build](../ros2_ws/evidence/gripper-centered-20261116/build-loading-joint.log). Perubahan bukaan setelah build berupa geometri Python; plugin C++ yang diuji sama dengan binary pada manifest.

Ulangi verifier dari `ros2_ws`: `bash tools/ros.sh python evidence/gripper-centered-20261116/verify.py`. Bukti gagal dan probe diagnostik tetap disimpan; collision tidak dimatikan pada produksi atau tiga misi penerimaan.

## Batas

Slider, gaya dan latch adalah mekanisme latihan simulator. Fixed joint pickup hanya dibuat setelah kontak teramati, tetapi belum merupakan model jepitan/gesekan servo dua jari nyata. Ruang rod di dalam body, ukuran dan daya aktuator belum tervalidasi untuk fabrikasi. Pengujian kendaraan fisik tetap dikecualikan sesuai permintaan pengguna. Source FBX/mesh hull tidak diubah.
