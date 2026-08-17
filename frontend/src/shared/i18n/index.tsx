/**
 * shared/i18n/index.tsx
 *
 * JA: 多言語表示の入口。画面側はこの useI18n() だけを使い、辞書や localStorage を
 *     直接触らない。
 *     使い方:
 *       const { t, locale, setLocale } = useI18n()
 *       <Button>{t('learningTree.review.start')}</Button>
 *       <span>{t('learningTree.due.overdue', { days: 3 })}</span>
 *     ★キーは補完が効き、存在しないキーを書くと型エラーになる(messages/index.ts)。
 * VI: Cửa vào của hiển thị đa ngôn ngữ. Phía màn hình chỉ dùng useI18n(), KHÔNG đụng
 *     trực tiếp vào từ điển hay localStorage.
 *     Cách dùng:
 *       const { t, locale, setLocale } = useI18n()
 *       <Button>{t('learningTree.review.start')}</Button>
 *       <span>{t('learningTree.due.overdue', { days: 3 })}</span>
 *     ★Khóa được gợi ý tự động, viết khóa không tồn tại sẽ báo lỗi kiểu (messages/index.ts).
 */
import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import { DEFAULT_LOCALE, loadLocale, saveLocale } from './locale'
import type { Locale } from './locale'
import { messages } from './messages'
import type { MessageKey } from './messages'

export { LOCALES, LOCALE_LABELS, LOCALE_TO_INTL, DEFAULT_LOCALE } from './locale'
export type { Locale } from './locale'
export type { MessageKey } from './messages'

// JA: '{days}日超過' のような差し込み用。値は数値か文字列だけ許す(表示に使うため)。
// VI: Dùng để chèn giá trị như '{days}日超過'. Chỉ cho phép số hoặc chuỗi (vì để hiển thị).
type Params = Record<string, string | number>

type I18nValue = {
  locale: Locale
  setLocale: (locale: Locale) => void
  t: (key: MessageKey, params?: Params) => string
}

const I18nContext = createContext<I18nValue | null>(null)

function interpolate(template: string, params?: Params): string {
  if (!params) return template
  return template.replace(/\{(\w+)\}/g, (match, name: string) =>
    name in params ? String(params[name]) : match
  )
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(() => loadLocale())

  const setLocale = useCallback((next: Locale) => {
    setLocaleState(next)
    saveLocale(next)
    // JA: <html lang> も合わせる。スクリーンリーダーの読み上げ言語と、
    //     CSSの言語別フォント指定が正しく効くようにするため。
    // VI: Cập nhật cả <html lang> để trình đọc màn hình đọc đúng ngôn ngữ và
    //     phần font theo ngôn ngữ trong CSS hoạt động đúng.
    document.documentElement.lang = next
  }, [])

  const t = useCallback(
    (key: MessageKey, params?: Params) => {
      // JA: 選択中の言語に無ければ既定言語(ja)へ、それも無ければキー自体を返す。
      //     型で守っているので通常ここは通らないが、保険として文字化けより
      //     「キーが見えている」方がバグに気づきやすい。
      // VI: Không có ở ngôn ngữ đang chọn thì lùi về ngôn ngữ mặc định (ja); vẫn không có
      //     thì trả về chính khóa. Kiểu đã chặn nên bình thường không tới đây, nhưng
      //     hiện ra khóa vẫn dễ phát hiện lỗi hơn là hiện chữ rỗng.
      const table = messages[locale] ?? messages[DEFAULT_LOCALE]
      const template = table[key] ?? messages[DEFAULT_LOCALE][key] ?? key
      return interpolate(template, params)
    },
    [locale]
  )

  const value = useMemo<I18nValue>(() => ({ locale, setLocale, t }), [locale, setLocale, t])

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export function useI18n(): I18nValue {
  const ctx = useContext(I18nContext)
  if (!ctx) {
    // JA: Provider の外で使うと文言が出ないまま静かに壊れるので、明示的に落とす。
    // VI: Dùng ngoài Provider sẽ hỏng âm thầm (mất chữ), nên ném lỗi rõ ràng.
    throw new Error('useI18n must be used inside <I18nProvider>')
  }
  return ctx
}
