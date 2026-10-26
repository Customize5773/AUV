import { computed, onMounted, onUnmounted, ref } from 'vue'

export type Field = {value: number; unit: string; source: string; ts: number; age: number; stale: boolean}
export type Event = {id: number; ts: number; level: string; kind: string; message: string; detail: Record<string, unknown>}
export type Connection = {kind: 'demo' | 'serial' | 'udp'; endpoint: string; baud: number; reconnect?: boolean}
export type Snapshot = {
  version: string; name: string; events: Event[];
  vehicle: {
    status: string; error: string | null; session: string; connection: Connection | null;
    identity: {system_id?: number; component_id?: number; firmware?: string; frame?: string; mode?: string; armed?: boolean; autopilot?: number; vehicle_type?: number};
    propulsion?: {profile_id: string; name: string; hardware_mixer_verified: boolean;
      mapping_status: 'unavailable' | 'waiting' | 'match' | 'mismatch'; different: string[]; missing: string[];
      motors: {id: string; motor: number; output: number; orientation: string; function: number; direction: number}[]};
    heartbeat_age: number | null; fields: Record<string, Field>; received: number;
    parameters: {count: number; expected: number; state: string; writing: boolean}; write_allowed: boolean;
  };
  system: {
    model: string; hostname: string; os: string; kernel: string; cpu_percent: number; cpu_count: number;
    memory: {used: number; total: number; percent: number}; disk: {used: number; total: number; percent: number};
    temperatures: {name: string; celsius: number}[]; uptime: number; process_memory: number; ts: number;
  };
}

export async function api<T = Record<string, unknown>>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const response = await fetch('/api' + path, {
    method, headers: {'Content-Type': 'application/json', 'X-Hydroships-Client': 'dashboard'},
    body: body === undefined ? undefined : JSON.stringify(body), signal: AbortSignal.timeout(12000),
  })
  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(typeof data.detail === 'string' ? data.detail : `Permintaan gagal (${response.status}).`)
  }
  return response.json()
}

export function useVehicle() {
  const state = ref<Snapshot | null>(null)
  const lastUpdate = ref(0)
  const liveInterval = ref<number | null>(null)
  let previousFrame = 0
  let intervals: number[] = []
  const now = ref(Date.now())
  const online = computed(() => now.value - lastUpdate.value < 3000)
  const history = ref<{roll: number; pitch: number; ts: number}[]>([])
  let ws: WebSocket | null = null
  let reconnect: ReturnType<typeof setTimeout> | undefined
  let timer: ReturnType<typeof setInterval>
  let destroyed = false
  let lastSession = ''

  function connect() {
    ws = new WebSocket(`${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/api/live`)
    ws.onmessage = event => {
      const next = JSON.parse(event.data) as Snapshot
      if (next.vehicle.session !== lastSession) {
        history.value = []
        lastSession = next.vehicle.session
      }
      const arrival = performance.now()
      if (previousFrame) {
        intervals = [...intervals.slice(-19), arrival - previousFrame]
        liveInterval.value = intervals.reduce((sum, interval) => sum + interval, 0) / intervals.length
      }
      previousFrame = arrival
      state.value = next
      lastUpdate.value = Date.now()
      now.value = Date.now()
      const roll = next.vehicle.fields.roll
      const pitch = next.vehicle.fields.pitch
      const lastPoint = history.value[history.value.length - 1]
      // Keep the 60-second chart window while rendering live telemetry at 10 Hz.
      if (roll && pitch && !roll.stale && !pitch.stale && (!lastPoint || now.value - lastPoint.ts >= 500)) {
        history.value = [...history.value.slice(-119), {roll: roll.value, pitch: pitch.value, ts: roll.ts}]
      }
    }
    ws.onclose = () => {
      lastUpdate.value = 0
      previousFrame = 0
      intervals = []
      liveInterval.value = null
      if (!destroyed) reconnect = setTimeout(connect, 1500)
    }
    ws.onerror = () => ws?.close()
  }
  onMounted(() => {connect(); timer = setInterval(() => {now.value = Date.now()}, 500)})
  onUnmounted(() => {destroyed = true; ws?.close(); clearTimeout(reconnect); clearInterval(timer)})
  return {state, online, history, now, lastUpdate, liveInterval}
}
