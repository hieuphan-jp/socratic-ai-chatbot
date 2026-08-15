/**
 * shared/api/client.ts
 *
 * JA: ★全HTTP通信の唯一の入口。
 * VI: ★Cửa duy nhất cho MỌI giao tiếp HTTP. features/pages KHÔNG gọi fetch trực tiếp mà luôn qua đây.
 */

// JA: API の基点。Vite プロキシ経由なので相対パスでよい。
// VI: Gốc API. Đi qua proxy Vite nên dùng đường dẫn tương đối là đủ.
const API_BASE = '/api'

// JA: ログイン画面のパス。401 時のリダイレクト先。
// VI: Đường dẫn trang đăng nhập, đích chuyển hướng khi 401.
const LOGIN_PATH = '/login'

/**
 * JA: 画面へ渡す統一エラー型。
 * VI: Kiểu lỗi thống nhất đưa lên màn hình.
 */
export class ApiError extends Error {
  status: number
  data: unknown
  constructor(status: number, message: string, data: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

// JA: Django が発行する csrftoken Cookie を読む。
// VI: Đọc Cookie csrftoken do Django phát hành.
function readCsrfToken(): string {
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/)
  return match ? decodeURIComponent(match[1]) : ''
}

// VI: Các method thay đổi dữ liệu cần CSRF token.
const CSRF_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE'])

type RequestOptions = {
  method?: string
  body?: unknown
  signal?: AbortSignal
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const method = (options.method ?? 'GET').toUpperCase()

  const headers: Record<string, string> = {}
  if (options.body !== undefined) headers['Content-Type'] = 'application/json'
  if (CSRF_METHODS.has(method)) headers['X-CSRFToken'] = readCsrfToken()

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    credentials: 'include',
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    signal: options.signal,
  })

  // VI: 401/403 = chưa xác thực hoặc hết session. Chuyển về trang đăng nhập.
  if (res.status === 401 || res.status === 403) {
    if (res.status === 401 && window.location.pathname !== LOGIN_PATH) {
      window.location.assign(LOGIN_PATH)
    }
  }

  // VI: 204 No Content không có body.
  if (res.status === 204) return undefined as T

  const data = await res.json().catch(() => null)

  if (!res.ok) {
    const message =
      (data && typeof data === 'object' && 'detail' in data && String((data as { detail: unknown }).detail)) ||
      `Yêu cầu thất bại (${res.status}) / リクエストに失敗しました (${res.status})`
    throw new ApiError(res.status, message, data)
  }

  return data as T
}

/**
 * VI: Export đối tượng api chuẩn dùng trong toàn bộ ứng dụng.
 */
export const api = {
  get: <T>(path: string, signal?: AbortSignal) => request<T>(path, { method: 'GET', signal }),
  post: <T>(path: string, body?: unknown) => request<T>(path, { method: 'POST', body }),
  put: <T>(path: string, body?: unknown) => request<T>(path, { method: 'PUT', body }),
  patch: <T>(path: string, body?: unknown) => request<T>(path, { method: 'PATCH', body }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}