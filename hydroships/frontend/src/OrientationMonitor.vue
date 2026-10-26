<script setup lang="ts">
import { computed } from 'vue'
import { Compass, ArrowRight } from 'lucide-vue-next'
import type { Snapshot } from './state'

const props = defineProps<{vehicle?: Snapshot['vehicle']; online: boolean; elapsed: number}>()
function fresh(key: string) {
  const field = props.vehicle?.fields[key]
  return props.online && props.vehicle?.status === 'connected' && !!field && !field.stale && field.age + props.elapsed < 3
}
const pitchMarks = Array.from({length: 37}, (_, index) => (index - 18) * 5).filter(mark => mark !== 0)
const rollMarks = Array.from({length: 37}, (_, index) => (index - 18) * 5)
const live = computed(() => fresh('roll') && fresh('pitch'))
const roll = computed(() => live.value ? props.vehicle!.fields.roll!.value : 0)
const pitch = computed(() => live.value ? props.vehicle!.fields.pitch!.value : 0)
const heading = computed(() => fresh('heading') ? ((props.vehicle!.fields.heading!.value % 360) + 360) % 360 : null)
const direction = computed(() => heading.value == null ? '—' : ['Utara', 'Timur laut', 'Timur', 'Tenggara', 'Selatan', 'Barat daya', 'Barat', 'Barat laut'][Math.round(heading.value / 45) % 8])
const age = computed(() => live.value ? Math.round(Math.max(props.vehicle!.fields.roll!.age, props.vehicle!.fields.pitch!.age) * 1000 + props.elapsed * 1000) : null)
function value(key: string) {return fresh(key) ? props.vehicle!.fields[key]!.value.toFixed(1) : '—'}
</script>

<template>
  <section class="panel orientation-monitor" aria-label="Orientasi kendaraan">
    <div class="panel-heading"><h3><Compass :size="17" /> Orientasi kendaraan</h3><span class="live-label" :class="{active: live}"><span class="small-dot" :class="{live}"></span>{{ live ? 'LIVE' : 'NO SIGNAL' }}</span></div>
    <div class="instruments">
      <div class="instrument">
        <svg viewBox="0 0 240 240" role="img" :aria-label="live ? `Roll ${value('roll')} derajat, pitch ${value('pitch')} derajat` : 'Orientasi belum tersedia'" :class="{inactive: !live}">
          <defs><clipPath id="orientation-horizon"><circle cx="120" cy="120" r="91" /></clipPath></defs>
          <circle cx="120" cy="120" r="115" class="bezel" />
          <g clip-path="url(#orientation-horizon)">
            <g :transform="`translate(120 120) rotate(${-roll})`">
              <g :transform="`translate(0 ${Math.max(-90, Math.min(90, pitch)) * 2})`">
                <rect x="-180" y="-400" width="360" height="400" class="att-sky" />
                <rect x="-180" y="0" width="360" height="400" class="att-sea" />
                <path d="M-180 0H180" class="horizon-line" />
                <g v-for="mark in pitchMarks" :key="mark" :transform="`translate(0 ${-mark * 2})`">
                  <path :d="`M${mark % 10 === 0 ? -30 : -12} 0H${mark % 10 === 0 ? 30 : 12}`" class="pitch-tick" :class="{negative: mark < 0}" />
                  <text v-if="mark % 10 === 0" x="-39" y="4" text-anchor="end" class="ladder-label">{{ mark }}</text><text v-if="mark % 10 === 0" x="39" y="4" class="ladder-label">{{ mark }}</text>
                </g>
              </g>
            </g>
          </g>
          <g v-for="mark in rollMarks" :key="mark" :transform="`rotate(${mark} 120 120)`">
            <path :d="mark % 10 === 0 || Math.abs(mark) === 45 ? 'M120 12V25' : 'M120 16V22'" class="roll-tick" /><text v-if="[0,30,45,60,90].includes(Math.abs(mark))" x="120" y="37" text-anchor="middle" class="roll-label">{{ Math.abs(mark) }}</text>
          </g>
          <path :transform="`rotate(${-roll} 120 120)`" d="M120 40l-5 9h10Z" class="roll-pointer" />
          <path d="M65 120h35l7 7h26l7-7h35M120 110v8" class="vehicle-marker" />
          <circle cx="120" cy="120" r="3" class="center-dot" />
        </svg>
        <span class="instrument-caption">HORIZON · ROLL / PITCH</span>
        <div class="horizon-readouts"><span>R <strong>{{ fresh('roll') ? `${props.vehicle!.fields.roll!.value.toFixed(2)}°` : '—' }}</strong></span><span>P <strong>{{ fresh('pitch') ? `${props.vehicle!.fields.pitch!.value.toFixed(2)}°` : '—' }}</strong></span></div>
        <span class="scale-caption">Pitch: 5° / label 10° · Roll: 5°</span>
      </div>
      <div class="instrument compass-instrument">
        <svg viewBox="0 0 240 240" role="img" :aria-label="heading == null ? 'Heading belum tersedia' : `Heading ${heading.toFixed(0)} derajat, ${direction}`" :class="{inactive: heading == null}">
          <circle cx="120" cy="120" r="115" class="bezel" /><circle cx="120" cy="120" r="88" class="compass-circle" />
          <g :transform="`rotate(${-(heading ?? 0)} 120 120)`">
            <path v-for="mark in 36" :key="mark" d="M120 21V28" :transform="`rotate(${(mark - 1) * 10} 120 120)`" class="roll-tick" />
            <text v-for="(label, index) in ['N','E','S','W']" :key="label" x="120" y="48" :transform="`rotate(${index * 90} 120 120)`" text-anchor="middle" :class="label === 'N' ? 'north-label' : 'compass-label'">{{ label }}</text>
          </g>
          <path d="M120 4l-6 11h12Z" class="roll-pointer" />
          <path d="M120 80l14 31-14-7-14 7Z" class="boat-pointer" />
          <text x="120" y="145" text-anchor="middle" class="heading-number">{{ heading == null ? '—' : `${heading.toFixed(0)}°` }}</text>
          <text x="120" y="168" text-anchor="middle" class="heading-direction">{{ direction }}</text>
        </svg>
        <span class="instrument-caption">HEADING · ARAH KENDARAAN</span>
      </div>
    </div>
    <div class="orientation-values">
      <div><small>ROLL</small><strong>{{ value('roll') }}<span>°</span></strong><span>Kemiringan kiri / kanan</span></div>
      <div><small>PITCH</small><strong>{{ value('pitch') }}<span>°</span></strong><span>Kemiringan depan / belakang</span></div>
      <div><small>HEADING</small><strong>{{ heading == null ? '—' : heading.toFixed(0) }}<span>°</span></strong><span>{{ heading == null ? 'Menunggu data heading' : direction }}</span></div>
    </div>
    <div class="panel-footer"><span>{{ age == null ? 'Data orientasi belum tersedia atau kedaluwarsa' : `ATTITUDE · usia data ${age} ms` }}{{ vehicle?.connection?.kind === 'demo' ? ' · DEMO' : '' }}</span><a href="#telemetry">Lihat telemetri <ArrowRight :size="14" /></a></div>
  </section>
</template>

<style scoped>
.instruments{display:grid;grid-template-columns:1fr 1fr;gap:20px;padding:22px 22px 18px}.instrument{min-width:0;display:flex;flex-direction:column;align-items:center;gap:10px}.instrument>svg{width:100%;max-width:240px;overflow:visible}.instrument-caption{font-size:9px;letter-spacing:1px;color:var(--sea-muted)}.bezel{fill:#081c29;stroke:var(--sea-border);stroke-width:2}.att-sky{fill:#22516c}.att-sea{fill:#102d38}.horizon-line{stroke:#d5eff4;stroke-width:2}.pitch-tick,.roll-tick{stroke:#a7c9d8;stroke-width:1.5;fill:none}.ladder-label,.roll-label{fill:#c8dce5;font-size:9px}.roll-pointer,.boat-pointer{fill:#00cee8}.vehicle-marker{stroke:#ffb348;stroke-width:3;fill:none;stroke-linecap:round}.center-dot{fill:#ffb348}.compass-circle{fill:none;stroke:var(--sea-border)}.compass-label{fill:#b7cfdd;font-size:16px;font-weight:600}.north-label{fill:#00cee8;font-size:16px;font-weight:700}.heading-number{fill:var(--sea-text,#e4eff5);font-size:32px;font-weight:600}.heading-direction{fill:var(--sea-muted);font-size:12px}.pitch-tick.negative{stroke-dasharray:4 3}.horizon-readouts{display:flex;gap:18px;font-size:11px;color:var(--sea-muted)}.horizon-readouts strong{font-size:14px;color:var(--sea-text,#e4eff5);font-variant-numeric:tabular-nums;margin-left:5px}.scale-caption{font-size:9px;color:var(--sea-muted)}.inactive{opacity:.3}.orientation-values{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));margin:0 22px 20px;border:1px solid var(--sea-border);border-radius:8px}.orientation-values>div{display:flex;flex-direction:column;gap:8px;padding:14px 12px}.orientation-values>div+div{border-left:1px solid var(--sea-border)}.orientation-values small{color:var(--sea-muted);font-size:10px;letter-spacing:1px}.orientation-values strong{font-size:23px;font-variant-numeric:tabular-nums}.orientation-values strong span{font-size:13px;margin-left:4px;color:var(--sea-muted)}.orientation-values>div>span{font-size:10px;line-height:1.5;color:var(--sea-muted)}
</style>
