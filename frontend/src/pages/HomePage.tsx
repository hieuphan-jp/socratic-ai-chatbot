/**
 * pages/HomePage.tsx
 *
 * JA: ログイン後の着地点。各機能への入口を並べる。
 *     ★デザイン統一の参考実装(お手本)。新しい画面を作る/直すときは、この形
 *     (PageContainer → PageHeader → Card/部品、文言は全て t() 経由)をコピー元にする。
 *     詳しくは DESIGN_SYSTEM.md を参照。
 * VI: Điểm đến sau khi đăng nhập. Liệt kê lối vào từng tính năng.
 *     ★Bản mẫu tham khảo cho việc thống nhất thiết kế. Khi tạo/sửa màn hình mới, dùng
 *     đúng khuôn này (PageContainer → PageHeader → Card/component, mọi câu chữ qua t()).
 *     Chi tiết xem DESIGN_SYSTEM.md.
 */
import { Link, useNavigate } from 'react-router-dom'

import { MessagesSquare, TreeDeciduous } from 'lucide-react'

import { useLogout, useMe } from '@/features/auth/api/hooks'
import { useI18n } from '@/shared/i18n'
import { Button, Card, LanguageSwitcher, PageContainer, PageHeader } from '@/shared/ui'

export function HomePage() {
  const navigate = useNavigate()
  const me = useMe()
  const logout = useLogout()
  const { t } = useI18n()

  return (
    <PageContainer>
      <PageHeader
        title={t('auth.home.title')}
        subtitle={t('auth.home.subtitle')}
        actions={
          <>
            <LanguageSwitcher />
            {me.data && <span className="text-xs text-slate-500">{me.data.username}</span>}
            <Button
              size="sm"
              onClick={() => logout.mutate(undefined, { onSuccess: () => navigate('/login') })}
            >
              {t('auth.logout')}
            </Button>
          </>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2">
        <Link to="/learning-tree" className="no-underline">
          <Card className="h-full transition-shadow hover:shadow-md">
            <div className="flex items-center gap-3">
              <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-leaf-100 text-leaf-ink">
                <TreeDeciduous className="h-5 w-5" />
              </span>
              <span className="text-sm font-semibold text-slate-800">
                {t('auth.home.learningTree')}
              </span>
            </div>
          </Card>
        </Link>

        <Link to="/hint-chat" className="no-underline">
          <Card className="h-full transition-shadow hover:shadow-md">
            <div className="flex items-center gap-3">
              <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-teal-100 text-teal-700">
                <MessagesSquare className="h-5 w-5" />
              </span>
              <span className="text-sm font-semibold text-slate-800">
                {t('auth.home.hintChat')}
              </span>
            </div>
          </Card>
        </Link>
      </div>
    </PageContainer>
  )
}
