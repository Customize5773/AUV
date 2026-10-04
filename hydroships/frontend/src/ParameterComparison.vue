<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { compareParameters, MAX_BACKUP_BYTES, parseParameterBackup, typeNames, type Difference, type ParameterValue } from './parameterComparison'

const props = defineProps<{
  ready: boolean; session: string;
  identity: {system_id?: number; component_id?: number; firmware?: string};
  source: unknown; items: ParameterValue[];
}>()
const fileInput = ref<HTMLInputElement | null>(null)
const error = ref('')
const loading = ref(false)
const result = ref<{
  filename: string; comparedAt: string; session: string; source: unknown;
  identity: typeof props.identity; backupTarget: {systemId: number; componentId: number}; rows: Difference[];
} | null>(null)
const onlyDifferences = ref(true)
const page = ref(1)
const labels = {'same': 'Sama', 'changed': 'Berubah', 'file-only': 'Hanya di file', 'vehicle-only': 'Hanya di kendaraan'}
const filtered = computed(() => result.value?.rows.filter(row => !onlyDifferences.value || row.status !== 'same') ?? [])
const pages = computed(() => Math.max(1, Math.ceil(filtered.value.length / 40)))
const visible = computed(() => filtered.value.slice((page.value - 1) * 40, page.value * 40))
const targetMismatch = computed(() => result.value && (result.value.identity.system_id !== result.value.backupTarget.systemId || result.value.identity.component_id !== result.value.backupTarget.componentId))
const counts = computed(() => Object.entries(labels).map(([key, label]) => ({label, count: result.value?.rows.filter(row => row.status === key).length ?? 0})))
let readVersion = 0
function clear() {
  readVersion++; result.value = null; error.value = ''; loading.value = false; page.value = 1
  if (fileInput.value) fileInput.value.value = ''
}
watch(() => [props.session, props.ready], clear)
watch(onlyDifferences, () => page.value = 1)
async function selectFile(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  clear()
  if (!file || !props.ready) return
  const version = readVersion
  loading.value = true
  try {
    if (file.size > MAX_BACKUP_BYTES) throw new Error('File melebihi batas 1 MiB.')
    const backup = parseParameterBackup(await file.text())
    if (version !== readVersion || !props.ready) return
    result.value = {
      filename: file.name, comparedAt: new Date().toISOString(), session: props.session,
      source: props.source, identity: {...props.identity},
      backupTarget: {systemId: backup.systemId, componentId: backup.componentId},
      rows: compareParameters(backup.items, props.items),
    }
  } catch (e) {if (version === readVersion) error.value = e instanceof Error ? e.message : 'File tidak dapat dibaca.'}
  finally {if (version === readVersion) loading.value = false}
}
function download() {
  const url = URL.createObjectURL(new Blob([JSON.stringify(result.value, null, 2)], {type: 'application/json'}))
  const link = document.createElement('a'); link.href = url; link.download = 'hydroships-parameter-comparison.json'; link.click(); URL.revokeObjectURL(url)
}
</script>

<template>
  <section class="panel comparison-panel" aria-labelledby="comparison-title">
    <div class="panel-heading"><h3 id="comparison-title">Bandingkan cadangan</h3><span class="subtle-tag">BACA SAJA</span></div>
    <div class="form-body">
      <p class="help-text">Pilih file .params hasil ekspor HydroShips. File dibaca di browser untuk membandingkan nilai, tanpa mengubah parameter kendaraan.</p>
      <label>File cadangan parameter<input ref="fileInput" type="file" accept=".params,.param,.txt" :disabled="!ready || loading" @change="selectFile"></label>
      <p v-if="!ready" class="help-text">Hubungkan autopilot atau demo dan tunggu daftar parameter lengkap.</p>
      <p v-if="loading" role="status">Membaca file…</p>
      <p v-if="error" class="inline-error" role="alert">{{ error }}</p>
      <template v-if="result">
        <p class="comparison-file">{{ result.filename }} · {{ new Date(result.comparedAt).toLocaleString('id-ID') }}</p>
        <p class="help-text">Hasil memakai nilai pada waktu perbandingan, bukan pembaruan langsung. Pilih ulang file untuk membandingkan kembali. ID yang sama belum membuktikan kendaraan fisik yang sama.</p>
        <div v-if="targetMismatch" class="banner warning" role="status">ID berbeda: file {{ result.backupTarget.systemId }}/{{ result.backupTarget.componentId }}, kendaraan {{ result.identity.system_id }}/{{ result.identity.component_id }}.</div>
        <div class="comparison-counts" role="status"><span v-for="item in counts" :key="item.label">{{ item.label }}: <strong>{{ item.count }}</strong></span></div>
        <label class="checkbox-label"><input v-model="onlyDifferences" type="checkbox">Hanya perbedaan</label>
        <div class="form-actions"><button class="button" @click="download">Unduh perbandingan</button><button class="button" @click="clear">Hapus perbandingan</button></div>
      </template>
    </div>
    <template v-if="result">
      <div class="table-scroll"><table><thead><tr><th>Parameter</th><th>Nilai file / tipe</th><th>Nilai kendaraan / tipe</th><th>Hasil</th></tr></thead><tbody>
        <tr v-for="row in visible" :key="row.name"><td><code>{{ row.name }}</code></td><td class="numeric">{{ row.backup ? `${row.backup.value} / ${typeNames[row.backup.type] || row.backup.type}` : '—' }}</td><td class="numeric">{{ row.current ? `${row.current.value} / ${typeNames[row.current.type] || row.current.type}` : '—' }}</td><td>{{ labels[row.status] }}</td></tr>
        <tr v-if="!visible.length"><td colspan="4" class="empty">Tidak ada perbedaan.</td></tr>
      </tbody></table></div>
      <div class="panel-footer"><span>{{ filtered.length }} hasil · halaman {{ page }} / {{ pages }}</span><div class="pagination"><button class="button small" :disabled="page <= 1" @click="page--">Sebelumnya</button><button class="button small" :disabled="page >= pages" @click="page++">Berikutnya</button></div></div>
    </template>
  </section>
</template>

<style scoped>
.comparison-panel { margin-top: 22px; }
.comparison-file { overflow-wrap: anywhere; }
.comparison-counts { display: flex; flex-wrap: wrap; gap: 12px; font-size: 13px; }
.form-body .checkbox-label { flex-direction: row; align-items: center; }
input[type=file] { max-width: 100%; }
</style>
