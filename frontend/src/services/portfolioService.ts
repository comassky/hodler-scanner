// Portfolio endpoints.
import { enc, getJson, sendJson } from './http'
import type { Portfolio } from '../types/portfolio'

export interface PositionInput {
  quantity: number
  avg_cost: number
  note: string | null
}

export const portfolioService = {
  get(): Promise<Portfolio> {
    return getJson<Portfolio>('/portfolio')
  },

  upsert(ticker: string, input: PositionInput): Promise<Portfolio> {
    return sendJson<Portfolio>(`/portfolio/${enc(ticker)}`, 'PUT', input)
  },

  remove(ticker: string): Promise<Portfolio> {
    return sendJson<Portfolio>(`/portfolio/${enc(ticker)}`, 'DELETE')
  },
}
