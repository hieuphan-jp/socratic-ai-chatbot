/**
 * shared/lib/cn.ts
 *
 * JA: className を条件付きで組み立てる小さなヘルパー。false/undefined を捨てて空白で繋ぐだけ。
 *     clsx などを足すほどの規模ではないので自前で持つ(依存を増やさない方針)。
 *     ※同じプロパティを2回指定した場合の勝敗はCSSの詳細度に従う(後勝ちではない)ため、
 *       打ち消し合うクラスを同時に渡さないこと。
 * VI: Helper nhỏ để ghép className theo điều kiện. Chỉ bỏ false/undefined rồi nối bằng dấu cách.
 *     Quy mô chưa cần tới clsx nên tự viết (giữ chủ trương không tăng dependency).
 *     ※Nếu truyền trùng thuộc tính, thắng thua theo độ ưu tiên CSS (KHÔNG phải cái sau thắng),
 *       nên đừng truyền cùng lúc các class triệt tiêu nhau.
 */
export function cn(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(' ')
}
