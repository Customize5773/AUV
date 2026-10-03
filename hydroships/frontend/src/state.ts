import { computed, onMounted, onUnmounted, ref } from 'vue'

export type Field = {value: number; unit: string; source: string; ts: number; age: number; stale: boolean}
export type Event = {id: number; ts: number; level: string; kind: string; message: string; detail: Record<string, unknown>}
export type Connection = {kind: 'demo' | 'serial' | 'udp'; endpoint: string; baud: number; reconnect?: boolean}
export type Snapshot = {
  version: string; name: string; events: Event[];
  vehicle: {
    status: string; error: string | null; session: string; connection: Connection | null;
    identity: {system_id?: number; component_id?: number; firmware?: string; mode?: string; armed?: boolean; autopilot?: number; vehicle_type?: number};
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
      state.value = next
      lastUpdate.value = Date.now()
      now.value = Date.now()
      const roll = next.vehicle.fields.roll
      const pitch = next.vehicle.fields.pitch
      if (roll && pitch && !roll.stale && !pitch.stale) {
        history.value = [...history.value.slice(-119), {roll: roll.value, pitch: pitch.value, ts: roll.ts}]
      }
    }
    ws.onclose = () => {
      lastUpdate.value = 0
      if (!destroyed) reconnect = setTimeout(connect, 1500)
    }
    ws.onerror = () => ws?.close()
  }
  onMounted(() => {connect(); timer = setInterval(() => {now.value = Date.now()}, 500)})
  onUnmounted(() => {destroyed = true; ws?.close(); clearTimeout(reconnect); clearInterval(timer)})
  return {state, online, history, now}
}
