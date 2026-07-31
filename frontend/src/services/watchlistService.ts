// Watchlist (favorites) endpoints.
import { enc, getJson, sendJson } from './http'

interface FavoritesResponse {
  favorites: string[]
}

export const watchlistService = {
  list(): Promise<string[]> {
    return getJson<FavoritesResponse>('/favorites').then(r => r.favorites)
  },

  replace(tickers: string[]): Promise<string[]> {
    return sendJson<FavoritesResponse>('/favorites', 'PUT', { tickers }).then(r => r.favorites)
  },

  add(ticker: string): Promise<string[]> {
    return sendJson<FavoritesResponse>(`/favorites/${enc(ticker)}`, 'POST').then(r => r.favorites)
  },

  remove(ticker: string): Promise<string[]> {
    return sendJson<FavoritesResponse>(`/favorites/${enc(ticker)}`, 'DELETE').then(r => r.favorites)
  },
}
