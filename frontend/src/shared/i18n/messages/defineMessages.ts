/**
 * shared/i18n/messages/defineMessages.ts
 *
 * JA: 翻訳辞書を「型安全に」定義するためのヘルパー。日本語(ja)をキーの正本とし、
 *     vi/en は ja と同じキーを全部持つことを型で強制する。
 *     → どれか1言語だけ翻訳を書き忘れると tsc(CIのtypecheck)で落ちる。
 *     ★実行時に何かする関数ではなく、型を効かせるためだけの薄い関数。
 * VI: Helper để định nghĩa từ điển dịch một cách "an toàn kiểu". Lấy tiếng Nhật (ja)
 *     làm bản gốc của khóa; kiểu sẽ bắt buộc vi/en phải có đủ mọi khóa của ja.
 *     → Quên dịch ở một ngôn ngữ nào đó là tsc (typecheck ở CI) sẽ báo lỗi.
 *     ★Đây chỉ là hàm mỏng để áp kiểu, không xử lý gì lúc chạy.
 */
import type { Locale } from '../locale'

export type MessageBundle<T extends Record<string, string>> = Record<Locale, Record<keyof T, string>>

export function defineMessages<const T extends Record<string, string>>(bundle: {
  ja: T
  vi: Record<keyof T, string>
  en: Record<keyof T, string>
}): MessageBundle<T> {
  return bundle
}
