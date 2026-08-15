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
// VI: index = mastery_level. 0 là chưa học (xám), 1-5 xanh đậm dần theo số lần ôn.
const LEAF_STYLES = [
  'bg-slate-100 border-slate-200 text-slate-500',
  'bg-emerald-50 border-emerald-200 text-emerald-700',
  'bg-emerald-100 border-emerald-300 text-emerald-700',
  'bg-emerald-200 border-emerald-400 text-emerald-800',
  'bg-emerald-400 border-emerald-500 text-white',
  'bg-emerald-600 border-emerald-700 text-white',
] as const

export function leafStyleForMastery(level: number): string {
  const idx = Math.min(Math.max(Math.round(level), 0), LEAF_STYLES.length - 1)
  return LEAF_STYLES[idx]
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
