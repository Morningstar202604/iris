import { replaceEqualDeep, useQuery } from '@tanstack/react-query'

import {
  getIrisConfigRecord,
  peekConfigReadOrigin,
  type ProfileScope,
  profileScopeKey,
  retainConfigReadOrigin
} from '@/iris'
import { queryClient } from '@/lib/query-client'
import type { IrisConfigRecord } from '@/types/iris'

// One shared cache for the whole profile config record (`GET /api/config`).
// Every settings surface (MCP, model, config) reads and writes through this key
// so a save in one shows in the others, and revisiting a tab paints the cache
// instead of blanking on a fresh fetch.
//
// Distinct from session/hooks/use-iris-config.ts, which is side-effecting —
// it pushes personality/cwd/voice/… into the session stores for live chat.
export const IRIS_CONFIG_KEY = ['iris-config-record'] as const

// Per-scope cache key. The base key (no suffix) is the app-wide active
// profile, unchanged for every caller that passes nothing. An explicit scope —
// the Capabilities scope selector configuring ANOTHER profile, possibly on
// another registered gateway — gets its own suffixed key so switching the
// selector refetches and never paints stale cross-profile config (the
// AGENTS.md scope-in-key rule). profileScopeKey folds a remote pin's
// connection id into the suffix, so two gateways' same-named profiles never
// share a cache row.
export const irisConfigKey = (profile?: ProfileScope) =>
  profile == null ? IRIS_CONFIG_KEY : ([...IRIS_CONFIG_KEY, profileScopeKey(profile)] as const)

// staleTime 0 → serve cache instantly, background-revalidate on every mount.
// `profile` scopes both the query key and the fetch; omitting it preserves the
// exact app-wide behavior (base key, `profileScoped(undefined)` fallback).
export const useIrisConfigRecord = (profile?: ProfileScope) => {
  const query = useQuery({
    queryKey: irisConfigKey(profile),
    // null/undefined both mean "no override" → fetch with undefined so
    // capabilityScoped falls back to the app-wide active profile (passing null
    // would wrongly target the primary backend).
    queryFn: () => getIrisConfigRecord(profile ?? undefined),
    staleTime: 0,
    // Keep structural sharing so an unchanged refetch (every consumer mount at
    // staleTime 0, every invalidate) yields the SAME object and consumers'
    // memos/autosave effects don't re-arm. The read origin lives in a WeakMap
    // keyed by the record, so re-stamp whatever object survives the merge with
    // the origin of the NEW fetch (`next`, bound by getIrisConfigRecord) —
    // otherwise a retained object would keep routing writes to the gateway
    // that served the previous GET.
    structuralSharing: (previous: unknown, next: unknown) =>
      retainConfigReadOrigin(
        replaceEqualDeep(previous as IrisConfigRecord | undefined, next as IrisConfigRecord),
        next as object
      )
  })

  // Attach `writeScope` as a lazy getter instead of spreading `query`: useQuery
  // hands back a tracked-props Proxy, and spreading enumerates EVERY key, which
  // subscribes each consumer to fetchStatus/dataUpdatedAt/… churn. The getter
  // reads `query.data` through the proxy, so only `data` is tracked.
  //
  // `undefined`, never `null`: callers hand this straight to saveIrisConfig
  // with sparse `setNested({}, …)` patches, so the WeakMap misses and the
  // fallback is capabilityScoped(writeScope) → profileScoped(writeScope).
  // profileScoped(undefined) keeps the app-wide `_apiProfile`; profileScoped
  // (null) drops it and would write the PRIMARY profile before the first
  // GET resolves.
  Object.defineProperty(query, 'writeScope', {
    get: () => peekConfigReadOrigin(query.data) ?? undefined,
    configurable: true,
    enumerable: false
  })

  return query as typeof query & { writeScope: ReturnType<typeof peekConfigReadOrigin> }
}

// setIrisConfigCache writes the app-wide (base-key) record. Pass a profile to
// write the suffixed per-profile cache instead — keeps the selector's optimistic
// write-through landing on the same key its query reads.
const writeIrisConfigCache =
  (key: ReturnType<typeof irisConfigKey>) =>
  (
    next:
      IrisConfigRecord | undefined | ((previous: IrisConfigRecord | undefined) => IrisConfigRecord | undefined)
  ) =>
    void queryClient.setQueryData<IrisConfigRecord>(key, previous => {
      const record = typeof next === 'function' ? next(previous) : next

      // setQueryData also runs the hook's structuralSharing (query.setData →
      // replaceData), but that pass stamps the origin of `record` (the NEW
      // value), which optimistic patches do not carry — and it only applies once
      // the observer has built the query. So the previous record's origin is
      // carried over explicitly here.
      return record ? retainConfigReadOrigin(record, previous) : record
    })

export const setIrisConfigCache = writeIrisConfigCache(IRIS_CONFIG_KEY)
export const irisConfigCacheWriter = (profile?: ProfileScope) => writeIrisConfigCache(irisConfigKey(profile))

export const invalidateIrisConfig = (profile?: ProfileScope) =>
  queryClient.invalidateQueries({ queryKey: irisConfigKey(profile) })
