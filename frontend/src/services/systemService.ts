// System-level endpoints (selective data reset).
import { sendJson } from './http'
import type { ResetOptions } from '../types/ui'

export const systemService = {
  /** Clear the selected caches / stored data server-side. */
  reset(options: ResetOptions): Promise<unknown> {
    return sendJson('/reset', 'POST', options)
  },
}
