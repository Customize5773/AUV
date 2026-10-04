"""End-to-end UI check. Only starts/writes the explicitly labelled demo vehicle."""
import argparse
import json
from pathlib import Path

import httpx
from playwright.sync_api import expect, sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument("--url", default="http://127.0.0.1:8081")
parser.add_argument("--output", type=Path, default=Path("evidence"))
parser.add_argument("--read-only", action="store_true", help="Inspect the existing connection without changing it or writing parameters")
parser.add_argument("--desktop-only", action="store_true", help="Check desktop layouts only")
args = parser.parse_args()
args.output.mkdir(exist_ok=True, parents=True)
with httpx.Client(base_url=args.url) as client:
    connection = client.get("/api/state").json()["vehicle"]["connection"]
    if connection and connection["kind"] != "demo" and not args.read_only:
        raise SystemExit("Disconnect the real/SITL connection before this demo-only browser check.")
    if args.read_only and not connection:
        raise SystemExit("Connect a source before running the read-only browser check.")

errors, external, failures, mutations = [], [], [], []
with sync_playwright() as p:
    browser = p.chromium.launch(channel="chromium", headless=True, args=["--no-sandbox"])
    context = browser.new_context(viewport={"width": 1440, "height": 1100}, accept_downloads=True)
    page = context.new_page()
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda e: errors.append(e.text) if e.type == "error" else None)
    page.on("request", lambda r: external.append(r.url) if not r.url.startswith(args.url) else None)
    page.on("request", lambda r: mutations.append({"url": r.url, "method": r.method}) if r.method not in ("GET", "HEAD", "OPTIONS") else None)
    page.on("response", lambda r: failures.append({"url": r.url, "status": r.status}) if r.status >= 400 else None)
    page.goto(args.url, wait_until="networkidle")
    expect(page.locator('.host-indicator')).to_contain_text('Jetson aktif')
    if not args.read_only:
        if page.get_by_role('button', name='Coba demo', exact=True).count():
            page.get_by_role('button', name='Coba demo', exact=True).click()
        else:
            page.get_by_role("link", name="Koneksi", exact=True).click()
            page.get_by_label("Jenis koneksi").select_option("demo")
            page.get_by_role("button", name="Mulai demo", exact=True).click()
    expect(page.locator(".status-chip")).to_contain_text("Terhubung", timeout=10000)
    if not args.read_only:
        expect(page.locator(".demo-banner")).to_contain_text("Mode demo")
        expect(page.locator("main")).to_contain_text("15.80")
    page.screenshot(path=str(args.output / "dashboard-demo.png"), full_page=True, animations="disabled")

    page.get_by_role("link", name="Parameter", exact=True).click()
    page.get_by_role("textbox", name="Cari parameter").fill("PILOT_SPEED_DN")
    row = page.get_by_role("row").filter(has_text="PILOT_SPEED_DN")
    expect(row).to_be_visible(timeout=10000)
    row.get_by_role("button", name="Ubah").click()
    page.get_by_label("Nilai baru", exact=True).fill("40")
    page.get_by_role("checkbox").check()
    if args.read_only:
        page.get_by_role("button", name="Batal", exact=True).click()
    else:
        page.get_by_role("button", name="Kirim perubahan").click()
        expect(page.get_by_role("dialog")).not_to_be_visible(timeout=10000)
        expect(row).to_contain_text("40")
    with page.expect_download() as download:
        page.get_by_role("link", name="Ekspor", exact=True).click()
    exported = Path(download.value.path()).read_text()
    assert ("PILOT_SPEED_DN" if args.read_only else "PILOT_SPEED_DN\t40\t9") in exported
    page.get_by_role("button", name="Bandingkan cadangan", exact=True).click()
    comparison = page.get_by_role("region", name="Bandingkan cadangan")
    upload = comparison.get_by_label("File cadangan parameter")
    before_comparison = len(mutations)
    upload.set_input_files({"name": "snapshot.params", "mimeType": "text/plain", "buffer": exported.encode()})
    expect(comparison).to_contain_text("Tidak ada perbedaan.")
    data = [line.split() for line in exported.splitlines() if line and not line.startswith("#")]
    pilot = next(fields for fields in data if fields[2] == "PILOT_SPEED_DN")
    pilot[3] = str(float(pilot[3]) + 1)
    missing = next(fields for fields in data if fields[2] != "PILOT_SPEED_DN")
    data.remove(missing)
    data.append([pilot[0], pilot[1], "ZZ_TEST_BACKUP", "1", "9"])
    changed = '\n'.join('\t'.join(fields) for fields in data).encode()
    upload.set_input_files({"name": "changed.params", "mimeType": "text/plain", "buffer": changed})
    expect(comparison.get_by_role("row").filter(has_text="PILOT_SPEED_DN")).to_contain_text("Berubah")
    expect(comparison.get_by_role("row").filter(has_text="ZZ_TEST_BACKUP")).to_contain_text("Hanya di file")
    expect(comparison.get_by_role("row").filter(has_text=missing[2])).to_contain_text("Hanya di kendaraan")
    with page.expect_download() as download:
        comparison.get_by_role("button", name="Unduh perbandingan").click()
    report_data = json.loads(Path(download.value.path()).read_text())
    assert report_data['session'] and report_data['source']
    assert sum(r['status'] != 'same' for r in report_data['rows']) == 3
    different_target = '\n'.join('\t'.join(['254', *fields[1:]]) for fields in data).encode()
    upload.set_input_files({"name": "different-target.params", "mimeType": "text/plain", "buffer": different_target})
    expect(comparison).to_contain_text("ID berbeda:")
    upload.set_input_files({"name": "broken.params", "mimeType": "text/plain", "buffer": b"# broken\n1 1 BAD NaN 9"})
    expect(comparison.get_by_role("alert")).to_contain_text("Baris 2")
    expect(comparison.get_by_role("button", name="Unduh perbandingan")).not_to_be_visible()
    upload.set_input_files({"name": "large.params", "mimeType": "text/plain", "buffer": b"#" * (1024 * 1024 + 1)})
    expect(comparison.get_by_role("alert")).to_contain_text("1 MiB")
    upload.set_input_files({"name": "changed.params", "mimeType": "text/plain", "buffer": changed})
    expect(comparison.get_by_role("button", name="Unduh perbandingan")).to_be_visible()
    comparison_mutations = mutations[before_comparison:]
    assert not comparison_mutations, 'Comparison must not issue mutations'
    if page.get_by_role('button', name='Tutup notifikasi').count():
        page.get_by_role('button', name='Tutup notifikasi').click()
    page.screenshot(path=str(args.output / "parameters-demo.png"), full_page=True, animations="disabled")
    page.get_by_role('button', name='Daftar parameter', exact=True).click()
    expect(comparison).not_to_be_visible()
    page.get_by_role('button', name='Hapus pencarian').click()
    expect(page.get_by_role('textbox', name='Cari parameter')).to_have_value('')
    expect(page.get_by_role('region', name='Tabel parameter')).to_be_visible()
    page.screenshot(path=str(args.output / 'parameter-list.png'), full_page=True, animations='disabled')
    page.get_by_role('button', name='Bandingkan cadangan', exact=True).click()
    expect(comparison).to_contain_text('changed.params')
    page.get_by_role('link', name='Lewati navigasi').focus()
    page.keyboard.press('Enter')
    expect(page.locator('#main-content')).to_be_focused()
    assert page.url.endswith('#parameters')

    for name in ("Telemetri", "Sistem", "Log", "Koneksi", "Dashboard"):
        page.get_by_role("link", name=name, exact=True).click()
        expect(page.get_by_role("heading", name=name, exact=True)).to_be_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    page.get_by_role("link", name="Log", exact=True).click()
    if not args.read_only:
        expect(page.locator(".event-list")).to_contain_text("Nilai parameter dikonfirmasi", timeout=10000)
    with page.expect_download() as download:
        page.get_by_role("link", name="Unduh", exact=True).first.click()
    assert "source" in json.loads(Path(download.value.path()).read_text().splitlines()[0])

    if args.desktop_only:
        for width, height in ((1280, 800), (1440, 900), (1920, 1080)):
            page.set_viewport_size({'width': width, 'height': height})
            for name in ('Dashboard', 'Koneksi', 'Telemetri', 'Parameter', 'Sistem', 'Log'):
                page.get_by_role('link', name=name, exact=True).click()
                expect(page.get_by_role('heading', name=name, exact=True)).to_be_visible()
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), (width, name)
                assert page.evaluate('getComputedStyle(document.querySelector(".topbar")).position') == 'sticky'
            page.get_by_role('link', name='Dashboard', exact=True).click()
            if page.get_by_role('button', name='Tutup notifikasi').count():
                page.get_by_role('button', name='Tutup notifikasi').click()
            page.screenshot(path=str(args.output / f'dashboard-{width}.png'), full_page=True, animations='disabled')

    if not args.desktop_only:
        page.set_viewport_size({"width": 390, "height": 844})
        for name in ("Dashboard", "Koneksi", "Telemetri", "Parameter", "Sistem", "Log"):
            page.get_by_role("button", name="Buka navigasi").click()
            page.get_by_role("link", name=name, exact=True).click()
            expect(page.get_by_role("heading", name=name, exact=True)).to_be_visible()
            if name == "Parameter":
                upload.set_input_files({"name": "changed.params", "mimeType": "text/plain", "buffer": changed})
                expect(comparison.get_by_role("button", name="Unduh perbandingan")).to_be_visible()
                if page.get_by_role("button", name="Tutup notifikasi").count():
                    page.get_by_role("button", name="Tutup notifikasi").click()
                page.screenshot(path=str(args.output / "parameter-comparison-mobile.png"), full_page=True, animations="disabled")
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), name
        page.get_by_role("button", name="Buka navigasi").click()
        page.get_by_role("link", name="Dashboard", exact=True).click()
        if page.get_by_role("button", name="Tutup notifikasi").count():
            page.get_by_role("button", name="Tutup notifikasi").click()
        page.screenshot(path=str(args.output / "dashboard-mobile.png"), full_page=True, animations="disabled")
    if not args.read_only:
        if not args.desktop_only:
            page.get_by_role("button", name="Buka navigasi").click()
        page.get_by_role("link", name="Parameter", exact=True).click()
        page.get_by_role("button", name="Bandingkan cadangan", exact=True).click()
        upload.set_input_files({"name": "changed.params", "mimeType": "text/plain", "buffer": changed})
        expect(comparison.get_by_role("button", name="Unduh perbandingan")).to_be_visible()
        page.get_by_role("button", name="Akhiri demo").click()
        expect(page.locator(".demo-banner")).not_to_be_visible()
        expect(page.locator(".status-chip")).to_contain_text("Belum terhubung")
        expect(comparison.get_by_role("button", name="Unduh perbandingan")).not_to_be_visible()
        expect(upload).to_be_disabled()
    browser.close()

report = {"ok": not errors and not external and not failures and (not args.read_only or not mutations), "read_only": args.read_only,
          "desktop_only": args.desktop_only,
          "mutations": mutations,
          "comparison_mutations": comparison_mutations,
          "javascript_errors": errors, "external_requests": external, "http_failures": failures,
          "checks": ["six desktop pages", "parameter view switching and search clear", "Jetson status indicator",
                     "parameter export", "telemetry download", "read-only backup comparison and report export",
                     "invalid and oversized backup rejected", "different target warning"] +
                    (["1280, 1440, 1920 desktop widths without overflow", "sticky desktop header"] if args.desktop_only else ["six mobile pages without overflow", "mobile backup comparison without overflow"]) +
                    (["parameter dialog opens and cancels"] if args.read_only else
                     ["explicit demo badge", "confirmed parameter write", "disconnect clears comparison"])}
(args.output / "browser-check.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
assert report["ok"]
