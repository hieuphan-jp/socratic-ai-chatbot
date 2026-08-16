/**
 * shared/ui/LanguageSwitcher.tsx
 *
 * JA: 表示言語(日本語/Tiếng Việt/English)の切替。選択は localStorage に保存され、
 *     次回アクセス時も保たれる(バックエンドには送らない)。
 *     ★どの画面からでも変えられるよう、各ページのヘッダー右側(PageHeaderのactions)に置く。
 * VI: Đổi ngôn ngữ hiển thị (日本語 / Tiếng Việt / English). Lựa chọn được lưu ở
 *     localStorage, giữ nguyên cho lần truy cập sau (không gửi lên backend).
 *     ★Đặt ở phía phải header mỗi trang (actions của PageHeader) để đổi được từ mọi màn hình.
 */
import { Languages } from 'lucide-react'

import { LOCALE_LABELS, LOCALES, useI18n } from '@/shared/i18n'
import type { Locale } from '@/shared/i18n'

export function LanguageSwitcher() {
  const { locale, setLocale, t } = useI18n()

  return (
    <label className="inline-flex items-center gap-1.5" title={t('common.language')}>
      <Languages className="h-4 w-4 shrink-0 text-slate-400" aria-hidden="true" />
      <span className="sr-only">{t('common.language')}</span>
      <select
        value={locale}
        onChange={(e) => setLocale(e.target.value as Locale)}
        className="rounded-xl border border-slate-200 bg-white px-2.5 py-1.5 text-xs text-slate-600 focus:border-teal-400 focus:outline-none focus:ring-2 focus:ring-teal-100"
      >
        {LOCALES.map((value) => (
          <option key={value} value={value}>
            {LOCALE_LABELS[value]}
          </option>
        ))}
      </select>
    </label>
  )
}
