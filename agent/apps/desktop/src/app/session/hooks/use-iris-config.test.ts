// @vitest-environment jsdom
import { act, renderHook } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { $terminalFontFamily, setTerminalFontFamilyFromConfig } from '@/app/right-sidebar/terminal/terminal-font'
import { getIrisConfig } from '@/iris'
import { persistString } from '@/lib/storage'
import { $showReasoning, setShowReasoningFromConfig } from '@/store/reasoning-disclosure'
import {
  $currentCwd,
  $currentFastMode,
  $currentReasoningEffort,
  $defaultReasoningEffort,
  markComposerSelectionManual,
  setCurrentCwd,
  setCurrentFastMode,
  setCurrentModelSource,
  setCurrentReasoningEffort,
  setDefaultReasoningEffort
} from '@/store/session'

import { deferred } from '../../../test/deferred'

import { useIrisConfig } from './use-iris-config'

vi.mock('@/iris', () => ({
  getIrisConfig: vi.fn(),
  getIrisConfigDefaults: vi.fn().mockResolvedValue({})
}))

const WORKSPACE_CWD_KEY = 'iris.desktop.workspace-cwd'

const mockConfig = (config: Record<string, unknown>) =>
  vi.mocked(getIrisConfig).mockResolvedValue(config as Awaited<ReturnType<typeof getIrisConfig>>)

describe('useIrisConfig refreshIrisConfig', () => {
  beforeEach(() => {
    // Reset atoms and localStorage between tests
    setShowReasoningFromConfig(undefined)
    setCurrentCwd('')
    setCurrentFastMode(false)
    setCurrentModelSource('')
    setCurrentReasoningEffort('')
    setDefaultReasoningEffort('')
    setTerminalFontFamilyFromConfig('')
    persistString(WORKSPACE_CWD_KEY, null)
  })

  // #49664: the Reasoning Blocks toggle wrote config but the renderer never
  // read it. A refresh mirrors the key (quoted "false" included) and a
  // missing key falls back to the DEFAULT_CONFIG default (on).
  it('mirrors display.show_reasoning and resets a missing key to the default', async () => {
    mockConfig({ display: { show_reasoning: 'false' } })
    const { result } = renderHook(() => useIrisConfig({ activeSessionIdRef: { current: null } }))

    await act(async () => {
      await result.current.refreshIrisConfig()
    })
    expect($showReasoning.get()).toBe(false)

    mockConfig({})
    await act(async () => {
      await result.current.refreshIrisConfig()
    })
    expect($showReasoning.get()).toBe(true)
  })

  // Regression: the composer keeps a manual model pick sticky, which skips the
  // composer reseed. The profile default must still be published, because the
  // model picker resolves "the default effort" from it when applying a model's
  // preset — otherwise selecting a model silently downgrades a configured
  // `agent.reasoning_effort: high` to Iris' built-in medium.
  it('publishes the profile default effort even when a manual pick blocks the composer reseed', async () => {
    setCurrentModelSource('manual')
    setCurrentReasoningEffort('low')

    mockConfig({ agent: { reasoning_effort: 'high' } })
    const { result } = renderHook(() => useIrisConfig({ activeSessionIdRef: { current: null } }))

    await act(async () => {
      await result.current.refreshIrisConfig()
    })

    expect($defaultReasoningEffort.get()).toBe('high')
    // The manual pick itself is still respected.
    expect($currentReasoningEffort.get()).toBe('low')
  })

  it('does not let terminal.cwd replace an inactive selected workspace', async () => {
    setCurrentCwd('/Users/example/repo/.worktrees/feature')

    mockConfig({ terminal: { cwd: '/Users/example/new-workspace' } })
    const { result } = renderHook(() => useIrisConfig({ activeSessionIdRef: { current: null } }))

    await act(async () => {
      await result.current.refreshIrisConfig()
    })

    expect($currentCwd.get()).toBe('/Users/example/repo/.worktrees/feature')
  })

  it('does not let terminal.cwd replace an active session workspace', async () => {
    setCurrentCwd('/Users/example/repo/.worktrees/attached')

    mockConfig({ terminal: { cwd: '/Users/example/new-workspace' } })
    const { result } = renderHook(() => useIrisConfig({ activeSessionIdRef: { current: 'session-1' } }))

    await act(async () => {
      await result.current.refreshIrisConfig()
    })

    expect($currentCwd.get()).toBe('/Users/example/repo/.worktrees/attached')
  })

  it('does not let a stale forced config refresh overwrite newer draft selector intent', async () => {
    const profileConfig = deferred<Awaited<ReturnType<typeof getIrisConfig>>>()
    vi.mocked(getIrisConfig).mockReturnValueOnce(profileConfig.promise)

    const { result } = renderHook(() => useIrisConfig({ activeSessionIdRef: { current: null } }))

    let pendingRefresh!: Promise<void>
    act(() => {
      pendingRefresh = result.current.refreshIrisConfig(true)
    })
    expect(getIrisConfig).toHaveBeenCalled()

    // The user turns Fast off and chooses a different effort while the profile
    // defaults are still loading. That newer picker intent owns the composer.
    markComposerSelectionManual()
    setCurrentReasoningEffort('high')
    setCurrentFastMode(false)
    profileConfig.resolve({
      agent: { reasoning_effort: 'low', service_tier: 'priority' }
    } as Awaited<ReturnType<typeof getIrisConfig>>)

    await act(async () => {
      await pendingRefresh
    })

    expect($currentReasoningEffort.get()).toBe('high')
    expect($currentFastMode.get()).toBe(false)
  })

  it('does not publish config after its switch loses ownership', async () => {
    const staleConfig = deferred<Awaited<ReturnType<typeof getIrisConfig>>>()
    vi.mocked(getIrisConfig).mockReturnValueOnce(staleConfig.promise)
    const { result } = renderHook(() => useIrisConfig({ activeSessionIdRef: { current: null } }))
    let ownsSwitch = true

    let refresh!: Promise<void>
    act(() => {
      refresh = result.current.refreshIrisConfig(false, () => ownsSwitch)
    })

    ownsSwitch = false
    staleConfig.resolve({
      display: { show_reasoning: false },
      agent: { reasoning_effort: 'high', service_tier: 'priority' },
      terminal: { font_family: 'MesloLGS NF' }
    } as Awaited<ReturnType<typeof getIrisConfig>>)

    await act(async () => {
      await refresh
    })

    expect($defaultReasoningEffort.get()).toBe('')
    expect($currentReasoningEffort.get()).toBe('')
    expect($currentFastMode.get()).toBe(false)
    expect($terminalFontFamily.get()).toBe('')
    expect($showReasoning.get()).toBe(true)
  })

  it('does not let an older profile config overwrite a newer profile', async () => {
    const profileB = deferred<Awaited<ReturnType<typeof getIrisConfig>>>()
    const profileC = deferred<Awaited<ReturnType<typeof getIrisConfig>>>()
    vi.mocked(getIrisConfig).mockReturnValueOnce(profileB.promise).mockReturnValueOnce(profileC.promise)

    const { result } = renderHook(() => useIrisConfig({ activeSessionIdRef: { current: null } }))

    let refreshB!: Promise<void>
    let refreshC!: Promise<void>
    act(() => {
      refreshB = result.current.refreshIrisConfig(true)
      refreshC = result.current.refreshIrisConfig(true)
    })

    profileC.resolve({ agent: { reasoning_effort: 'low', service_tier: 'normal' } })
    await act(async () => {
      await refreshC
    })
    profileB.resolve({ agent: { reasoning_effort: 'high', service_tier: 'priority' } })
    await act(async () => {
      await refreshB
    })

    expect($currentReasoningEffort.get()).toBe('low')
    expect($currentFastMode.get()).toBe(false)
  })

  it('does not let an older profile response restore its terminal font', async () => {
    const profileB = deferred<Awaited<ReturnType<typeof getIrisConfig>>>()
    const profileC = deferred<Awaited<ReturnType<typeof getIrisConfig>>>()
    vi.mocked(getIrisConfig).mockReturnValueOnce(profileB.promise).mockReturnValueOnce(profileC.promise)
    const { result } = renderHook(() => useIrisConfig({ activeSessionIdRef: { current: null } }))

    let refreshB!: Promise<void>
    let refreshC!: Promise<void>
    act(() => {
      refreshB = result.current.refreshIrisConfig(true)
      refreshC = result.current.refreshIrisConfig(true)
    })

    profileC.resolve({ terminal: { font_family: 'Hack Nerd Font' } })
    await act(async () => {
      await refreshC
    })
    profileB.resolve({ terminal: { font_family: 'MesloLGS NF' } })
    await act(async () => {
      await refreshB
    })

    expect($terminalFontFamily.get()).toBe('Hack Nerd Font')
  })
})
