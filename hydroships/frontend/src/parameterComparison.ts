export type ParameterValue = {name: string; value: number; type: number}
export type ParameterBackup = {systemId: number; componentId: number; items: ParameterValue[]}
export type Difference = {name: string; status: 'same' | 'changed' | 'file-only' | 'vehicle-only'; backup: ParameterValue | null; current: ParameterValue | null}
export const MAX_BACKUP_BYTES = 1024 * 1024
export const typeNames: Record<number, string> = {1: 'UINT8', 2: 'INT8', 3: 'UINT16', 4: 'INT16', 5: 'UINT32', 6: 'INT32', 9: 'FLOAT32'}
const ranges: Record<number, [number, number]> = {1: [0, 255], 2: [-128, 127], 3: [0, 65535], 4: [-32768, 32767], 5: [0, 4294967295], 6: [-2147483648, 2147483647]}

// Parse the five-column format produced by HydroShips parameter export.
export function parseParameterBackup(text: string): ParameterBackup {
  if (new TextEncoder().encode(text).length > MAX_BACKUP_BYTES) throw new Error('File melebihi batas 1 MiB.')
  const items: ParameterValue[] = []
  const names = new Set<string>()
  let systemId = 0, componentId = 0
  for (const [index, raw] of text.split(/\r?\n/).entries()) {
    const line = raw.trim()
    if (!line || line.startsWith('#')) continue
    const fail = (message: string): never => {throw new Error(`Baris ${index + 1}: ${message}`)}
    const fields = line.split(/\s+/)
    if (fields.length !== 5) fail('harus berisi system ID, component ID, nama, nilai, dan tipe.')
    const [sys, comp, name, valueText, typeText] = fields as [string, string, string, string, string]
    if (![sys, comp].every(v => /^\d+$/.test(v) && Number(v) >= 1 && Number(v) <= 255)) fail('ID kendaraan tidak valid.')
    if (items.length && (systemId !== Number(sys) || componentId !== Number(comp))) fail('file berisi lebih dari satu kendaraan/component.')
    systemId = Number(sys); componentId = Number(comp)
    if (!/^[A-Z0-9_]{1,16}$/.test(name)) fail('nama parameter tidak valid.')
    if (names.has(name)) fail(`parameter ${name} muncul lebih dari sekali.`)
    if (!/^[1-6]$|^9$/.test(typeText)) fail('tipe parameter belum didukung.')
    const value = Number(valueText), type = Number(typeText)
    if (!/^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$/.test(valueText) || !Number.isFinite(value)) fail('nilai harus berupa angka yang finite.')
    if (type === 9) {
      if (!Number.isFinite(Math.fround(value))) fail('nilai di luar rentang FLOAT32.')
    } else if (!Number.isInteger(value) || value < ranges[type][0] || value > ranges[type][1]) fail('nilai di luar rentang tipe integer.')
    names.add(name)
    items.push({name, value, type})
  }
  if (!items.length) throw new Error('File tidak berisi parameter.')
  return {systemId, componentId, items}
}

export function compareParameters(backup: ParameterValue[], current: ParameterValue[]): Difference[] {
  const saved = new Map(backup.map(p => [p.name, p]))
  const live = new Map(current.map(p => [p.name, p]))
  return [...new Set([...saved.keys(), ...live.keys()])].sort().map(name => {
    const a = saved.get(name) ?? null, b = live.get(name) ?? null
    const equal = a && b && a.type === b.type && (a.type === 9 ? Math.fround(a.value) === Math.fround(b.value) : a.value === b.value)
    return {name, backup: a, current: b, status: !a ? 'vehicle-only' : !b ? 'file-only' : equal ? 'same' : 'changed'}
  })
}
