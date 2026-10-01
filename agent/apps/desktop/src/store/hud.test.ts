import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { $activeGatewayProfile } from '@/store/profile'
import { $sessions } from '@/store/session'
import type { SessionInfo } from '@/types/iris'

import { $hudActive, $hudSession, openHud } from './hud'

const desktopWindow = window as unknown as { irisDesktop?: Window['irisDesktop'] }
const initialIrisDesktop = desktopWindow.irisDesktop

const open = vi.fn().mockResolvedValue({ ok: true })

function installBridge() {
  desktopWindow.irisDesktop = {
    hud: { open }
  } as unknown as Window['irisDesktop']
}

function session(overrides: Partial<SessionInfo>): SessionInfo {
  return { id: 's', title: '', created_at: '', updated_at: '', ...overrides } as SessionInfo
}

beforeEach(() => {
  open.mockClear()
  installBridge()
  $hudActive.set(false)
  $hudSession.set(null)
  $sessions.set([])
  $activeGatewayProfile.set('default')
})

afterEach(() => {
  if (initialIrisDesktop) {
    desktopWindow.irisDesktop = initialIrisDesktop
  } else {
    delete desktopWindow.irisDesktop
  }
})

describe('openHud profile targeting (#82285)', () => {
  it('carries the session-stamped profile when the target belongs to another profile', () => {
    $sessions.set([session({ id: 'abc', profile: 'work' })])
    $activeGatewayProfile.set('default')

    openHud('abc')

    expect(open).toHaveBeenCalledWith({ sessionId: 'abc', profile: 'work' })
  })

  it('falls back to the active gateway profile for an unstamped session', () => {
    $sessions.set([session({ id: 'abc', profile: '' })])
    $activeGatewayProfile.set('work')

    openHud('abc')

    expect(open).toHaveBeenCalledWith({ sessionId: 'abc', profile: 'work' })
  })

  it('uses the active gateway profile when opening without a session', () => {
    $activeGatewayProfile.set('research')

    openHud()

    expect(open).toHaveBeenCalledWith({ sessionId: null, profile: 'research' })
  })

  it('uses the active profile when the target session is not in the cache', () => {
    $activeGatewayProfile.set('work')

    openHud('unknown-session')

    expect(open).toHaveBeenCalledWith({ sessionId: 'unknown-session', profile: 'work' })
  })
})
