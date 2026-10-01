import type { ModelOptionsResult } from '@iris/shared'

import type {
  AnalyticsResponse,
  AuxiliaryModelsResponse,
  MoaConfigResponse,
  ModelAssignmentRequest,
  ModelAssignmentResponse,
  ModelInfoResponse
} from '@/types/iris'

import { capabilityScoped, irisApi, type ProfileScope, profileScoped, STARTUP_REQUEST_TIMEOUT_MS } from './client'

export function getGlobalModelInfo(profile?: null | string): Promise<ModelInfoResponse> {
  return irisApi<ModelInfoResponse>({
    ...profileScoped(profile),
    path: '/api/model/info',
    timeoutMs: STARTUP_REQUEST_TIMEOUT_MS
  })
}

export function getUsageAnalytics(days = 30, profile?: ProfileScope): Promise<AnalyticsResponse> {
  return window.irisDesktop.api<AnalyticsResponse>({
    ...capabilityScoped(profile),
    path: `/api/analytics/usage?days=${Math.max(1, Math.floor(days))}`
  })
}

export function getGlobalModelOptions(
  opts?: {
    refresh?: boolean
    includeUnconfigured?: boolean
    explicitOnly?: boolean
  },
  profile?: null | string
): Promise<ModelOptionsResult> {
  const params = new URLSearchParams()

  if (opts?.refresh) {
    params.set('refresh', '1')
  }

  if (opts?.includeUnconfigured) {
    params.set('include_unconfigured', '1')
  }

  if (opts?.explicitOnly !== false) {
    params.set('explicit_only', '1')
  }

  return irisApi<ModelOptionsResult>({
    ...profileScoped(profile),
    path: params.size > 0 ? `/api/model/options?${params.toString()}` : '/api/model/options',
    timeoutMs: STARTUP_REQUEST_TIMEOUT_MS
  })
}

export interface RecommendedDefaultModel {
  provider: string
  model: string
  /** True/false for Nous (free vs paid tier); null for other providers. */
  free_tier: boolean | null
}

// Recommended default model for a freshly-authenticated provider. Mirrors the
// curation `iris model` does — for Nous it honors the free/paid tier so a
// free user gets a free model instead of a paid default.
export function getRecommendedDefaultModel(
  provider: string,
  profile?: null | string
): Promise<RecommendedDefaultModel> {
  return irisApi<RecommendedDefaultModel>({
    ...profileScoped(profile),
    path: `/api/model/recommended-default?provider=${encodeURIComponent(provider)}`
  })
}

export function setGlobalModel(
  provider: string,
  model: string
): Promise<{ ok: boolean; provider: string; model: string }> {
  return irisApi<{ ok: boolean; provider: string; model: string }>({
    ...profileScoped(),
    path: '/api/model/set',
    method: 'POST',
    body: {
      scope: 'main',
      provider,
      model
    }
  })
}

export function getAuxiliaryModels(profile?: null | string): Promise<AuxiliaryModelsResponse> {
  return irisApi<AuxiliaryModelsResponse>({
    ...profileScoped(profile),
    path: '/api/model/auxiliary'
  })
}

export function getMoaModels(profile?: null | string): Promise<MoaConfigResponse> {
  return irisApi<MoaConfigResponse>({
    ...profileScoped(profile),
    path: '/api/model/moa'
  })
}

export function saveMoaModels(
  body: MoaConfigResponse,
  profile?: null | string
): Promise<MoaConfigResponse & { ok: boolean }> {
  return irisApi<MoaConfigResponse & { ok: boolean }>({
    ...profileScoped(profile),
    path: '/api/model/moa',
    method: 'PUT',
    body
  })
}

export function setModelAssignment(
  body: ModelAssignmentRequest,
  profile?: null | string
): Promise<ModelAssignmentResponse> {
  return irisApi<ModelAssignmentResponse>({
    ...profileScoped(profile),
    path: '/api/model/set',
    method: 'POST',
    body
  })
}
