import { QueryClientProvider } from '@tanstack/react-query'
import { cleanup, renderHook, waitFor } from '@testing-library/react'
import { createElement } from 'react'
import { afterEach, expect, it, vi } from 'vitest'

import type * as IrisApi from '@/iris'
import { bindConfigReadOrigin, getIrisConfigRecord } from '@/iris'
import { queryClient } from '@/lib/query-client'

import { IRIS_CONFIG_KEY, useIrisConfigRecord } from './use-config-record'

vi.mock('@/iris', async importOriginal => ({
  ...(await importOriginal<typeof IrisApi>()),
  getIrisConfigRecord: vi.fn()
}))

afterEach(() => {
  cleanup()
  queryClient.clear()
  vi.clearAllMocks()
})

const wrapper = ({ children }: { children: React.ReactNode }) =>
  createElement(QueryClientProvider, { client: queryClient }, children)

it('updates the write origin when a refetch replaces the displayed record', async () => {
  const first = { display: { theme: 'dark' } }
  const second = { display: { theme: 'light' } }
  bindConfigReadOrigin(first, { connectionId: 'connection-a', profile: 'worker' })
  bindConfigReadOrigin(second, { connectionId: 'connection-b', profile: 'worker' })
  vi.mocked(getIrisConfigRecord).mockResolvedValueOnce(first).mockResolvedValueOnce(second)

  const { result } = renderHook(() => useIrisConfigRecord(), { wrapper })

  // Before the first GET resolves the scope must be `undefined` (not `null`):
  // profileScoped(null) drops the active profile and targets the PRIMARY.
  expect(result.current.data).toBeUndefined()
  expect(result.current.writeScope).toBeUndefined()
  expect(result.current.writeScope).not.toBeNull()

  await waitFor(() => expect(result.current.data).toBe(first))
  expect(result.current.writeScope).toEqual({ connectionId: 'connection-a', profile: 'worker' })

  await queryClient.invalidateQueries({ queryKey: IRIS_CONFIG_KEY })

  await waitFor(() => expect(result.current.data).toEqual(second))
  await waitFor(() => expect(result.current.writeScope).toEqual({ connectionId: 'connection-b', profile: 'worker' }))
})
