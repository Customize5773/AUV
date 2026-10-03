import json
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright

out = Path(__file__).resolve().parents[3] / 'plan/evidence/blueos-jetson'
out.mkdir(exist_ok=True)
report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'pages': [], 'page_errors': [], 'failed_requests': [], 'disabled_service_requests': []}
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 1000})
    # Keep the browser check local; external documentation/analytics are unnecessary.
    page.route('**/*', lambda route: route.continue_() if route.request.url.startswith(('http://127.0.0.1:8080/', 'data:', 'blob:')) else route.abort())
    disabled_prefixes = ('/wifi-manager/', '/cable-guy/', '/commander/', '/version-chooser/', '/kraken/')
    page.on('request', lambda request: report['disabled_service_requests'].append(request.url) if any('8080' + prefix in request.url for prefix in disabled_prefixes) else None)
    page.on('pageerror', lambda error: report['page_errors'].append(str(error)))
    page.on('response', lambda response: report['failed_requests'].append({'url': response.url, 'status': response.status}) if response.status >= 400 else None)
    for name, path in [('home', '/'), ('video', '/vehicle/video-manager'), ('system', '/tools/system-information')]:
        response = page.goto('http://127.0.0.1:8080' + path, wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(10000)
        tour = page.get_by_role('button', name='Skip tour', exact=True)
        if tour.count() and tour.first.is_visible():
            tour.first.click()
        skip = page.get_by_role('button', name='Skip Wizard', exact=True)
        if skip.count() and skip.first.is_visible():
            skip.first.click()
            page.get_by_role('button', name='Remind me later', exact=True).click()
            page.wait_for_timeout(2000)
        for _ in range(3):
            close = page.get_by_role('button', name='Close', exact=True)
            visible = [close.nth(i) for i in range(close.count()) if close.nth(i).is_visible()]
            if not visible:
                break
            visible[-1].click()
            page.wait_for_timeout(500)
        body = page.inner_text('body')
        page.screenshot(path=str(out / f'blueos-browser-{name}.png'), full_page=True)
        report['pages'].append({'name': name, 'url': page.url, 'status': response.status, 'title': page.title(), 'body_text': body})
    page.get_by_role('tab', name='About', exact=True).click()
    page.wait_for_timeout(2500)
    report['about_text'] = page.inner_text('body')
    page.screenshot(path=str(out / 'blueos-browser-about.png'), full_page=True)
    browser.close()
report['checks'] = {
    'no_javascript_exceptions': not report['page_errors'],
    'no_502': not any(r['status'] == 502 for r in report['failed_requests']),
    'no_disabled_service_requests': not report['disabled_service_requests'],
    'direct_routes_http_200': all(p['status'] == 200 for p in report['pages']),
    'hydroships_visible': all('HydroShips' in p['body_text'] for p in report['pages']),
    'temperature_rendered': any(p['name'] == 'system' and 'cpu-thermal' in p['body_text'] and 'Peak (session)' in p['body_text'] for p in report['pages']),
    'jetson_model_rendered': 'NVIDIA Jetson Orin NX' in report['about_text'],
}
(out / 'blueos-browser-check.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report['checks'], indent=2))
raise SystemExit(0 if all(report['checks'].values()) else 1)
