/**
 * app/providers.tsx
 *
 * JA: アプリ全体を包む Provider をここに集約する。TanStack Query の QueryClientProvider と、
 *     表示言語(ja/vi/en)を配る I18nProvider。
 *     全画面がサーバ状態キャッシュと表示言語を共有できるよう、最上位で一度だけ生成する。
 * VI: Gom các Provider bao toàn app ở đây: QueryClientProvider của TanStack Query và
 *     I18nProvider (phát ngôn ngữ hiển thị ja/vi/en).
 *     Tạo một lần ở cấp cao nhất để mọi màn hình chia sẻ cache trạng thái server và ngôn ngữ.
 */
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

import { I18nProvider } from '@/shared/i18n'

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
  return (
    <QueryClientProvider client={queryClient}>
      <I18nProvider>{children}</I18nProvider>
    </QueryClientProvider>
  )
}
