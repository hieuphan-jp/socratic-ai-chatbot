/**
 * pages/LoginPage.tsx
 *
 * JA: ログイン画面。pages は「組み立て」だけを担う（部品を並べ、遷移を指示するのみ）。
 *     ログインの中身は features/auth の LoginForm、遷移は router に任せる。
 *     ★ログイン前でも言語を変えられるよう、この画面にも言語切替を置く。
 * VI: Trang đăng nhập. pages chỉ lo "lắp ghép" (đặt component, chỉ định điều hướng).
 *     Nội dung đăng nhập giao cho LoginForm của features/auth, điều hướng giao cho router.
 *     ★Đặt cả nút đổi ngôn ngữ ở màn này để đổi được ngay cả khi chưa đăng nhập.
 */
import { useNavigate } from 'react-router-dom'

import { LoginForm } from '@/features/auth/components/LoginForm'
import { useI18n } from '@/shared/i18n'
import { Card, LanguageSwitcher, PageContainer } from '@/shared/ui'

export function LoginPage() {
  const navigate = useNavigate()
  const { t } = useI18n()

  return (
    <PageContainer width="narrow" className="pt-16">
      <div className="flex justify-end">
        <LanguageSwitcher />
      </div>
      <Card>
        <h1 className="mb-4 text-lg font-semibold text-slate-800">{t('auth.login.title')}</h1>
        {/* JA: 成功したらトップへ / VI: Thành công thì về trang chủ */}
        <LoginForm onSuccess={() => navigate('/')} />
      </Card>
    </PageContainer>
  )
}
