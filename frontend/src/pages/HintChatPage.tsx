/**
 * pages/HintChatPage.tsx
 *
 * JA: ヒントチャット画面。組み立てのみ行い、中身は features/hintChat に置く。
 *     ★URLに :sessionId があれば、そのセッションを開いた状態で始める(学習木の葉から
 *     「復習を始める」で入ってくる経路)。無ければ従来通り新規チャットとして始まる。
 *     セッションが変わったらkeyで再マウントし、前のセッションの入力欄や思考ツリーの
 *     状態が残らないようにする。
 *     ★2026-08 修正: 新規チャットでセッションが作られた直後、URLを /hint-chat/:sessionId
 *     に置き換える(onSessionCreated)。これが無いと、セッションIDはReactのstateにしか
 *     残らないため、ページ再読み込みやHMR等での再マウントが起きた瞬間に「どのセッションを
 *     表示すべきか」が分からなくなり、会話がまるごと消えたように見えるバグがあった
 *     (データ自体はサーバーに残っているが、フロントエンドが参照を失うだけ)。
 * VI: Trang chat hint. Chỉ lắp ghép, nội dung nằm ở features/hintChat.
 *     ★Nếu URL có :sessionId thì mở sẵn phiên đó (đường vào từ nút "Bắt đầu ôn tập"
 *     ở lá cây học tập). Không có thì bắt đầu như một phiên chat mới như trước.
 *     Khi đổi phiên thì remount qua key để state ô nhập/cây tư duy của phiên cũ không sót lại.
 *     ★Sửa 08/2026: Ngay sau khi session mới được tạo ở chat tự do, thay URL thành
 *     /hint-chat/:sessionId (onSessionCreated). Thiếu bước này thì sessionId chỉ nằm
 *     trong state của React, nên chỉ cần tải lại trang hoặc bị remount do HMR... là
 *     mất dấu "đang xem session nào", trông như cả cuộc hội thoại biến mất (dữ liệu
 *     vẫn còn trên server, chỉ là frontend mất tham chiếu).
 */
import { Link, useNavigate, useParams } from 'react-router-dom'

import { HintChatView } from '@/features/hintChat/components/HintChatView'
import { useI18n } from '@/shared/i18n'
import { PageContainer, PageHeader } from '@/shared/ui'

// JA: ヘッダーの2つのリンクは画面遷移なので Link のまま。見た目だけ Button の
//     ghost/sm に揃える(学習内容ツリー画面のヘッダーとも共通)。
// VI: 2 link ở header là điều hướng, không phải hành động, nên giữ Link. Chỉ
//     đồng bộ hình thức với ghost/sm của Button (dùng chung với header cây học tập).
const HEADER_LINK_CLASS =
  'inline-flex shrink-0 items-center rounded-xl px-3 py-1.5 text-sm font-medium text-slate-500 no-underline transition-colors hover:bg-slate-100 hover:text-slate-700'

export function HintChatPage() {
  const { sessionId } = useParams<{ sessionId?: string }>()
  const { t } = useI18n()
  const navigate = useNavigate()

  return (
    <>
      <PageHeader
        title={t('hintChat.title')}
        subtitle={t('hintChat.subtitle')}
        width="wide"
        actions={
          <>
            <Link to="/learning-tree" className={HEADER_LINK_CLASS}>
              {t('learningTree.title')}
            </Link>
            <Link to="/" className={HEADER_LINK_CLASS}>
              {t('common.back')}
            </Link>
          </>
        }
      />
      <PageContainer width="wide">
        <HintChatView
          key={sessionId ?? 'new'}
          activeSessionId={sessionId}
          onSessionCreated={(newSessionId) => navigate(`/hint-chat/${newSessionId}`, { replace: true })}
        />
      </PageContainer>
    </>
  )
}
