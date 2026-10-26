<script setup lang="ts">
import { computed } from 'vue'
import type { Snapshot } from './state'
const props = defineProps<{vehicle: Snapshot['vehicle'] | null | undefined; online: boolean; elapsed: number}>()
const profile = computed(() => props.vehicle?.propulsion)
const live = computed(() => props.online && props.vehicle?.status === 'connected' &&
  (props.vehicle.heartbeat_age ?? 99) + props.elapsed < 3)
const labels = {unavailable: 'Belum terhubung', waiting: 'Menunggu parameter', match: 'Pemetaan output sesuai profil', mismatch: 'Pemetaan berbeda dari profil'}
const status = computed(() => live.value ? profile.value?.mapping_status ?? 'waiting' : 'unavailable')
function pwm(motor: number) {
  const field = props.vehicle?.fields[`thruster_${motor}_pwm`]
  if (!live.value || profile.value?.mapping_status !== 'match' || !field || field.stale || field.age + props.elapsed > 3) return '—'
  return field.value === 0 ? 'Tidak aktif' : `${Math.round(field.value)} µs`
}
</script>

<template>
  <section class="panel thruster-config">
    <div class="panel-heading">
      <h3>Konfigurasi 7 thruster</h3>
      <span class="subtle-tag">4 horizontal · 3 vertikal</span>
    </div>
    <div class="thruster-content">
      <p>{{ labels[status] }}<span v-if="vehicle?.connection?.kind === 'demo'"> · DEMO sintetis</span></p>
      <p v-if="live && profile?.different.length">Parameter berbeda: {{ profile.different.join(', ') }}</p>
      <div class="thruster-table" v-if="profile">
        <table>
          <thead><tr><th>Motor</th><th>Orientasi</th><th>Output</th><th>PWM teramati</th></tr></thead>
          <tbody><tr v-for="motor in profile.motors" :key="motor.id">
            <td>{{ motor.id }}</td><td>{{ motor.orientation === 'horizontal' ? 'Horizontal' : 'Vertikal' }}</td>
            <td>SERVO{{ motor.output }}</td><td>{{ pwm(motor.motor) }}</td>
          </tr></tbody>
        </table>
      </div>
      <p class="thruster-note">Profil T1–T4 horizontal, T5–T7 vertikal. Kesesuaian posisi, arah thrust dan mixer fisik belum diverifikasi. PWM telemetri bukan bukti motor bergerak.</p>
    </div>
  </section>
</template>

<style scoped>
.thruster-config{margin:22px 0}.thruster-content{padding:16px 22px;font-size:12px;line-height:1.7}
.thruster-table{overflow-x:auto;margin:12px 0}table{width:100%;border-collapse:collapse;text-align:left}
th,td{padding:8px 12px;border-bottom:1px solid #edf1f4;white-space:nowrap}th{font-weight:600}
.thruster-note{color:#617285}
</style>
