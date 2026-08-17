/**
 * pages/LoginPage.tsx
 *
 * JA: ログイン画面。pages は「組み立て」だけを担う（部品を並べ、遷移を指示するのみ）。
 *     ログインの中身は features/auth の LoginForm、遷移は router に任せる。
 *     ★ログイン前でも言語を変えられるよう、この画面にも言語切替を置く。
 *     ★発表デモでの同時利用向けに、ログイン/新規登録をこの画面内でトグル切替する。
 *     別ルートに分けない理由: 発表中に聴衆が「まずログイン画面を開いてから登録画面へ
 *     移動する」という追加の1ステップを踏まなくて済むようにするため。
 * VI: Trang đăng nhập. pages chỉ lo "lắp ghép" (đặt component, chỉ định điều hướng).
 *     Nội dung đăng nhập giao cho LoginForm của features/auth, điều hướng giao cho router.
 *     ★Đặt cả nút đổi ngôn ngữ ở màn này để đổi được ngay cả khi chưa đăng nhập.
 *     ★Chuyển đổi đăng nhập/đăng ký ngay trong màn này, dùng cho việc nhiều người dùng
 *     đồng thời khi demo thuyết trình. Lý do không tách route riêng: để khán giả không
 *     phải tốn thêm 1 bước "mở màn đăng nhập rồi mới qua màn đăng ký" giữa buổi thuyết trình.
 */
import { useState } from 'react'

import { useNavigate } from 'react-router-dom'

import { LoginForm } from '@/features/auth/components/LoginForm'
import { SignupForm } from '@/features/auth/components/SignupForm'
import { useI18n } from '@/shared/i18n'
import { Card, LanguageSwitcher, PageContainer } from '@/shared/ui'

export function LoginPage() {
  const navigate = useNavigate()
  const { t } = useI18n()
  const [mode, setMode] = useState<'login' | 'signup'>('login')

  return (
    <PageContainer width="narrow" className="pt-16">
      <div className="flex justify-end">
        <LanguageSwitcher />
      </div>
      <Card>
        <h1 className="mb-4 text-lg font-semibold text-slate-800">
          {mode === 'login' ? t('auth.login.title') : t('auth.signup.title')}
        </h1>
        {/* JA: 成功したらトップへ / VI: Thành công thì về trang chủ */}
        {mode === 'login' ? (
          <LoginForm onSuccess={() => navigate('/')} />
        ) : (
          <SignupForm onSuccess={() => navigate('/')} />
        )}
        <button
          type="button"
          onClick={() => setMode(mode === 'login' ? 'signup' : 'login')}
          className="mt-4 w-full border-0 bg-transparent p-0 text-center text-sm text-teal-700 underline-offset-2 hover:underline"
        >
          {mode === 'login' ? t('auth.login.toSignup') : t('auth.signup.toLogin')}
        </button>
      </Card>
    </PageContainer>
  )
}
