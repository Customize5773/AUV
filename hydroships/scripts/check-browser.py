"""End-to-end UI check. Only starts/writes the explicitly labelled demo vehicle."""
import argparse
import json
from pathlib import Path

import httpx
from playwright.sync_api import expect, sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument("--url", default="http://127.0.0.1:8081")
parser.add_argument("--output", type=Path, default=Path("evidence"))
args = parser.parse_args()
args.output.mkdir(exist_ok=True, parents=True)
with httpx.Client(base_url=args.url) as client:
    connection = client.get("/api/state").json()["vehicle"]["connection"]
    if connection and connection["kind"] != "demo":
        raise SystemExit("Disconnect the real/SITL connection before this demo-only browser check.")

errors, external, failures = [], [], []
with sync_playwright() as p:
    browser = p.chromium.launch(channel="chromium", headless=True, args=["--no-sandbox"])
    context = browser.new_context(viewport={"width": 1440, "height": 1100}, accept_downloads=True)
    page = context.new_page()
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda e: errors.append(e.text) if e.type == "error" else None)
    page.on("request", lambda r: external.append(r.url) if not r.url.startswith(args.url) else None)
    page.on("response", lambda r: failures.append({"url": r.url, "status": r.status}) if r.status >= 400 else None)
    page.goto(args.url, wait_until="networkidle")
    page.get_by_role("link", name="Koneksi", exact=True).click()
    page.get_by_label("Jenis koneksi").select_option("demo")
    page.get_by_role("button", name="Mulai demo", exact=True).click()
    expect(page.locator(".status-chip")).to_contain_text("Terhubung", timeout=10000)
    expect(page.locator(".demo-banner")).to_contain_text("Mode demo")
    expect(page.locator("main")).to_contain_text("15.80")
    page.screenshot(path=str(args.output / "dashboard-demo.png"), full_page=True)

    page.get_by_role("link", name="Parameter", exact=True).click()
    page.get_by_role("textbox", name="Cari parameter").fill("PILOT_SPEED_DN")
    row = page.get_by_role("row").filter(has_text="PILOT_SPEED_DN")
    expect(row).to_contain_text("50", timeout=10000)
    row.get_by_role("button", name="Ubah").click()
    page.get_by_label("Nilai baru", exact=True).fill("40")
    page.get_by_role("checkbox").check()
    page.get_by_role("button", name="Kirim perubahan").click()
    expect(page.get_by_role("dialog")).not_to_be_visible(timeout=10000)
    expect(row).to_contain_text("40")
    with page.expect_download() as download:
        page.get_by_role("link", name="Ekspor", exact=True).click()
    assert "PILOT_SPEED_DN\t40\t9" in Path(download.value.path()).read_text()
    page.screenshot(path=str(args.output / "parameters-demo.png"), full_page=True)

    for name in ("Telemetri", "Sistem", "Log", "Koneksi", "Dashboard"):
        page.get_by_role("link", name=name, exact=True).click()
        expect(page.get_by_role("heading", name=name, exact=True)).to_be_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    page.get_by_role("link", name="Log", exact=True).click()
    expect(page.locator(".event-list")).to_contain_text("Nilai parameter dikonfirmasi", timeout=10000)
    with page.expect_download() as download:
        page.get_by_role("link", name="Unduh", exact=True).first.click()
    assert json.loads(Path(download.value.path()).read_text().splitlines()[0])["source"]["kind"] == "demo"

    page.set_viewport_size({"width": 390, "height": 844})
    for name in ("Dashboard", "Koneksi", "Telemetri", "Parameter", "Sistem", "Log"):
        page.get_by_role("button", name="Buka navigasi").click()
        page.get_by_role("link", name=name, exact=True).click()
        expect(page.get_by_role("heading", name=name, exact=True)).to_be_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), name
    page.get_by_role("button", name="Buka navigasi").click()
    page.get_by_role("link", name="Dashboard", exact=True).click()
    page.screenshot(path=str(args.output / "dashboard-mobile.png"), full_page=True)
    page.get_by_role("button", name="Akhiri demo").click()
    expect(page.locator(".demo-banner")).not_to_be_visible()
    expect(page.locator(".status-chip")).to_contain_text("Belum terhubung")
    browser.close()

report = {"ok": not errors and not external and not failures,
          "javascript_errors": errors, "external_requests": external, "http_failures": failures,
          "checks": ["six desktop pages", "six mobile pages without overflow", "explicit demo badge",
                     "confirmed parameter write", "parameter export", "telemetry download", "disconnect"]}
(args.output / "browser-check.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
assert report["ok"]
