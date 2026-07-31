// Backtest payloads — derived from the backend OpenAPI schema.
// Regenerate with `pnpm gen:api` after changing the backend response models.
import type { components } from './api'

type S = components['schemas']

export type BandKey = S['BandKey']
export type TimingLevel = S['TimingLevel']
export type BacktestSeriesPoint = S['BacktestSeriesPoint']
export type HorizonStats = S['HorizonStats']
export type ScoreBand = S['ScoreBand']
export type Baseline = S['Baseline']
export type Timing = S['Timing']
export type BacktestReport = S['BacktestReport']
