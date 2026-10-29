# Graphify untuk repo AUV

Diperbarui 29 Oktober 2026 ke **graphifyy 0.9.97**, cocok dengan upstream resmi [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify), commit `0a8cd4e1e342235fe53e881fb5d591bf0460071f`. Skill lama yang terdeteksi bertanda 0.9.30. CLI sebelumnya gagal `ModuleNotFoundError: No module named 'graphify'`; sekarang dipasang lewat `uv tool` pada lingkungan Python tersendiri, terpisah dari ROS dan HydroShips.

## Penggunaan

Jalankan dari root repo:

```bash
cd /home/rasya/AUV
graphify --version
GRAPHIFY_BACKEND=none graphify query "StateEstimator" --budget 1500
GRAPHIFY_BACKEND=none graphify path "PhysicalRuntime" "StateEstimator" --undirected
# Setelah perubahan source:
GRAPHIFY_BACKEND=none graphify update .
```

Hasil lokal:

- [graph.html](../graphify-out/graph.html): peta interaktif, buka melalui browser.
- [GRAPH_REPORT.md](../graphify-out/GRAPH_REPORT.md): ringkasan komunitas dan hubungan.
- [graph.json](../graphify-out/graph.json): indeks untuk query/path/explain.
- [verification.json](../graphify-out/verification.json): versi, integritas graph, dan hasil pemeriksaan pembaruan.

`graphify-out/` tetap diabaikan Git. Indeks dibangun ulang karena folder lama tidak tersedia. Ekstraksi awal memakai `graphify extract . --code-only`; `graphify update .` kemudian menambahkan ekstraksi struktural Markdown yang didukung versi ini. `GRAPHIFY_BACKEND=none` menonaktifkan backend LLM, termasuk pemberian nama komunitas melalui LLM. Token API pada laporan: 0. Struktur Markdown tidak sama dengan pemahaman semantik penuh isi dokumen.

PDF, gambar, video, dan konversi DOCX belum diaktifkan. Sebagian berkas kode tidak menghasilkan simbol, misalnya modul kosong atau aset frontend hasil build; berkas dengan ekstensi tidak didukung dicatat oleh laporan. `.gitignore` tetap dihormati, termasuk pengecualian `vision-test/`. Graph tidak mewakili seluruh berkas fisik repo.

## Integrasi assistant

Instalasi resmi untuk repo menghasilkan:

- [AGENTS.md](../AGENTS.md): panduan penggunaan graph dan pembaruan sesudah perubahan kode.
- [.codex/skills/graphify/SKILL.md](../.codex/skills/graphify/SKILL.md) beserta references dan penanda versi.
- [.codex/hooks.json](../.codex/hooks.json): hook kompatibilitas `graphify hook-check`. Pada versi ini hook Codex sengaja no-op; panduan aktif berasal dari AGENTS.md, bukan layanan watcher latar belakang.

Skill global Claude dan Copilot yang sebelumnya sudah ada juga diperbarui; installer menyimpan salinan `SKILL.md.bak` bila berbeda. Registrasi skill baru mungkin baru terlihat setelah sesi assistant dimuat ulang. CLI bisa langsung digunakan.

## Memasang ulang dan memperbarui

Pada mesin baru:

```bash
uv tool install graphifyy==0.9.97
graphify install --project --platform codex
GRAPHIFY_BACKEND=none graphify extract . --code-only --max-workers 2
GRAPHIFY_BACKEND=none graphify update .
```

Untuk mengikuti rilis berikutnya:

```bash
uv tool upgrade graphifyy
graphify install --project --platform codex
# Perbarui juga integrasi global yang memang dipakai:
graphify install --platform claude
graphify install --platform copilot
GRAPHIFY_BACKEND=none graphify update .
```

Uji lokal membuktikan CLI, pembuatan graph/report/HTML, query, path, serta pembaruan inkremental bekerja. Pemeriksaan graph menemukan satu self-loop yang benar-benar mewakili rekursi `clean()` pada `hydroships/backend/hydroships/storage.py`; tidak ada endpoint hilang. Tampilan HTML dibuat tetapi interaksi browser belum diuji. MCP/server dan ekstraksi semantik berbayar tidak dikonfigurasi.
