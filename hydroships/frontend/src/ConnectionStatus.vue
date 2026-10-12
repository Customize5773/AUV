<script setup lang="ts">
import { computed } from 'vue'
import { Cable, Activity } from 'lucide-vue-next'
import type { Snapshot } from './state'

const props = defineProps<{vehicle?: Snapshot['vehicle']; online: boolean; statusLabel: string; elapsed: number; interval: number | null}>()
const connected = computed(() => props.online && props.vehicle?.status === 'connected')
const heartbeat = computed(() => props.vehicle?.heartbeat_age == null ? null : props.vehicle.heartbeat_age + props.elapsed)
const attitudeAge = computed(() => props.vehicle?.fields.roll ? props.vehicle.fields.roll.age + props.elapsed : null)
const fresh = computed(() => connected.value && heartbeat.value != null && heartbeat.value < 3 && attitudeAge.value != null && attitudeAge.value < 3 && !props.vehicle?.fields.roll?.stale)
const source = computed(() => ({serial: 'USB / serial', udp: 'UDP lokal', demo: 'Demo sintetis'})[props.vehicle?.connection?.kind || 'demo'])
</script>

<template>
  <section class="panel connection-status" aria-label="Status koneksi">
    <div class="panel-heading"><h3><Cable :size="18" /> Status koneksi</h3><span class="subtle-tag" :class="{healthy: fresh}"><span class="small-dot" :class="{live: fresh}"></span>{{ fresh ? 'DATA LIVE' : connected ? 'PERIKSA DATA' : 'OFFLINE' }}</span></div>
    <div class="connection-summary"><strong>{{ statusLabel }}</strong><span>{{ connected ? `${source} · MAVLink` : 'Menunggu koneksi autopilot' }}</span></div>
    <div class="connection-metrics">
      <div><small>INTERVAL LIVE</small><strong>{{ online && interval != null ? `${Math.round(interval)} ms` : '—' }}</strong><span>{{ online && interval != null ? `${(1000 / interval).toFixed(1)} pembaruan/detik` : 'Menunggu snapshot' }}</span></div>
      <div><small>USIA DATA ATTITUDE</small><strong>{{ connected && attitudeAge != null ? `${Math.round(attitudeAge * 1000)} ms` : '—' }}</strong><span>{{ fresh ? 'Telemetri segar' : 'Kesegaran belum terkonfirmasi' }}</span></div>
    </div>
    <p class="connection-note"><Activity :size="14" /> Interval diukur di browser, rata-rata hingga 20 snapshot. Usia attitude dihitung sejak data diterima Jetson; bukan latensi gerakan sensor sampai layar.</p>
    <dl class="detail-list">
      <div><dt>Perangkat / endpoint</dt><dd class="endpoint" :title="vehicle?.connection?.endpoint">{{ vehicle?.connection?.endpoint || '—' }}</dd></div>
      <div v-if="vehicle?.connection?.kind === 'serial'"><dt>Baud rate</dt><dd>{{ vehicle.connection.baud.toLocaleString('id-ID') }} bps</dd></div>
      <div><dt>System / component ID</dt><dd>{{ vehicle?.identity.system_id ?? '—' }} / {{ vehicle?.identity.component_id ?? '—' }}</dd></div>
      <div><dt>Firmware</dt><dd>{{ vehicle?.identity.firmware || '—' }}</dd></div>
      <div><dt>Heartbeat terakhir</dt><dd>{{ connected && heartbeat != null ? `${heartbeat.toFixed(1)} detik lalu` : '—' }}</dd></div>
      <div><dt>Pesan diterima · sesi ini</dt><dd>{{ vehicle?.received.toLocaleString('id-ID') || '0' }}</dd></div>
      <div><dt>Sambung ulang otomatis</dt><dd>{{ vehicle?.connection ? vehicle.connection.reconnect ? 'Aktif' : 'Tidak aktif' : '—' }}</dd></div>
    </dl>
    <div v-if="vehicle?.error" class="inline-error">{{ vehicle.error }}</div>
  </section>
</template>

<style scoped>
.connection-summary{padding:22px 24px 18px;display:flex;flex-direction:column;gap:7px}.connection-summary strong{font-size:21px}.connection-summary>span,.connection-metrics span{font-size:12px;color:var(--sea-muted)}.connection-metrics{display:grid;grid-template-columns:1fr 1fr;margin:0 24px;border:1px solid var(--sea-border);border-radius:8px;overflow:hidden}.connection-metrics>div{padding:18px;display:flex;flex-direction:column;gap:8px}.connection-metrics>div+div{border-left:1px solid var(--sea-border)}.connection-metrics small{font-size:10px;letter-spacing:.7px;color:var(--sea-muted)}.connection-metrics strong{font-size:25px;font-variant-numeric:tabular-nums}.connection-note{display:flex;gap:8px;margin:14px 24px;font-size:11px;line-height:1.7;color:var(--sea-muted)}.connection-note svg{flex-shrink:0;margin-top:3px}.endpoint{max-width:65%;overflow-wrap:anywhere;font-family:monospace;font-size:11px}.healthy{color:var(--sea-green)}.subtle-tag{display:flex;align-items:center;gap:7px}
</style>
