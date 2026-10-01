import { describe, expect, it } from 'vitest'

import {
  normalizeIrisOpenString,
  pathFromIrisDeepLink,
  pathFromOpenDeepLink,
  resolveIrisOpenPath
} from './iris-open-target'

describe('normalizeIrisOpenString', () => {
  it('accepts hash-router paths and strips a leading hash', () => {
    expect(normalizeIrisOpenString('/index-network/intent/1')).toBe('/index-network/intent/1')
    expect(normalizeIrisOpenString('#/index-network/intent/1')).toBe('/index-network/intent/1')
  })

  it('maps plugin-scoped iris:// deep links to the same path', () => {
    expect(normalizeIrisOpenString('iris://index-network/intent/1')).toBe('/index-network/intent/1')
    expect(normalizeIrisOpenString('iris://index-network/intent/1?focus=true')).toBe(
      '/index-network/intent/1?focus=true'
    )
  })

  it('maps iris://open/… deep links by stripping the open host', () => {
    expect(normalizeIrisOpenString('iris://open/index-network/intent/1')).toBe('/index-network/intent/1')
    expect(normalizeIrisOpenString('iris://open/settings/plugins')).toBe('/settings/plugins')
  })

  it('rejects reserved iris kinds and unsafe paths', () => {
    expect(normalizeIrisOpenString('iris://blueprint/morning-brief')).toBeNull()
    expect(normalizeIrisOpenString('iris://plugin/install')).toBeNull()
    expect(normalizeIrisOpenString('https://example.com/x')).toBeNull()
    expect(normalizeIrisOpenString('/../etc/passwd')).toBeNull()
    expect(normalizeIrisOpenString('index-network')).toBeNull()
  })
})

describe('resolveIrisOpenPath', () => {
  it('merges structured path + params', () => {
    expect(resolveIrisOpenPath({ path: '/index-network/intent/1', params: { focus: 'true' } })).toBe(
      '/index-network/intent/1?focus=true'
    )
  })

  it('resolves href the same as a bare string', () => {
    expect(resolveIrisOpenPath({ href: 'iris://index-network/intent/1' })).toBe('/index-network/intent/1')
  })
})

describe('pathFromIrisDeepLink', () => {
  it('builds the navigate path from a plugin-scoped deep-link payload', () => {
    expect(pathFromIrisDeepLink('index-network', 'intent/1')).toBe('/index-network/intent/1')
  })

  it('builds the navigate path from iris://open/… payloads', () => {
    expect(pathFromOpenDeepLink('index-network/intent/1')).toBe('/index-network/intent/1')
    expect(pathFromIrisDeepLink('open', 'agent/42')).toBe('/agent/42')
  })

  it('ignores reserved kinds', () => {
    expect(pathFromIrisDeepLink('blueprint', 'morning-brief')).toBeNull()
    expect(pathFromIrisDeepLink('plugin', 'install')).toBeNull()
  })
})
