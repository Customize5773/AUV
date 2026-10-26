import assert from 'node:assert/strict'
import test from 'node:test'
import { compareParameters, parseParameterBackup } from '../src/parameterComparison.ts'

test('export round-trip, differences, and invalid backup input', () => {
  const backup = parseParameterBackup('\uFEFF# HydroShips parameter snapshot\r\n1\t1\tGAIN\t0.100000001\t9\r\n1 1 COUNT 2 6\n')
  assert.equal(backup.systemId, 1)
  assert.equal(backup.componentId, 1)
  assert.equal(backup.items.length, 2)
  assert.equal(compareParameters(backup.items, [{name: 'GAIN', value: Math.fround(0.1), type: 9}]).find(p => p.name === 'GAIN')?.status, 'same')
  const rows = compareParameters(backup.items, [
    {name: 'GAIN', value: 0.2, type: 9}, {name: 'NEW', value: 1, type: 1},
  ])
  assert.deepEqual(rows.map(p => [p.name, p.status]), [['COUNT', 'file-only'], ['GAIN', 'changed'], ['NEW', 'vehicle-only']])
  assert.equal(compareParameters([{name: 'TYPE', value: 1, type: 9}], [{name: 'TYPE', value: 1, type: 6}])[0].status, 'changed')
  assert.equal(compareParameters([{name: 'INT', value: 16777217, type: 6}], [{name: 'INT', value: 16777216, type: 6}])[0].status, 'changed')
  for (const value of ['NaN', 'Infinity', '1e500', '0x10', '1,5', '1e39', '1e', '--1']) {
    assert.throws(() => parseParameterBackup(`# comment\n1 1 GAIN ${value} 9`), /Baris 2:/)
  }
  for (const content of [
    '1 1 GAIN 1', '0 1 GAIN 1 9', '1 256 GAIN 1 9', '1.5 1 GAIN 1 9',
    '1 1 bad-name 1 9', '1 1 NAME_TOO_LONG_FOR_MAVLINK 1 9',
    '1 1 GAIN 1 7', '1 1 GAIN 1 09', '1 1 GAIN 1.5 6',
    '1 1 GAIN 256 1', '1 1 GAIN -129 2', '1 1 GAIN 65536 3',
    '1 1 GAIN -32769 4', '1 1 GAIN 4294967296 5', '1 1 GAIN 2147483648 6',
    '1 1 GAIN 1 9\n1 1 GAIN 2 9', '1 1 GAIN 1 9\n2 1 OTHER 2 9',
    '1 1 GAIN 1 9\n1 2 OTHER 2 9',
  ]) assert.throws(() => parseParameterBackup(content), /Baris/)
  assert.throws(() => parseParameterBackup('# empty\n'), /tidak berisi/)
  assert.throws(() => parseParameterBackup('#'.repeat(1024 * 1024 + 1)), /1 MiB/)
  for (const [value, type] of [[255, 1], [-128, 2], [65535, 3], [-32768, 4], [4294967295, 5], [-2147483648, 6]]) {
    assert.equal(parseParameterBackup(`1 1 EDGE ${value} ${type}`).items[0].value, value)
  }
})
