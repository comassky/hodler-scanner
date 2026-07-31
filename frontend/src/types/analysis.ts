// Ticker analysis payload — derived from the backend OpenAPI schema (backend/schemas.py).
// Regenerate with `pnpm gen:api` after changing the backend response models.
import type { components } from './api'

type S = components['schemas']

export type MarketRegime = S['MarketRegime']
export type AnalysisPrice = S['AnalysisPrice']
export type AnalysisIndicators = S['AnalysisIndicators']
export type AnalysisDistances = S['AnalysisDistances']
export type AnalysisFundamentals = S['AnalysisFundamentals']
export type AnalysisSignals = S['AnalysisSignals']
export type AnalysisSynthese = S['AnalysisSynthese']
export type Diagnostic = S['Diagnostic']
export type AnalysisBlock = S['AnalysisBlock']
export type Analysis = S['Analysis']

/** Signed per-factor score contributions, keyed by factor code (see scoreComp i18n). */
export type ScoreDetails = Record<string, number>

/** A dashboard batch item: a full analysis, or an error stub for a failed ticker. */
export interface DashboardItem extends Partial<Analysis> {
  ticker: string
  name?: string
  error?: string | null
}
