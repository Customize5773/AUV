<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { Activity, ArrowDownToLine, ArrowRight, Battery, Cable, Check, ChevronRight, CircleHelp,
  Compass, Cpu, Database, FileText, Gauge, LayoutDashboard, LoaderCircle, Menu, Radio,
  RefreshCw, Search, Settings2, ShieldCheck, Thermometer, Waves, WifiOff, X } from 'lucide-vue-next'
import { api, useVehicle, type Connection, type Event } from './state'

const tabs = [
  {id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, caption: 'Ringkasan kendaraan'},
  {id: 'connection', label: 'Koneksi', icon: Cable, caption: 'Hubungkan autopilot'},
  {id: 'telemetry', label: 'Telemetri', icon: Activity, caption: 'Data kendaraan secara langsung'},
  {id: 'parameters', label: 'Parameter', icon: Settings2, caption: 'Konfigurasi autopilot'},
  {id: 'system', label: 'Sistem', icon: Cpu, caption: 'Kesehatan komputer onboard'},
  {id: 'logs', label: 'Log', icon: FileText, caption: 'Rekaman dan riwayat kejadian'},
]
const page = ref(tabs.some(t => t.id === location.hash.slice(1)) ? location.hash.slice(1) : 'dashboard')
const mobileMenu = ref(false)
function navigate(id: string) {location.hash = id; page.value = id; mobileMenu.value = false}
function hashChanged() {page.value = tabs.some(t => t.id === location.hash.slice(1)) ? location.hash.slice(1) : 'dashboard'}
const currentTab = computed(() => tabs.find(t => t.id === page.value)!)
const {state, online, history, now} = useVehicle()
const vehicle = computed(() => state.value?.vehicle)
const system = computed(() => state.value?.system)
const connected = computed(() => online.value && vehicle.value?.status === 'connected')
const attitudeLive = computed(() => connected.value && !!vehicle.value?.fields.roll && !!vehicle.value?.fields.pitch && !stale('roll') && !stale('pitch'))
const demo = computed(() => vehicle.value?.connection?.kind === 'demo')
const busy = ref(false)
const notice = ref<{text: string; error: boolean} | null>(null)
let noticeTimer: ReturnType<typeof setTimeout>
function notify(text: string, error = false) {notice.value = {text, error}; clearTimeout(noticeTimer); noticeTimer = setTimeout(() => notice.value = null, 7000)}
async function action(task: () => Promise<unknown>, success?: string) {
  if (busy.value) return
  busy.value = true
  try {await task(); if (success) notify(success)}
  catch (e) {notify(e instanceof Error ? e.message : 'Operasi gagal.', true)}
  finally {busy.value = false}
}
const statusLabel = computed(() => {
  if (!online.value) return 'Layanan terputus'
  return ({connected: 'Terhubung', connecting: 'Menghubungkan', reconnecting: 'Menyambung ulang', disconnected: 'Belum terhubung'} as Record<string, string>)[vehicle.value?.status || 'disconnected']
})
function field(key: string, digits = 1) {const f = vehicle.value?.fields[key]; return f ? f.value.toFixed(digits) : '—'}
function stale(key: string) {return !online.value || !!vehicle.value?.fields[key]?.stale}
function bytes(n?: number) {return n == null ? '—' : `${(n / 1024 ** 3).toFixed(1)} GB`}
function time(ts: number) {return new Date(ts * 1000).toLocaleTimeString('id-ID', {hour: '2-digit', minute: '2-digit', second: '2-digit'})}
function date(ts: number) {return new Date(ts * 1000).toLocaleString('id-ID')}
function duration(seconds?: number) {if (seconds == null) return '—'; const h = Math.floor(seconds / 3600); return `${h}j ${Math.floor(seconds % 3600 / 60)}m`}
const hottest = computed(() => system.value?.temperatures.length ? Math.max(...system.value.temperatures.map(t => t.celsius)) : null)
const clock = computed(() => new Date(now.value).toLocaleTimeString('id-ID', {hour: '2-digit', minute: '2-digit', second: '2-digit'}))
const telemetry = [
  {key: 'roll', label: 'Roll', unit: '°', icon: Gauge}, {key: 'pitch', label: 'Pitch', unit: '°', icon: Gauge},
  {key: 'heading', label: 'Heading', unit: '°', icon: Compass}, {key: 'voltage', label: 'Tegangan', unit: 'V', icon: Battery},
  {key: 'current', label: 'Arus', unit: 'A', icon: Activity}, {key: 'battery', label: 'Baterai', unit: '%', icon: Battery},
  {key: 'pressure', label: 'Tekanan eksternal', unit: 'hPa', icon: Waves},
  {key: 'water_temperature', label: 'Suhu sensor eksternal', unit: '°C', icon: Thermometer},
  {key: 'altitude', label: 'Altitude autopilot', unit: 'm', icon: Gauge},
]
function chart(key: 'roll' | 'pitch') {
  return history.value.map((p, i) => `${i / 119 * 600},${80 - Math.max(-30, Math.min(30, p[key])) / 30 * 65}`).join(' ')
}

type Port = {path: string; description: string; stable: boolean; serial: string | null}
const ports = ref<Port[]>([])
const connection = ref<Connection>({kind: 'serial', endpoint: '', baud: 115200})
const name = ref('HydroShips')
watch(() => connection.value.kind, kind => {
  if (kind === 'udp' && !connection.value.endpoint.startsWith('127.0.0.1:')) connection.value.endpoint = '127.0.0.1:14560'
  if (kind === 'serial' && !ports.value.some(p => p.path === connection.value.endpoint)) connection.value.endpoint = ''
})
async function loadPorts() {try {ports.value = (await api<{items: Port[]}>('/ports')).items} catch (e) {notify(String(e), true)}}
async function connectVehicle() {await action(async () => {await api('/connection', 'POST', connection.value); navigate('dashboard')}, 'Koneksi sedang dibuka. Menunggu heartbeat autopilot.')}
async function startDemo() {await action(() => api('/connection', 'POST', {kind: 'demo'})); navigate('dashboard')}
async function disconnect() {await action(() => api('/connection', 'DELETE'), 'Koneksi diputus.')}

type Parameter = {name: string; value: number; type: number; index: number; updated: number}
const parameters = ref<{session: string; state: string; expected: number; items: Parameter[]}>({session: '', state: 'idle', expected: 0, items: []})
const search = ref('')
const paramPage = ref(1)
const filteredParams = computed(() => parameters.value.items.filter(p => p.name.toLowerCase().includes(search.value.toLowerCase())))
const visibleParams = computed(() => filteredParams.value.slice((paramPage.value - 1) * 40, paramPage.value * 40))
const paramPages = computed(() => Math.max(1, Math.ceil(filteredParams.value.length / 40)))
const editing = ref<Parameter | null>(null)
const editingSession = ref('')
// Vue converts number inputs to numbers even without the .number modifier.
const newValue = ref<string | number>('')
const parameterInputValid = computed(() => String(newValue.value).trim() !== '' && Number.isFinite(Number(newValue.value)))
const dialog = ref<HTMLDialogElement | null>(null)
const confirmed = ref(false)
const editAllowed = computed(() => connected.value && vehicle.value?.write_allowed && parameters.value.state === 'complete')
const typeNames: Record<number, string> = {1: 'UINT8', 2: 'INT8', 3: 'UINT16', 4: 'INT16', 5: 'UINT32', 6: 'INT32', 9: 'FLOAT32'}
async function loadParameters() {parameters.value = await api('/parameters')}
function editParameter(p: Parameter) {editing.value = {...p}; editingSession.value = parameters.value.session; newValue.value = String(p.value); confirmed.value = false; dialog.value?.showModal()}
function closeEditor() {dialog.value?.close(); editing.value = null}
async function saveParameter() {
  const p = editing.value
  if (!p || !confirmed.value || !parameterInputValid.value) return
  await action(async () => {
    await api(`/parameters/${p.name}`, 'PUT', {session: editingSession.value, expected: p.value, value: Number(newValue.value)})
    closeEditor(); await loadParameters(); notify('Nilai parameter dikonfirmasi oleh autopilot.')
  })
}
const events = ref<Event[]>([])
const logFiles = ref<{name: string; bytes: number; modified: number}[]>([])
const logFilter = ref('all')
const filteredEvents = computed(() => events.value.filter(e => logFilter.value === 'all' || e.level === logFilter.value))
async function loadLogs() {
  const [ev, logs] = await Promise.all([api<{items: Event[]}>('/events?limit=200'), api<{items: typeof logFiles.value}>('/logs')])
  events.value = ev.items; logFiles.value = logs.items
}
function exportEvents() {
  const blob = new Blob([JSON.stringify(events.value, null, 2)], {type: 'application/json'})
  const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = 'hydroships-events.json'; a.click(); URL.revokeObjectURL(url)
}
watch(search, () => paramPage.value = 1)
watch(() => vehicle.value?.session, () => {parameters.value = {session: '', state: 'idle', expected: 0, items: []}; if (editing.value) {closeEditor(); notify('Sesi berubah. Editor parameter ditutup.', true)}})
watch(page, () => {if (page.value === 'connection') void loadPorts(); if (page.value === 'parameters') void action(loadParameters); if (page.value === 'logs') void action(loadLogs)})
let poll: ReturnType<typeof setInterval>
let polling = false
onMounted(async () => {
  window.addEventListener('hashchange', hashChanged)
  await loadPorts()
  try {
    const settings = await api<{name: string; connection: Connection | null}>('/settings')
    name.value = settings.name
    if (settings.connection) connection.value = {kind: settings.connection.kind, endpoint: settings.connection.kind === 'demo' ? '' : settings.connection.endpoint, baud: settings.connection.baud || 115200}
    if (page.value === 'parameters') await loadParameters()
    if (page.value === 'logs') await loadLogs()
  } catch (e) {notify(String(e), true)}
  poll = setInterval(async () => {
    if (!online.value || polling || busy.value) return
    polling = true
    try {if (page.value === 'parameters') await loadParameters(); if (page.value === 'logs') await loadLogs()}
    catch { /* WebSocket status shows an unavailable service; avoid repetitive toasts. */ }
    finally {polling = false}
  }, 2000)
})
onUnmounted(() => {clearInterval(poll); clearTimeout(noticeTimer); window.removeEventListener('hashchange', hashChanged)})
</script>

<template>
  <div class="shell">
    <button v-if="mobileMenu" class="sidebar-backdrop" aria-label="Tutup menu" @click="mobileMenu = false"></button>
    <aside class="sidebar" :class="{open: mobileMenu}">
      <a class="brand" href="#dashboard" @click="navigate('dashboard')"><span class="brand-mark"><Waves :size="25" /></span><span>HYDRO<span class="brand-light">SHIPS</span><small>ONBOARD CONSOLE</small></span></a>
      <div class="nav-caption">WORKSPACE</div>
      <nav aria-label="Navigasi utama"><a v-for="tab in tabs" :key="tab.id" :href="`#${tab.id}`" :class="{active: page === tab.id}" :aria-current="page === tab.id ? 'page' : undefined" @click="navigate(tab.id)"><component :is="tab.icon" :size="19" /><span>{{ tab.label }}</span><span v-if="tab.id === 'connection'" class="nav-dot" :class="{live: connected}"></span></a></nav>
      <div class="sidebar-bottom"><div class="onboard-card"><span class="small-dot" :class="{live: online}"></span><div><strong>{{ online ? 'Layanan aktif' : 'Menghubungkan layanan' }}</strong><small>JETSON COMPANION</small></div><Cpu :size="18" /></div><div class="sidebar-foot"><span>HydroShips <b>v{{ state?.version || '0.1.0' }}</b></span><ShieldCheck :size="15" /></div></div>
    </aside>

    <div class="workspace">
      <header class="topbar"><div class="breadcrumb"><button class="icon-button mobile-toggle" aria-label="Buka navigasi" @click="mobileMenu = true"><Menu :size="22" /></button><span>Workspace</span><ChevronRight :size="14" /><strong>{{ currentTab.label }}</strong></div><div class="topbar-right"><span class="local-clock">{{ clock }} <span>LOCAL</span></span><span class="status-chip" :class="{green: connected, muted: !connected}"><span class="small-dot" :class="{live: connected}"></span>{{ statusLabel }}</span><span class="avatar" title="HydroShips">HS</span></div></header>
      <main>
        <div v-if="!online" class="banner warning" role="status"><WifiOff :size="18" /><span>Layanan belum tersambung. Menyambung ulang otomatis; data yang tersimpan mungkin sudah lama.</span></div>
        <div v-if="demo" class="banner demo-banner" role="status"><Radio :size="18" /><span><strong>Mode demo.</strong> Data kendaraan berasal dari simulator MAVLink sederhana. Informasi Jetson tetap data nyata.</span><button :disabled="busy" @click="disconnect">Akhiri demo <X :size="14" /></button></div>
        <div v-if="vehicle?.connection?.kind === 'udp'" class="banner neutral" role="status"><Radio :size="18" /><span>Sumber telemetri: <strong>UDP lokal</strong> · {{ vehicle.connection.endpoint }}</span></div>
        <div class="page-heading"><div><div class="eyebrow">{{ page === 'dashboard' ? 'VEHICLE OVERVIEW' : 'VEHICLE CONSOLE' }}</div><h1>{{ currentTab.label }}</h1><p>{{ currentTab.caption }}{{ page === 'dashboard' ? ' dan komputer onboard dalam satu tempat.' : '.' }}</p></div><button v-if="page === 'dashboard'" class="button primary" @click="navigate('connection')"><Cable :size="17" /> Kelola koneksi <ArrowRight :size="16" /></button><button v-if="page === 'logs'" class="button" :disabled="busy" @click="action(loadLogs)"><RefreshCw :size="16" /> Muat ulang</button></div>

        <template v-if="page === 'dashboard'">
          <section class="vehicle-hero"><div class="hero-content"><div class="hero-label"><span class="small-dot" :class="{live: connected}"></span>{{ demo ? 'DEMO VEHICLE' : 'AUTONOMOUS UNDERWATER VEHICLE' }}</div><h2>{{ state?.name || 'HydroShips' }}</h2><p>{{ connected ? 'Telemetri masuk. Pantau status dan konfigurasi kendaraan.' : 'Siap terhubung. Pilih Pixhawk untuk mulai membaca telemetri.' }}</p><div class="hero-tags"><span><Cpu :size="14" /> Jetson onboard</span><span><Cable :size="14" /> {{ connected ? (demo ? 'MAVLink demo' : 'MAVLink connected') : 'Menunggu autopilot' }}</span></div></div><div class="hero-instrument" aria-hidden="true"><div class="sonar sonar-one"></div><div class="sonar sonar-two"></div><div class="sonar sonar-three"></div><div class="sonar-axis"></div><div class="vehicle-symbol"><span></span><i></i><b></b></div><div class="sonar-label">{{ connected ? 'LINK ESTABLISHED' : 'AWAITING CONNECTION' }}</div></div></section>
          <div class="metric-grid four"><article class="metric-card"><div class="metric-top">Autopilot <Cable :size="18" /></div><div class="metric-value small">{{ connected ? (demo ? 'ArduSub demo' : vehicle?.identity.autopilot === 3 ? 'ArduPilot' : 'Autopilot') : 'Belum terhubung' }}</div><div class="metric-foot"><span class="small-dot" :class="{live: connected}"></span>{{ vehicle?.identity.firmware ? `Firmware ${vehicle.identity.firmware}` : 'Menunggu identitas perangkat' }}</div></article><article class="metric-card"><div class="metric-top">Mode kendaraan <Gauge :size="18" /></div><div class="metric-value small">{{ connected ? vehicle?.identity.mode || '—' : '—' }}</div><div class="metric-foot">{{ connected ? (vehicle?.identity.armed ? 'Armed' : 'Disarmed') : 'Diperbarui dari heartbeat' }}</div></article><article class="metric-card" :class="{stale: stale('voltage')}"><div class="metric-top">Tegangan baterai <Battery :size="18" /></div><div class="metric-value">{{ field('voltage', 2) }} <small>V</small></div><div class="metric-foot">{{ vehicle?.fields.voltage ? (stale('voltage') ? 'Data lama' : `Sisa baterai ${field('battery', 0)}%`) : 'Menunggu telemetri baterai' }}</div></article><article class="metric-card"><div class="metric-top">Suhu Jetson tertinggi <Thermometer :size="18" /></div><div class="metric-value">{{ hottest?.toFixed(1) || '—' }} <small>°C</small></div><div class="metric-foot">{{ system?.temperatures.length || 0 }} sensor termal · {{ online ? 'Langsung' : 'Data lama' }}</div></article></div>
          <div class="dashboard-grid"><section class="panel"><div class="panel-heading"><h3><Compass :size="17" /> Orientasi kendaraan</h3><span class="live-label" :class="{active: attitudeLive}"><span class="small-dot" :class="{live: attitudeLive}"></span>{{ attitudeLive ? 'LIVE' : 'NO SIGNAL' }}</span></div><div class="attitude-area"><div class="attitude-dial" :class="{inactive: !attitudeLive}"><div class="attitude-world" :style="{transform: `rotate(${-(vehicle?.fields.roll?.value || 0)}deg) translateY(${(vehicle?.fields.pitch?.value || 0) * 2}px)`}"><div class="sky"></div><div class="sea"></div><div class="horizon"></div><div class="pitch-line p1"></div><div class="pitch-line p2"></div><div class="pitch-line p3"></div></div><span class="attitude-n">N</span><div class="aircraft-marker"></div><div class="attitude-cross"></div></div><div class="attitude-values"><div><span>ROLL</span><strong>{{ field('roll') }}<small>°</small></strong></div><div><span>PITCH</span><strong>{{ field('pitch') }}<small>°</small></strong></div><div><span>HEADING</span><strong>{{ field('heading', 0) }}<small>°</small></strong></div></div></div><div class="panel-footer"><span>{{ attitudeLive ? 'Orientasi dari autopilot' : vehicle?.fields.roll ? 'Data orientasi kedaluwarsa' : 'Visual aktif setelah data orientasi diterima' }}</span><a href="#telemetry" @click="navigate('telemetry')">Lihat telemetri <ArrowRight :size="14" /></a></div></section>
          <section class="panel"><div class="panel-heading"><h3><Cpu :size="17" /> Komputer onboard</h3><span class="subtle-tag">JETSON</span></div><div class="system-summary"><h4>{{ system?.model || 'Memuat informasi sistem…' }}</h4><p>{{ system?.os || '—' }}</p><div class="resource"><div><span>CPU</span><strong>{{ system?.cpu_percent.toFixed(1) || '—' }}<small>%</small></strong></div><meter min="0" max="100" :value="system?.cpu_percent || 0" aria-label="Penggunaan CPU"></meter></div><div class="resource"><div><span>Memori</span><strong>{{ bytes(system?.memory.used) }} <small>/ {{ bytes(system?.memory.total) }}</small></strong></div><meter min="0" max="100" :value="system?.memory.percent || 0" aria-label="Penggunaan memori"></meter></div><div class="resource"><div><span>Penyimpanan</span><strong>{{ bytes(system?.disk.used) }} <small>/ {{ bytes(system?.disk.total) }}</small></strong></div><meter min="0" max="100" :value="system?.disk.percent || 0" aria-label="Penggunaan disk"></meter></div></div><div class="panel-footer"><span>Uptime {{ duration(system?.uptime) }}</span><a href="#system" @click="navigate('system')">Detail sistem <ArrowRight :size="14" /></a></div></section></div>
          <section class="panel activity-panel"><div class="panel-heading"><h3><Activity :size="17" /> Aktivitas terbaru</h3><a href="#logs" @click="navigate('logs')">Semua log <ArrowRight :size="14" /></a></div><div v-if="!state?.events.length" class="empty compact">Belum ada aktivitas.</div><div v-for="event in state?.events.slice(0, 4)" :key="event.id" class="event-row"><span class="event-mark" :class="event.level"><Check v-if="event.level === 'info'" :size="14" /><CircleHelp v-else :size="14" /></span><div><strong>{{ event.message }}</strong><small>{{ event.kind }}</small></div><time>{{ time(event.ts) }}</time></div></section>
        </template>

        <template v-else-if="page === 'connection'">
          <div class="two-columns"><section class="panel"><div class="panel-heading"><h3><Cable :size="18" /> Koneksi autopilot</h3><span class="subtle-tag">MAVLINK</span></div><form class="form-body" @submit.prevent="connectVehicle"><label>Jenis koneksi<select v-model="connection.kind" :disabled="busy"><option value="serial">USB serial · Pixhawk</option><option value="udp">UDP lokal · ArduSub SITL</option><option value="demo">Demo · simulator MAVLink</option></select></label><template v-if="connection.kind === 'serial'"><label>Perangkat<div class="input-action"><select v-model="connection.endpoint" required><option value="" disabled>Pilih perangkat USB</option><option v-for="port in ports" :key="port.path" :value="port.path">{{ port.description }} — {{ port.path }}</option></select><button class="icon-button" type="button" aria-label="Pindai ulang port" @click="loadPorts"><RefreshCw :size="18" /></button></div></label><p v-if="!ports.length" class="inline-note"><Cable :size="16" /> Belum ada port serial terdeteksi. Hubungkan Pixhawk melalui USB, lalu pindai ulang.</p><label>Baud rate<select v-model.number="connection.baud"><option v-for="rate in [57600, 115200, 230400, 460800, 921600]" :key="rate" :value="rate">{{ rate }}</option></select></label><p class="help-text">Pilih baud rate sesuai konfigurasi port autopilot. Sambung ulang otomatis tersedia untuk perangkat dengan identitas USB yang stabil.</p></template><template v-else-if="connection.kind === 'udp'"><label>Alamat penerima<input v-model="connection.endpoint" placeholder="127.0.0.1:14560" required pattern="127\.0\.0\.1:[0-9]{4,5}"></label><p class="help-text">Arahkan keluaran MAVLink SITL ke alamat ini. Layanan mendengarkan pada Jetson.</p></template><div v-else class="info-box"><Radio :size="22" /><div><strong>Jelajahi tanpa perangkat</strong><p>Demo menghasilkan telemetri dan parameter contoh melalui MAVLink. Demo tidak mensimulasikan fisika atau firmware ArduSub.</p></div></div><div class="form-actions"><button class="button primary" :disabled="busy || !online || (connection.kind === 'serial' && !connection.endpoint)"><LoaderCircle v-if="busy" class="spin" :size="16" /><Cable v-else :size="16" /> {{ connection.kind === 'demo' ? 'Mulai demo' : 'Hubungkan' }}</button><button class="button" type="button" :disabled="busy || !vehicle?.connection" @click="disconnect">Putuskan</button></div></form></section><div class="stack"><section class="panel"><div class="panel-heading"><h3>Status koneksi</h3><span class="small-dot" :class="{live: connected}"></span></div><dl class="detail-list"><div><dt>Status</dt><dd>{{ statusLabel }}</dd></div><div><dt>Sumber</dt><dd>{{ vehicle?.connection?.kind || '—' }}</dd></div><div><dt>System / component ID</dt><dd>{{ vehicle?.identity.system_id ?? '—' }} / {{ vehicle?.identity.component_id ?? '—' }}</dd></div><div><dt>Firmware</dt><dd>{{ vehicle?.identity.firmware || '—' }}</dd></div><div><dt>Heartbeat terakhir</dt><dd>{{ vehicle?.heartbeat_age == null ? '—' : `${vehicle.heartbeat_age.toFixed(1)} detik lalu` }}</dd></div><div><dt>Pesan diterima</dt><dd>{{ vehicle?.received.toLocaleString('id-ID') || '0' }}</dd></div></dl><div v-if="vehicle?.error" class="inline-error">{{ vehicle.error }}</div></section><section class="tip-card"><ShieldCheck :size="24" /><h3>Koneksi yang bisa dipantau</h3><p>Konfigurasi terakhir disimpan. Setelah aplikasi dimulai ulang, hubungkan perangkat dari halaman ini.</p><p>Perubahan parameter yang belum dikonfirmasi dibatalkan ketika koneksi terputus.</p></section><button v-if="connection.kind !== 'demo' && !connected" class="demo-button" :disabled="busy || !online" @click="startDemo"><Radio :size="18" /><span>Belum ada Pixhawk?<strong>Coba dengan data demo</strong></span><ArrowRight :size="18" /></button></div></div>
        </template>

        <template v-else-if="page === 'telemetry'">
          <div class="metric-grid three"><article v-for="item in telemetry" :key="item.key" class="metric-card" :class="{stale: stale(item.key)}"><div class="metric-top">{{ item.label }}<component :is="item.icon" :size="18" /></div><div class="metric-value">{{ field(item.key) }} <small>{{ item.unit }}</small></div><div class="metric-foot">{{ vehicle?.fields[item.key] ? (stale(item.key) ? 'Data lama · ' : '') + `${vehicle.fields[item.key].source} · ${vehicle.fields[item.key].age.toFixed(1)} dtk` : 'Belum ada data' }}</div></article></div><section class="panel"><div class="panel-heading"><h3><Activity :size="18" /> Riwayat orientasi</h3><div class="chart-legend"><span class="roll-key">Roll</span><span class="pitch-key">Pitch</span><span>60 detik terakhir</span></div></div><div v-if="!history.length" class="empty"><Activity :size="32" /><h3>Menunggu telemetri</h3><p>Grafik akan muncul setelah data orientasi diterima.</p><button class="button" @click="navigate('connection')">Buka koneksi <ArrowRight :size="15" /></button></div><div v-else class="chart-wrap"><div class="chart-scale"><span>+30°</span><span>0°</span><span>−30°</span></div><svg viewBox="0 0 600 160" preserveAspectRatio="none" role="img" aria-label="Grafik roll dan pitch, rentang minus 30 sampai 30 derajat"><path d="M0 15H600 M0 80H600 M0 145H600" class="chart-grid"/><polyline :points="chart('roll')" class="chart-line roll-line"/><polyline :points="chart('pitch')" class="chart-line pitch-line-chart"/></svg></div><div class="panel-footer"><span>Grafik mulai dari saat halaman terhubung; rekaman lengkap tersedia di Log.</span></div></section><p class="help-text telemetry-note">Altitude berasal dari VFR_HUD autopilot dan belum menjadi kedalaman terhadap permukaan air. Kedalaman memerlukan validasi sensor serta acuan permukaan pada perangkat nyata.</p>
        </template>

        <template v-else-if="page === 'parameters'">
          <div class="banner neutral"><ShieldCheck :size="18" /><span>Perubahan tersedia saat ArduSub teridentifikasi, disarmed, dan daftar parameter lengkap. Setiap nilai menunggu konfirmasi autopilot.</span></div><section class="panel"><div class="parameter-toolbar"><label class="search-field"><Search :size="18" /><input v-model="search" placeholder="Cari parameter…" aria-label="Cari parameter"></label><span class="parameter-count">{{ parameters.items.length }} / {{ parameters.expected }} parameter <span class="subtle-tag">{{ parameters.state }}</span></span><button class="button" :disabled="!connected || busy || vehicle?.parameters.writing" @click="action(async () => {await api('/parameters/refresh', 'POST'); await loadParameters()})"><RefreshCw :size="16" /> Baca ulang</button><a class="button" :class="{disabled: parameters.state !== 'complete' || !connected}" :aria-disabled="parameters.state !== 'complete' || !connected" :href="parameters.state === 'complete' && connected ? '/api/parameters/export' : undefined"><ArrowDownToLine :size="16" /> Ekspor</a></div><div v-if="!parameters.items.length" class="empty"><Settings2 :size="34" /><h3>{{ connected ? 'Membaca parameter…' : 'Hubungkan autopilot terlebih dahulu' }}</h3><p>{{ connected ? 'Parameter akan muncul saat respons autopilot diterima.' : 'Daftar parameter dibaca langsung dari perangkat yang terhubung.' }}</p><button v-if="!connected" class="button" @click="navigate('connection')">Buka koneksi <ArrowRight :size="15" /></button></div><div v-else class="table-scroll"><table><thead><tr><th>Parameter</th><th>Nilai saat ini</th><th>Tipe</th><th>Terakhir diterima</th><th><span class="sr-only">Tindakan</span></th></tr></thead><tbody><tr v-for="p in visibleParams" :key="p.name"><td><code>{{ p.name }}</code></td><td class="numeric">{{ Number(p.value.toPrecision(8)) }}</td><td><span class="subtle-tag">{{ typeNames[p.type] || `TYPE ${p.type}` }}</span></td><td class="secondary">{{ time(p.updated) }}</td><td><button class="text-button" :disabled="!editAllowed || busy" @click="editParameter(p)">Ubah <ChevronRight :size="14" /></button></td></tr><tr v-if="!visibleParams.length"><td colspan="5" class="empty">Tidak ada parameter yang cocok.</td></tr></tbody></table></div><div v-if="parameters.items.length" class="panel-footer"><span>{{ filteredParams.length }} hasil · halaman {{ paramPage }} / {{ paramPages }}</span><div class="pagination"><button class="button small" :disabled="paramPage <= 1" @click="paramPage--">Sebelumnya</button><button class="button small" :disabled="paramPage >= paramPages" @click="paramPage++">Berikutnya</button></div></div></section>
        </template>

        <template v-else-if="page === 'system'">
          <div class="metric-grid four"><article class="metric-card"><div class="metric-top">CPU <Cpu :size="18" /></div><div class="metric-value">{{ system?.cpu_percent.toFixed(1) || '—' }} <small>%</small></div><div class="metric-foot">{{ system?.cpu_count || '—' }} logical cores</div></article><article class="metric-card"><div class="metric-top">RAM <Database :size="18" /></div><div class="metric-value small">{{ bytes(system?.memory.used) }}</div><div class="metric-foot">dari {{ bytes(system?.memory.total) }}</div></article><article class="metric-card"><div class="metric-top">Penyimpanan <Database :size="18" /></div><div class="metric-value small">{{ bytes(system?.disk.used) }}</div><div class="metric-foot">dari {{ bytes(system?.disk.total) }}</div></article><article class="metric-card"><div class="metric-top">Uptime <Activity :size="18" /></div><div class="metric-value small">{{ duration(system?.uptime) }}</div><div class="metric-foot">Sejak host dinyalakan</div></article></div><div class="two-columns"><section class="panel"><div class="panel-heading"><h3><Cpu :size="18" /> Informasi perangkat</h3></div><dl class="detail-list"><div><dt>Model</dt><dd>{{ system?.model || '—' }}</dd></div><div><dt>Hostname</dt><dd>{{ system?.hostname || '—' }}</dd></div><div><dt>Sistem operasi</dt><dd>{{ system?.os || '—' }}</dd></div><div><dt>Kernel</dt><dd>{{ system?.kernel || '—' }}</dd></div><div><dt>RAM aplikasi</dt><dd>{{ system ? (system.process_memory / 1024 ** 2).toFixed(1) + ' MB' : '—' }}</dd></div><div><dt>Pembaruan terakhir</dt><dd>{{ system ? time(system.ts) : '—' }}</dd></div></dl></section><section class="panel"><div class="panel-heading"><h3><Thermometer :size="18" /> Sensor termal</h3><span class="subtle-tag">{{ system?.temperatures.length || 0 }} SENSOR</span></div><div v-if="!system?.temperatures.length" class="empty compact">Sensor termal belum tersedia pada host ini.</div><div class="thermal-list"><div v-for="sensor in system?.temperatures" :key="sensor.name"><span>{{ sensor.name }}</span><meter min="0" max="110" :value="sensor.celsius" :aria-label="`Suhu ${sensor.name}`"></meter><strong>{{ sensor.celsius.toFixed(1) }} <small>°C</small></strong></div></div></section></div><section class="panel identity-panel"><div><h3>Identitas kendaraan</h3><p>Nama yang ditampilkan pada dashboard dan disimpan di Jetson.</p></div><form @submit.prevent="action(() => api('/settings', 'PUT', {name}), 'Nama kendaraan disimpan.')"><label class="sr-only" for="vehicle-name">Nama kendaraan</label><input id="vehicle-name" v-model="name" maxlength="60" required><button class="button primary" :disabled="busy || !online">Simpan</button></form></section>
        </template>

        <template v-else-if="page === 'logs'">
          <section class="panel"><div class="panel-heading"><h3><FileText :size="18" /> Riwayat kejadian</h3><div class="log-actions"><select v-model="logFilter" aria-label="Filter tingkat log"><option value="all">Semua kejadian</option><option value="info">Informasi</option><option value="warning">Peringatan</option></select><button class="button small" :disabled="!events.length" @click="exportEvents"><ArrowDownToLine :size="15" /> Ekspor</button></div></div><div v-if="!filteredEvents.length" class="empty compact">Belum ada kejadian untuk filter ini.</div><div class="event-list"><div v-for="event in filteredEvents" :key="event.id" class="event-row"><span class="event-mark" :class="event.level"><Check v-if="event.level === 'info'" :size="14" /><CircleHelp v-else :size="14" /></span><div><strong>{{ event.message }}</strong><small>{{ event.kind }}<template v-if="Object.keys(event.detail).length"> · {{ JSON.stringify(event.detail) }}</template></small></div><time>{{ date(event.ts) }}</time></div></div><div class="panel-footer"><span>Menampilkan maksimal 200 kejadian terbaru. Penyimpanan menyimpan 10.000 kejadian.</span></div></section><section class="panel"><div class="panel-heading"><h3><Database :size="18" /> Rekaman telemetri</h3><span class="subtle-tag">JSONL</span></div><div v-if="!logFiles.length" class="empty compact"><p>Rekaman dibuat otomatis saat pesan autopilot diterima.</p></div><div v-for="file in logFiles" :key="file.name" class="recording-row"><FileText :size="22" /><div><strong>{{ file.name }}</strong><small>{{ (file.bytes / 1024).toFixed(1) }} KB · {{ date(file.modified) }}</small></div><a class="button small" :href="`/api/logs/${file.name}`"><ArrowDownToLine :size="15" /> Unduh</a></div><div class="panel-footer"><span>Rotasi otomatis: maksimal 8 berkas × 8 MiB. Rekaman tertua diganti saat batas tercapai.</span></div></section>
        </template>
        <footer class="page-footer"><span><Waves :size="14" /> HydroShips · Onboard console</span><span>Jetson + Pixhawk <span class="footer-separator">/</span> AUV2027</span></footer>
      </main>
    </div>
    <div v-if="notice" class="toast" :class="{error: notice.error}" role="alert"><CircleHelp v-if="notice.error" :size="20" /><Check v-else :size="20" /><span>{{ notice.text }}</span><button class="icon-button" aria-label="Tutup notifikasi" @click="notice = null"><X :size="17" /></button></div>
    <dialog ref="dialog" @cancel="editing = null" aria-labelledby="parameter-dialog-title"><form @submit.prevent="saveParameter"><div class="dialog-heading"><h2 id="parameter-dialog-title">Ubah parameter</h2><button type="button" class="icon-button" aria-label="Tutup editor" :disabled="busy" @click="closeEditor"><X :size="20" /></button></div><template v-if="editing"><code class="editing-name">{{ editing.name }}</code><p>Nilai saat ini: <strong>{{ editing.value }}</strong> · {{ typeNames[editing.type] || editing.type }}</p><label>Nilai baru<input v-model="newValue" type="number" step="any" required autofocus :disabled="busy"></label><label class="checkbox-label"><input v-model="confirmed" type="checkbox" :disabled="busy">Saya telah memeriksa perubahan ini untuk kendaraan yang terhubung.</label><div class="dialog-note">Keberhasilan ditentukan oleh nilai yang dikembalikan autopilot. Saat timeout, baca ulang untuk memastikan keadaan perangkat.</div><div class="form-actions"><button type="button" class="button" :disabled="busy" @click="closeEditor">Batal</button><button class="button primary" :disabled="busy || !confirmed || !editAllowed || !parameterInputValid"><LoaderCircle v-if="busy" :size="16" class="spin" />{{ busy ? 'Menunggu konfirmasi…' : 'Kirim perubahan' }}</button></div></template></form></dialog>
  </div>
</template>
