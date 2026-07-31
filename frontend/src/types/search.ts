// Search payload — derived from the backend OpenAPI schema.
// Regenerate with `pnpm gen:api` after changing the backend response models.
import type { components } from './api'

export type SearchResult = components['schemas']['SearchResult']
