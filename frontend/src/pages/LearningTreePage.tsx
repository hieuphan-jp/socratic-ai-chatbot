/**
 * pages/LearningTreePage.tsx
 *
 * JA: 学習内容の検索木構造画面。組み立てのみ行い、中身は features/learningTree に置く。
 *     ★「木構造」/「タイムログ」をボタンで切り替えられるようにする。木構造は
 *     知識ノード化されたものしか出ないため、途中まで学習した内容も含めて時系列で
 *     振り返れるタイムログ(ChatTimelineView)を同じ画面に用意する。
 *     ★「今日の復習」一覧(DueReviewList)はどちらのビューでも上に固定表示する。
 *     木を自分で開いて葉を探さなくても、放置が長い順に復習に入れるようにするため
 *     (実用化監査 P1-1)。
 * VI: Trang cây nội dung đã học (có tìm kiếm). Chỉ lắp ghép, nội dung nằm ở features/learningTree.
 *     ★Cho phép bấm nút chuyển "Cây" / "Nhật ký thời gian". Cây chỉ hiện phần đã thành
 *     knowledge node, nên chuẩn bị thêm Nhật ký thời gian (ChatTimelineView) ngay trong
 *     cùng màn hình để xem lại cả phần học dở theo thứ tự thời gian.
 *     ★Danh sách "Ôn tập hôm nay" (DueReviewList) luôn hiện cố định phía trên, ở cả 2 view.
 *     Để không cần tự mở cây tìm lá, vào ôn theo thứ tự bỏ quên lâu nhất
 *     (audit thực dụng hóa P1-1).
 */
import { useState } from 'react'

import { Link } from 'react-router-dom'

import { ChatTimelineView } from '@/features/learningTree/components/ChatTimelineView'
import { LearningTreeView } from '@/features/learningTree/components/LearningTreeView'
import { DueReviewList } from '@/features/reviews/components/DueReviewList'
import { useI18n } from '@/shared/i18n'
import { PageContainer, PageHeader, SegmentedControl } from '@/shared/ui'
import type { SegmentedOption } from '@/shared/ui'

type ViewMode = 'tree' | 'timeline'

// JA: ヘッダーの「戻る」はボタンではなく画面遷移なので Link のまま。見た目だけ
//     Button の ghost/sm に揃える(ヒントチャット画面のヘッダーとも共通)。
// VI: "戻る" ở header là điều hướng, không phải hành động, nên giữ Link. Chỉ
//     đồng bộ hình thức với ghost/sm của Button (dùng chung với header chat).
const HEADER_LINK_CLASS =
  'inline-flex shrink-0 items-center rounded-xl px-3 py-1.5 text-sm font-medium text-slate-500 no-underline transition-colors hover:bg-slate-100 hover:text-slate-700'

export function LearningTreePage() {
  const [viewMode, setViewMode] = useState<ViewMode>('tree')
  const { t } = useI18n()

  const viewOptions: ReadonlyArray<SegmentedOption<ViewMode>> = [
    { value: 'tree', label: t('learningTree.view.tree') },
    { value: 'timeline', label: t('learningTree.view.timeline') },
  ]

  return (
    <>
      <PageHeader
        title={t('learningTree.title')}
        subtitle={t('learningTree.subtitle')}
        actions={
          <Link to="/" className={HEADER_LINK_CLASS}>
            {t('common.back')}
          </Link>
        }
      />
      <PageContainer>
        <DueReviewList />

        <SegmentedControl
          options={viewOptions}
          value={viewMode}
          onChange={setViewMode}
          ariaLabel={t('learningTree.title')}
        />

        {viewMode === 'tree' ? <LearningTreeView /> : <ChatTimelineView />}
      </PageContainer>
    </>
  )
}
