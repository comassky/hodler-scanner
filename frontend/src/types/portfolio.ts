// Portfolio payloads — derived from the backend OpenAPI schema.
// Regenerate with `pnpm gen:api` after changing the backend response models.
import type { components } from './api'

type S = components['schemas']

export type Position = S['Position']
export type PortfolioTotals = S['PortfolioTotals']
export type Portfolio = S['Portfolio']
