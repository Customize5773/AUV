"""Exercise the autonomous UI against an isolated software-test service."""
import argparse
import json
import time
from pathlib import Path

import httpx
from playwright.sync_api import expect, sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--url', default='http://127.0.0.1:8083')
parser.add_argument('--output', type=Path, default=Path('evidence/autonomy'))
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
with httpx.Client(base_url=args.url) as client:
    initial = client.get('/api/autonomy').json()
    assert initial['runtime']['task_driver'] == 'synthetic'
    assert initial['runtime']['domain'] == 77, 'Use the isolated test service/domain 77.'
errors, failures = [], []
mission_name = f'Uji browser SAUVC {time.time_ns() % 1000000}'
with sync_playwright() as p:
    browser = p.chromium.launch(channel='chromium', headless=True, args=['--no-sandbox'])
    context = browser.new_context(viewport={'width': 1440, 'height': 1100}, accept_downloads=True)
    page = context.new_page()
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('console', lambda e: errors.append(e.text) if e.type == 'error' else None)
    page.on('response', lambda r: failures.append({'url': r.url, 'status': r.status}) if r.status >= 400 else None)
    page.goto(args.url + '/#autonomy')
    expect(page.get_by_role('heading', name='Autonomous', exact=True)).to_be_visible()
    expect(page.get_by_label('Runtime ROS 2')).to_contain_text('Siap', timeout=15000)
    page.get_by_label('Nama misi', exact=True).fill(mission_name)
    page.get_by_label('Timeout tahap 1', exact=True).fill('3')
    page.get_by_role('button', name='Tambah tahap').click()
    page.get_by_label('Nama tahap 3', exact=True).fill('Lokalisasi uji')
    page.get_by_label('Jenis tugas 3', exact=True).select_option('localization')
    page.get_by_role('button', name='Naikkan tahap 3', exact=True).click()
    expect(page.get_by_label('Nama tahap 2', exact=True)).to_have_value('Lokalisasi uji')
    page.get_by_role('button', name='Hapus tahap 2', exact=True).click()
    page.get_by_role('button', name='Simpan rencana', exact=True).click()
    expect(page.get_by_role('button', name='Jalankan uji software')).to_be_enabled()
    page.reload()
    expect(page.get_by_label('Nama misi', exact=True)).to_have_value(mission_name)
    status = page.get_by_test_id('mission-status')
    for scenario, result in [('success', 'Selesai'), ('failure', 'Gagal'), ('no_response', 'Gagal')]:
        page.get_by_label('Skenario respons tugas').select_option(scenario)
        page.get_by_role('button', name='Jalankan uji software').click()
        expect(status).to_have_text('Berjalan', timeout=10000)
        expect(page.get_by_label('Nama misi', exact=True)).to_be_disabled()
        expect(status).to_have_text(result, timeout=12000)
        with page.expect_download() as download:
            page.locator('.auto-history a').first.click()
        report = json.loads(Path(download.value.path()).read_text())
        assert report['scenario'] == scenario and report['mode'] == 'software_test'
        if scenario == 'no_response': assert 'Timeout' in report['detail']
    page.get_by_role('button', name='Jalankan uji software').click()
    expect(status).to_have_text('Berjalan')
    page.get_by_role('button', name='Batalkan', exact=True).click()
    expect(status).to_have_text('Dibatalkan')
    page.get_by_role('button', name='Hentikan runtime', exact=True).click()
    expect(page.get_by_role('button', name='Mulai runtime', exact=True)).to_be_visible()
    expect(page.get_by_role('button', name='Jalankan uji software')).to_be_disabled()
    page.get_by_role('button', name='Mulai runtime', exact=True).click()
    expect(page.get_by_label('Runtime ROS 2')).to_contain_text('Siap', timeout=15000)
    expect(status).to_have_text('Dibatalkan')
    expect(page.locator('.auto-graph')).to_contain_text('/auv2027/mission_executor')
    for width in [1280, 1440, 1920]:
        page.set_viewport_size({'width': width, 'height': 1100})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'Horizontal overflow: {width}'
        page.screenshot(path=str(args.output / f'autonomous-{width}.png'), full_page=True, animations='disabled')
    page.reload()
    expect(status).to_have_text('Dibatalkan')
    assert not errors, errors
    assert not failures, failures
    browser.close()
summary = {'result': 'passed', 'desktop_widths': [1280, 1440, 1920],
           'checks': ['plan edit/add/reorder/delete/save/reload', 'success/failure/timeout',
                      'abort', 'runtime stop/start without resume', 'JSON reports', 'ROS graph'],
           'console_errors': errors, 'http_failures': failures}
(args.output / 'browser.json').write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
