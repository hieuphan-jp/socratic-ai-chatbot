/**
 * shared/i18n/locale.ts
 *
 * JA: 対応言語の定義と、選択中の言語の保存/復元。保存先は localStorage のみで、
 *     バックエンドは関与しない(User モデルの変更もマイグレーションも不要)。
 *     ★ここは「どの言語があるか」だけを持ち、翻訳文そのものは messages/ に置く。
 * VI: Định nghĩa các ngôn ngữ hỗ trợ và lưu/khôi phục ngôn ngữ đang chọn. Chỉ lưu
 *     ở localStorage, không liên quan backend (không cần sửa model User hay migration).
 *     ★File này chỉ giữ "có những ngôn ngữ nào", còn câu dịch nằm ở messages/.
 */

export const LOCALES = ['ja', 'vi', 'en'] as const
export type Locale = (typeof LOCALES)[number]

export const DEFAULT_LOCALE: Locale = 'ja'

// JA: 言語切替UIに出す表示名。その言語の話者自身が読める綴りで書く(自称表記)。
// VI: Tên hiển thị trên UI đổi ngôn ngữ. Viết theo cách người bản ngữ tự gọi.
export const LOCALE_LABELS: Record<Locale, string> = {
  ja: '日本語',
  vi: 'Tiếng Việt',
  en: 'English',
}

// JA: Date#toLocaleDateString 等に渡すIntlロケール文字列。日付・時刻の書式
//     (年月日の順番、区切り文字)も選択言語に揃えるために使う。
// VI: Chuỗi locale của Intl để truyền vào Date#toLocaleDateString v.v. Dùng để
//     định dạng ngày/giờ (thứ tự năm-tháng-ngày, dấu phân cách) khớp với ngôn ngữ đang chọn.
export const LOCALE_TO_INTL: Record<Locale, string> = {
  ja: 'ja-JP',
  vi: 'vi-VN',
  en: 'en-US',
}

const STORAGE_KEY = 'app.locale'

function isLocale(value: unknown): value is Locale {
  return typeof value === 'string' && (LOCALES as readonly string[]).includes(value)
}

export function loadLocale(): Locale {
  // JA: localStorage が使えない環境(プライベートモード等)でも落ちないようにする。
  // VI: Không để crash ở môi trường không dùng được localStorage (chế độ riêng tư, v.v).
  try {
    const saved = window.localStorage.getItem(STORAGE_KEY)
    if (isLocale(saved)) return saved
  } catch {
    // 無視して既定言語にフォールバック / Bỏ qua, quay về ngôn ngữ mặc định
  }
  return DEFAULT_LOCALE
}

export function saveLocale(locale: Locale): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, locale)
  } catch {
    // 保存できなくても表示自体は続行できる / Không lưu được thì vẫn hiển thị bình thường
  }
}
