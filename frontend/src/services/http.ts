// Typed HTTP client. Wraps `ofetch` so composables never touch the transport
// layer directly and always receive a normalized `ApiError` on failure.
import { ofetch, FetchError } from 'ofetch'

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

// TanStack Query already owns retries; disable ofetch's own retry to avoid doubling.
const request = ofetch.create({ retry: 0 })

/** Map ofetch failures to `ApiError`, preferring FastAPI's `{ detail }` message. */
function toApiError(e: unknown): ApiError {
  if (e instanceof FetchError) {
    const detail = e.data?.detail
    return new ApiError(e.statusCode ?? 0, typeof detail === 'string' ? detail : e.message)
  }
  return new ApiError(0, e instanceof Error ? e.message : String(e))
}

/** GET + parse JSON, throwing `ApiError` on a non-2xx response. */
export async function getJson<T>(url: string): Promise<T> {
  try {
    return await request<T>(url)
  } catch (e) {
    throw toApiError(e)
  }
}

/** GET returning `null` instead of throwing on failure (for optional resources). */
export async function getJsonOrNull<T>(url: string): Promise<T | null> {
  try {
    return await request<T>(url)
  } catch {
    return null
  }
}

/** Send a JSON body with the given method and parse the JSON response. */
export async function sendJson<T>(
  url: string,
  method: 'POST' | 'PUT' | 'DELETE',
  body?: unknown,
): Promise<T> {
  try {
    return await request<T>(url, { method, body: body as Record<string, unknown> | undefined })
  } catch (e) {
    throw toApiError(e)
  }
}

export const enc = (s: string): string => encodeURIComponent(s)
