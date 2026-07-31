// Chart / fundamentals / news payloads — derived from the backend OpenAPI schema.
// Regenerate with `pnpm gen:api` after changing the backend response models.
import type { components } from './api'

type S = components['schemas']

/** Numeric series may contain nulls where the indicator is undefined. */
export type NumberSeries = Array<number | null>

export type ChartData = S['ChartData']
export type Fundamentals = S['Fundamentals']
export type NewsItem = S['NewsItem']
export type News = S['News']
