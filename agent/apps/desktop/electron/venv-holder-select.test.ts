import assert from 'node:assert/strict'

import { test } from 'vitest'

import { hasWindowsPathPrefix, isIrisOwnedVenvDaemon } from './venv-holder-select'

const SCRIPTS = 'C:\\Iris\\venv\\Scripts'

test('matches the hindsight daemon shim (exe under venv Scripts + hindsight cmdline)', () => {
  assert.equal(
    isIrisOwnedVenvDaemon(
      'C:\\Iris\\venv\\Scripts\\pythonw.exe',
      'C:\\Iris\\venv\\Scripts\\pythonw.exe -m hindsight_api.main --daemon --idle-timeout 300 --port 9177',
      SCRIPTS
    ),
    true
  )
})

test('Windows path prefix match is ordinal case-insensitive', () => {
  assert.equal(
    isIrisOwnedVenvDaemon(
      'c:\\iris\\venv\\scripts\\python.exe',
      'python.exe -m hindsight_api.main --daemon',
      'C:\\Iris\\venv\\Scripts'
    ),
    true
  )
})

test('excludes external venv holders that are not the hindsight daemon', () => {
  // a user terminal running the iris CLI from the venv — must NOT be killed
  assert.equal(isIrisOwnedVenvDaemon('C:\\Iris\\venv\\Scripts\\iris.exe', 'iris chat -q "hi"', SCRIPTS), false)
  // an unrelated python script using the venv interpreter
  assert.equal(
    isIrisOwnedVenvDaemon('C:\\Iris\\venv\\Scripts\\python.exe', 'python C:\\tools\\import.py', SCRIPTS),
    false
  )
})

test('excludes exes outside the venv even when the cmdline mentions hindsight', () => {
  assert.equal(
    isIrisOwnedVenvDaemon('C:\\Other\\pythonw.exe', 'pythonw -m hindsight_api.main --daemon', SCRIPTS),
    false
  )
})

test('prefix boundary: sibling dirs (ScriptsX) do not match', () => {
  assert.equal(hasWindowsPathPrefix('C:\\Iris\\venv\\ScriptsX\\python.exe', SCRIPTS), false)
  assert.equal(hasWindowsPathPrefix('C:\\Iris\\venv\\Scripts\\python.exe', SCRIPTS), true)
})

test('null/undefined fields never match', () => {
  assert.equal(isIrisOwnedVenvDaemon(null, 'x', SCRIPTS), false)
  assert.equal(isIrisOwnedVenvDaemon('C:\\Iris\\venv\\Scripts\\pythonw.exe', null, SCRIPTS), false)
  assert.equal(isIrisOwnedVenvDaemon(undefined, undefined, SCRIPTS), false)
})
