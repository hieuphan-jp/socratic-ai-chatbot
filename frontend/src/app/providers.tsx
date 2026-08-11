/**
 * app/providers.tsx
 *
 * JA: アプリ全体を包む Provider をここに集約する。今は TanStack Query の QueryClientProvider。
 *     全画面がサーバ状態キャッシュを共有できるよう、最上位で一度だけ生成する。
 * VI: Gom các Provider bao toàn app ở đây. Hiện có QueryClientProvider của TanStack Query.
 *     Tạo một lần ở cấp cao nhất để mọi màn hình chia sẻ cache trạng thái server.
 */
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

// JA: QueryClient はモジュールスコープで1つだけ作る（再レンダーで作り直さない）。
// VI: Chỉ tạo 1 QueryClient ở phạm vi module (không tạo lại khi re-render).
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // JA: 401/403 でのリダイレクトは client 側で処理するのでリトライは控えめに。
      // VI: Redirect khi 401/403 do client lo, nên hạn chế retry.
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

export function AppProviders({ children }: { children: ReactNode }) {
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
}
