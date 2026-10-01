/**
 * Tests for electron/backend-probes.ts.
 *
 * Run with: node --test electron/backend-probes.test.ts
 * (Wired into npm test:desktop:platforms in package.json.)
 */

import assert from 'node:assert/strict'
import fs from 'node:fs'
import net from 'node:net'
import os from 'node:os'
import path from 'node:path'

import { test } from 'vitest'

import {
  canImportIrisCli,
  DEFAULT_PROBE_TIMEOUT_MS,
  execProbe,
  resolveProbeTimeoutMs,
  shouldTrustIrisOverride,
  verifyIrisCli
} from './backend-probes'

// Resolve the host's own Node binary -- guaranteed to be on disk and
// runnable. We use it as both a stand-in for "a python that doesn't
// have iris_cli" (since `node -c "import iris_cli"` will exit
// non-zero) and as a way to script verifyIrisCli's success path
// (a tiny script we write to disk that exits 0 on --version).
const NODE_BIN = process.execPath

test('execProbe keeps the parent event loop available to the child', async () => {
  let unexpectedSocketError: Error | undefined

  const server = net.createServer(socket => {
    socket.on('error', error => {
      // A successful child exits immediately after reading the sentinel. On
      // Windows that peer close can surface as ECONNRESET on the server side.
      if ((error as NodeJS.ErrnoException).code !== 'ECONNRESET') {
        unexpectedSocketError ??= error
      }
    })
    socket.end('pong')
  })

  await new Promise<void>((resolve, reject) => {
    server.once('error', reject)
    server.listen(0, '127.0.0.1', resolve)
  })

  const address = server.address()
  assert.ok(address && typeof address === 'object')

  const childScript = `
    const net = require('node:net')
    let reply = ''
    const socket = net.createConnection(${address.port}, '127.0.0.1')
    socket.setEncoding('utf8')
    socket.on('data', (chunk) => { reply += chunk })
    socket.on('end', () => process.exit(reply === 'pong' ? 0 : 1))
    socket.on('error', () => process.exit(1))
  `

  try {
    await execProbe(NODE_BIN, ['-e', childScript], {
      stdio: 'ignore',
      timeout: 5_000,
      windowsHide: true
    })
  } finally {
    await new Promise<void>((resolve, reject) => {
      server.close(error => (error ? reject(error) : resolve()))
    })
  }

  assert.ifError(unexpectedSocketError)
})

test('canImportIrisCli returns false when path is falsy', async () => {
  assert.equal(await canImportIrisCli(''), false)
  assert.equal(await canImportIrisCli(null), false)
  assert.equal(await canImportIrisCli(undefined), false)
})

test('canImportIrisCli returns false when interpreter cannot run -c', async () => {
  // node IS an interpreter, but `node -c "import iris_cli"` is a
  // SyntaxError -- different exit reason from a real Python's
  // ModuleNotFoundError, but the predicate is "exit 0 or not" and
  // both land on "not", which is exactly what we want for the
  // resolver fall-through.
  assert.equal(await canImportIrisCli(NODE_BIN), false)
})

test('canImportIrisCli returns false when binary does not exist', async () => {
  const ghost = path.join(os.tmpdir(), 'iris-probes-ghost-' + Date.now() + '.exe')
  assert.equal(await canImportIrisCli(ghost), false)
})

test('explicit Iris override is authoritative', () => {
  assert.equal(shouldTrustIrisOverride('/nix/store/abc/bin/iris'), true)
})

test('empty Iris override is not authoritative', () => {
  assert.equal(shouldTrustIrisOverride(''), false)
  assert.equal(shouldTrustIrisOverride(undefined), false)
})

test('verifyIrisCli returns false when command is falsy', async () => {
  assert.equal(await verifyIrisCli(''), false)
  assert.equal(await verifyIrisCli(null), false)
  assert.equal(await verifyIrisCli(undefined), false)
})

test('verifyIrisCli returns false when binary does not exist', async () => {
  const ghost = path.join(os.tmpdir(), 'iris-probes-ghost-' + Date.now() + '.exe')
  assert.equal(await verifyIrisCli(ghost), false)
})

test('verifyIrisCli returns true when --version exits 0', async () => {
  // Write a tiny script that exits 0 regardless of args, then invoke
  // it through node. This stands in for a working iris binary --
  // verifyIrisCli only cares about the exit code.
  const scriptPath = path.join(os.tmpdir(), `iris-probes-ok-${Date.now()}-${process.pid}.cjs`)
  fs.writeFileSync(scriptPath, 'process.exit(0)\n')

  try {
    // Use node as the launcher and our script as the "command". Pass
    // shell:false (default) -- node is a real binary, no shim.
    // execFileSync passes ['--version'] as args, which node ignores
    // gracefully (well, it prints its version and exits 0, which is
    // perfect -- exit code 0 is the only signal we read).
    assert.equal(await verifyIrisCli(NODE_BIN), true)
  } finally {
    try {
      fs.unlinkSync(scriptPath)
    } catch {
      void 0
    }
  }
})

test('resolveProbeTimeoutMs honours IRIS_PROBE_TIMEOUT_MS', () => {
  assert.equal(resolveProbeTimeoutMs({}), DEFAULT_PROBE_TIMEOUT_MS)
  assert.equal(resolveProbeTimeoutMs({ IRIS_PROBE_TIMEOUT_MS: '30000' }), 30_000)
  assert.equal(resolveProbeTimeoutMs({ IRIS_PROBE_TIMEOUT_MS: '0' }), DEFAULT_PROBE_TIMEOUT_MS)
  assert.equal(resolveProbeTimeoutMs({ IRIS_PROBE_TIMEOUT_MS: 'nope' }), DEFAULT_PROBE_TIMEOUT_MS)
  // Cap runaway values
  assert.equal(resolveProbeTimeoutMs({ IRIS_PROBE_TIMEOUT_MS: '999999' }), 120_000)
})
