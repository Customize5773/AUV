<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { ArrowDown, ArrowUp, CircleStop, Download, Network, Play, Plus, Route, Save, Trash2 } from 'lucide-vue-next'
import { api } from './state'

type Step = {name: string; task: string; timeout: number}
type Plan = {name: string; time_limit: number; steps: Step[]}
type Run = {run_id: string; status: string; detail: string; elapsed: number; scenario: string; plan: Plan;
  steps: {name: string; task: string; status: string; elapsed: number}[]; events: {elapsed: number; message: string}[]}
type Snapshot = {
  config: {revision: number; plan: Plan}; tasks: Record<string, string>;
  runtime: {status: string; error: string | null; domain: number; age: number | null; logs: string[]; task_driver: string};
  graph: {nodes: string[]; topics: {name: string; types: string[]}[]};
  legacy: {state: string | null; age: number | null} | null; current: Run | null;
  history: {run_id: string; status: string; name: string; started_at: number; elapsed: number; scenario: string}[];
}
const props = defineProps<{online: boolean}>()
const data = ref<Snapshot | null>(null)
const draft = ref<Plan | null>(null)
const revision = ref(0)
const saved = ref('')
const scenario = ref('success')
const busy = ref(false)
const fetchError = ref('')
const notice = ref('')
const error = ref(false)
const current = computed(() => data.value?.current)
const active = computed(() => ['starting', 'running'].includes(current.value?.status || ''))
const dirty = computed(() => JSON.stringify(draft.value) !== saved.value)
const conflict = computed(() => !!data.value && revision.value !== data.value.config.revision)
const ready = computed(() => props.online && !fetchError.value && data.value?.runtime.status === 'ready')
const locked = computed(() => busy.value || active.value || !props.online || !!fetchError.value)
const completed = computed(() => current.value?.steps.filter(s => s.status === 'succeeded').length || 0)
const labels: Record<string, string> = {stopped: 'Berhenti', starting: 'Memulai', ready: 'Siap', stale: 'Data lama', error: 'Terputus', unavailable: 'Tidak tersedia',
  running: 'Berjalan', succeeded: 'Selesai', failed: 'Gagal', aborted: 'Dibatalkan', interrupted: 'Terhenti', rejected: 'Ditolak', pending: 'Menunggu', skipped: 'Dilewati'}
const label = (status: string) => labels[status] || status
const scenarios: Record<string, string> = {success: 'Semua tahap berhasil', failure: 'Tugas melaporkan gagal', no_response: 'Tugas tidak merespons'}
const seconds = (value: number) => `${value.toFixed(1)} dtk`
function loadDraft() {
  if (!data.value) return
  draft.value = JSON.parse(JSON.stringify(data.value.config.plan))
  revision.value = data.value.config.revision
  saved.value = JSON.stringify(draft.value)
}
let polling = false
let disposed = false
let timer: ReturnType<typeof setInterval>
async function refresh() {
  if (polling) return
  polling = true
  try {
    const next = await api<Snapshot>('/autonomy')
    if (disposed) return
    data.value = next; fetchError.value = ''
    if (!draft.value) loadDraft()
  } catch (e) {if (!disposed) fetchError.value = e instanceof Error ? e.message : 'Status misi belum tersedia.'}
  finally {polling = false}
}
async function action(task: () => Promise<unknown>, message: string) {
  if (busy.value) return
  busy.value = true; notice.value = ''
  try {await task(); notice.value = message; error.value = false}
  catch (e) {notice.value = e instanceof Error ? e.message : 'Operasi gagal.'; error.value = true}
  finally {busy.value = false; await refresh()}
}
function save() {
  void action(async () => {
    const config = await api<Snapshot['config']>('/autonomy/plan', 'PUT', {revision: revision.value, plan: draft.value})
    if (data.value) data.value.config = config
    loadDraft()
  }, 'Rencana tersimpan. Eksekusi berikutnya memakai revisi ini.')
}
function move(index: number, offset: number) {
  const steps = draft.value!.steps
  const step = steps.splice(index, 1)[0]!
  steps.splice(index + offset, 0, step)
}
onMounted(() => {void refresh(); timer = setInterval(() => void refresh(), 1000)})
onUnmounted(() => {disposed = true; clearInterval(timer)})
</script>

<template>
  <div class="autonomy">
    <div class="banner neutral"><Route :size="19" /><span><strong>Platform misi · SAUVC 2027</strong><br>{{ data?.runtime.task_driver === 'external' ? 'Menunggu hasil dari modul tugas ROS 2 eksternal. Kontrak ini untuk uji software; kendali kendaraan belum terhubung.' : 'Uji alur software melalui ROS 2. Modul tugas saat ini memberi respons sintetis; navigasi, persepsi, dan kendali kendaraan belum terhubung.' }}</span><span class="subtle-tag">SOFTWARE TEST</span></div>
    <div v-if="fetchError" class="banner warning" role="alert">{{ fetchError }} Data terakhir mungkin sudah lama.</div>
    <div v-if="notice" class="banner" :class="error ? 'warning' : 'neutral'" role="status">{{ notice }}</div>
    <template v-if="data && draft">
      <section class="auto-runtime panel" aria-label="Runtime ROS 2">
        <div><span class="eyebrow">RUNTIME ROS 2</span><strong><span class="small-dot" :class="{live: ready}"></span> {{ !online || fetchError ? 'Status belum tersedia' : label(data.runtime.status) }}</strong><small>{{ data.graph.nodes.length }} node terdeteksi · Domain {{ data.runtime.domain }} · {{ data.runtime.task_driver === 'external' ? 'Modul tugas eksternal' : 'Modul tugas sintetis' }}</small></div>
        <p v-if="data.runtime.error">{{ data.runtime.error }}</p>
        <div class="auto-actions"><button v-if="['stopped', 'error', 'unavailable'].includes(data.runtime.status)" class="button" :disabled="busy || !online" @click="action(() => api('/autonomy/runtime', 'POST'), 'Runtime sedang dimulai. Misi tetap menunggu perintah.')"><Play :size="15" /> Mulai runtime</button><button v-else class="button" :disabled="busy || !online" @click="action(() => api('/autonomy/runtime', 'DELETE'), 'Runtime dihentikan. Eksekusi aktif ditandai terhenti.')"><CircleStop :size="15" /> Hentikan runtime</button></div>
      </section>
      <div class="auto-workbench">
        <section class="panel auto-plan">
          <div class="panel-heading"><h3><Route :size="18" /> Rencana misi</h3><span class="subtle-tag">REV {{ revision }}{{ dirty ? ' · BELUM DISIMPAN' : '' }}</span></div>
          <form @submit.prevent="save">
            <fieldset :disabled="locked">
              <div class="auto-plan-meta"><label>Nama misi<input v-model="draft.name" required maxlength="80"></label><label>Batas total (detik)<input v-model.number="draft.time_limit" type="number" min="1" max="1800" step="0.1" required></label></div>
              <div class="auto-section-label"><span>URUTAN TAHAP</span><span>{{ draft.steps.length }} / 16</span></div>
              <ol class="auto-editor">
                <li v-for="(step, index) in draft.steps" :key="index">
                  <span class="auto-number">{{ String(index + 1).padStart(2, '0') }}</span>
                  <div class="auto-step-fields"><label :for="`step-name-${index}`" class="auto-sr">Nama tahap {{ index + 1 }}</label><input :id="`step-name-${index}`" v-model="step.name" required maxlength="80"><div><label>Jenis tugas<select v-model="step.task" :aria-label="`Jenis tugas ${index + 1}`"><option v-for="(name, key) in data.tasks" :key="key" :value="key">{{ name }}</option></select></label><label>Timeout (detik)<input v-model.number="step.timeout" :aria-label="`Timeout tahap ${index + 1}`" type="number" min="1" max="600" step="0.1" required></label></div></div>
                  <div class="auto-order"><button type="button" class="icon-button" :disabled="index === 0" :aria-label="`Naikkan tahap ${index + 1}`" @click="move(index, -1)"><ArrowUp :size="15" /></button><button type="button" class="icon-button" :disabled="index === draft.steps.length - 1" :aria-label="`Turunkan tahap ${index + 1}`" @click="move(index, 1)"><ArrowDown :size="15" /></button><button type="button" class="icon-button" :disabled="draft.steps.length === 1" :aria-label="`Hapus tahap ${index + 1}`" @click="draft.steps.splice(index, 1)"><Trash2 :size="15" /></button></div>
                </li>
              </ol>
              <button type="button" class="button small" :disabled="draft.steps.length >= 16" @click="draft.steps.push({name: 'Tahap baru', task: 'navigation', timeout: 15})"><Plus :size="15" /> Tambah tahap</button>
              <div v-if="conflict" class="auto-conflict" role="alert">Rencana berubah di sesi lain. Muat versi tersimpan sebelum melanjutkan.</div>
              <div class="auto-plan-footer"><button class="button primary" :disabled="!dirty || conflict"><Save :size="15" /> Simpan rencana</button><button type="button" class="text-button" :disabled="!dirty && !conflict" @click="loadDraft">Muat versi tersimpan</button></div>
            </fieldset>
          </form>
        </section>
        <section class="panel auto-execution">
          <div class="panel-heading"><h3><Play :size="17" /> Eksekusi uji</h3><span class="auto-status" :class="current?.status" data-testid="mission-status">{{ current ? label(current.status) : 'Belum ada eksekusi' }}</span></div>
          <div class="auto-execution-body">
            <label>Skenario respons tugas<select v-model="scenario" :disabled="busy || active || data.runtime.task_driver === 'external'"><option v-for="(name, key) in scenarios" :key="key" :value="key">{{ name }}</option></select></label>
            <div class="auto-run-actions"><button class="button primary" :disabled="busy || active || !ready || dirty || conflict" @click="action(() => api('/autonomy/run', 'POST', {revision, scenario}), 'Perintah mulai diterima oleh ROS 2.')"><Play :size="16" /> Jalankan uji software</button><button class="button auto-abort" :disabled="busy || !active || !ready" @click="action(() => api('/autonomy/abort', 'POST', {run_id: current!.run_id}), 'Pembatalan diterima oleh ROS 2.')"><CircleStop :size="16" /> Batalkan</button></div>
            <p class="auto-hint">{{ dirty || conflict ? 'Simpan atau muat rencana tersimpan sebelum menjalankan.' : 'Menjalankan rencana tersimpan. Setiap tahap menunggu hasil tugas ROS 2.' }}</p>
            <template v-if="current">
              <div class="auto-run-summary"><div><small>EKSEKUSI TERAKHIR</small><strong>{{ current.plan.name }}</strong></div><b>{{ seconds(current.elapsed) }}</b></div>
              <progress :value="completed" :max="current.plan.steps.length" :aria-label="`${completed} dari ${current.plan.steps.length} tahap selesai`"></progress>
              <ol class="auto-progress"><li v-for="(step, index) in current.steps" :key="index" :class="step.status"><span class="auto-number">{{ index + 1 }}</span><div><strong>{{ step.name }}</strong><small>{{ data.tasks[step.task] }}</small></div><span class="auto-status" :class="step.status">{{ label(step.status) }}</span><small>{{ seconds(step.elapsed) }}</small></li></ol>
              <p class="auto-detail">{{ current.detail }}</p>
              <details class="auto-details"><summary>Jejak eksekusi · {{ current.events.length }} kejadian</summary><ol class="auto-events"><li v-for="(event, index) in current.events" :key="index"><time>{{ seconds(event.elapsed) }}</time><span>{{ event.message }}</span></li></ol></details>
            </template>
            <div v-else class="auto-empty"><Route :size="36" /><h3>Siapkan alur pertama</h3><p>Susun tahap di sebelah kiri, lalu jalankan uji untuk melihat progres dan hasilnya di sini.</p></div>
          </div>
        </section>
      </div>
      <section class="panel auto-history"><div class="panel-heading"><h3>Riwayat eksekusi</h3><span class="subtle-tag">{{ data.history.length }} TERBARU</span></div><div v-if="!data.history.length" class="auto-empty compact">Belum ada eksekusi. Hasil uji akan tersimpan otomatis.</div><div v-else class="auto-table"><table><thead><tr><th>Misi / waktu mulai</th><th>Skenario</th><th>Hasil</th><th>Durasi</th><th>Laporan</th></tr></thead><tbody><tr v-for="run in data.history" :key="run.run_id"><td><strong>{{ run.name }}</strong><small>{{ new Date(run.started_at * 1000).toLocaleString('id-ID') }}</small></td><td>{{ scenarios[run.scenario] || run.scenario }}</td><td><span class="auto-status" :class="run.status">{{ label(run.status) }}</span></td><td>{{ seconds(run.elapsed) }}</td><td><a class="button small" :href="`/api/autonomy/runs/${run.run_id}`" :aria-label="`Unduh laporan ${run.name}`"><Download :size="14" /> JSON</a></td></tr></tbody></table></div></section>
      <section class="panel auto-graph"><div class="panel-heading"><h3><Network :size="18" /> Diagnostik ROS 2</h3><span class="subtle-tag">{{ ready ? 'LIVE' : 'TIDAK AKTIF' }}</span></div><div class="auto-graph-body"><div><h4>Node terdeteksi</h4><ul><li v-for="node in data.graph.nodes" :key="node"><span class="small-dot" :class="{live: ready}"></span><code>{{ node }}</code></li></ul><p v-if="!data.graph.nodes.length" class="auto-hint">Menunggu penemuan node.</p></div><div><h4>Jembatan ROV sebelumnya <span class="subtle-tag">BACA SAJA</span></h4><code>/hydroships/mission/state</code><p class="auto-hint">{{ data.legacy?.state || 'Belum ada pesan dari sistem ROV lama.' }}{{ data.legacy?.age != null ? ` · ${seconds(data.legacy.age)} lalu` : '' }}</p><details class="auto-details"><summary>Topic terdeteksi · {{ data.graph.topics.length }}</summary><ul><li v-for="topic in data.graph.topics" :key="topic.name"><code>{{ topic.name }}<small>{{ topic.types.join(', ') }}</small></code></li></ul></details></div></div><details v-if="data.runtime.logs.length" class="auto-details auto-runtime-logs"><summary>Log proses ROS 2</summary><pre>{{ data.runtime.logs.join('\n') }}</pre></details></section>
    </template>
    <div v-else-if="!fetchError" class="auto-empty" role="status">Memuat platform autonomous…</div>
  </div>
</template>

<style scoped>
.autonomy{display:grid;gap:22px}.autonomy>.banner{margin:0;line-height:1.7}.banner>.subtle-tag{margin-left:auto}.auto-runtime{display:flex;align-items:center;gap:24px;padding:20px 24px}.auto-runtime .eyebrow{display:block}.auto-runtime strong{display:block;font-size:20px}.auto-runtime small{display:block;color:var(--sea-muted);margin-top:9px}.auto-runtime>p{font-size:12px;color:var(--sea-orange);overflow-wrap:anywhere}.auto-actions{margin-left:auto}.auto-workbench{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);gap:22px;align-items:start}fieldset{border:0;padding:22px;margin:0;min-width:0}fieldset:disabled{opacity:.65}.auto-plan-meta{display:grid;grid-template-columns:minmax(0,1fr) 130px;gap:16px}.auto-section-label{display:flex;justify-content:space-between;font-size:10px;color:var(--sea-muted);letter-spacing:1px;margin:28px 0 12px}.auto-editor{list-style:none;margin:0 0 16px;padding:0;display:grid;gap:12px}.auto-editor>li{display:flex;gap:12px;align-items:flex-start;border:1px solid var(--sea-border);border-radius:8px;padding:13px;background:var(--sea-bg)}.auto-number{display:grid;place-items:center;border:1px solid var(--sea-border);border-radius:6px;width:28px;height:28px;flex-shrink:0;color:var(--sea-cyan);font-size:11px;font-variant-numeric:tabular-nums}.auto-step-fields{flex:1;min-width:0}.auto-step-fields>input{width:100%}.auto-step-fields>div{display:grid;grid-template-columns:minmax(0,1fr) 110px;gap:10px;margin-top:12px}.auto-step-fields label{font-size:10px;color:var(--sea-muted);gap:6px}.auto-step-fields select,.auto-step-fields input{font-size:12px;min-width:0;width:100%}.auto-order{display:flex;flex-direction:column;gap:2px}.auto-order .icon-button{min-width:27px;min-height:27px;padding:5px}.auto-plan-footer{display:flex;gap:12px;align-items:center;margin-top:24px;padding-top:20px;border-top:1px solid var(--sea-border)}.auto-conflict{color:var(--sea-orange);font-size:12px;line-height:1.6;margin-top:16px}.auto-execution-body{padding:22px}.auto-run-actions{display:flex;gap:10px;margin-top:16px;flex-wrap:wrap}.auto-abort{color:var(--sea-red);border-color:#743e49}.auto-hint{color:var(--sea-muted);font-size:11px;line-height:1.8;margin-top:12px}.auto-status{display:inline-flex;font-size:10px;color:var(--sea-muted);background:var(--sea-bg);border:1px solid var(--sea-border);border-radius:5px;padding:5px 8px;white-space:nowrap}.auto-status.succeeded,.auto-status.ready{color:var(--sea-green);border-color:#226b5a}.auto-status.running,.auto-status.starting{color:var(--sea-cyan);border-color:#206180}.auto-status.failed,.auto-status.interrupted,.auto-status.rejected{color:#ff9b91;border-color:#784647}.auto-status.aborted{color:var(--sea-orange)}.auto-run-summary{display:flex;gap:15px;justify-content:space-between;align-items:center;margin:25px 0 16px;border-top:1px solid var(--sea-border);padding-top:24px}.auto-run-summary small{font-size:9px;color:var(--sea-muted);letter-spacing:1px}.auto-run-summary strong{display:block;font-size:15px;margin-top:8px;overflow-wrap:anywhere}.auto-run-summary b{font-size:20px;white-space:nowrap;font-variant-numeric:tabular-nums;color:var(--sea-cyan);font-weight:500}progress{width:100%;height:5px;appearance:none;border:0;border-radius:4px;background:var(--sea-bg)}progress::-webkit-progress-bar{background:var(--sea-bg);border-radius:4px}progress::-webkit-progress-value{background:var(--sea-green);border-radius:4px}.auto-progress{padding:0;margin:12px 0;list-style:none}.auto-progress li{display:flex;align-items:center;gap:10px;padding:14px 0;border-bottom:1px solid var(--sea-border)}.auto-progress li>div{flex:1;min-width:0}.auto-progress strong{font-size:12px;overflow-wrap:anywhere}.auto-progress small{display:block;color:var(--sea-muted);font-size:10px;margin-top:4px;white-space:nowrap}.auto-progress .running .auto-number{background:#154458;border-color:var(--sea-cyan)}.auto-detail{font-size:12px;line-height:1.7;color:var(--sea-muted);margin-top:16px;overflow-wrap:anywhere}.auto-details{margin-top:18px;font-size:11px;color:var(--sea-muted)}summary{cursor:pointer;padding:8px 0;color:var(--sea-text)}summary:focus-visible{outline:2px solid var(--sea-cyan)}.auto-events{list-style:none;padding:0;max-height:230px;overflow:auto}.auto-events li{display:flex;gap:14px;padding:8px 0;line-height:1.6}.auto-events time{white-space:nowrap;color:var(--sea-cyan);min-width:56px}.auto-empty{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px;min-height:255px;padding:32px;color:var(--sea-muted);text-align:center}.auto-empty>svg{color:var(--sea-cyan)}.auto-empty p{font-size:12px;line-height:1.9;max-width:300px}.auto-empty.compact{min-height:95px;font-size:12px}.auto-table{overflow:auto;max-height:380px}.auto-table table{width:100%;border-collapse:collapse;font-size:12px}.auto-table th{text-align:left;font-size:10px;color:var(--sea-muted);font-weight:500;background:var(--sea-bg);position:sticky;top:0}.auto-table th,.auto-table td{padding:14px 22px;border-bottom:1px solid var(--sea-border)}.auto-table td:first-child{max-width:290px;overflow-wrap:anywhere}.auto-table td small{display:block;margin-top:5px;font-size:10px;color:var(--sea-muted)}.auto-graph-body{display:grid;grid-template-columns:1fr 1fr;gap:30px;padding:22px}.auto-graph h4{font-size:12px;margin-bottom:15px;font-weight:500}.auto-graph ul{padding:0;margin:0;list-style:none}.auto-graph li{display:flex;gap:10px;align-items:center;margin:12px 0}.auto-graph code{font-size:11px;overflow-wrap:anywhere}.auto-graph code small{display:block;font-size:10px;color:var(--sea-muted);margin-top:5px}.auto-graph .auto-details ul{max-height:250px;overflow:auto}.auto-runtime-logs{margin:0 22px 18px}.auto-runtime-logs pre{white-space:pre-wrap;overflow-wrap:anywhere;max-height:200px;overflow:auto}.auto-sr{position:absolute;width:1px;height:1px;padding:0;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}@media(min-width:1100px) and (max-width:1350px){.auto-workbench{grid-template-columns:minmax(0,1.15fr) minmax(0,1fr)}fieldset,.auto-execution-body{padding:16px}.auto-editor>li{gap:8px;padding:10px}.auto-step-fields>div{grid-template-columns:minmax(0,1fr) 85px}.auto-order .icon-button{min-width:24px}.auto-plan-meta{grid-template-columns:minmax(0,1fr) 105px}.auto-progress li{gap:7px}.auto-progress li>small{display:none}}
</style>
