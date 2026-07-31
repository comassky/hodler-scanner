// Ticker search endpoint.
import { getJson } from './http'
import type { SearchResult } from '../types/search'

export const searchService = {
  query(q: string): Promise<SearchResult[]> {
    return getJson<SearchResult[]>(`/search?q=${encodeURIComponent(q)}`)
  },
}
