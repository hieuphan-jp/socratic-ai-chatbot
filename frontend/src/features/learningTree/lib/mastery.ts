/**
 * features/learningTree/lib/mastery.ts
 *
 * JA: mastery_level(定着度・0〜mastery_max_level)と is_due(復習タイミング)を
 *     見た目(色・バッジ)に変換する。CONVENTIONS.md §12の通り、バックエンドは
 *     数値・フラグだけを返し色は返さないので、対応表はフロントのこの1箇所に閉じる。
 *     色の濃さ(定着度)と復習タイミングは別軸(設計方針C)なので、関数も分けてある。
 * VI: Chuyển mastery_level (độ ghi nhớ, 0 đến mastery_max_level) và is_due (thời điểm
 *     ôn tập) thành hình thức hiển thị (màu, badge). Theo CONVENTIONS.md §12, backend
 *     chỉ trả số/cờ chứ không trả màu, nên bảng ánh xạ gói gọn ở đây. Độ đậm màu (độ ghi
 *     nhớ) và thời điểm ôn tập là 2 trục riêng (phương án thiết kế C) nên tách 2 hàm.
 */
import type { ReviewSchedule, TreeNode } from '@/shared/types'

// JA: index = mastery_level。0は未学習(灰)、1〜5は復習回数に応じて緑が濃くなる。
//     ★葉の塗り色/枠線色はindex.cssの@themeで定義したleaf-*(パステル系)トークンを
//     CSS変数として直接参照する(var(--color-leaf-400)など)。SVGのfill/stroke属性は
//     CSS変数をそのまま解決できるので、16進値をここに重複させる必要がない
//     (色を変えたい時はindex.cssの@themeを直すだけで両方の木に反映される)。
//     最上段(5)も彩度を抑え、白文字にはしない(パステル方針)。
// VI: index = mastery_level. 0 là chưa học (xám), 1-5 xanh đậm dần theo số lần ôn.
//     ★Màu nền/viền của lá tham chiếu trực tiếp biến CSS của token leaf-* (tông
//     pastel) định nghĩa ở @theme trong index.css (vd var(--color-leaf-400)).
//     Thuộc tính fill/stroke của SVG đọc được biến CSS bình thường nên không cần
//     lặp lại giá trị hex ở đây (muốn đổi màu chỉ cần sửa @theme trong index.css,
//     cả 2 cây đều tự cập nhật theo).
//     Bậc cao nhất (5) vẫn giữ độ bão hòa thấp, không đổi sang chữ trắng.
const LEAF_TONES = [
  { fill: '#f1f5f9', stroke: '#cbd5e1', textClassName: 'text-slate-500' }, // 0: 未学習(Tailwind標準色のまま)
  { fill: 'var(--color-leaf-50)', stroke: 'var(--color-leaf-200)', textClassName: 'text-leaf-ink' }, // 1
  { fill: 'var(--color-leaf-100)', stroke: 'var(--color-leaf-300)', textClassName: 'text-leaf-ink' }, // 2
  { fill: 'var(--color-leaf-200)', stroke: 'var(--color-leaf-400)', textClassName: 'text-leaf-ink' }, // 3
  { fill: 'var(--color-leaf-300)', stroke: 'var(--color-leaf-500)', textClassName: 'text-leaf-ink' }, // 4
  { fill: 'var(--color-leaf-400)', stroke: 'var(--color-leaf-600)', textClassName: 'text-leaf-ink' }, // 5
] as const

export function leafToneForMastery(level: number): (typeof LEAF_TONES)[number] {
  const idx = Math.min(Math.max(Math.round(level), 0), LEAF_TONES.length - 1)
  return LEAF_TONES[idx]
}

// JA: node_id -> ReviewSchedule の対応表を作る。無い葉は「未学習」。
// VI: Tạo bảng tra node_id -> ReviewSchedule. Lá không có nghĩa là "chưa học".
export function indexSchedulesByNodeId(
  schedules: ReviewSchedule[]
): Map<string, ReviewSchedule> {
  return new Map(schedules.map((s) => [s.node_id, s]))
}

// JA: 木全体の定着率(%)。「復習タイミングをまだ迎えていない葉」÷「葉の総数」
//     (方針C)。未学習(スケジュール無し)の葉は分子に入らないが分母には入る。
// VI: Tỉ lệ ghi nhớ của cả cây (%). "Số lá chưa tới hạn ôn" ÷ "tổng số lá"
//     (phương án C). Lá chưa học (không có schedule) không tính vào tử số nhưng vẫn tính vào mẫu số.
export function computeRetentionPercent(
  tree: TreeNode[],
  scheduleByNodeId: Map<string, ReviewSchedule>
): { total: number; notDue: number; percent: number } {
  let total = 0
  let notDue = 0

  function walk(nodes: TreeNode[]) {
    for (const node of nodes) {
      if (node.type === 'knowledge_node') {
        total += 1
        const schedule = scheduleByNodeId.get(node.id)
        if (schedule && !schedule.is_due) notDue += 1
      }
      if (node.children) walk(node.children)
    }
  }
  walk(tree)

  return { total, notDue, percent: total === 0 ? 0 : Math.round((notDue / total) * 100) }
}
